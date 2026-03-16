from .mqtt_service import MQTTService

_mqtt_service = None

def get_mqtt_service():
    global _mqtt_service

    if _mqtt_service is None:
        _mqtt_service = MQTTService()

    return _mqtt_service