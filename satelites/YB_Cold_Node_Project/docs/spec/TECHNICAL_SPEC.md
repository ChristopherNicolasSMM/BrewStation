
# Technical Specification — YB Cold Node

## Hardware

Core MCU:
ESP32

Sensors:
DS18B20 temperature sensors

Outputs:
Relay modules for compressor control

Display:
LCD 20x4 I2C

Inputs:
5 push buttons

Optional:
- Buzzer
- Status LEDs
- Door sensor

## Firmware Components

Modules:

ConfigManager
Stores configuration in flash.

SensorManager
Reads and validates sensors.

TemperatureController
Implements temperature control logic.

RelayController
Controls outputs.

DisplayManager
Handles UI screens.

WiFiManager
Handles connectivity.

APIClient
Sends telemetry and alerts.

Logger
Stores device logs.

## Data Transmission

Example telemetry payload:

{
  "device_id": "ybcn_freezer_01",
  "timestamp": 1700000000,
  "temperature": -18.4,
  "relay_state": true,
  "wifi_signal": -62
}
