# src/interfaces/__init__.py
"""
Pacote de interfaces de comunicação.
Fornece MQTT e REST API para expor os dispositivos.
"""

from src.interfaces.mqtt_interface import MQTTInterface
from src.interfaces.rest_api import RESTAPI

__all__ = ['MQTTInterface', 'RESTAPI']