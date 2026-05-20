#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
device_manager.py
Gerenciador central de dispositivos para o BrewStation Device Server.
Coordena todos os sensores e atuadores, gerencia o ciclo de vida,
polling e interfaces de comunicação.

Este é o coração do sistema, responsável por orquestrar todos os componentes.
"""

import logging
import threading
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class DeviceStatus(Enum):
    """Status possíveis para dispositivos."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    DISABLED = "disabled"
    INITIALIZING = "initializing"

class DeviceType(Enum):
    """Tipos de dispositivos."""
    SENSOR = "sensor"
    ACTUATOR = "actuator"
    GATEWAY = "gateway"
    CONTROLLER = "controller"

class DeviceManager:
    """
    Gerenciador central de dispositivos.
    
    Responsabilidades:
    - Manter registro de todos os dispositivos (sensores e atuadores)
    - Gerenciar ciclo de vida (inicialização, polling, desligamento)
    - Coordenar comunicação entre dispositivos e interfaces
    - Fornecer API unificada para acesso aos dispositivos
    - Monitorar saúde dos dispositivos
    """
    
    def __init__(self, config_manager):
        """
        Inicializa o gerenciador de dispositivos.
        
        Args:
            config_manager: Instância do ConfigManager com as configurações
        """
        self.config = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Registros de dispositivos
        self.sensors: Dict[str, Any] = {}
        self.actuators: Dict[str, Any] = {}
        self.devices: Dict[str, Any] = {}  # Registro unificado
        
        # Status do sistema
        self.status = DeviceStatus.INITIALIZING
        self.running = False
        self.start_time = None
        
        # Threads
        self.polling_thread = None
        self.health_check_thread = None
        self.monitoring_threads = []
        
        # Callbacks
        self.sensor_update_callbacks: List[Callable] = []
        self.actuator_change_callbacks: List[Callable] = []
        
        # Estatísticas
        self.stats = {
            'total_readings': 0,
            'total_commands': 0,
            'errors': 0,
            'last_updated': None
        }
        
        self.logger.info("Device Manager inicializado")
    
    # =========================================================================
    # MÉTODOS DE REGISTRO DE DISPOSITIVOS
    # =========================================================================
    
    def register_sensor(self, name: str, sensor_instance) -> bool:
        """
        Registra um sensor no gerenciador.
        
        Args:
            name: Nome único do sensor
            sensor_instance: Instância do sensor (deve herdar de BaseSensor)
            
        Returns:
            True se registrado com sucesso
        """
        if name in self.sensors:
            self.logger.warning(f"Sensor '{name}' já registrado. Substituindo.")
        
        self.sensors[name] = sensor_instance
        self.devices[name] = {
            'instance': sensor_instance,
            'type': DeviceType.SENSOR,
            'status': DeviceStatus.ONLINE,
            'registered_at': datetime.now()
        }
        
        self.logger.info(f"Sensor registrado: '{name}' ({sensor_instance.__class__.__name__})")
        return True
    
    def register_actuator(self, name: str, actuator_instance) -> bool:
        """
        Registra um atuador no gerenciador.
        
        Args:
            name: Nome único do atuador
            actuator_instance: Instância do atuador (deve herdar de BaseActuator)
            
        Returns:
            True se registrado com sucesso
        """
        if name in self.actuators:
            self.logger.warning(f"Atuador '{name}' já registrado. Substituindo.")
        
        self.actuators[name] = actuator_instance
        self.devices[name] = {
            'instance': actuator_instance,
            'type': DeviceType.ACTUATOR,
            'status': DeviceStatus.ONLINE,
            'registered_at': datetime.now()
        }
        
        self.logger.info(f"Atuador registrado: '{name}' ({actuator_instance.__class__.__name__})")
        return True
    
    def unregister_device(self, name: str) -> bool:
        """
        Remove um dispositivo do registro.
        
        Args:
            name: Nome do dispositivo
            
        Returns:
            True se removido com sucesso
        """
        if name in self.sensors:
            del self.sensors[name]
            del self.devices[name]
            self.logger.info(f"Sensor '{name}' removido")
            return True
            
        elif name in self.actuators:
            del self.actuators[name]
            del self.devices[name]
            self.logger.info(f"Atuador '{name}' removido")
            return True
        
        self.logger.warning(f"Tentativa de remover dispositivo inexistente: '{name}'")
        return False
    
    # =========================================================================
    # MÉTODOS DE ACESSO A DISPOSITIVOS
    # =========================================================================
    
    def get_sensor(self, name: str) -> Optional[Any]:
        """Obtém um sensor pelo nome."""
        return self.sensors.get(name)
    
    def get_actuator(self, name: str) -> Optional[Any]:
        """Obtém um atuador pelo nome."""
        return self.actuators.get(name)
    
    def get_device(self, name: str) -> Optional[Any]:
        """Obtém qualquer dispositivo pelo nome."""
        device_info = self.devices.get(name)
        return device_info['instance'] if device_info else None
    
    def get_all_sensors(self) -> Dict[str, Any]:
        """Retorna todos os sensores."""
        return self.sensors.copy()
    
    def get_all_actuators(self) -> Dict[str, Any]:
        """Retorna todos os atuadores."""
        return self.actuators.copy()
    
    def get_device_list(self) -> List[Dict[str, Any]]:
        """
        Retorna lista com informações de todos os dispositivos.
        
        Returns:
            Lista de dicionários com informações de cada dispositivo
        """
        device_list = []
        
        for name, info in self.devices.items():
            instance = info['instance']
            device_list.append({
                'name': name,
                'type': info['type'].value,
                'status': info['status'].value,
                'class': instance.__class__.__name__,
                'registered_at': info['registered_at'].isoformat(),
                'details': instance.get_status() if hasattr(instance, 'get_status') else {}
            })
        
        return device_list
    
    # =========================================================================
    # MÉTODOS DE CONTROLE DE ATUADORES
    # =========================================================================
    
    def control_actuator(self, name: str, command: str) -> bool:
        """
        Controla um atuador.
        
        Args:
            name: Nome do atuador
            command: Comando ('on', 'off', 'toggle')
            
        Returns:
            True se comando executado com sucesso
        """
        if name not in self.actuators:
            self.logger.error(f"Atuador '{name}' não encontrado")
            return False
        
        actuator = self.actuators[name]
        
        # Executa comando
        if command == 'on':
            success = actuator.turn_on()
        elif command == 'off':
            success = actuator.turn_off()
        elif command == 'toggle':
            success = actuator.toggle()
        else:
            self.logger.error(f"Comando inválido para atuador '{name}': {command}")
            return False
        
        if success:
            self.stats['total_commands'] += 1
            self.stats['last_updated'] = datetime.now()
            
            # Notifica callbacks
            self._notify_actuator_change(name, command, actuator.get_state())
        
        return success
    
    def get_actuator_state(self, name: str) -> Optional[str]:
        """Obtém o estado de um atuador."""
        if name in self.actuators:
            return self.actuators[name].get_state()
        return None
    
    # =========================================================================
    # MÉTODOS DE LEITURA DE SENSORES
    # =========================================================================
    
    def read_sensor(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Lê um sensor específico.
        
        Args:
            name: Nome do sensor
            
        Returns:
            Dados do sensor ou None se erro
        """
        if name not in self.sensors:
            self.logger.error(f"Sensor '{name}' não encontrado")
            return None
        
        try:
            sensor = self.sensors[name]
            data = sensor.read()
            
            if data and data.get('status') == 'success':
                self.stats['total_readings'] += 1
                self.stats['last_updated'] = datetime.now()
                
                # Notifica callbacks
                self._notify_sensor_update(name, data)
            
            return data
            
        except Exception as e:
            self.logger.error(f"Erro ao ler sensor '{name}': {e}")
            self.stats['errors'] += 1
            return None
    
    def read_all_sensors(self) -> Dict[str, Any]:
        """
        Lê todos os sensores.
        
        Returns:
            Dicionário com nome do sensor e dados lidos
        """
        results = {}
        
        for name in self.sensors:
            data = self.read_sensor(name)
            if data:
                results[name] = data
        
        return results
    
    # =========================================================================
    # MÉTODOS DE CALLBACK
    # =========================================================================
    
    def add_sensor_callback(self, callback: Callable):
        """Adiciona callback para atualizações de sensores."""
        if callback not in self.sensor_update_callbacks:
            self.sensor_update_callbacks.append(callback)
            self.logger.debug(f"Callback de sensor adicionado: {callback.__name__}")
    
    def add_actuator_callback(self, callback: Callable):
        """Adiciona callback para mudanças em atuadores."""
        if callback not in self.actuator_change_callbacks:
            self.actuator_change_callbacks.append(callback)
            self.logger.debug(f"Callback de atuador adicionado: {callback.__name__}")
    
    def remove_callback(self, callback: Callable):
        """Remove um callback."""
        if callback in self.sensor_update_callbacks:
            self.sensor_update_callbacks.remove(callback)
        if callback in self.actuator_change_callbacks:
            self.actuator_change_callbacks.remove(callback)
    
    def _notify_sensor_update(self, sensor_name: str, data: Dict):
        """Notifica todos os callbacks sobre atualização de sensor."""
        for callback in self.sensor_update_callbacks:
            try:
                callback(sensor_name, data)
            except Exception as e:
                self.logger.error(f"Erro em callback de sensor: {e}")
    
    def _notify_actuator_change(self, actuator_name: str, command: str, new_state: str):
        """Notifica todos os callbacks sobre mudança em atuador."""
        for callback in self.actuator_change_callbacks:
            try:
                callback(actuator_name, command, new_state)
            except Exception as e:
                self.logger.error(f"Erro em callback de atuador: {e}")
    
    # =========================================================================
    # MÉTODOS DE MONITORAMENTO E SAÚDE
    # =========================================================================
    
    def _health_check_loop(self):
        """Loop de verificação de saúde dos dispositivos."""
        self.logger.info("Iniciando health check loop")
        
        while self.running:
            try:
                for name, info in self.devices.items():
                    instance = info['instance']
                    
                    # Verifica se dispositivo responde
                    try:
                        if info['type'] == DeviceType.SENSOR:
                            # Testa sensor com leitura rápida
                            if hasattr(instance, 'get_status'):
                                status = instance.get_status()
                                if status.get('active', True):
                                    info['status'] = DeviceStatus.ONLINE
                                else:
                                    info['status'] = DeviceStatus.ERROR
                        else:
                            # Testa atuador
                            if hasattr(instance, 'get_state'):
                                instance.get_state()  # Só para testar
                                info['status'] = DeviceStatus.ONLINE
                    
                    except Exception as e:
                        self.logger.warning(f"Dispositivo '{name}' parece offline: {e}")
                        info['status'] = DeviceStatus.OFFLINE
                        self.stats['errors'] += 1
                
                # Aguarda intervalo
                time.sleep(30)  # Health check a cada 30 segundos
                
            except Exception as e:
                self.logger.error(f"Erro no health check: {e}")
                time.sleep(5)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Retorna status completo do sistema.
        
        Returns:
            Dicionário com status do sistema
        """
        return {
            'status': self.status.value,
            'running': self.running,
            'uptime': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0,
            'devices': {
                'total': len(self.devices),
                'sensors': len(self.sensors),
                'actuators': len(self.actuators),
                'online': sum(1 for d in self.devices.values() if d['status'] == DeviceStatus.ONLINE),
                'offline': sum(1 for d in self.devices.values() if d['status'] == DeviceStatus.OFFLINE),
                'error': sum(1 for d in self.devices.values() if d['status'] == DeviceStatus.ERROR)
            },
            'stats': self.stats.copy(),
            'timestamp': datetime.now().isoformat()
        }
    
    # =========================================================================
    # MÉTODOS DE CICLO DE VIDA
    # =========================================================================
    
    def start(self):
        """Inicia o gerenciador de dispositivos."""
        if self.running:
            self.logger.warning("Device Manager já está em execução")
            return
        
        self.logger.info("Iniciando Device Manager")
        self.running = True
        self.start_time = datetime.now()
        self.status = DeviceStatus.ONLINE
        
        # Inicia thread de health check
        self.health_check_thread = threading.Thread(target=self._health_check_loop, daemon=True)
        self.health_check_thread.start()
        
        self.logger.info(f"Device Manager iniciado com {len(self.devices)} dispositivos")
    
    def stop(self):
        """Para o gerenciador de dispositivos."""
        self.logger.info("Parando Device Manager")
        self.running = False
        self.status = DeviceStatus.OFFLINE
        
        # Aguarda threads terminarem
        if self.health_check_thread and self.health_check_thread.is_alive():
            self.health_check_thread.join(timeout=5)
        
        self.logger.info("Device Manager parado")
    
    # =========================================================================
    # MÉTODOS DE UTILIDADE
    # =========================================================================
    
    def discover_devices(self):
        """
        Tenta descobrir dispositivos automaticamente.
        Útil para desenvolvimento e debugging.
        """
        self.logger.info("Iniciando descoberta automática de dispositivos")
        
        # Tenta descobrir sensores DS18B20
        try:
            from src.sensors.ds18b20_sensor import DS18B20Sensor
            devices = DS18B20Sensor.list_devices()
            
            for device_id in devices:
                name = f"temp_ds18b20_{device_id[-4:]}"
                if name not in self.sensors:
                    self.logger.info(f"DS18B20 encontrado: {device_id}")
                    # Não registra automaticamente, apenas informa
        except Exception as e:
            self.logger.debug(f"Erro na descoberta DS18B20: {e}")
        
        return self.get_device_list()