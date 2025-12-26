"""
Serviço de integração com device_manager.

Bridge entre mash_control e device_manager para acesso a sensores e atuadores.
"""

import logging
from typing import Dict, List, Optional, Callable, Any
from flask import current_app

logger = logging.getLogger(__name__)


class DeviceIntegrationService:
    """
    Serviço para integração com device_manager.
    
    Fornece métodos para listar dispositivos, enviar comandos e inscrever-se
    em telemetria através da API pública do device_manager.
    """
    
    def __init__(self):
        """Inicializa o serviço de integração."""
        self._device_api = None
        self._check_device_manager()
    
    def _check_device_manager(self):
        """Verifica se device_manager está disponível."""
        try:
            from plugins.plugin_device_manager.utils.device_api import DeviceAPIService
            self._device_api = DeviceAPIService
            logger.info("DeviceIntegrationService: device_manager API disponível")
        except ImportError:
            logger.error("DeviceIntegrationService: device_manager não está disponível")
            self._device_api = None
    
    def is_available(self) -> bool:
        """Verifica se device_manager está disponível."""
        return self._device_api is not None
    
    def get_available_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista dispositivos disponíveis filtrados por tipo.
        
        Args:
            filters: Dicionário com filtros (device_type, protocol, is_active)
            
        Returns:
            Lista de dispositivos disponíveis
        """
        if not self.is_available():
            logger.warning("DeviceIntegrationService: device_manager não disponível")
            return []
        
        try:
            # Obter todos os dispositivos
            devices = self._device_api.list_devices()
            
            # Aplicar filtros se fornecidos
            if filters:
                filtered_devices = []
                for device in devices:
                    match = True
                    if 'device_type' in filters and device.get('type') != filters['device_type']:
                        match = False
                    if 'protocol' in filters and device.get('protocol') != filters['protocol']:
                        match = False
                    if 'is_active' in filters and device.get('is_active') != filters['is_active']:
                        match = False
                    if match:
                        filtered_devices.append(device)
                return filtered_devices
            
            return devices
        except Exception as e:
            logger.error(f"Erro ao obter dispositivos disponíveis: {e}", exc_info=True)
            return []
    
    def get_sensors(self) -> List[Dict[str, Any]]:
        """
        Lista apenas sensores disponíveis.
        
        Returns:
            Lista de sensores
        """
        if not self.is_available():
            return []
        
        try:
            sensors = self._device_api.list_devices_by_port_type('sensor')
            return sensors
        except Exception as e:
            logger.error(f"Erro ao obter sensores: {e}", exc_info=True)
            return []
    
    def get_actuators(self) -> List[Dict[str, Any]]:
        """
        Lista apenas atuadores disponíveis.
        
        Returns:
            Lista de atuadores
        """
        if not self.is_available():
            return []
        
        try:
            actuators = self._device_api.list_devices_by_port_type('actuator')
            return actuators
        except Exception as e:
            logger.error(f"Erro ao obter atuadores: {e}", exc_info=True)
            return []
    
    def map_device_to_function(self, device_id: str, function: str) -> bool:
        """
        Mapeia dispositivo para função na brassagem.
        
        Args:
            device_id: ID do dispositivo
            function: Função (ex: 'mash_tun_heater', 'boil_kettle_temp_sensor')
            
        Returns:
            True se mapeamento foi salvo com sucesso
        """
        # Este mapeamento é armazenado no equipment_mapping da receita
        # Este método é apenas um helper para validação
        if not self.is_available():
            return False
        
        try:
            device_status = self._device_api.get_device_status(device_id)
            if device_status:
                logger.info(f"Dispositivo {device_id} mapeado para função {function}")
                return True
            return False
        except Exception as e:
            logger.error(f"Erro ao mapear dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def send_command(self, device_id: str, command: str, payload: Dict[str, Any] = None) -> bool:
        """
        Envia comando para dispositivo via device_manager.
        
        Args:
            device_id: ID do dispositivo
            command: Tipo de comando (ex: 'set_port', 'get_status')
            payload: Dados do comando
            
        Returns:
            True se comando foi enviado com sucesso
        """
        if not self.is_available():
            return False
        
        try:
            if command == 'set_port' and payload:
                port = payload.get('port')
                value = payload.get('value')
                result = self._device_api.set_port_value(device_id, port, value)
                return result
            else:
                result = self._device_api.send_command(device_id, command, payload)
                return result
        except Exception as e:
            logger.error(f"Erro ao enviar comando para dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def subscribe_telemetry(self, device_id: str, callback: Callable[[str, Dict], None]) -> bool:
        """
        Inscreve-se em telemetria de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            callback: Função chamada quando telemetria é recebida
            
        Returns:
            True se inscrição foi bem-sucedida
        """
        if not self.is_available():
            return False
        
        try:
            result = self._device_api.subscribe_telemetry(device_id, callback)
            return result
        except Exception as e:
            logger.error(f"Erro ao inscrever-se em telemetria de {device_id}: {e}", exc_info=True)
            return False
    
    def get_device_status(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém status atual de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Status do dispositivo ou None se não encontrado
        """
        if not self.is_available():
            return None
        
        try:
            status = self._device_api.get_device_status(device_id)
            return status
        except Exception as e:
            logger.error(f"Erro ao obter status do dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    def get_port_value(self, device_id: str, port: str) -> Optional[Any]:
        """
        Obtém valor de uma porta específica de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            port: Nome da porta
            
        Returns:
            Valor da porta ou None se não encontrado
        """
        if not self.is_available():
            return None
        
        try:
            value = self._device_api.get_port_value(device_id, port)
            return value
        except Exception as e:
            logger.error(f"Erro ao obter valor da porta {port} do dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    def set_port_value(self, device_id: str, port: str, value: Any) -> bool:
        """
        Define valor de uma porta específica de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            port: Nome da porta
            value: Valor a ser definido
            
        Returns:
            True se valor foi definido com sucesso
        """
        if not self.is_available():
            return False
        
        try:
            result = self._device_api.set_port_value(device_id, port, value)
            return result
        except Exception as e:
            logger.error(f"Erro ao definir valor da porta {port} do dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def get_all_ports(self, device_id: str) -> Dict[str, Any]:
        """
        Obtém todas as portas de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Dicionário com todas as portas e seus valores
        """
        if not self.is_available():
            return {}
        
        try:
            ports = self._device_api.get_all_ports(device_id)
            return ports
        except Exception as e:
            logger.error(f"Erro ao obter portas do dispositivo {device_id}: {e}", exc_info=True)
            return {}

