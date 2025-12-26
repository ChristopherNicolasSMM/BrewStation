"""
API pública para outros plugins acessarem dispositivos.

Fornece interface simples para outros plugins interagirem com dispositivos IoT
sem precisar conhecer detalhes de implementação.

SUPORTE PARA MÚLTIPLAS PORTAS:
- Cada dispositivo pode ter múltiplas portas IoT (sensores, atuadores, etc.)
- Portas são configuradas individualmente com tipo, direção e função
- Valores das portas são armazenados separadamente e podem ser acessados individualmente
- Outros plugins podem acessar todas as portas ou portas específicas de um dispositivo
"""

import logging
from typing import Dict, Optional, Callable, Any, List
from pathlib import Path

logger = logging.getLogger(__name__)


class DeviceAPIService:
    """
    Serviço de API para outros plugins acessarem dispositivos.
    
    Esta classe fornece métodos estáticos que podem ser chamados por outros
    plugins para obter status, enviar comandos e inscrever-se em telemetria.
    
    SUPORTE PARA MÚLTIPLAS PORTAS:
    - Cada dispositivo pode ter múltiplas portas IoT configuradas
    - Métodos para acessar portas individuais ou todas as portas
    - Filtragem de dispositivos por tipo de porta
    """
    
    _registry = None
    _mqtt_service = None
    
    @classmethod
    def initialize(cls, plugin_path: Path, mqtt_service):
        """
        Inicializa o serviço com referências necessárias.
        
        Args:
            plugin_path: Caminho do diretório do plugin
            mqtt_service: Instância do MQTTService
        """
        from plugins.plugin_device_manager.utils.device_registry import DeviceRegistry
        
        cls._registry = DeviceRegistry(plugin_path)
        cls._mqtt_service = mqtt_service
    
    @classmethod
    def get_device_status(cls, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém status atual de um dispositivo.
        
        Para uso por outros plugins.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Dicionário com status do dispositivo ou None se não encontrado
        """
        if not cls._registry:
            logger.error("DeviceAPIService não foi inicializado")
            return None
        
        try:
            state = cls._registry.get_state(device_id)
            if not state:
                return None
            
            config = cls._registry.get_device(device_id)
            
            return {
                'device_id': device_id,
                'name': config.get('name') if config else 'Desconhecido',
                'status': state.get('status', 'offline'),
                'last_seen': state.get('last_seen'),
                'telemetry': state.get('telemetry', {}),
                'ports': state.get('ports', {}),
                'last_error': state.get('last_error')
            }
        except Exception as e:
            logger.error(f"Erro ao obter status do dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    @classmethod
    def send_command(cls, device_id: str, command: str, payload: Dict[str, Any] = None) -> bool:
        """
        Envia comando para um dispositivo.
        
        Para uso por outros plugins.
        
        Args:
            device_id: ID do dispositivo
            command: Nome do comando
            payload: Dados do comando (opcional)
            
        Returns:
            True se comando enviado com sucesso
        """
        if not cls._registry or not cls._mqtt_service:
            logger.error("DeviceAPIService não foi inicializado")
            return False
        
        try:
            config = cls._registry.get_device(device_id)
            if not config:
                logger.error(f"Dispositivo {device_id} não encontrado")
                return False
            
            topics = config.get('topics', {})
            command_topic = topics.get('command')
            
            if not command_topic:
                logger.error(f"Tópico de comando não configurado para dispositivo {device_id}")
                return False
            
            # Preparar mensagem
            message = {
                'command': command,
                'payload': payload or {},
                'timestamp': None
            }
            
            import json
            from datetime import datetime
            message['timestamp'] = datetime.utcnow().isoformat()
            
            # Publicar comando
            result = cls._mqtt_service.publish(
                command_topic,
                json.dumps(message),
                qos=1
            )
            
            if result:
                logger.info(f"Comando '{command}' enviado para dispositivo {device_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao enviar comando para dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    @classmethod
    def subscribe_telemetry(cls, device_id: str, callback: Callable[[str, Dict], None]) -> bool:
        """
        Inscreve-se em telemetria de um dispositivo.
        
        Para uso por outros plugins.
        
        Args:
            device_id: ID do dispositivo
            callback: Função callback(device_id, telemetry_data)
            
        Returns:
            True se inscrito com sucesso
        """
        if not cls._registry or not cls._mqtt_service:
            logger.error("DeviceAPIService não foi inicializado")
            return False
        
        try:
            config = cls._registry.get_device(device_id)
            if not config:
                logger.error(f"Dispositivo {device_id} não encontrado")
                return False
            
            topics = config.get('topics', {})
            telemetry_topic = topics.get('telemetry')
            
            if not telemetry_topic:
                logger.error(f"Tópico de telemetria não configurado para dispositivo {device_id}")
                return False
            
            # Wrapper para callback
            def telemetry_callback(dev_id, topic, payload):
                try:
                    import json
                    telemetry_data = json.loads(payload)
                    callback(device_id, telemetry_data)
                except Exception as e:
                    logger.error(f"Erro ao processar telemetria: {e}", exc_info=True)
            
            # Inscrever no tópico
            result = cls._mqtt_service.subscribe(telemetry_topic, telemetry_callback)
            
            if result:
                logger.info(f"Inscrito em telemetria do dispositivo {device_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao inscrever-se em telemetria do dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    @classmethod
    def get_port_value(cls, device_id: str, port: str) -> Optional[Any]:
        """
        Obtém valor atual de uma porta específica.
        
        Para uso por outros plugins.
        
        Args:
            device_id: ID do dispositivo
            port: Nome da porta (ex: 'GPIO_32')
            
        Returns:
            Valor da porta ou None se não encontrado
        """
        if not cls._registry:
            logger.error("DeviceAPIService não foi inicializado")
            return None
        
        try:
            return cls._registry.get_port_value(device_id, port)
        except Exception as e:
            logger.error(f"Erro ao obter valor da porta {port} do dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    @classmethod
    def set_port_value(cls, device_id: str, port: str, value: Any) -> bool:
        """
        Define valor de uma porta específica.
        
        Para uso por outros plugins.
        
        Args:
            device_id: ID do dispositivo
            port: Nome da porta (ex: 'GPIO_32')
            value: Valor a definir
            
        Returns:
            True se definido com sucesso
        """
        if not cls._registry:
            logger.error("DeviceAPIService não foi inicializado")
            return False
        
        try:
            # Atualizar estado local
            result = cls._registry.set_port_value(device_id, port, value)
            
            if result:
                # Enviar comando para dispositivo atualizar porta
                cls.send_command(device_id, 'set_port', {'port': port, 'value': value})
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao definir valor da porta {port} do dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    @classmethod
    def get_all_ports(cls, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém todas as portas e seus valores de um dispositivo.
        
        Para uso por outros plugins. Retorna um dicionário onde cada chave é o nome
        da porta e o valor contém configuração e estado atual.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Dicionário com todas as portas e seus valores ou None se não encontrado
        """
        if not cls._registry:
            logger.error("DeviceAPIService não foi inicializado")
            return None
        
        try:
            state = cls._registry.get_state(device_id)
            config = cls._registry.get_device(device_id)
            
            if not config:
                return None
            
            ports_config = config.get('ports', {})
            ports_state = state.get('ports', {}) if state else {}
            
            # Combinar configuração e estado
            all_ports = {}
            for port_name, port_config in ports_config.items():
                port_state = ports_state.get(port_name, {})
                all_ports[port_name] = {
                    **port_config,
                    'current_value': port_state.get('value'),
                    'last_update': port_state.get('timestamp'),
                    'status': 'active' if port_state.get('value') is not None else 'inactive'
                }
            
            return all_ports
        except Exception as e:
            logger.error(f"Erro ao obter portas do dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    @classmethod
    def get_port_config(cls, device_id: str, port: str = None) -> Optional[Dict[str, Any]]:
        """
        Obtém configuração de uma ou todas as portas de um dispositivo.
        
        Para uso por outros plugins.
        
        Args:
            device_id: ID do dispositivo
            port: Nome da porta específica (opcional). Se None, retorna todas as portas
            
        Returns:
            Dicionário com configuração da(s) porta(s) ou None se não encontrado
        """
        if not cls._registry:
            logger.error("DeviceAPIService não foi inicializado")
            return None
        
        try:
            device = cls._registry.get_device(device_id)
            if not device:
                return None
            
            ports_config = device.get('ports', {})
            
            if port:
                return ports_config.get(port)
            else:
                return ports_config
        except Exception as e:
            logger.error(f"Erro ao obter configuração de portas do dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    @classmethod
    def list_devices_by_port_type(cls, port_type: str = None) -> List[Dict[str, Any]]:
        """
        Lista dispositivos filtrados por tipo de porta.
        
        Para uso por outros plugins. Útil para encontrar todos os dispositivos
        que possuem sensores ou atuadores de um tipo específico.
        
        Args:
            port_type: Tipo de porta ('sensor', 'actuator'). Se None, retorna todos
            
        Returns:
            Lista de dispositivos que possuem portas do tipo especificado
        """
        if not cls._registry:
            logger.error("DeviceAPIService não foi inicializado")
            return []
        
        try:
            devices = cls._registry.list_devices()
            
            if not port_type:
                return devices
            
            # Filtrar dispositivos que têm pelo menos uma porta do tipo especificado
            filtered_devices = []
            for device in devices:
                ports = device.get('ports', {})
                for port_name, port_config in ports.items():
                    if port_config.get('type') == port_type:
                        filtered_devices.append(device)
                        break
            
            return filtered_devices
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos por tipo de porta: {e}", exc_info=True)
            return []
