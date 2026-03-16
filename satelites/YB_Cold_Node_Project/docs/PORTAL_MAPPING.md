# Firmware Architecture Notes

O portal foi estruturado para refletir as áreas de configuração planejadas do firmware.

## Grupos principais de configuração
- status_runtime
- wifi_config
- api_config
- temperature_control
- defrost_config
- sensors_config
- alert_config
- display_config
- device_config
- admin_config
- logs_runtime

## Sugestão de endpoints locais
- GET /api/status
- GET /api/config
- POST /api/config/wifi
- POST /api/config/api
- POST /api/config/temperature
- POST /api/config/defrost
- POST /api/config/sensors
- POST /api/config/alerts
- POST /api/config/display
- POST /api/config/device
- POST /api/config/admin
- GET /api/logs
- POST /api/action/test-alarm
- POST /api/action/defrost
- POST /api/action/reboot
