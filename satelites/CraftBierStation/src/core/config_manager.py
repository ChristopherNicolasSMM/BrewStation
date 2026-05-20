#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_manager.py
Gerenciador de configurações para o servidor de dispositivos.
Responsável por ler e interpretar o arquivo .conf, fornecendo
acesso estruturado às configurações para outros módulos.
"""

import configparser
import logging
import os
from typing import Any, Dict, List, Optional, Tuple


class ConfigManager:
    """
    Gerenciador de configurações que carrega e valida o arquivo .conf
    e fornece métodos para acessar as configurações de forma tipada.
    """
    
    def __init__(self, config_path: str = "config/device_manager.conf"):
        """
        Inicializa o gerenciador de configurações.
        
        Args:
            config_path: Caminho para o arquivo de configuração .conf
        """
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.logger = logging.getLogger(__name__)
        self._load_config()
        
    def _load_config(self) -> None:
        """
        Carrega o arquivo de configuração e valida se as seções necessárias existem.
        
        Raises:
            FileNotFoundError: Se o arquivo de configuração não existir
            configparser.Error: Se houver erro na leitura do arquivo
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        
        try:
            self.config.read(self.config_path)
            self.logger.info(f"Configuração carregada de: {self.config_path}")
            
            # Valida se as seções principais existem
            required_sections = ['general', 'gpio_mapping']
            for section in required_sections:
                if not self.config.has_section(section):
                    self.logger.warning(f"Seção obrigatória '{section}' não encontrada no arquivo de configuração")
                    
        except configparser.Error as e:
            self.logger.error(f"Erro ao ler arquivo de configuração: {e}")
            raise
    
    # =========================================================================
    # MÉTODOS DE ACESSO GERAL
    # =========================================================================
    
    def get(self, section: str, key: str, fallback: Any = None) -> str:
        """
        Obtém um valor string da configuração.
        
        Args:
            section: Seção no arquivo .conf
            key: Chave dentro da seção
            fallback: Valor padrão se a chave não existir
            
        Returns:
            Valor da configuração como string
        """
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return fallback
    
    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Obtém um valor inteiro da configuração."""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_float(self, section: str, key: str, fallback: float = 0.0) -> float:
        """Obtém um valor float da configuração."""
        try:
            return self.config.getfloat(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    def get_boolean(self, section: str, key: str, fallback: bool = False) -> bool:
        """Obtém um valor booleano da configuração."""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return fallback
    
    # =========================================================================
    # MÉTODOS ESPECÍFICOS PARA GPIO
    # =========================================================================
    
    def get_gpio_pin(self, logical_name: str) -> Optional[int]:
        """
        Obtém o número do pino GPIO para um nome lógico.
        
        Args:
            logical_name: Nome lógico definido na seção [gpio_mapping]
                         (ex: SENSOR_TEMP_MOSTURA)
        
        Returns:
            Número do pino GPIO ou None se não encontrado
        
        Exemplo:
            >>> pin = config.get_gpio_pin(constants.SENSOR_TEMP_MOSTURA)
            >>> if pin:
            ...     GPIO.setup(pin, GPIO.IN)
        """
        pin_str = self.get('gpio_mapping', logical_name)
        if pin_str and pin_str.isdigit():
            return int(pin_str)
        return None
    
    def get_all_gpio_mappings(self) -> Dict[str, int]:
        """
        Retorna todos os mapeamentos de GPIO como dicionário.
        
        Returns:
            Dicionário com {nome_logico: numero_pino}
        """
        mappings = {}
        if self.config.has_section('gpio_mapping'):
            for key, value in self.config.items('gpio_mapping'):
                if value.isdigit():
                    mappings[key] = int(value)
        return mappings
    
    # =========================================================================
    # MÉTODOS PARA SENSORES E ATUADORES
    # =========================================================================
    
    def get_sensors(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de todos os sensores configurados.
        
        Returns:
            Lista de dicionários com configuração de cada sensor
            Cada dicionário contém: name, type, pin_logical, interval
        """
        sensors = []
        if self.config.has_section('sensors'):
            for name, value in self.config.items('sensors'):
                # Formato esperado: tipo, pino_logico, intervalo
                parts = [p.strip() for p in value.split(',')]
                if len(parts) >= 2:
                    sensor_config = {
                        'name': name,
                        'type': parts[0],
                        'pin_logical': parts[1],
                        'interval': int(parts[2]) if len(parts) > 2 else self.get_int('general', 'polling_interval', 5)
                    }
                    sensors.append(sensor_config)
        return sensors
    
    def get_actuators(self) -> List[Dict[str, Any]]:
        """
        Retorna lista de todos os atuadores configurados.
        
        Returns:
            Lista de dicionários com configuração de cada atuador
            Cada dicionário contém: name, type, pin_logical, initial_state
        """
        actuators = []
        if self.config.has_section('actuators'):
            for name, value in self.config.items('actuators'):
                # Formato esperado: tipo, pino_logico, estado_inicial
                parts = [p.strip() for p in value.split(',')]
                if len(parts) >= 2:
                    actuator_config = {
                        'name': name,
                        'type': parts[0],
                        'pin_logical': parts[1],
                        'initial_state': parts[2] if len(parts) > 2 else 'off'
                    }
                    actuators.append(actuator_config)
        return actuators
    
    # =========================================================================
    # MÉTODOS PARA INTERFACES
    # =========================================================================
    
    def get_mqtt_config(self) -> Dict[str, Any]:
        """
        Retorna configuração completa do MQTT.
        
        Returns:
            Dicionário com todas as configurações MQTT
        """
        return {
            'enabled': self.get_boolean('mqtt', 'enabled', False),
            'mode': self.get('mqtt', 'mode', 'client'),
            'host': self.get('mqtt', 'host', 'localhost'),
            'port': self.get_int('mqtt', 'port', 1883),
            'username': self.get('mqtt', 'username'),
            'password': self.get('mqtt', 'password'),
            'topic_prefix': self.get('mqtt', 'topic_prefix', 'brewstation/devices'),
            'qos': self.get_int('mqtt', 'qos', 1),
            'keepalive': self.get_int('mqtt', 'keepalive', 60)
        }
    
    def get_http_config(self) -> Dict[str, Any]:
        """
        Retorna configuração completa do HTTP/REST API.
        
        Returns:
            Dicionário com todas as configurações HTTP
        """
        return {
            'enabled': self.get_boolean('http', 'enabled', False),
            'port': self.get_int('http', 'port', 5001),
            'host': self.get('http', 'host', '127.0.0.1'),
            'api_key': self.get('http', 'api_key'),
            'cors_enabled': self.get_boolean('http', 'cors_enabled', False),
            'debug': self.get_boolean('http', 'debug', False)
        }
    
    # =========================================================================
    # MÉTODOS DE VALIDAÇÃO
    # =========================================================================
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Valida se a configuração é consistente.
        
        Returns:
            Tupla (valido, lista_de_erros)
        """
        errors = []
        
        # Valida seção general
        if not self.config.has_section('general'):
            errors.append("Seção [general] obrigatória")
        
        # Valida seção gpio_mapping
        if not self.config.has_section('gpio_mapping'):
            errors.append("Seção [gpio_mapping] obrigatória")
        
        # Valida sensores
        for sensor in self.get_sensors():
            pin = self.get_gpio_pin(sensor['pin_logical'])
            if pin is None:
                errors.append(f"Sensor '{sensor['name']}' refere-se a pino lógico inexistente: {sensor['pin_logical']}")
        
        # Valida atuadores
        for actuator in self.get_actuators():
            pin = self.get_gpio_pin(actuator['pin_logical'])
            if pin is None:
                errors.append(f"Atuador '{actuator['name']}' refere-se a pino lógico inexistente: {actuator['pin_logical']}")
        
        return len(errors) == 0, errors