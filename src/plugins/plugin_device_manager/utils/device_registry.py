"""
Serviço de registro e gerenciamento de dispositivos IoT.

Gerencia CRUD de dispositivos, salvando configurações em JSON
e mantendo apenas metadados no banco de dados.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DeviceRegistry:
    """
    Registry para gerenciar dispositivos IoT.
    
    Salva configurações detalhadas em arquivos JSON dentro do plugin
    e mantém apenas metadados no banco de dados.
    """
    
    def __init__(self, plugin_path: Path):
        """
        Inicializa o registry.
        
        Args:
            plugin_path: Caminho do diretório do plugin
        """
        self.plugin_path = plugin_path
        self.data_path = plugin_path / "data"
        self.configs_path = self.data_path / "devices" / "configs"
        self.states_path = self.data_path / "devices" / "states"
        
        # Garantir que os diretórios existam
        self.configs_path.mkdir(parents=True, exist_ok=True)
        self.states_path.mkdir(parents=True, exist_ok=True)
        
        # Cache em memória para estados frequentes
        self._state_cache: Dict[str, Dict] = {}
    
    def register_device(self, device_config: Dict[str, Any]) -> str:
        """
        Registra um novo dispositivo.
        
        Args:
            device_config: Dicionário com configuração do dispositivo
            
        Returns:
            ID do dispositivo criado
        """
        try:
            # Gerar ID se não fornecido
            device_id = device_config.get('device_id') or str(uuid.uuid4())
            
            # Preparar configuração completa
            full_config = {
                'device_id': device_id,
                'name': device_config.get('name', 'Dispositivo sem nome'),
                'type': device_config.get('type', 'sensor'),
                'protocol': device_config.get('protocol', 'mqtt'),
                'connection': device_config.get('connection', {}),
                'topics': device_config.get('topics', {}),
                'ports': device_config.get('ports', {}),
                'properties': device_config.get('properties', {}),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            
            # Salvar configuração em JSON
            config_file = self.configs_path / f"{device_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(full_config, f, indent=2, ensure_ascii=False)
            
            # Criar estado inicial
            initial_state = {
                'device_id': device_id,
                'status': 'offline',
                'last_seen': None,
                'ports': {},
                'telemetry': {},
                'last_error': None
            }
            
            state_file = self.states_path / f"{device_id}.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(initial_state, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Dispositivo {device_id} registrado com sucesso")
            return device_id
            
        except Exception as e:
            logger.error(f"Erro ao registrar dispositivo: {e}", exc_info=True)
            raise
    
    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém configuração de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Dicionário com configuração ou None se não encontrado
        """
        try:
            config_file = self.configs_path / f"{device_id}.json"
            if not config_file.exists():
                return None
            
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Erro ao obter dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    def update_device(self, device_id: str, updates: Dict[str, Any]) -> bool:
        """
        Atualiza configuração de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            updates: Dicionário com campos a atualizar
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            config = self.get_device(device_id)
            if not config:
                return False
            
            # Atualizar campos
            config.update(updates)
            config['updated_at'] = datetime.utcnow().isoformat()
            
            # Salvar configuração atualizada
            config_file = self.configs_path / f"{device_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Dispositivo {device_id} atualizado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def delete_device(self, device_id: str) -> bool:
        """
        Remove um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            True se removido com sucesso
        """
        try:
            # Remover arquivos JSON
            config_file = self.configs_path / f"{device_id}.json"
            state_file = self.states_path / f"{device_id}.json"
            
            if config_file.exists():
                config_file.unlink()
            
            if state_file.exists():
                state_file.unlink()
            
            # Remover do cache
            self._state_cache.pop(device_id, None)
            
            logger.info(f"Dispositivo {device_id} removido com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao remover dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def list_devices(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os dispositivos, opcionalmente filtrados.
        
        Args:
            filters: Dicionário com filtros (type, protocol, is_active, etc.)
            
        Returns:
            Lista de configurações de dispositivos
        """
        try:
            devices = []
            
            # Listar todos os arquivos de configuração
            for config_file in self.configs_path.glob("*.json"):
                try:
                    with open(config_file, 'r', encoding='utf-8') as f:
                        device = json.load(f)
                        
                        # Aplicar filtros se fornecidos
                        if filters:
                            match = True
                            for key, value in filters.items():
                                if device.get(key) != value:
                                    match = False
                                    break
                            if not match:
                                continue
                        
                        devices.append(device)
                except Exception as e:
                    logger.warning(f"Erro ao carregar dispositivo de {config_file}: {e}")
                    continue
            
            return devices
            
        except Exception as e:
            logger.error(f"Erro ao listar dispositivos: {e}", exc_info=True)
            return []
    
    def update_state(self, device_id: str, state_data: Dict[str, Any]) -> bool:
        """
        Atualiza estado de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            state_data: Dicionário com dados de estado
            
        Returns:
            True se atualizado com sucesso
        """
        try:
            state_file = self.states_path / f"{device_id}.json"
            
            # Carregar estado atual ou criar novo
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            else:
                state = {
                    'device_id': device_id,
                    'status': 'offline',
                    'last_seen': None,
                    'ports': {},
                    'telemetry': {},
                    'last_error': None
                }
            
            # Atualizar estado
            state.update(state_data)
            state['last_seen'] = datetime.utcnow().isoformat()
            
            # Salvar estado
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            # Atualizar cache
            self._state_cache[device_id] = state
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao atualizar estado do dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def get_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém estado atual de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            
        Returns:
            Dicionário com estado ou None se não encontrado
        """
        try:
            # Verificar cache primeiro
            if device_id in self._state_cache:
                return self._state_cache[device_id]
            
            state_file = self.states_path / f"{device_id}.json"
            if not state_file.exists():
                return None
            
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # Atualizar cache
            self._state_cache[device_id] = state
            
            return state
            
        except Exception as e:
            logger.error(f"Erro ao obter estado do dispositivo {device_id}: {e}", exc_info=True)
            return None
    
    def save_port_config(self, device_id: str, port_config: Dict[str, Any]) -> bool:
        """
        Salva configuração de portas de um dispositivo.
        
        Args:
            device_id: ID do dispositivo
            port_config: Dicionário com configuração de portas
            
        Returns:
            True se salvo com sucesso
        """
        try:
            config = self.get_device(device_id)
            if not config:
                return False
            
            # Atualizar configuração de portas
            config['ports'] = port_config
            config['updated_at'] = datetime.utcnow().isoformat()
            
            # Salvar configuração atualizada
            config_file = self.configs_path / f"{device_id}.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuração de portas do dispositivo {device_id} salva com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao salvar configuração de portas do dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def get_port_value(self, device_id: str, port: str) -> Optional[Any]:
        """
        Obtém valor atual de uma porta específica.
        
        Args:
            device_id: ID do dispositivo
            port: Nome da porta (ex: 'GPIO_32')
            
        Returns:
            Valor da porta ou None se não encontrado
        """
        state = self.get_state(device_id)
        if not state:
            return None
        
        ports = state.get('ports', {})
        port_data = ports.get(port)
        
        if port_data:
            return port_data.get('value')
        
        return None
    
    def set_port_value(self, device_id: str, port: str, value: Any) -> bool:
        """
        Define valor de uma porta específica no estado.
        
        Args:
            device_id: ID do dispositivo
            port: Nome da porta (ex: 'GPIO_32')
            value: Valor a definir
            
        Returns:
            True se definido com sucesso
        """
        try:
            state = self.get_state(device_id)
            if not state:
                # Criar estado inicial se não existir
                state = {
                    'device_id': device_id,
                    'status': 'offline',
                    'last_seen': None,
                    'ports': {},
                    'telemetry': {},
                    'last_error': None
                }
            
            # Atualizar valor da porta
            if 'ports' not in state:
                state['ports'] = {}
            
            if port not in state['ports']:
                state['ports'][port] = {}
            
            state['ports'][port]['value'] = value
            state['ports'][port]['timestamp'] = datetime.utcnow().isoformat()
            
            # Salvar estado atualizado
            return self.update_state(device_id, state)
            
        except Exception as e:
            logger.error(f"Erro ao definir valor da porta {port} do dispositivo {device_id}: {e}", exc_info=True)
            return False

