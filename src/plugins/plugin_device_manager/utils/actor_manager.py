"""
Gerenciador de atores de dispositivos IoT.

Gerencia criação, consulta e execução de atores que associam
portas de devices a funções e permitem integração com outros plugins.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ActorManager:
    """
    Gerenciador de atores de dispositivos.
    
    Responsável por criar, consultar e executar ações através de atores
    que associam portas de devices a funções específicas.
    """
    
    def __init__(self, plugin_path: Path):
        """
        Inicializa o gerenciador.
        
        Args:
            plugin_path: Caminho do diretório do plugin
        """
        self.plugin_path = plugin_path
    
    def create_actor(self, device_id: str, port_name: str, function_id: int, 
                     actor_type: str, name: str, description: str = None, 
                     config: Dict[str, Any] = None) -> Optional[str]:
        """
        Cria novo ator.
        
        Args:
            device_id: ID do device
            port_name: Nome da porta (ex: GPIO1, ADC0)
            function_id: ID da função
            actor_type: Tipo do ator (sensor, actuator, rule_trigger)
            name: Nome do ator
            description: Descrição do ator
            config: Configuração específica do ator (dict)
            
        Returns:
            ID do ator criado ou None em caso de erro
        """
        try:
            from db.database import db
            from plugins.plugin_device_manager.utils.model_loader import (
                get_device_actor, get_device_function, get_device_metadata)
            
            DeviceActor = get_device_actor()
            DeviceMetadata = get_device_metadata()
            DeviceFunction = get_device_function()
            
            if not all([DeviceActor, DeviceMetadata, DeviceFunction]):
                logger.error("Modelos não disponíveis")
                return None
            
            # Verificar se device existe
            device = DeviceMetadata.query.get(device_id)
            if not device:
                logger.error(f"Device {device_id} não encontrado")
                return None
            
            # Verificar se função existe
            function = DeviceFunction.query.get(function_id)
            if not function:
                logger.error(f"Função {function_id} não encontrada")
                return None
            
            # Gerar ID do ator
            actor_id = str(uuid.uuid4())
            
            # Criar ator
            actor = DeviceActor(
                id=actor_id,
                device_id=device_id,
                port_name=port_name,
                function_id=function_id,
                actor_type=actor_type,
                name=name,
                description=description,
                is_active=True
            )
            
            # Definir configuração se fornecida
            if config:
                actor.set_config(config)
            
            db.session.add(actor)
            db.session.commit()
            
            logger.info(f"Actor {actor_id} criado com sucesso")
            return actor_id
            
        except Exception as e:
            logger.error(f"Erro ao criar ator: {e}", exc_info=True)
            from db.database import db
            db.session.rollback()
            return None
    
    def get_actor(self, actor_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém ator por ID.
        
        Args:
            actor_id: ID do ator
            
        Returns:
            Dicionário com dados do ator ou None
        """
        try:
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            DeviceActor = get_device_actor()
            
            if not DeviceActor:
                return None
            
            actor = DeviceActor.query.get(actor_id)
            if not actor:
                return None
            
            return actor.to_dict(include_relationships=True)
            
        except Exception as e:
            logger.error(f"Erro ao obter ator {actor_id}: {e}", exc_info=True)
            return None
    
    def get_actors_by_device(self, device_id: str) -> List[Dict[str, Any]]:
        """
        Lista atores de um device.
        
        Args:
            device_id: ID do device
            
        Returns:
            Lista de atores
        """
        try:
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            DeviceActor = get_device_actor()
            
            if not DeviceActor:
                return []
            
            actors = DeviceActor.query.filter_by(device_id=device_id).all()
            return [actor.to_dict() for actor in actors]
            
        except Exception as e:
            logger.error(f"Erro ao listar atores do device {device_id}: {e}", exc_info=True)
            return []
    
    def get_actors_by_plugin(self, plugin_name: str, plugin_entity_id: str = None) -> List[Dict[str, Any]]:
        """
        Lista atores usados por um plugin.
        
        Args:
            plugin_name: Nome do plugin
            plugin_entity_id: ID da entidade no plugin (opcional)
            
        Returns:
            Lista de atores
        """
        try:
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            DeviceActor = get_device_actor()
            
            if not DeviceActor:
                return []
            
            query = DeviceActor.query.filter_by(plugin_name=plugin_name)
            if plugin_entity_id:
                query = query.filter_by(plugin_entity_id=plugin_entity_id)
            
            actors = query.all()
            return [actor.to_dict() for actor in actors]
            
        except Exception as e:
            logger.error(f"Erro ao listar atores do plugin {plugin_name}: {e}", exc_info=True)
            return []
    
    def get_actors_by_type(self, actor_type: str, plugin_name: str = None) -> List[Dict[str, Any]]:
        """
        Lista atores por tipo.
        
        Args:
            actor_type: Tipo do ator (sensor, actuator, rule_trigger)
            plugin_name: Filtrar por plugin (opcional)
            
        Returns:
            Lista de atores
        """
        try:
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            DeviceActor = get_device_actor()
            
            if not DeviceActor:
                return []
            
            query = DeviceActor.query.filter_by(actor_type=actor_type)
            if plugin_name:
                query = query.filter_by(plugin_name=plugin_name)
            
            actors = query.all()
            return [actor.to_dict() for actor in actors]
            
        except Exception as e:
            logger.error(f"Erro ao listar atores do tipo {actor_type}: {e}", exc_info=True)
            return []
    
    def link_actor_to_plugin(self, actor_id: str, plugin_name: str, 
                             plugin_entity_id: str) -> bool:
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
            from db.database import db
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            
            DeviceActor = get_device_actor()
            if not DeviceActor:
                return False
            
            actor = DeviceActor.query.get(actor_id)
            if not actor:
                return False
            
            actor.plugin_name = plugin_name
            actor.plugin_entity_id = plugin_entity_id
            
            db.session.commit()
            
            logger.info(f"Actor {actor_id} associado ao plugin {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao associar ator {actor_id}: {e}", exc_info=True)
            from db.database import db
            db.session.rollback()
            return False
    
    def execute_actor_action(self, actor_id: str, value: Any) -> bool:
        """
        Executa ação do ator (publica comando MQTT).
        
        Args:
            actor_id: ID do ator
            value: Valor a enviar (pode ser bool, int, float, string)
            
        Returns:
            True se executado com sucesso
        """
        try:
            from plugins.plugin_device_manager.utils.device_registry import \
                DeviceRegistry
            from plugins.plugin_device_manager.utils.model_loader import (
                get_device_actor, get_device_metadata)
            
            DeviceActor = get_device_actor()
            DeviceMetadata = get_device_metadata()
            
            if not all([DeviceActor, DeviceMetadata]):
                return False
            
            actor = DeviceActor.query.get(actor_id)
            if not actor or not actor.is_active:
                logger.error(f"Actor {actor_id} não encontrado ou inativo")
                return False
            
            if actor.actor_type not in ['actuator', 'rule_trigger']:
                logger.error(f"Actor {actor_id} não é do tipo actuator ou rule_trigger")
                return False
            
            # Obter device
            device = DeviceMetadata.query.get(actor.device_id)
            if not device:
                return False
            
            # Obter configuração do device
            registry = DeviceRegistry(self.plugin_path)
            device_config = registry.get_device(actor.device_id)
            if not device_config:
                return False
            
            # Construir tópico MQTT para comando
            topics = device_config.get('topics', {})
            base_topic = topics.get('command', f"brewstation/devices/{actor.device_id}/command")
            topic = f"{base_topic}/{actor.port_name}"
            
            # Preparar payload
            payload = {
                'port': actor.port_name,
                'value': value,
                'actor_id': actor_id
            }
            payload_str = json.dumps(payload)
            
            # Publicar via MQTT
            mqtt_service = self._get_mqtt_service()
            if mqtt_service:
                success = mqtt_service.publish(topic, payload_str, qos=1)
                if success:
                    logger.info(f"Ação executada no ator {actor_id}: {value}")
                    return True
            
            logger.error(f"Erro ao publicar comando MQTT para ator {actor_id}")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao executar ação do ator {actor_id}: {e}", exc_info=True)
            return False
    
    def read_actor_sensor(self, actor_id: str) -> Optional[Any]:
        """
        Lê valor atual do sensor.
        
        Args:
            actor_id: ID do ator
            
        Returns:
            Valor do sensor ou None
        """
        try:
            from plugins.plugin_device_manager.utils.device_registry import \
                DeviceRegistry
            from plugins.plugin_device_manager.utils.model_loader import (
                get_device_actor, get_device_metadata)
            
            DeviceActor = get_device_actor()
            DeviceMetadata = get_device_metadata()
            
            if not all([DeviceActor, DeviceMetadata]):
                return None
            
            actor = DeviceActor.query.get(actor_id)
            if not actor or not actor.is_active:
                return None
            
            if actor.actor_type != 'sensor':
                logger.error(f"Actor {actor_id} não é do tipo sensor")
                return None
            
            # Obter estado do device
            registry = DeviceRegistry(self.plugin_path)
            state = registry.get_state(actor.device_id)
            if not state:
                return None
            
            # Obter valor da porta no estado
            ports = state.get('ports', {})
            port_state = ports.get(actor.port_name, {})
            
            # Retornar valor atual
            return port_state.get('value')
            
        except Exception as e:
            logger.error(f"Erro ao ler sensor do ator {actor_id}: {e}", exc_info=True)
            return None
    
    def update_actor(self, actor_id: str, updates: Dict[str, Any]) -> bool:
        """
        Atualiza ator.
        
        Args:
            actor_id: ID do ator
            updates: Dicionário com campos a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            from db.database import db
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            
            DeviceActor = get_device_actor()
            if not DeviceActor:
                return False
            
            actor = DeviceActor.query.get(actor_id)
            if not actor:
                return False
            
            # Atualizar campos permitidos
            updatable_fields = ['name', 'description', 'actor_type', 'is_active', 
                              'plugin_name', 'plugin_entity_id']
            
            for field in updatable_fields:
                if field in updates:
                    setattr(actor, field, updates[field])
            
            # Atualizar configuração se fornecida
            if 'config' in updates:
                actor.set_config(updates['config'])
            
            db.session.commit()
            
            logger.info(f"Actor {actor_id} atualizado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar ator {actor_id}: {e}", exc_info=True)
            from db.database import db
            db.session.rollback()
            return False
    
    def delete_actor(self, actor_id: str) -> bool:
        """
        Remove ator.
        
        Args:
            actor_id: ID do ator
            
        Returns:
            True se removido com sucesso
        """
        try:
            from db.database import db
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            
            DeviceActor = get_device_actor()
            if not DeviceActor:
                return False
            
            actor = DeviceActor.query.get(actor_id)
            if not actor:
                return False
            
            db.session.delete(actor)
            db.session.commit()
            
            logger.info(f"Actor {actor_id} removido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover ator {actor_id}: {e}", exc_info=True)
            from db.database import db
            db.session.rollback()
            return False
    
    def _get_mqtt_service(self):
        """Obtém instância do MQTTService."""
        try:
            from flask import current_app
            plugin_manager = current_app.plugin_manager
            plugin = plugin_manager.get_plugin('device_manager')
            if plugin and hasattr(plugin, '_mqtt_service'):
                return plugin._mqtt_service
            return None
        except Exception:
            return None
