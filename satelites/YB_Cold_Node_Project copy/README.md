# YB Cold Node — ESP32 MVP funcional

Este pacote foi ajustado para entregar um **MVP funcional em ESP32** para o subprojeto de controle de temperatura do YeastBank.

Nesta versão, o projeto já vem preparado para:

- ler **1 ou 2 sensores DS18B20** no mesmo barramento OneWire
- controlar **1 relé principal** por histerese
- operar localmente com **LCD 16x2 + keypad analógico**
- subir **portal web local** em SPIFFS
- salvar configuração em **Preferences / NVS**
- entrar em **modo AP local** para configuração quando necessário

## O que foi implementado

### Firmware ESP32
Arquivos principais:

- `platformio.ini`
- `partitions.csv`
- `include/AppConfig.h`
- `src/main.cpp`

### Portal embarcado
Arquivos usados pelo SPIFFS:

- `data/index.html`
- `data/style.css`
- `data/script.js`

Os arquivos em `template_portal/` foram mantidos como referência visual, mas o firmware serve o conteúdo de `data/`.

## Hardware assumido nesta implementação

### MCU
- ESP32 DevKit / `esp32dev`

### Display
- LCD 16x2 tipo **HD44780** em **modo 4-bit**
- teclado resistivo analógico do tipo **LCD Keypad Shield 1602**

> Importante: esse display/shield normalmente é pensado para Arduino Uno. No ESP32 ele precisa ser **cabeado**, não encaixado diretamente como shield.

### Sensores
- 1 a 2 sensores **DS18B20**
- resistor pull-up de **4.7k** entre DATA e VCC do barramento OneWire

### Relé
- 1 relé para controle do compressor/refrigeração
- lógica ativa configurável por software (`relayActiveHigh`)

## Mapeamento de pinos padrão

Definidos em `include/AppConfig.h`:

```cpp
TEMP_ONEWIRE_PIN = 4
RELAY_PIN        = 27
LCD_RS           = 14
LCD_EN           = 12
LCD_D4           = 13
LCD_D5           = 26
LCD_D6           = 25
LCD_D7           = 33
KEYPAD_ADC_PIN   = 34
BUZZER_PIN       = 15
STATUS_LED_PIN   = 2
```

Se quiser trocar, altere apenas o header `AppConfig.h`.

## Fluxo de operação

### Boot
1. Inicializa LCD, relé, ADC e serial
2. Carrega configuração salva do NVS
3. Monta SPIFFS
4. Descobre sensores DS18B20
5. Sobe AP local
6. Tenta conectar no Wi‑Fi salvo
7. Inicia servidor web na porta 80

### Loop principal
1. Processa servidor HTTP
2. Atualiza status do Wi‑Fi
3. Lê sensores no intervalo configurado
4. Executa controle térmico
5. Atualiza LCD
6. Processa botões locais
7. Pisca LED / buzzer de alarme

## Controle térmico implementado

Lógica atual: **refrigeração por histerese**

- liga relé quando `temperatura >= setpoint + histerese/2`
- desliga relé quando `temperatura <= setpoint - histerese/2`

### Segurança atual
- se o sensor de controle estiver inválido ou desconectado, o firmware entra em **failsafe** e desliga o relé

### Itens ainda recomendados para próxima fase
- tempo mínimo entre partidas do compressor
- tempo mínimo ligado/desligado
- degelo real
- telemetria externa para API YeastBank
- fila offline persistente

## Navegação local no LCD

Telas disponíveis:

- Home
- Sensores
- Rede
- Configuração
- Diagnóstico
- Editar setpoint
- Editar histerese

### Botões
- `LEFT` / `RIGHT`: troca de tela
- na tela de configuração:
  - `UP`: editar setpoint
  - `DOWN`: editar histerese
- em edição:
  - `LEFT` / `RIGHT`: altera valor
  - `SELECT`: salva
- na tela de diagnóstico:
  - `SELECT`: redetecta sensores

## Portal web local

### Endereços
- modo AP: `192.168.4.1`
- modo STA: IP recebido pela rede Wi‑Fi

### Endpoints implementados
- `GET /api/status`
- `GET /api/config`
- `POST /api/config/temperature`
- `POST /api/config/wifi`
- `POST /api/config/device`
- `GET /api/logs`
- `POST /api/action/reboot`
- `POST /api/action/factory-reset`

## Como subir no ESP32

### 1. Compilar
```bash
pio run
```

### 2. Gravar firmware
```bash
pio run -t upload
```

### 3. Gravar SPIFFS do portal
```bash
pio run -t uploadfs
```

### 4. Monitor serial
```bash
pio device monitor -b 115200
```

## Observações importantes sobre o keypad analógico

Os valores de ADC variam entre fabricantes do shield. Por isso os thresholds foram deixados configuráveis e persistentes:

- `keyRightMax`
- `keyUpMax`
- `keyDownMax`
- `keyLeftMax`
- `keySelectMax`

Se algum botão estiver “trocado”, ajuste esses limites no firmware ou via endpoint futuro.

## Estrutura do projeto

```text
YB_Cold_Node_Project
├── api/
├── data/
├── docs/
├── hardware/
├── include/
├── src/
├── template_portal/
├── partitions.csv
├── platformio.ini
└── README.md
```

## Próximo passo recomendado

A base já está boa para bancada e integração inicial. O próximo ganho real seria adicionar:

1. proteção de compressor
2. configuração completa do keypad no portal
3. API YeastBank com telemetria e alertas
4. degelo funcional
5. exportação/importação de configuração
