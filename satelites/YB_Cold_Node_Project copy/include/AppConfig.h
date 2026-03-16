#pragma once

#include <Arduino.h>

/**
 * Regras deste arquivo
 * --------------------
 * 1. Manter aqui apenas configurações persistentes e defaults do equipamento.
 * 2. Evitar lógica complexa no header. A implementação e validação ficam no main.cpp.
 * 3. Se novos campos forem adicionados, atualizar:
 *    - função loadConfig()
 *    - função saveConfig()
 *    - endpoint GET /api/config
 *    - endpoints POST relacionados
 *    - telas locais do LCD, se fizer sentido para operação offline
 */

struct AppConfig {
  // Identidade do dispositivo
  String deviceName = "yb-cold-node-01";
  String apSsid = "YB-Cold-Node-Setup";
  String apPassword = "yeastbank123";

  // Wi-Fi de infraestrutura
  String wifiSsid = "";
  String wifiPassword = "";
  String wifiHostname = "yb-cold-node";

  // Controle térmico
  float setpointC = 4.0f;
  float hysteresisC = 1.0f;
  bool relayActiveHigh = true;
  bool relayEnabled = true;
  uint8_t controlSensorIndex = 0;

  // Hardware / leitura local
  uint16_t sampleIntervalMs = 2000;
  uint16_t lcdBacklightPercent = 100;
  bool beepOnAlarm = false;

  // Thresholds do keypad analógico 16x2 shield.
  // Os valores são pensados para ADC 12-bit do ESP32 (0..4095) com shield típico.
  // Ajuste no campo caso o teclado do lote comprado use outra escada resistiva.
  uint16_t keyRightMax = 300;
  uint16_t keyUpMax = 900;
  uint16_t keyDownMax = 1700;
  uint16_t keyLeftMax = 2600;
  uint16_t keySelectMax = 3500;
};

namespace DefaultPins {
  // Barramento OneWire dos DS18B20
  static constexpr uint8_t TEMP_ONEWIRE_PIN = 4;

  // Relé principal de refrigeração
  static constexpr uint8_t RELAY_PIN = 27;

  // LCD 16x2 em modo 4-bit (compatível com LCD Keypad 1602 cabeado no ESP32)
  static constexpr uint8_t LCD_RS = 14;
  static constexpr uint8_t LCD_EN = 12;
  static constexpr uint8_t LCD_D4 = 13;
  static constexpr uint8_t LCD_D5 = 26;
  static constexpr uint8_t LCD_D6 = 25;
  static constexpr uint8_t LCD_D7 = 33;

  // Pino analógico do keypad resistivo do shield/display.
  static constexpr uint8_t KEYPAD_ADC_PIN = 34;

  // Saídas opcionais
  static constexpr uint8_t BUZZER_PIN = 15;
  static constexpr uint8_t STATUS_LED_PIN = 2;
}
