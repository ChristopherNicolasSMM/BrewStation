"""
API pública para outros plugins acessarem dispositivos via atores.

Fornece interface simples para outros plugins interagirem com atores
de dispositivos IoT sem precisar conhecer detalhes de implementação.
"""

import logging
from typing import Dict, Optional, Callable, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DeviceAPI:
    """
    API pública para outros plugins usarem devices através de atores.
    
    Esta classe fornece métodos estáticos que podem ser chamados por outros
    plugins para obter atores, executar ações e ler sensores.
    """
    
    _plugin_path = None
    
    @classmethod
    def initialize(cls, plugin_path: Path):
        """
        Inicializa a API com referências necessárias.
        
        Args:
            plugin_path: Caminho do diretório do plugin
        """
        cls._plugin_path = plugin_path
    
    @staticmethod
    def get_actor(actor_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém ator por ID.
        
        Args:
            actor_id: ID do ator
            
        Returns:
            Dicionário com dados do ator ou None
        """
        try:
            from plugins.plugin_device_manager.utils.actor_manager import ActorManager
            from flask import current_app
            
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if not plugin:
                return None
            
            manager = ActorManager(plugin.plugin_path)
            return manager.get_actor(actor_id)
            
        except Exception as e:
            logger.error(f"Erro ao obter ator {actor_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def execute_action(actor_id: str, value: Any) -> bool:
        """
        Executa ação (liga/desliga, seta valor).
        
        Args:
            actor_id: ID do ator
            value: Valor a enviar (bool, int, float, string)
            
        Returns:
            True se executado com sucesso
        """
        try:
            from plugins.plugin_device_manager.utils.actor_manager import ActorManager
            from flask import current_app
            
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if not plugin:
                return False
            
            manager = ActorManager(plugin.plugin_path)
            return manager.execute_actor_action(actor_id, value)
            
        except Exception as e:
            logger.error(f"Erro ao executar ação do ator {actor_id}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def read_sensor(actor_id: str) -> Optional[Any]:
        """
        Lê valor de sensor.
        
        Args:
            actor_id: ID do ator (deve ser do tipo sensor)
            
        Returns:
            Valor do sensor ou None
        """
        try:
            from plugins.plugin_device_manager.utils.actor_manager import ActorManager
            from flask import current_app
            
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if not plugin:
                return None
            
            manager = ActorManager(plugin.plugin_path)
            return manager.read_actor_sensor(actor_id)
            
        except Exception as e:
            logger.error(f"Erro ao ler sensor do ator {actor_id}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def subscribe_sensor(actor_id: str, callback: Callable[[str, Any], None]) -> bool:
        """
        Inscreve em mudanças de sensor.
        
        Args:
            actor_id: ID do ator (deve ser do tipo sensor)
            callback: Função callback(actor_id, value) chamada quando valor muda
            
        Returns:
            True se inscrito com sucesso
        """
        try:
            from plugins.plugin_device_manager.utils.actor_manager import ActorManager
            from plugins.plugin_device_manager.utils.device_registry import DeviceRegistry
            from plugins.plugin_device_manager.utils.mqtt_service import MQTTService
            from flask import current_app
            
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if not plugin:
                return False
            
            # Obter ator
            manager = ActorManager(plugin.plugin_path)
            actor = manager.get_actor(actor_id)
            if not actor or actor.get('actor_type') != 'sensor':
                return False
            
            # Obter configuração do device
            registry = DeviceRegistry(plugin.plugin_path)
            device_config = registry.get_device(actor['device_id'])
            if not device_config:
                return False
            
            # Construir tópico de telemetria
            topics = device_config.get('topics', {})
            telemetry_topic = topics.get('telemetry', f"brewstation/devices/{actor['device_id']}/telemetry")
            
            # Wrapper para callback
            def mqtt_callback(device_id, topic, payload):
                try:
                    import json
                    data = json.loads(payload)
                    port_data = data.get(actor['port_name'], {})
                    value = port_data.get('value')
                    callback(actor_id, value)
                except Exception as e:
                    logger.error(f"Erro ao processar callback de sensor: {e}", exc_info=True)
            
            # Obter MQTT service
            mqtt_service = plugin._mqtt_service if hasattr(plugin, '_mqtt_service') else None
            if not mqtt_service:
                return False
            
            # Inscrever no tópico
            return mqtt_service.subscribe(telemetry_topic, mqtt_callback)
            
        except Exception as e:
            logger.error(f"Erro ao inscrever-se em sensor {actor_id}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def list_actors_by_type(actor_type: str, plugin_name: str = None) -> List[Dict[str, Any]]:
        """
        Lista atores por tipo.
        
        Args:
            actor_type: Tipo do ator (sensor, actuator, rule_trigger)
            plugin_name: Filtrar por plugin (opcional)
            
        Returns:
            Lista de atores
        """
        try:
            from plugins.plugin_device_manager.utils.actor_manager import ActorManager
            from flask import current_app
            
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if not plugin:
                return []
            
            manager = ActorManager(plugin.plugin_path)
            return manager.get_actors_by_type(actor_type, plugin_name)
            
        except Exception as e:
            logger.error(f"Erro ao listar atores do tipo {actor_type}: {e}", exc_info=True)
            return []
    
    @staticmethod
    def list_actors_by_plugin(plugin_name: str, plugin_entity_id: str = None) -> List[Dict[str, Any]]:
        """
        Lista atores usados por um plugin.
        
        Args:
            plugin_name: Nome do plugin
            plugin_entity_id: ID da entidade no plugin (opcional)
            
        Returns:
            Lista de atores
        """
        try:
            from plugins.plugin_device_manager.utils.actor_manager import ActorManager
            from flask import current_app
            
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if not plugin:
                return []
            
            manager = ActorManager(plugin.plugin_path)
            return manager.get_actors_by_plugin(plugin_name, plugin_entity_id)
            
        except Exception as e:
            logger.error(f"Erro ao listar atores do plugin {plugin_name}: {e}", exc_info=True)
            return []
    
    @staticmethod
    def link_actor_to_plugin(actor_id: str, plugin_name: str, plugin_entity_id: str) -> bool:
        """
        Associa ator a entidade de outro plugin.
        
        Args:
            actor_id: ID do ator
            plugin_name: Nome do plugin
            plugin_entity_id: ID da entidade no plugin
            
        Returns:
            True se associado com sucesso
        """
        try:
            from plugins.plugin_device_manager.utils.actor_manager import ActorManager
            from flask import current_app
            
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if not plugin:
                return False
            
            manager = ActorManager(plugin.plugin_path)
            return manager.link_actor_to_plugin(actor_id, plugin_name, plugin_entity_id)
            
        except Exception as e:
            logger.error(f"Erro ao associar ator {actor_id}: {e}", exc_info=True)
            return False
