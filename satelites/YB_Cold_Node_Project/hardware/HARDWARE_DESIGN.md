# Hardware Design

## Core MCU
ESP32 DevKit

## Sensores
DS18B20 waterproof temperature sensors

- Quantidade suportada no MVP: 1 a 2
- Barramento: OneWire único
- Recomendado resistor pull-up de 4.7k entre DATA e VCC

## Display
LCD 16x2 tipo HD44780 com teclado resistivo analógico (LCD Keypad 1602)

> Observação: no ESP32 este módulo deve ser ligado por fios. Não considerar encaixe direto estilo Arduino Uno.

## Outputs
Relé principal para compressor / refrigeração

- tensão lógica do comando: 3.3V do ESP32
- validar em bancada se o módulo de relé realmente aceita disparo em 3.3V
- verificar se a lógica é ativa em HIGH ou LOW

## Inputs
Teclado analógico do display

## Optional
- buzzer
- LED de status
- segundo relé em fases futuras
- sensor de porta em fases futuras

## Power
- alimentação estável para ESP32
- evitar compartilhar fonte ruidosa do compressor com a lógica sem isolação adequada
- usar aterramento e proteção apropriados ao trabalhar com carga AC
