"""
Registry para o serviço MQTT.
Permite acesso global ao serviço MQTT de qualquer lugar da aplicação.
"""

from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Variável global para armazenar a instância do MQTTService
_mqtt_service_instance = None


def set_mqtt_service(service):
    """
    Define a instância global do serviço MQTT.
    
    Args:
        service: Instância do MQTTService
    """
    global _mqtt_service_instance
    _mqtt_service_instance = service
    logger.debug("Instância do MQTTService registrada globalmente")


def get_mqtt_service():
    """
    Obtém a instância global do serviço MQTT.
    
    Returns:
        Instância do MQTTService ou None se não disponível
    """
    return _mqtt_service_instance


def clear_mqtt_service():
    """Limpa a instância global do serviço MQTT."""
    global _mqtt_service_instance
    _mqtt_service_instance = None
    logger.debug("Instância do MQTTService removida")
    
    
    
#from .mqtt_service import MQTTService
#
#_mqtt_service = None
#
#def get_mqtt_service():
#    global _mqtt_service
#
#    if _mqtt_service is None:
#        _mqtt_service = MQTTService()
#
#    return _mqtt_service