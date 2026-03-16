
# YB Cold Node Firmware Architecture

## Core Modules

### ConfigManager
Responsible for storing and loading configuration from flash memory.

### SensorManager
Handles DS18B20 temperature sensors.

### RelayController
Controls compressor relay outputs.

### TemperatureController
Implements hysteresis logic and temperature regulation.

### DisplayManager
Handles LCD UI and menu navigation.

### WiFiManager
Manages WiFi connection and fallback AP mode.

### APIClient
Handles communication with YeastBank backend.

### Logger
Stores runtime logs for diagnostics.

## Execution Loop

1. Read sensors
2. Run temperature control
3. Update display
4. Send telemetry
5. Process alerts
