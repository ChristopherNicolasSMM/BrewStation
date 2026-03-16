
# YeastBank IoT API

## Device Registration
POST /api/iot/devices

## Telemetry
POST /api/iot/telemetry

Payload example:

{
 "device_id": "ybcn_001",
 "temperature": -18.4,
 "relay": true,
 "wifi": -60,
 "timestamp": 1700000000
}

## Alerts
POST /api/iot/alerts
