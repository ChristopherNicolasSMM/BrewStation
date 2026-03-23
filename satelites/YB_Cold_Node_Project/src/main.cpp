#include <Arduino.h>
#include <ArduinoJson.h>
#include <DallasTemperature.h>
#include <LiquidCrystal.h>
#include <OneWire.h>
#include <Preferences.h>
#include <SPIFFS.h>
#include <WebServer.h>
#include <WiFi.h>

#include "AppConfig.h"

/**
 * =====================================================================================
 * YB Cold Node - Firmware base para ESP32
 * =====================================================================================
 * Objetivo deste firmware:
 * - Ler 1 a 2 sensores DS18B20
 * - Controlar 1 relé de refrigeração por histerese
 * - Exibir estado local em LCD 16x2 com keypad analógico
 * - Publicar portal web local para status e configuração
 * - Persistir parâmetros no NVS (Preferences)
 *
 * REGRAS DE MANUTENÇÃO PARA FUTUROS DESENVOLVEDORES
 * -------------------------------------------------
 * 1. Priorizar operação offline. O controle do relé não pode depender de Wi-Fi.
 * 2. Em qualquer falha crítica de leitura do sensor de controle, entrar em modo seguro:
 *    relé desligado e indicação local/portal do erro.
 * 3. Evitar delay() longos no loop principal. O firmware foi organizado por tarefas curtas.
 * 4. Toda nova configuração persistente deve passar por validação antes de salvar.
 * 5. Toda alteração de pinos deve ser concentrada em include/AppConfig.h.
 * 6. O shield LCD Keypad 16x2 é alimentado pelo pino 3V3 do ESP32 (nunca 5V/VIN).
 *    Com VCC=3.3V o keypad nunca excede 3.3V no ADC. Se o teclado responder errado,
 *    recalibre os thresholds em AppConfig.h seguindo as instruções lá descritas.
 * 7. O backlight é controlado via PWM no canal LEDC 0 (GPIO 32, shield D10).
 *    Em plataformas espressif32 >= 3.x o ledcSetup/ledcAttachPin foram depreciados;
 *    se houver erro de compilação, trocar por: ledcAttach(pin, freq, res) + ledcWrite(pin, duty).
 * 8. Se futuramente houver compressor real e não apenas teste de bancada, adicionar:
 *    - atraso mínimo entre partidas
 *    - tempo mínimo ligado/desligado
 *    - alarme de sensor e watchdog de congelamento/degelo
 *
 * OBSERVAÇÃO SOBRE O SHIELD LCD KEYPAD
 * -------------------------------------
 * O shield não encaixa diretamente no ESP32 (pinout diferente). Ligue por jumpers:
 *   Shield VCC → ESP32 3V3    Shield GND → ESP32 GND
 *   Shield D4  → GPIO 13      Shield D5  → GPIO 26
 *   Shield D6  → GPIO 25      Shield D7  → GPIO 33
 *   Shield D8  → GPIO 14      Shield D9  → GPIO 12
 *   Shield D10 → GPIO 32      Shield A0  → GPIO 34
 * Ver diagrama completo na documentação do projeto.
 */

namespace Constants {
  static constexpr uint8_t MAX_SENSORS = 2;
  static constexpr uint16_t LCD_COLUMNS = 16;
  static constexpr uint16_t LCD_ROWS = 2;
  static constexpr uint32_t SENSOR_DISCOVERY_INTERVAL_MS = 10000;
  static constexpr uint32_t DISPLAY_REFRESH_MS = 300;
  static constexpr uint32_t WIFI_RETRY_INTERVAL_MS = 15000;
  static constexpr uint32_t STATUS_BLINK_MS = 500;
  static constexpr uint32_t LONG_PRESS_MS = 900;
  static constexpr uint32_t KEY_DEBOUNCE_MS = 160;
  // Canal LEDC para backlight do LCD (0-15 disponíveis no ESP32)
  static constexpr uint8_t  LCD_LEDC_CHANNEL = 0;
}

enum class KeyCode : uint8_t {
  None,
  Right,
  Up,
  Down,
  Left,
  Select
};

enum class ScreenId : uint8_t {
  Home = 0,
  Sensors = 1,
  Network = 2,
  Config = 3,
  Diagnostics = 4,
  EditSetpoint = 5,
  EditHysteresis = 6
};

struct SensorState {
  DeviceAddress address{};
  bool present = false;
  bool valid = false;
  float temperatureC = NAN;
  uint32_t lastReadMs = 0;
  char addressText[24] = {0};
};

struct RuntimeState {
  SensorState sensors[Constants::MAX_SENSORS];
  uint8_t sensorCount = 0;
  bool relayOn = false;
  bool wifiConnected = false;
  bool apMode = false;
  bool sensorAlarm = false;
  bool editing = false;
  bool lastControlSensorValid = false;
  uint32_t lastSampleMs = 0;
  uint32_t lastDisplayMs = 0;
  uint32_t lastWifiAttemptMs = 0;
  uint32_t lastDiscoveryMs = 0;
  uint32_t relaySwitchMs = 0;
  uint32_t bootMs = 0;
  ScreenId currentScreen = ScreenId::Home;
} runtimeState;

AppConfig config;
Preferences preferences;
WebServer server(80);
OneWire oneWire(DefaultPins::TEMP_ONEWIRE_PIN);
DallasTemperature ds18b20(&oneWire);
LiquidCrystal lcd(
  DefaultPins::LCD_RS,
  DefaultPins::LCD_EN,
  DefaultPins::LCD_D4,
  DefaultPins::LCD_D5,
  DefaultPins::LCD_D6,
  DefaultPins::LCD_D7
);

static String logBuffer[24];
static uint8_t logHead = 0;

void addLog(const String &message) {
  Serial.println(message);
  logBuffer[logHead] = message;
  logHead = (logHead + 1) % 24;
}

String makeUptimeString() {
  const uint32_t seconds = (millis() - runtimeState.bootMs) / 1000;
  const uint32_t hours = seconds / 3600;
  const uint32_t minutes = (seconds % 3600) / 60;
  const uint32_t secs = seconds % 60;
  char buffer[24];
  snprintf(buffer, sizeof(buffer), "%02lu:%02lu:%02lu",
           static_cast<unsigned long>(hours),
           static_cast<unsigned long>(minutes),
           static_cast<unsigned long>(secs));
  return String(buffer);
}

String formatTemperature(float tempC) {
  if (isnan(tempC)) {
    return "ERR";
  }
  char buffer[12];
  snprintf(buffer, sizeof(buffer), "%.1fC", tempC);
  return String(buffer);
}

void setRelayState(bool on) {
  runtimeState.relayOn = on;
  runtimeState.relaySwitchMs = millis();

  const bool outputLevel = config.relayActiveHigh ? on : !on;
  digitalWrite(DefaultPins::RELAY_PIN, outputLevel ? HIGH : LOW);
}

void applyFailsafeRelayOff() {
  setRelayState(false);
  runtimeState.sensorAlarm = true;
}

void validateConfig() {
  if (config.deviceName.isEmpty()) {
    config.deviceName = "yb-cold-node-01";
  }
  if (config.apSsid.isEmpty()) {
    config.apSsid = "YB-Cold-Node-Setup";
  }
  if (config.apPassword.length() < 8) {
    config.apPassword = "yeastbank123";
  }
  if (config.wifiHostname.isEmpty()) {
    config.wifiHostname = "yb-cold-node";
  }
  config.setpointC = constrain(config.setpointC, -30.0f, 30.0f);
  config.hysteresisC = constrain(config.hysteresisC, 0.2f, 10.0f);
  config.sampleIntervalMs = constrain(config.sampleIntervalMs, 500U, 10000U);
  config.lcdBacklightPercent = constrain(config.lcdBacklightPercent, static_cast<uint16_t>(0), static_cast<uint16_t>(100));
  config.controlSensorIndex = constrain(config.controlSensorIndex, static_cast<uint8_t>(0), static_cast<uint8_t>(Constants::MAX_SENSORS - 1));

  // Garantir ordem crescente dos thresholds do teclado analógico.
  const uint16_t baseRight = constrain(config.keyRightMax, static_cast<uint16_t>(50), static_cast<uint16_t>(800));
  const uint16_t baseUp = max<uint16_t>(baseRight + 50, constrain(config.keyUpMax, static_cast<uint16_t>(300), static_cast<uint16_t>(1500)));
  const uint16_t baseDown = max<uint16_t>(baseUp + 50, constrain(config.keyDownMax, static_cast<uint16_t>(800), static_cast<uint16_t>(2400)));
  const uint16_t baseLeft = max<uint16_t>(baseDown + 50, constrain(config.keyLeftMax, static_cast<uint16_t>(1200), static_cast<uint16_t>(3200)));
  const uint16_t baseSelect = max<uint16_t>(baseLeft + 50, constrain(config.keySelectMax, static_cast<uint16_t>(1800), static_cast<uint16_t>(3900)));

  config.keyRightMax  = baseRight;
  config.keyUpMax     = baseUp;
  config.keyDownMax   = baseDown;
  config.keyLeftMax   = baseLeft;
  config.keySelectMax = baseSelect;
}

void loadConfig() {
  preferences.begin("yb-cold-node", true);

  config.deviceName     = preferences.getString("dev_name",  config.deviceName);
  config.apSsid         = preferences.getString("ap_ssid",   config.apSsid);
  config.apPassword     = preferences.getString("ap_pass",   config.apPassword);
  config.wifiSsid       = preferences.getString("wifi_ssid", config.wifiSsid);
  config.wifiPassword   = preferences.getString("wifi_pass", config.wifiPassword);
  config.wifiHostname   = preferences.getString("hostname",  config.wifiHostname);
  config.setpointC      = preferences.getFloat("setpoint",   config.setpointC);
  config.hysteresisC    = preferences.getFloat("hysteresis", config.hysteresisC);
  config.relayActiveHigh  = preferences.getBool("relay_ah",  config.relayActiveHigh);
  config.relayEnabled     = preferences.getBool("relay_en",  config.relayEnabled);
  config.controlSensorIndex = preferences.getUChar("ctrl_sensor", config.controlSensorIndex);
  config.sampleIntervalMs   = preferences.getUShort("sample_ms",  config.sampleIntervalMs);
  config.lcdBacklightPercent = preferences.getUShort("lcd_pct",   config.lcdBacklightPercent);
  config.beepOnAlarm    = preferences.getBool("beep_alarm",  config.beepOnAlarm);
  config.keyRightMax    = preferences.getUShort("key_r",     config.keyRightMax);
  config.keyUpMax       = preferences.getUShort("key_u",     config.keyUpMax);
  config.keyDownMax     = preferences.getUShort("key_d",     config.keyDownMax);
  config.keyLeftMax     = preferences.getUShort("key_l",     config.keyLeftMax);
  config.keySelectMax   = preferences.getUShort("key_s",     config.keySelectMax);

  preferences.end();
  validateConfig();
}

void saveConfig() {
  validateConfig();

  preferences.begin("yb-cold-node", false);
  preferences.putString("dev_name",    config.deviceName);
  preferences.putString("ap_ssid",     config.apSsid);
  preferences.putString("ap_pass",     config.apPassword);
  preferences.putString("wifi_ssid",   config.wifiSsid);
  preferences.putString("wifi_pass",   config.wifiPassword);
  preferences.putString("hostname",    config.wifiHostname);
  preferences.putFloat("setpoint",     config.setpointC);
  preferences.putFloat("hysteresis",   config.hysteresisC);
  preferences.putBool("relay_ah",      config.relayActiveHigh);
  preferences.putBool("relay_en",      config.relayEnabled);
  preferences.putUChar("ctrl_sensor",  config.controlSensorIndex);
  preferences.putUShort("sample_ms",   config.sampleIntervalMs);
  preferences.putUShort("lcd_pct",     config.lcdBacklightPercent);
  preferences.putBool("beep_alarm",    config.beepOnAlarm);
  preferences.putUShort("key_r",       config.keyRightMax);
  preferences.putUShort("key_u",       config.keyUpMax);
  preferences.putUShort("key_d",       config.keyDownMax);
  preferences.putUShort("key_l",       config.keyLeftMax);
  preferences.putUShort("key_s",       config.keySelectMax);
  preferences.end();
}

void clearConfig() {
  preferences.begin("yb-cold-node", false);
  preferences.clear();
  preferences.end();
}

/**
 * Aplica o brilho configurado (lcdBacklightPercent) no backlight do LCD.
 *
 * O backlight é controlado via PWM no canal LEDC 0 (GPIO LCD_BACKLIGHT_PIN).
 * Deve ser chamado após qualquer alteração de lcdBacklightPercent.
 *
 * COMPAT: ledcSetup/ledcAttachPin funcionam em espressif32 < 3.x.
 * Para espressif32 >= 3.x substituir por:
 *   ledcAttach(DefaultPins::LCD_BACKLIGHT_PIN, 1000, 8);
 *   ledcWrite(DefaultPins::LCD_BACKLIGHT_PIN, duty);
 */
void applyBacklightBrightness() {
  const uint8_t duty = static_cast<uint8_t>(
    (static_cast<uint32_t>(config.lcdBacklightPercent) * 255UL) / 100UL
  );
  ledcWrite(Constants::LCD_LEDC_CHANNEL, duty);
}

String deviceAddressToString(const DeviceAddress &address) {
  char buffer[24];
  snprintf(buffer, sizeof(buffer),
           "%02X%02X%02X%02X%02X%02X%02X%02X",
           address[0], address[1], address[2], address[3],
           address[4], address[5], address[6], address[7]);
  return String(buffer);
}

void discoverSensors() {
  runtimeState.sensorCount = min<uint8_t>(ds18b20.getDeviceCount(), Constants::MAX_SENSORS);

  for (uint8_t i = 0; i < Constants::MAX_SENSORS; ++i) {
    runtimeState.sensors[i].present = false;
    runtimeState.sensors[i].valid = false;
    runtimeState.sensors[i].temperatureC = NAN;
    runtimeState.sensors[i].addressText[0] = '\0';
  }

  for (uint8_t i = 0; i < runtimeState.sensorCount; ++i) {
    if (ds18b20.getAddress(runtimeState.sensors[i].address, i)) {
      runtimeState.sensors[i].present = true;
      ds18b20.setResolution(runtimeState.sensors[i].address, 12);
      const String addrText = deviceAddressToString(runtimeState.sensors[i].address);
      addrText.toCharArray(runtimeState.sensors[i].addressText, sizeof(runtimeState.sensors[i].addressText));
    }
  }

  addLog("[sensor] sensores detectados: " + String(runtimeState.sensorCount));
}

void readSensors() {
  ds18b20.requestTemperatures();
  runtimeState.sensorAlarm = false;

  for (uint8_t i = 0; i < runtimeState.sensorCount; ++i) {
    float t = ds18b20.getTempC(runtimeState.sensors[i].address);
    runtimeState.sensors[i].lastReadMs = millis();

    if (t == DEVICE_DISCONNECTED_C || t < -80.0f || t > 125.0f) {
      runtimeState.sensors[i].valid = false;
      runtimeState.sensors[i].temperatureC = NAN;
      runtimeState.sensorAlarm = true;
      continue;
    }

    runtimeState.sensors[i].valid = true;
    runtimeState.sensors[i].temperatureC = t;
  }
}

void runTemperatureControl() {
  if (!config.relayEnabled) {
    setRelayState(false);
    runtimeState.lastControlSensorValid = false;
    return;
  }

  if (config.controlSensorIndex >= runtimeState.sensorCount) {
    applyFailsafeRelayOff();
    runtimeState.lastControlSensorValid = false;
    return;
  }

  const SensorState &controlSensor = runtimeState.sensors[config.controlSensorIndex];
  if (!controlSensor.present || !controlSensor.valid || isnan(controlSensor.temperatureC)) {
    applyFailsafeRelayOff();
    runtimeState.lastControlSensorValid = false;
    return;
  }

  runtimeState.lastControlSensorValid = true;
  runtimeState.sensorAlarm = false;

  const float upperThreshold = config.setpointC + (config.hysteresisC / 2.0f);
  const float lowerThreshold = config.setpointC - (config.hysteresisC / 2.0f);
  const float currentTemp = controlSensor.temperatureC;

  if (!runtimeState.relayOn && currentTemp >= upperThreshold) {
    setRelayState(true);
  } else if (runtimeState.relayOn && currentTemp <= lowerThreshold) {
    setRelayState(false);
  }
}

KeyCode readKeypad() {
  static uint32_t lastAcceptedMs = 0;
  const int raw = analogRead(DefaultPins::KEYPAD_ADC_PIN);

  KeyCode key = KeyCode::None;
  if (raw <= static_cast<int>(config.keyRightMax)) {
    key = KeyCode::Right;
  } else if (raw <= static_cast<int>(config.keyUpMax)) {
    key = KeyCode::Up;
  } else if (raw <= static_cast<int>(config.keyDownMax)) {
    key = KeyCode::Down;
  } else if (raw <= static_cast<int>(config.keyLeftMax)) {
    key = KeyCode::Left;
  } else if (raw <= static_cast<int>(config.keySelectMax)) {
    key = KeyCode::Select;
  }

  if (key == KeyCode::None) {
    return KeyCode::None;
  }

  const uint32_t now = millis();
  if (now - lastAcceptedMs < Constants::KEY_DEBOUNCE_MS) {
    return KeyCode::None;
  }

  lastAcceptedMs = now;
  return key;
}

String ipToString(IPAddress ip) {
  return String(ip[0]) + "." + String(ip[1]) + "." + String(ip[2]) + "." + String(ip[3]);
}

void startAccessPoint() {
  WiFi.mode(WIFI_AP_STA);
  runtimeState.apMode = true;
  WiFi.softAP(config.apSsid.c_str(), config.apPassword.c_str());
  addLog("[wifi] AP ativo em " + ipToString(WiFi.softAPIP()));
}

void connectWifiIfConfigured() {
  if (config.wifiSsid.isEmpty()) {
    // Logar apenas uma vez — evitar spam no Serial quando sem SSID configurado
    static bool _loggedOnce = false;
    if (!_loggedOnce) {
      addLog("[wifi] sem SSID salvo, mantendo somente AP");
      _loggedOnce = true;
    }
    return;
  }

  if (WiFi.status() == WL_CONNECTED) {
    runtimeState.wifiConnected = true;
    return;
  }

  const uint32_t now = millis();
  if (now - runtimeState.lastWifiAttemptMs < Constants::WIFI_RETRY_INTERVAL_MS) {
    return;
  }

  runtimeState.lastWifiAttemptMs = now;
  runtimeState.wifiConnected = false;

  WiFi.setHostname(config.wifiHostname.c_str());
  WiFi.begin(config.wifiSsid.c_str(), config.wifiPassword.c_str());
  addLog("[wifi] tentando conectar em " + config.wifiSsid);
}

void updateWifiState() {
  const wl_status_t status = WiFi.status();
  runtimeState.wifiConnected = (status == WL_CONNECTED);
}

void drawLcdLine(uint8_t row, const String &text) {
  String padded = text;
  if (padded.length() < Constants::LCD_COLUMNS) {
    while (padded.length() < Constants::LCD_COLUMNS) {
      padded += ' ';
    }
  }
  lcd.setCursor(0, row);
  lcd.print(padded.substring(0, Constants::LCD_COLUMNS));
}

void renderScreenHome() {
  const float primary = runtimeState.sensorCount > 0 ? runtimeState.sensors[0].temperatureC : NAN;
  String line1 = "T1 " + formatTemperature(primary);
  if (runtimeState.sensorCount > 1) {
    line1 += " T2 " + formatTemperature(runtimeState.sensors[1].temperatureC);
  }
  drawLcdLine(0, line1);

  String line2 = runtimeState.relayOn ? "RELE:ON  " : "RELE:OFF ";
  line2 += "SP:" + String(config.setpointC, 1);
  drawLcdLine(1, line2);
}

void renderScreenSensors() {
  String line1 = "Sensores:" + String(runtimeState.sensorCount);
  drawLcdLine(0, line1);

  if (runtimeState.sensorCount == 0) {
    drawLcdLine(1, "Nenhum DS18B20");
    return;
  }

  const SensorState &control = runtimeState.sensors[config.controlSensorIndex];
  String line2 = "CTRL S" + String(config.controlSensorIndex + 1) + " " + formatTemperature(control.temperatureC);
  drawLcdLine(1, line2);
}

void renderScreenNetwork() {
  drawLcdLine(0, runtimeState.wifiConnected ? "WiFi OK" : "WiFi offline");
  if (runtimeState.wifiConnected) {
    drawLcdLine(1, ipToString(WiFi.localIP()));
  } else {
    drawLcdLine(1, ipToString(WiFi.softAPIP()));
  }
}

void renderScreenConfig() {
  drawLcdLine(0, "SP:" + String(config.setpointC, 1) + " H:" + String(config.hysteresisC, 1));
  drawLcdLine(1, "SEL editar   >");
}

void renderScreenDiagnostics() {
  drawLcdLine(0, "UP:" + makeUptimeString());
  drawLcdLine(1, runtimeState.sensorAlarm ? "ALARME SENSOR" : "Sistema normal");
}

void renderEditSetpoint() {
  drawLcdLine(0, "Editar Setpoint");
  drawLcdLine(1, "< >  " + String(config.setpointC, 1) + "C  SEL");
}

void renderEditHysteresis() {
  drawLcdLine(0, "Editar Hist.");
  drawLcdLine(1, "< >  " + String(config.hysteresisC, 1) + "C  SEL");
}

void updateDisplay() {
  const uint32_t now = millis();
  if (now - runtimeState.lastDisplayMs < Constants::DISPLAY_REFRESH_MS) {
    return;
  }
  runtimeState.lastDisplayMs = now;

  switch (runtimeState.currentScreen) {
    case ScreenId::Home:          renderScreenHome();      break;
    case ScreenId::Sensors:       renderScreenSensors();   break;
    case ScreenId::Network:       renderScreenNetwork();   break;
    case ScreenId::Config:        renderScreenConfig();    break;
    case ScreenId::Diagnostics:   renderScreenDiagnostics(); break;
    case ScreenId::EditSetpoint:  renderEditSetpoint();    break;
    case ScreenId::EditHysteresis:renderEditHysteresis();  break;
  }
}

void cycleScreen(int delta) {
  if (runtimeState.currentScreen == ScreenId::EditSetpoint || runtimeState.currentScreen == ScreenId::EditHysteresis) {
    return;
  }

  int next = static_cast<int>(runtimeState.currentScreen) + delta;
  if (next < static_cast<int>(ScreenId::Home)) {
    next = static_cast<int>(ScreenId::Diagnostics);
  }
  if (next > static_cast<int>(ScreenId::Diagnostics)) {
    next = static_cast<int>(ScreenId::Home);
  }
  runtimeState.currentScreen = static_cast<ScreenId>(next);
}

void handleLocalButtons() {
  const KeyCode key = readKeypad();
  if (key == KeyCode::None) {
    return;
  }

  if (runtimeState.currentScreen == ScreenId::EditSetpoint) {
    if (key == KeyCode::Left) {
      config.setpointC -= 0.1f;
      validateConfig();
    } else if (key == KeyCode::Right) {
      config.setpointC += 0.1f;
      validateConfig();
    } else if (key == KeyCode::Select) {
      saveConfig();
      runtimeState.currentScreen = ScreenId::Config;
      addLog("[cfg] setpoint salvo");
    }
    return;
  }

  if (runtimeState.currentScreen == ScreenId::EditHysteresis) {
    if (key == KeyCode::Left) {
      config.hysteresisC -= 0.1f;
      validateConfig();
    } else if (key == KeyCode::Right) {
      config.hysteresisC += 0.1f;
      validateConfig();
    } else if (key == KeyCode::Select) {
      saveConfig();
      runtimeState.currentScreen = ScreenId::Config;
      addLog("[cfg] histerese salva");
    }
    return;
  }

  switch (key) {
    case KeyCode::Left:
      cycleScreen(-1);
      break;
    case KeyCode::Right:
      cycleScreen(1);
      break;
    case KeyCode::Up:
      if (runtimeState.currentScreen == ScreenId::Config) {
        runtimeState.currentScreen = ScreenId::EditSetpoint;
      }
      break;
    case KeyCode::Down:
      if (runtimeState.currentScreen == ScreenId::Config) {
        runtimeState.currentScreen = ScreenId::EditHysteresis;
      }
      break;
    case KeyCode::Select:
      if (runtimeState.currentScreen == ScreenId::Diagnostics) {
        discoverSensors();
      }
      break;
    case KeyCode::None:
      break;
  }
}

void sendJsonOk(JsonDocument &doc) {
  String payload;
  serializeJson(doc, payload);
  server.send(200, "application/json", payload);
}

bool parseJsonBody(JsonDocument &doc) {
  if (!server.hasArg("plain")) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"Body JSON ausente\"}");
    return false;
  }

  DeserializationError error = deserializeJson(doc, server.arg("plain"));
  if (error) {
    server.send(400, "application/json", "{\"ok\":false,\"error\":\"JSON inválido\"}");
    return false;
  }
  return true;
}

/*
void handleApiStatus() {
  JsonDocument doc;
  doc["ok"] = true;
  doc["device_name"] = config.deviceName;
  doc["uptime"] = makeUptimeString();
  doc["wifi_connected"] = runtimeState.wifiConnected;
  doc["ap_mode"] = runtimeState.apMode;
  doc["wifi_ip"] = runtimeState.wifiConnected ? ipToString(WiFi.localIP()) : "";
  doc["ap_ip"] = ipToString(WiFi.softAPIP());
  doc["relay_on"] = runtimeState.relayOn;
  doc["relay_enabled"] = config.relayEnabled;
  doc["sensor_alarm"] = runtimeState.sensorAlarm;
  doc["setpoint_c"] = config.setpointC;
  doc["hysteresis_c"] = config.hysteresisC;
  doc["control_sensor_index"] = config.controlSensorIndex;

  JsonArray sensors = doc["sensors"].to<JsonArray>();
  for (uint8_t i = 0; i < runtimeState.sensorCount; ++i) {
    JsonObject item = sensors.add<JsonObject>();
    item["index"] = i;
    item["present"] = runtimeState.sensors[i].present;
    item["valid"] = runtimeState.sensors[i].valid;
    item["temperature_c"] = runtimeState.sensors[i].valid ? runtimeState.sensors[i].temperatureC : nullptr;
    item["address"] = runtimeState.sensors[i].addressText;
  }

  sendJsonOk(doc);
}
*/

void handleApiStatus() {
  JsonDocument doc;
  doc["ok"] = true;
  doc["device_name"] = config.deviceName;
  doc["uptime"] = makeUptimeString();
  doc["wifi_connected"] = runtimeState.wifiConnected;
  doc["ap_mode"] = runtimeState.apMode;
  doc["wifi_ip"] = runtimeState.wifiConnected ? ipToString(WiFi.localIP()) : "";
  doc["ap_ip"] = ipToString(WiFi.softAPIP());
  doc["relay_on"] = runtimeState.relayOn;
  doc["relay_enabled"] = config.relayEnabled;
  doc["sensor_alarm"] = runtimeState.sensorAlarm;
  doc["setpoint_c"] = config.setpointC;
  doc["hysteresis_c"] = config.hysteresisC;
  doc["control_sensor_index"] = config.controlSensorIndex;

  JsonArray sensors = doc["sensors"].to<JsonArray>();
  for (uint8_t i = 0; i < runtimeState.sensorCount; ++i) {
    JsonObject item = sensors.add<JsonObject>();
    item["index"] = i;
    item["present"] = runtimeState.sensors[i].present;
    item["valid"] = runtimeState.sensors[i].valid;
    
    // Corrigido: só adiciona temperature_c se for válido
    if (runtimeState.sensors[i].valid) {
      item["temperature_c"] = runtimeState.sensors[i].temperatureC;
    }
    // Opcional: adicionar campo como null explicitamente
    // else {
    //   item["temperature_c"] = nullptr;
    // }
    
    item["address"] = runtimeState.sensors[i].addressText;
  }

  sendJsonOk(doc);
}


void handleApiConfigGet() {
  JsonDocument doc;
  doc["ok"] = true;
  doc["device_name"] = config.deviceName;
  doc["ap_ssid"] = config.apSsid;
  doc["wifi_ssid"] = config.wifiSsid;
  doc["wifi_hostname"] = config.wifiHostname;
  doc["setpoint_c"] = config.setpointC;
  doc["hysteresis_c"] = config.hysteresisC;
  doc["relay_active_high"] = config.relayActiveHigh;
  doc["relay_enabled"] = config.relayEnabled;
  doc["control_sensor_index"] = config.controlSensorIndex;
  doc["sample_interval_ms"] = config.sampleIntervalMs;
  doc["lcd_backlight_percent"] = config.lcdBacklightPercent;   // ← adicionado
  doc["beep_on_alarm"] = config.beepOnAlarm;
  doc["keypad_thresholds"]["right_max"]  = config.keyRightMax;
  doc["keypad_thresholds"]["up_max"]     = config.keyUpMax;
  doc["keypad_thresholds"]["down_max"]   = config.keyDownMax;
  doc["keypad_thresholds"]["left_max"]   = config.keyLeftMax;
  doc["keypad_thresholds"]["select_max"] = config.keySelectMax;
  sendJsonOk(doc);
}

void handleApiConfigTemperature() {
  JsonDocument doc;
  if (!parseJsonBody(doc)) {
    return;
  }

  if (doc["setpoint_c"].is<float>()) {
    config.setpointC = doc["setpoint_c"].as<float>();
  }
  if (doc["hysteresis_c"].is<float>()) {
    config.hysteresisC = doc["hysteresis_c"].as<float>();
  }
  if (doc["control_sensor_index"].is<uint8_t>()) {
    config.controlSensorIndex = doc["control_sensor_index"].as<uint8_t>();
  }
  if (doc["relay_enabled"].is<bool>()) {
    config.relayEnabled = doc["relay_enabled"].as<bool>();
  }
  if (doc["relay_active_high"].is<bool>()) {
    config.relayActiveHigh = doc["relay_active_high"].as<bool>();
  }
  if (doc["sample_interval_ms"].is<uint16_t>()) {
    config.sampleIntervalMs = doc["sample_interval_ms"].as<uint16_t>();
  }

  saveConfig();
  addLog("[api] config de temperatura atualizada");
  handleApiConfigGet();
}

void handleApiConfigWifi() {
  JsonDocument doc;
  if (!parseJsonBody(doc)) {
    return;
  }

  if (doc["wifi_ssid"].is<String>()) {
    config.wifiSsid = doc["wifi_ssid"].as<String>();
  }
  if (doc["wifi_password"].is<String>()) {
    config.wifiPassword = doc["wifi_password"].as<String>();
  }
  if (doc["wifi_hostname"].is<String>()) {
    config.wifiHostname = doc["wifi_hostname"].as<String>();
  }
  if (doc["ap_ssid"].is<String>()) {
    config.apSsid = doc["ap_ssid"].as<String>();
  }
  if (doc["ap_password"].is<String>()) {
    config.apPassword = doc["ap_password"].as<String>();
  }

  saveConfig();
  addLog("[api] config wifi atualizada");
  WiFi.disconnect(true, true);
  connectWifiIfConfigured();
  handleApiConfigGet();
}

void handleApiConfigDevice() {
  JsonDocument doc;
  if (!parseJsonBody(doc)) {
    return;
  }

  if (doc["device_name"].is<String>()) {
    config.deviceName = doc["device_name"].as<String>();
  }
  if (doc["beep_on_alarm"].is<bool>()) {
    config.beepOnAlarm = doc["beep_on_alarm"].as<bool>();
  }
  // ── Brilho do backlight ──────────────────────────────────────────────────
  // Aceita lcd_backlight_percent (0-100). Aplica imediatamente via PWM.
  if (doc["lcd_backlight_percent"].is<uint16_t>()) {
    config.lcdBacklightPercent = doc["lcd_backlight_percent"].as<uint16_t>();
  }
  // ── Thresholds do keypad ─────────────────────────────────────────────────
  if (doc["keypad_thresholds"].is<JsonObject>()) {
    JsonObject thresholds = doc["keypad_thresholds"].as<JsonObject>();
    if (thresholds["right_max"].is<uint16_t>())  config.keyRightMax  = thresholds["right_max"].as<uint16_t>();
    if (thresholds["up_max"].is<uint16_t>())     config.keyUpMax     = thresholds["up_max"].as<uint16_t>();
    if (thresholds["down_max"].is<uint16_t>())   config.keyDownMax   = thresholds["down_max"].as<uint16_t>();
    if (thresholds["left_max"].is<uint16_t>())   config.keyLeftMax   = thresholds["left_max"].as<uint16_t>();
    if (thresholds["select_max"].is<uint16_t>()) config.keySelectMax = thresholds["select_max"].as<uint16_t>();
  }

  saveConfig();
  applyBacklightBrightness();   // ← aplica PWM imediatamente
  addLog("[api] config do dispositivo atualizada");
  handleApiConfigGet();
}

void handleApiLogs() {
  JsonDocument doc;
  doc["ok"] = true;
  JsonArray logs = doc["logs"].to<JsonArray>();
  for (uint8_t i = 0; i < 24; ++i) {
    const uint8_t index = (logHead + i) % 24;
    if (!logBuffer[index].isEmpty()) {
      logs.add(logBuffer[index]);
    }
  }
  sendJsonOk(doc);
}

void handleApiActionReboot() {
  server.send(200, "application/json", "{\"ok\":true,\"message\":\"Reiniciando\"}");
  delay(200);
  ESP.restart();
}

void handleApiActionFactoryReset() {
  clearConfig();
  server.send(200, "application/json", "{\"ok\":true,\"message\":\"Configuração apagada. Reiniciando\"}");
  delay(200);
  ESP.restart();
}

void handleRootPage() {
  File file = SPIFFS.open("/index.html", FILE_READ);
  if (!file) {
    server.send(500, "text/plain", "index.html nao encontrado em SPIFFS");
    return;
  }
  server.streamFile(file, "text/html; charset=utf-8");
  file.close();
}

void handleStaticFile(const char *path, const char *contentType) {
  File file = SPIFFS.open(path, FILE_READ);
  if (!file) {
    server.send(404, "text/plain", "Arquivo nao encontrado");
    return;
  }
  server.streamFile(file, contentType);
  file.close();
}

void setupWebServer() {
  server.on("/",           HTTP_GET,  handleRootPage);
  server.on("/index.html", HTTP_GET,  handleRootPage);
  server.on("/script.js",  HTTP_GET,  []() { handleStaticFile("/script.js",  "application/javascript"); });
  server.on("/style.css",  HTTP_GET,  []() { handleStaticFile("/style.css",  "text/css"); });

  server.on("/api/status",                HTTP_GET,  handleApiStatus);
  server.on("/api/config",                HTTP_GET,  handleApiConfigGet);
  server.on("/api/config/temperature",    HTTP_POST, handleApiConfigTemperature);
  server.on("/api/config/wifi",           HTTP_POST, handleApiConfigWifi);
  server.on("/api/config/device",         HTTP_POST, handleApiConfigDevice);
  server.on("/api/logs",                  HTTP_GET,  handleApiLogs);
  server.on("/api/action/reboot",         HTTP_POST, handleApiActionReboot);
  server.on("/api/action/factory-reset",  HTTP_POST, handleApiActionFactoryReset);
  server.onNotFound([]() {
    server.send(404, "application/json", "{\"ok\":false,\"error\":\"Endpoint nao encontrado\"}");
  });
  server.begin();
  addLog("[http] servidor web iniciado na porta 80");
}

void setupFilesystem() {
  if (!SPIFFS.begin(true)) {
    addLog("[fs] falha ao montar SPIFFS");
    return;
  }
  addLog("[fs] SPIFFS montado");
}

void setupHardware() {
  pinMode(DefaultPins::RELAY_PIN,      OUTPUT);
  pinMode(DefaultPins::STATUS_LED_PIN, OUTPUT);
  pinMode(DefaultPins::BUZZER_PIN,     OUTPUT);
  analogReadResolution(12);
  analogSetPinAttenuation(DefaultPins::KEYPAD_ADC_PIN, ADC_11db);

  // ── Backlight PWM ────────────────────────────────────────────────────────
  // Canal LEDC 0, frequência 1 kHz, resolução 8-bit (duty 0-255).
  // Shield D10 → GPIO 32. Com duty=255 o backlight fica em 100%.
  //
  // Se usar espressif32 >= 3.x e receber erro de compilação nesta seção,
  // substitua as três linhas abaixo por:
  //   ledcAttach(DefaultPins::LCD_BACKLIGHT_PIN, 1000, 8);
  //   ledcWrite(DefaultPins::LCD_BACKLIGHT_PIN, 255);
  ledcSetup(Constants::LCD_LEDC_CHANNEL, 1000, 8);
  ledcAttachPin(DefaultPins::LCD_BACKLIGHT_PIN, Constants::LCD_LEDC_CHANNEL);
  ledcWrite(Constants::LCD_LEDC_CHANNEL, 255);   // liga backlight imediatamente

  lcd.begin(Constants::LCD_COLUMNS, Constants::LCD_ROWS);
  lcd.clear();
  drawLcdLine(0, "YB Cold Node");
  drawLcdLine(1, "Inicializando");

  setRelayState(false);
}

void setupSensors() {
  ds18b20.begin();
  discoverSensors();
}

void maybeBeepAlarm() {
  if (!config.beepOnAlarm || !runtimeState.sensorAlarm) {
    digitalWrite(DefaultPins::BUZZER_PIN, LOW);
    return;
  }

  const bool pulse = ((millis() / 180) % 2) == 0;
  digitalWrite(DefaultPins::BUZZER_PIN, pulse ? HIGH : LOW);
}

void blinkStatusLed() {
  const bool on = ((millis() / Constants::STATUS_BLINK_MS) % 2) == 0;
  if (runtimeState.sensorAlarm) {
    digitalWrite(DefaultPins::STATUS_LED_PIN, on ? HIGH : LOW);
    return;
  }
  if (runtimeState.wifiConnected) {
    digitalWrite(DefaultPins::STATUS_LED_PIN, HIGH);
    return;
  }
  digitalWrite(DefaultPins::STATUS_LED_PIN, on ? HIGH : LOW);
}

void setup() {
  Serial.begin(115200);
  delay(250);
  runtimeState.bootMs = millis();

  setupHardware();
  loadConfig();
  applyBacklightBrightness();   // ← aplica brilho persistido logo após carregar config

  setupFilesystem();
  setupSensors();

  startAccessPoint();
  connectWifiIfConfigured();
  setupWebServer();

  addLog("[boot] firmware pronto");
}

void loop() {
  server.handleClient();
  updateWifiState();
  connectWifiIfConfigured();

  const uint32_t now = millis();
  if (now - runtimeState.lastSampleMs >= config.sampleIntervalMs) {
    runtimeState.lastSampleMs = now;
    readSensors();
    runTemperatureControl();
  }

  if (now - runtimeState.lastDiscoveryMs >= Constants::SENSOR_DISCOVERY_INTERVAL_MS) {
    runtimeState.lastDiscoveryMs = now;
    discoverSensors();
  }

  handleLocalButtons();
  updateDisplay();
  maybeBeepAlarm();
  blinkStatusLed();
}
