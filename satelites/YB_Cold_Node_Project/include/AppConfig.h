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
 *
 * ==========================================================================
 * NOTA SOBRE ALIMENTAÇÃO DO SHIELD DFR0009 COM ESP32
 * ==========================================================================
 *
 * O shield DFR0009 é especificado para 5V. Há duas formas de usá-lo com
 * ESP32 e cada uma exige uma abordagem diferente para o pino A0 do keypad:
 *
 * OPÇÃO A — Shield em 3.3V (mais simples, conexão direta)
 * --------------------------------------------------------
 * Shield VCC → pino 3V3 do ESP32
 * A0 do shield → GPIO 34 (direto, sem resistores extras)
 *
 * VANTAGENS: conexão direta sem risco ao GPIO 34 (input-only, max 3.3V)
 * DESVANTAGENS: LCD pode ter contraste instável; backlight mais fraco
 * USE se o display funcionar satisfatoriamente na bancada.
 *
 * OPÇÃO B — Shield em 5V com divisor resistivo no A0 (recomendada)
 * ----------------------------------------------------------------
 * Shield VCC → pino 5V (ou VIN) do ESP32
 * A0 do shield → R1 (1kΩ) → GPIO 34
 *                             GPIO 34 → R2 (2kΩ) → GND
 * Resultado: tensão máxima no GPIO34 = 5V × (2k/3k) = 3.33V (seguro)
 *
 * VANTAGENS: LCD opera no voltage nominal, contraste e backlight corretos
 * DESVANTAGENS: requer dois resistores soldados nos fios
 * USE se o display não exibir bem na Opção A.
 *
 * ==========================================================================
 * THRESHOLDS DO KEYPAD — COMO FORAM CALCULADOS
 * ==========================================================================
 *
 * O datasheet DFR0009 fornece os centros de leitura com Arduino (ADC 10-bit,
 * Vref=5V): RIGHT≈0, UP≈144, DOWN≈329, LEFT≈504, SELECT≈741, NONE≈1023.
 *
 * Para ESP32 com ADC_11db (escala 0–3.1V, 12-bit 0–4095) e VCC=3.3V:
 *   tensão_botão = (centro_arduino / 1023) × 5V × (3.3V / 5V)
 *   adc_esp32    = (tensão_botão / 3.1V) × 4095
 *
 * Centros resultantes (VCC=3.3V):
 *   RIGHT=0  UP=613  DOWN=1401  LEFT=2147  SELECT=3157  NONE=4095
 *
 * Thresholds = ponto médio entre centros adjacentes:
 *   RIGHT  < 306   → threshold 300
 *   UP     < 1007  → threshold 1000
 *   DOWN   < 1774  → threshold 1750
 *   LEFT   < 2652  → threshold 2600
 *   SELECT < 3626  → threshold 3600  ← CRÍTICO: era 3100, abaixo do centro 3157
 *
 * Se os botões responderem errado após montar, leia o ADC bruto no Serial:
 *   Serial.println(analogRead(DefaultPins::KEYPAD_ADC_PIN));
 * Pressione cada botão e ajuste os thresholds para que cada leitura caia
 * entre dois thresholds consecutivos.
 *
 * ATENÇÃO: com Opção B (5V), os centros serão proporcionalmente maiores.
 * Refaça o cálculo usando VCC=5V e escala ADC_11db para recalibrar.
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

  // Thresholds do keypad analógico — calibrados para VCC=3.3V no shield.
  // Veja cálculo detalhado no cabeçalho deste arquivo.
  // Se usar VCC=5V + divisor resistivo (Opção B), os valores serão maiores;
  // recalibre medindo os botões com Serial.println(analogRead(34)).
  uint16_t keyRightMax  =  300;  // RIGHT  centro ~0
  uint16_t keyUpMax     = 1000;  // UP     centro ~613
  uint16_t keyDownMax   = 1750;  // DOWN   centro ~1401
  uint16_t keyLeftMax   = 2600;  // LEFT   centro ~2147
  uint16_t keySelectMax = 3600;  // SELECT centro ~3157  (era 3100 — ERRADO)
};

namespace DefaultPins {
  // Barramento OneWire dos DS18B20
  static constexpr uint8_t TEMP_ONEWIRE_PIN = 4;

  // Relé principal de refrigeração
  static constexpr uint8_t RELAY_PIN = 27;

  // ──────────────────────────────────────────────────────────────────────────
  // LCD 16x2 DFR0009 em modo 4-bit
  //
  // Cabeamento (shield → ESP32 DevKit, por jumpers):
  //   Shield D4  → GPIO 13    (DB4 do HD44780)
  //   Shield D5  → GPIO 26    (DB5)
  //   Shield D6  → GPIO 25    (DB6)
  //   Shield D7  → GPIO 33    (DB7)
  //   Shield D8  → GPIO 14    (RS — Register Select)
  //   Shield D9  → GPIO 12    (EN — Enable)
  //   Shield D10 → GPIO 32    (Backlight — controle PWM)
  //   Shield A0  → GPIO 34    (Keypad analógico)
  //   Shield VCC → 3V3        (Opção A) ou 5V + divisor em A0 (Opção B)
  //   Shield GND → GND
  //
  // Confirmado contra datasheet DFR0009:
  //   D4=DB4, D5=DB5, D6=DB6, D7=DB7, D8=RS, D9=EN, D10=Backlight, A0=Keypad
  // ──────────────────────────────────────────────────────────────────────────
  static constexpr uint8_t LCD_RS = 14;
  static constexpr uint8_t LCD_EN = 12;
  static constexpr uint8_t LCD_D4 = 13;
  static constexpr uint8_t LCD_D5 = 26;
  static constexpr uint8_t LCD_D6 = 25;
  static constexpr uint8_t LCD_D7 = 33;

  // Backlight — shield D10 → GPIO 32 (PWM via LEDC canal 0, 1 kHz, 8-bit)
  static constexpr uint8_t LCD_BACKLIGHT_PIN = 32;

  // Keypad analógico — shield A0 → GPIO 34 (input-only, max 3.3V)
  // Com VCC=3.3V no shield: tensão máxima no pino ≤ 3.3V — conexão direta, segura.
  // Com VCC=5V: OBRIGATÓRIO divisor resistivo 1kΩ/2kΩ antes do GPIO34.
  static constexpr uint8_t KEYPAD_ADC_PIN = 34;

  // Saídas opcionais
  static constexpr uint8_t BUZZER_PIN     = 15;
  static constexpr uint8_t STATUS_LED_PIN = 2;
}
