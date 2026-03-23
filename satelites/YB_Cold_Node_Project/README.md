# YB Cold Node — ESP32 MVP funcional

Firmware base para o subprojeto de controle de temperatura do YeastBank.

## O que este firmware faz

- Lê **1 ou 2 sensores DS18B20** no mesmo barramento OneWire
- Controla **1 relé principal** por histerese
- Exibe estado local em **LCD 16x2 + keypad analógico** (DFR0009)
- Sobe **portal web local** servido via SPIFFS
- Persiste configuração em **Preferences / NVS**
- Opera em **modo AP local** para configuração inicial sem rede

---

## Estrutura do projeto

```text
YB_Cold_Node_Project/
├── include/
│   └── AppConfig.h        ← pinos, defaults, thresholds do keypad
├── src/
│   └── main.cpp           ← firmware completo
├── data/
│   ├── index.html         ← portal web (enviado via uploadfs)
│   ├── style.css
│   └── script.js
├── template_portal/       ← referência visual (não enviado ao ESP32)
├── api/
│   └── API_SPEC.md
├── docs/
├── hardware/
├── partitions.csv
├── platformio.ini
└── README.md
```

---

## Hardware

### MCU
- **ESP32 DevKit** (`esp32dev`)

### Display e teclado
- **DFR0009** — LCD Keypad Shield 1602 (DFRobot)
- Display HD44780 em modo 4-bit
- Teclado resistivo analógico com 5 botões em divisor de tensão

> O shield foi projetado para Arduino Uno (5V). No ESP32 ele **não encaixa diretamente** — precisa ser cabeado com jumpers.
> Veja a seção [Cabeamento do shield](#cabeamento-do-shield) abaixo.

### Sensores de temperatura
- 1 a 2 sensores **DS18B20** no mesmo barramento OneWire
- Resistor pull-up de **4.7 kΩ** entre DATA e VCC

### Relé
- 1 relé para compressor / refrigeração
- Lógica ativa (HIGH ou LOW) configurável via `relayActiveHigh`

---

## Mapeamento de pinos

Definidos em `include/AppConfig.h`. Para trocar algum pino, edite apenas esse arquivo.

| Função | GPIO |
|---|---|
| OneWire DS18B20 | 4 |
| Relé | 27 |
| LCD RS | 14 |
| LCD EN | 12 |
| LCD D4 | 13 |
| LCD D5 | 26 |
| LCD D6 | 25 |
| LCD D7 | 33 |
| LCD Backlight (PWM) | **32** |
| Keypad ADC | 34 |
| Buzzer | 15 |
| LED de status | 2 |

---

## Cabeamento do shield

O shield DFR0009 usa os pinos D4–D10 e A0 do Arduino. Ligue cada um ao ESP32 com um fio jumper:

| Pino no shield | GPIO no ESP32 | Função |
|---|---|---|
| VCC | Ver nota abaixo | Alimentação |
| GND | GND | Terra |
| D4 | GPIO 13 | DB4 |
| D5 | GPIO 26 | DB5 |
| D6 | GPIO 25 | DB6 |
| D7 | GPIO 33 | DB7 |
| D8 | GPIO 14 | RS |
| D9 | GPIO 12 | EN |
| D10 | GPIO 32 | Backlight (PWM) |
| A0 | GPIO 34 | Keypad analógico |

### Alimentação do shield — escolha uma das opções

**Opção A — Shield em 3.3V (mais simples)**

```
Shield VCC → pino 3V3 do ESP32
Shield A0  → GPIO 34  (direto, sem resistores)
```

Com 3.3V no VCC do shield, a tensão máxima no A0 nunca excede 3.3V, deixando o GPIO 34 completamente seguro. Use esta opção primeiro; se o LCD não exibir bem (contraste fraco ou instável), passe para a Opção B.

**Opção B — Shield em 5V com divisor resistivo (maior brilho e contraste)**

```
Shield VCC → pino 5V (ou VIN) do ESP32
Shield A0  → R1 (1 kΩ) → GPIO 34
                          GPIO 34 → R2 (2 kΩ) → GND
```

O divisor 1kΩ / 2kΩ limita a tensão máxima no GPIO 34 a `5V × 2k/3k = 3.33 V`, protegendo o pino. Se usar esta opção, recalibre os thresholds do keypad (veja seção abaixo).

---

## Calibração do keypad analógico

O shield DFR0009 lê todos os botões num único pino ADC por meio de um divisor resistivo. Os thresholds no `AppConfig.h` foram calculados com base nos centros de tensão documentados pelo datasheet, escalonados para VCC=3.3V e ADC 12-bit do ESP32 com `ADC_11db`:

| Botão | Centro ADC (3.3V) | Threshold padrão |
|---|---|---|
| RIGHT | ~0 | 300 |
| UP | ~613 | 1000 |
| DOWN | ~1401 | 1750 |
| LEFT | ~2147 | 2600 |
| SELECT | ~3157 | 3600 |
| (nenhum) | ~4095 | — |

> Os thresholds são os pontos médios entre centros adjacentes, garantindo margem igual para cada lado.

Se usar a **Opção B (5V)**, os centros serão proporcionalmente maiores — recalibre medindo cada botão via Serial Monitor:

```cpp
// Adicione temporariamente no loop() para calibrar:
Serial.println(analogRead(DefaultPins::KEYPAD_ADC_PIN));
```

Pressione cada botão, anote o valor exibido e ajuste as constantes `key*Max` em `AppConfig.h` (ou persistidas via NVS) de forma que cada leitura caia entre dois thresholds consecutivos. Os valores são persistentes: podem ser salvos via `POST /api/config/device`.

---

## Controle de brilho do LCD

O backlight é controlado por PWM no canal LEDC 0 (GPIO 32, 1 kHz, 8-bit). O campo `lcdBacklightPercent` (0–100) é persistido no NVS e aplicado automaticamente no boot.

Para alterar via API:

```json
POST /api/config/device
{ "lcd_backlight_percent": 80 }
```

A mudança é aplicada imediatamente, sem precisar reiniciar.

---

## Portal web local

### Endereços

| Modo | Endereço |
|---|---|
| AP (configuração inicial) | `192.168.4.1` |
| STA (rede Wi-Fi) | IP recebido pelo roteador |

### Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/api/status` | Estado completo (sensores, relé, Wi-Fi) |
| GET | `/api/config` | Configuração atual |
| POST | `/api/config/temperature` | Setpoint, histerese, sensor de controle, relé |
| POST | `/api/config/wifi` | SSID, senha, hostname |
| POST | `/api/config/device` | Nome, buzzer, brilho LCD, thresholds keypad |
| GET | `/api/logs` | Últimas 24 entradas do log interno |
| POST | `/api/action/reboot` | Reinicia o ESP32 |
| POST | `/api/action/factory-reset` | Apaga NVS e reinicia |

---

## Navegação no LCD

### Telas disponíveis

```
Home → Sensores → Rede → Configuração → Diagnóstico
```

### Botões

| Contexto | Botão | Ação |
|---|---|---|
| Qualquer tela | LEFT / RIGHT | Troca de tela |
| Tela Configuração | UP | Entrar em edição de setpoint |
| Tela Configuração | DOWN | Entrar em edição de histerese |
| Em edição | LEFT / RIGHT | Decrementa / incrementa valor |
| Em edição | SELECT | Salva e volta |
| Tela Diagnóstico | SELECT | Redetecta sensores DS18B20 |

---

## Controle térmico

**Lógica:** refrigeração por histerese simétrica

```
Liga relé   → temperatura ≥ setpoint + (histerese / 2)
Desliga relé → temperatura ≤ setpoint - (histerese / 2)
```

**Failsafe:** se o sensor de controle estiver inválido ou desconectado, o relé é desligado imediatamente e o alarme é ativado.

---

## Como gravar no ESP32

```bash
# Compilar
pio run

# Gravar firmware
pio run -t upload

# Gravar portal web (SPIFFS)
pio run -t uploadfs

# Monitor serial
pio device monitor -b 115200
```

---

## Próximos passos recomendados

1. **Proteção de compressor** — tempo mínimo entre partidas, tempo mínimo ligado/desligado
2. **Configuração do keypad pelo portal** — formulário de calibração no `index.html`
3. **Telemetria YeastBank** — integração com a API externa, fila offline persistente
4. **Degelo** — lógica de ciclo de degelo real
5. **Exportação de configuração** — backup/restore via portal

---

## Notas de manutenção

- Todo novo pino deve ser centralizado em `include/AppConfig.h`
- Toda nova configuração persistente deve passar por `loadConfig()`, `saveConfig()` e pelo endpoint `GET /api/config`
- O controle térmico **não depende de Wi-Fi** — opera plenamente offline
- O ESP32 com `espressif32 >= 3.x` usa API nova do LEDC: se `ledcSetup` / `ledcAttachPin` gerarem erro de compilação, substituir por `ledcAttach(pin, freq, res)` + `ledcWrite(pin, duty)` conforme documentado no `main.cpp`
