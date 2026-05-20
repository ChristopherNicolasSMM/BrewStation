"""
Serviço de integração com device_manager.

Bridge entre mash_control e device_manager para acesso a sensores e atuadores através
da API pública DeviceAPI que utiliza ActorManager como interface real.
"""

import logging
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeviceIntegrationService:
    """
    Serviço para integração com device_manager.

    Fornece métodos para listar dispositivos, enviar comandos e inscrever-se
    em telemetria através da API pública DeviceAPI do device_manager.
    A API real se baseia em DeviceAPI → ActorManager para acesso a atores e sensores.
    """

    def __init__(self):
        """Inicializa o serviço de integração."""
        self._device_api = None
        self._check_device_manager()

    def _check_device_manager(self):
        """
        Verifica se device_manager está disponível tentando importar DeviceAPI.

        A classe real no device_manager.utils é `DeviceAPI` (sem "Service").
        """
        try:
            from plugins.plugin_device_manager.utils.device_api import \
                DeviceAPI
            self._device_api = DeviceAPI
            logger.info("DeviceIntegrationService: device_manager API disponível")
        except ImportError:
            logger.warning("DeviceIntegrationService: device_manager não está instalado")
            self._device_api = None

    def is_available(self) -> bool:
        """Verifica se device_manager está disponível."""
        return self._device_api is not None

    def get_available_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista atores disponíveis (sensores e atuadores) da device_manager API.

        Args:
            filters: Dicionário com filtros (actor_type: 'sensor'|'actuator')

        Returns:
            Lista de atores disponíveis
        """
        if not self.is_available():
            logger.warning("DeviceIntegrationService: device_manager não disponível")
            return []

        try:
            if filters and filters.get('actor_type'):
                actors = self._device_api.list_actors_by_type(filters['actor_type'])
            else:
                sensors = self._device_api.list_actors_by_type('sensor')
                actuators = self._device_api.list_actors_by_type('actuator')
                actors = sensors + actuators
            return actors
        except Exception as e:
            logger.error(f"Erro ao obter atores: {e}", exc_info=True)
            return []

    def get_sensors(self) -> List[Dict[str, Any]]:
        """
        Lista apenas sensores disponíveis via DeviceAPI.

        Returns:
            Lista de atores do tipo sensor
        """
        if not self.is_available():
            return []

        try:
            return self._device_api.list_actors_by_type('sensor')
        except Exception as e:
            logger.error(f"Erro ao obter sensores: {e}", exc_info=True)
            return []

    def get_actuators(self) -> List[Dict[str, Any]]:
        """
        Lista apenas atuadores disponíveis via DeviceAPI.

        Returns:
            Lista de atores do tipo actuator
        """
        if not self.is_available():
            return []

        try:
            return self._device_api.list_actors_by_type('actuator')
        except Exception as e:
            logger.error(f"Erro ao obter atuadores: {e}", exc_info=True)
            return []

    def map_device_to_function(self, actor_id: str, function: str) -> bool:
        """
        Mapeia ator para função na brassagem.

        Args:
            actor_id: ID do ator (não do device físico)
            function: Função (ex: 'mash_tun_heater', 'boil_kettle_temp_sensor')

        Returns:
            True se o ator existe e está acessível
        """
        if not self.is_available():
            return False

        try:
            actor = self._device_api.get_actor(actor_id)
            if actor:
                logger.info(f"Actor {actor_id} mapeado para função {function}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao mapear ator {actor_id}: {e}", exc_info=True)
            return False

    def send_command(self, actor_id: str, command: str, payload: Dict[str, Any] = None) -> bool:
        """
        Envia comando para um atuador via device_manager.

        Args:
            actor_id: ID do ator
            command: Tipo de comando
            payload: Dados do comando (para 'set' usa payload.get('value'))

        Returns:
            True se comando foi enviado com sucesso
        """
        if not self.is_available():
            return False

        try:
            if command == 'set' and payload:
                value = payload.get('value', payload)
                return self._device_api.execute_action(actor_id, value)
            else:
                return self._device_api.execute_action(actor_id, command)
        except Exception as e:
            logger.error(f"Erro ao enviar comando para ator {actor_id}: {e}", exc_info=True)
            return False

    def subscribe_telemetry(self, actor_id: str, callback: Callable[[str, Any], None]) -> bool:
        """
        Inscreve-se em telemetria de um sensor via device_manager.

        Args:
            actor_id: ID do ator (deve ser do tipo sensor)
            callback: Função callback(actor_id, value) chamada quando valor muda

        Returns:
            True se inscrição foi bem-sucedida
        """
        if not self.is_available():
            return False

        try:
            return self._device_api.subscribe_sensor(actor_id, callback)
        except Exception as e:
            logger.error(f"Erro ao inscrever-se em telemetria do ator {actor_id}: {e}", exc_info=True)
            return False

    def get_device_status(self, actor_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém status atual de um ator (sensor ou atuador).

        NOTA: actor_id aqui é o ID do ator no device_manager, não um device físico.
        Para sensores, lê o valor atual. Para atuadores, retorna o estado do ator.

        Args:
            actor_id: ID do ator

        Returns:
            Dict com status do ator ou None
        """
        if not self.is_available():
            return None

        try:
            # Primeiro tenta obter o ator para saber o tipo
            actor = self._device_api.get_actor(actor_id)
            if not actor:
                return None

            result = {
                'id': actor_id,
                'status': 'online',
                'actor_type': actor.get('actor_type'),
                'device_id': actor.get('device_id'),
                'port_name': actor.get('port_name'),
                'name': actor.get('name')
            }

            # Se for sensor, tenta ler o valor
            if actor.get('actor_type') == 'sensor':
                try:
                    value = self._device_api.read_sensor(actor_id)
                    result['value'] = value
                except Exception:
                    result['value'] = None

            return result
        except Exception as e:
            logger.error(f"Erro ao obter status do ator {actor_id}: {e}", exc_info=True)
            return None

    def get_port_value(self, actor_id: str, port: str = None) -> Optional[Any]:
        """
        Obtém valor de leitura de um sensor.

        Args:
            actor_id: ID do ator (sensor)
            port: Ignorado (compatibilidade, o ator já sabe sua porta)

        Returns:
            Valor do sensor ou None
        """
        if not self.is_available():
            return None

        try:
            return self._device_api.read_sensor(actor_id)
        except Exception as e:
            logger.error(f"Erro ao ler sensor {actor_id}: {e}", exc_info=True)
            return None

    def set_port_value(self, actor_id: str, port: str, value: Any) -> bool:
        """
        Define valor de um atuador.

        Args:
            actor_id: ID do ator
            port: Ignorado (compatibilidade)
            value: Valor a ser definido

        Returns:
            True se valor foi definido com sucesso
        """
        if not self.is_available():
            return False

        try:
            return self._device_api.execute_action(actor_id, value)
        except Exception as e:
            logger.error(f"Erro ao definir valor do ator {actor_id}: {e}", exc_info=True)
            return False

    def get_all_ports(self, actor_id: str) -> Dict[str, Any]:
        """
        Obtém informações completas do ator (compatibilidade com interface anterior).

        Args:
            actor_id: ID do ator

        Returns:
            Dicionário com dados do ator
        """
        if not self.is_available():
            return {}

        try:
            actor = self._device_api.get_actor(actor_id)
            if not actor:
                return {}

            result = dict(actor)

            # Se for sensor, incluir leitura
            if actor.get('actor_type') == 'sensor':
                try:
                    value = self._device_api.read_sensor(actor_id)
                    result['current_value'] = value
                except Exception:
                    result['current_value'] = None

            return result
        except Exception as e:
            logger.error(f"Erro ao obter dados do ator {actor_id}: {e}", exc_info=True)
            return {}

