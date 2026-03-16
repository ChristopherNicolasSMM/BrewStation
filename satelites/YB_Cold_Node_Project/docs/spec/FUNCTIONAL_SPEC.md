
# Functional Specification — YB Cold Node

## Functional Requirements

### RF01 Temperature Monitoring
Device must read temperature from sensors.

### RF02 Multiple Sensors
Minimum of two sensors supported.

### RF03 Relay Control
At least one relay output for compressor control.

### RF04 Temperature Control
Setpoint and hysteresis configuration.

### RF05 Local Interface
Device must provide configuration using display and buttons.

### RF06 Web Configuration
Device must allow configuration through local web interface.

### RF07 Telemetry
Device must send telemetry to YeastBank API.

### RF08 Offline Operation
Device must buffer data locally if internet fails.

### RF09 Alerts
Alerts must be generated for:
- High temperature
- Low temperature
- Sensor failure
- Power loss
- Connectivity loss

### RF10 Device Identification
Each device must have unique device_id.
