# Ponto de entrada principal
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
server.py
Ponto de entrada principal para o BrewStation Device Server.
Gerencia a inicialização de todos os componentes:
- Configuração
- Sensores
- Atuadores
- Interfaces (MQTT e HTTP)
"""

import logging
import os
import signal
import sys
import threading
import time

# Adiciona o diretório raiz ao path para importações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.actuators import GPIOActuator
from src.core.config_manager import ConfigManager
from src.interfaces import RESTAPI, MQTTInterface
from src.sensors import DHTSensor, DS18B20Sensor


class DeviceServer:
    """
    Servidor principal de dispositivos.
    Orquestra todos os componentes do sistema.
    """
    
    def __init__(self, config_path: str = "config/device_manager.conf"):
        """
        Inicializa o servidor.
        
        Args:
            config_path: Caminho para o arquivo de configuração
        """
        self.config_path = config_path
        self.running = False
        self.sensors = {}
        self.actuators = {}
        self.mqtt = None
        self.http = None
        self.polling_thread = None
        
        # Configura logging
        self._setup_logging()
        
        # Carrega configuração
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando BrewStation Device Server")
        
        try:
            self.config = ConfigManager(config_path)
            
            # Valida configuração
            valid, errors = self.config.validate()
            if not valid:
                for error in errors:
                    self.logger.error(f"Erro de configuração: {error}")
                raise ValueError("Configuração inválida")
            
            self.logger.info("Configuração carregada com sucesso")
            
        except Exception as e:
            self.logger.error(f"Erro fatal na inicialização: {e}")
            sys.exit(1)
    
    def _setup_logging(self):
        """Configura o sistema de logging."""
        log_dir = self.config.get('general', 'log_dir', 'logs')
        log_level = self.config.get('general', 'log_level', 'INFO')
        
        # Cria diretório de logs se não existir
        os.makedirs(log_dir, exist_ok=True)
        
        # Configura formato do log
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        date_format = '%Y-%m-%d %H:%M:%S'
        
        # Configura logging para arquivo e console
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format=log_format,
            datefmt=date_format,
            handlers=[
                logging.FileHandler(os.path.join(log_dir, 'device_manager.log')),
                logging.StreamHandler()
            ]
        )
    
    def _setup_sensors(self):
        """Inicializa todos os sensores configurados."""
        sensor_configs = self.config.get_sensors()
        
        for sensor_cfg in sensor_configs:
            try:
                sensor_type = sensor_cfg['type']
                sensor_name = sensor_cfg['name']
                pin_logical = sensor_cfg['pin_logical']
                
                self.logger.info(f"Configurando sensor '{sensor_name}' (tipo: {sensor_type})")
                
                # Obtém o pino GPIO real
                gpio_pin = self.config.get_gpio_pin(pin_logical)
                if gpio_pin is None and sensor_type != 'ds18b20':
                    self.logger.error(f"Pino lógico '{pin_logical}' não encontrado para sensor {sensor_name}")
                    continue
                
                # Cria o sensor baseado no tipo
                if sensor_type.startswith('dht'):
                    # Sensor DHT22/DHT11
                    sensor = DHTSensor(sensor_name, sensor_cfg, gpio_pin)
                    self.sensors[sensor_name] = sensor
                    self.logger.info(f"Sensor DHT '{sensor_name}' configurado no GPIO {gpio_pin}")
                    
                elif sensor_type == 'ds18b20':
                    # Sensor DS18B20 (usa device_id em vez de pino)
                    device_id = pin_logical  # Para DS18B20, pin_logical é o device_id
                    try:
                        sensor = DS18B20Sensor(sensor_name, sensor_cfg, device_id)
                        self.sensors[sensor_name] = sensor
                        self.logger.info(f"Sensor DS18B20 '{sensor_name}' configurado (ID: {device_id})")
                    except FileNotFoundError as e:
                        self.logger.error(f"Falha ao configurar DS18B20: {e}")
                        
                elif sensor_type == 'gpio_input':
                    # Sensor digital simples (futura implementação)
                    self.logger.warning(f"Tipo de sensor '{sensor_type}' ainda não implementado")
                    
                else:
                    self.logger.warning(f"Tipo de sensor desconhecido: {sensor_type}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao configurar sensor {sensor_cfg.get('name', 'desconhecido')}: {e}")
        
        self.logger.info(f"Total de sensores configurados: {len(self.sensors)}")
    
    def _setup_actuators(self):
        """Inicializa todos os atuadores configurados."""
        actuator_configs = self.config.get_actuators()
        
        for act_cfg in actuator_configs:
            try:
                act_type = act_cfg['type']
                act_name = act_cfg['name']
                pin_logical = act_cfg['pin_logical']
                initial_state = act_cfg.get('initial_state', 'off')
                
                self.logger.info(f"Configurando atuador '{act_name}' (tipo: {act_type})")
                
                # Obtém o pino GPIO real
                gpio_pin = self.config.get_gpio_pin(pin_logical)
                if gpio_pin is None:
                    self.logger.error(f"Pino lógico '{pin_logical}' não encontrado para atuador {act_name}")
                    continue
                
                # Cria o atuador baseado no tipo
                if act_type == 'gpio_output':
                    actuator = GPIOActuator(act_name, act_cfg, gpio_pin, initial_state)
                    self.actuators[act_name] = actuator
                    self.logger.info(f"Atuador '{act_name}' configurado no GPIO {gpio_pin}")
                else:
                    self.logger.warning(f"Tipo de atuador desconhecido: {act_type}")
                    
            except Exception as e:
                self.logger.error(f"Erro ao configurar atuador {act_cfg.get('name', 'desconhecido')}: {e}")
        
        self.logger.info(f"Total de atuadores configurados: {len(self.actuators)}")
    
    def _setup_interfaces(self):
        """Inicializa as interfaces de comunicação."""
        
        # Configura MQTT
        mqtt_config = self.config.get_mqtt_config()
        if mqtt_config.get('enabled', False):
            self.logger.info("Configurando interface MQTT")
            
            # Callback para comandos de atuadores via MQTT
            def mqtt_actuator_callback(name, command):
                self.logger.info(f"Comando MQTT recebido: {name} -> {command}")
                if name in self.actuators:
                    self.actuators[name].set_state(command)
                    # Publica status atualizado
                    if self.mqtt:
                        self.mqtt.publish_actuator_status(name, self.actuators[name].get_status())
                else:
                    self.logger.warning(f"Atuador '{name}' não encontrado para comando MQTT")
            
            self.mqtt = MQTTInterface(mqtt_config, mqtt_actuator_callback)
        else:
            self.logger.info("Interface MQTT desabilitada")
        
        # Configura HTTP/REST API
        http_config = self.config.get_http_config()
        if http_config.get('enabled', False):
            self.logger.info("Configurando interface HTTP/REST")
            self.http = RESTAPI(http_config, self.sensors, self.actuators)
        else:
            self.logger.info("Interface HTTP desabilitada")
    
    def _polling_loop(self):
        """
        Loop principal de polling dos sensores.
        Executa em thread separada.
        """
        self.logger.info("Iniciando loop de polling de sensores")
        
        while self.running:
            try:
                # Lê todos os sensores
                for name, sensor in self.sensors.items():
                    data = sensor.read()
                    
                    if data and data.get('status') == 'success':
                        # Publica via MQTT se habilitado
                        if self.mqtt and self.mqtt.is_connected():
                            self.mqtt.publish_sensor_data(name, data)
                        
                        # Log em nível DEBUG
                        self.logger.debug(f"Sensor {name}: {data.get('value')} {data.get('unit')}")
                
                # Aguarda o intervalo configurado
                interval = self.config.get_int('general', 'polling_interval', 5)
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Erro no loop de polling: {e}")
                time.sleep(1)  # Evita loop rápido em caso de erro
    
    def _handle_actuator_command(self, name: str, command: str):
        """
        Processa comandos para atuadores.
        
        Args:
            name: Nome do atuador
            command: Comando (on/off/toggle)
        """
        if name in self.actuators:
            self.logger.info(f"Executando comando {command} no atuador {name}")
            
            if command == 'on':
                success = self.actuators[name].turn_on()
            elif command == 'off':
                success = self.actuators[name].turn_off()
            elif command == 'toggle':
                success = self.actuators[name].toggle()
            else:
                self.logger.warning(f"Comando desconhecido: {command}")
                return
            
            if success and self.mqtt:
                # Publica novo status via MQTT
                self.mqtt.publish_actuator_status(name, self.actuators[name].get_status())
        else:
            self.logger.warning(f"Atuador '{name}' não encontrado")
    
    def start(self):
        """Inicia todos os componentes do servidor."""
        self.logger.info("Iniciando BrewStation Device Server")
        
        # Inicializa componentes
        self._setup_sensors()
        self._setup_actuators()
        self._setup_interfaces()
        
        # Marca como em execução
        self.running = True
        
        # Inicia interfaces
        if self.mqtt:
            self.mqtt.start()
        
        if self.http:
            self.http.start()
        
        # Inicia thread de polling
        self.polling_thread = threading.Thread(target=self._polling_loop, daemon=True)
        self.polling_thread.start()
        
        self.logger.info("Servidor iniciado com sucesso!")
        self.logger.info(f"Sensores ativos: {len(self.sensors)}")
        self.logger.info(f"Atuadores ativos: {len(self.actuators)}")
        
        # Mantém o programa principal em execução
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Recebido sinal de interrupção")
            self.stop()
    
    def stop(self):
        """Para todos os componentes do servidor."""
        self.logger.info("Parando BrewStation Device Server")
        
        self.running = False
        
        # Para interfaces
        if self.mqtt:
            self.mqtt.stop()
        
        # Aguarda thread de polling terminar
        if self.polling_thread and self.polling_thread.is_alive():
            self.polling_thread.join(timeout=5)
        
        self.logger.info("Servidor parado")


def main():
    """Função principal."""
    # Configura tratamento de sinais
    def signal_handler(sig, frame):
        print("\nRecebido sinal para encerrar")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Inicia servidor
    server = DeviceServer()
    
    try:
        server.start()
    except Exception as e:
        logging.error(f"Erro não tratado: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()