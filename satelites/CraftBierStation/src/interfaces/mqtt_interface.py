# Gerencia a comunicaÃ§Ã£o MQTT (cliente/broker)
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mqtt_interface.py
Interface MQTT para o servidor de dispositivos.
Gerencia a comunicação via protocolo MQTT, permitindo
publicar dados de sensores e receber comandos para atuadores.
"""

import json
import logging
import time
from typing import Any, Callable, Dict, Optional

import paho.mqtt.client as mqtt


class MQTTInterface:
    """
    Gerenciador de comunicação MQTT.
    Pode atuar como cliente conectando a um broker externo
    ou como broker embutido (futura implementação).
    """
    
    def __init__(self, config: Dict[str, Any], actuator_callback: Optional[Callable] = None):
        """
        Inicializa a interface MQTT.
        
        Args:
            config: Dicionário com configurações MQTT
            actuator_callback: Função para processar comandos de atuadores
        """
        self.config = config
        self.actuator_callback = actuator_callback
        self.logger = logging.getLogger(__name__)
        
        # Configurações
        self.enabled = config.get('enabled', False)
        self.mode = config.get('mode', 'client')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 1883)
        self.username = config.get('username')
        self.password = config.get('password')
        self.topic_prefix = config.get('topic_prefix', 'brewstation/devices')
        self.qos = config.get('qos', 1)
        self.keepalive = config.get('keepalive', 60)
        
        # Cliente MQTT
        self.client = None
        self.connected = False
        self.connection_attempts = 0
        self.max_reconnect_attempts = 5
        
        # Thread para manter a conexão
        self.connection_thread = None
        self.running = False
        
        if self.enabled:
            self._setup_client()
    
    def _setup_client(self):
        """Configura o cliente MQTT com callbacks."""
        self.client = mqtt.Client()
        
        # Configura credenciais se fornecidas
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)
        
        # Configura callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        
        self.logger.info(f"Cliente MQTT configurado para {self.host}:{self.port}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback quando conecta ao broker."""
        if rc == 0:
            self.connected = True
            self.connection_attempts = 0
            self.logger.info(f"Conectado ao broker MQTT {self.host}:{self.port}")
            
            # Inscreve em tópicos de comando
            command_topic = f"{self.topic_prefix}/+/set"
            self.client.subscribe(command_topic, qos=self.qos)
            self.logger.info(f"Inscrito no tópico: {command_topic}")
        else:
            self.connected = False
            self.logger.error(f"Falha na conexão MQTT, código: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback quando desconecta do broker."""
        self.connected = False
        if rc != 0:
            self.logger.warning(f"Desconectado inesperadamente do broker MQTT (código: {rc})")
            self._attempt_reconnect()
        else:
            self.logger.info("Desconectado do broker MQTT")
    
    def _on_message(self, client, userdata, msg):
        """
        Callback quando recebe uma mensagem.
        Processa comandos para atuadores.
        """
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            self.logger.debug(f"Mensagem MQTT recebida: {topic} -> {payload}")
            
            # Extrai o nome do atuador do tópico
            # Formato esperado: prefixo/atuador/set
            parts = topic.split('/')
            if len(parts) >= 3 and parts[-1] == 'set':
                actuator_name = parts[-2]  # O nome do atuador é o penúltimo
                
                # Tenta parsear JSON
                try:
                    data = json.loads(payload)
                    if isinstance(data, dict) and 'state' in data:
                        command = data['state']
                    else:
                        command = payload  # Assume que é o comando direto
                except json.JSONDecodeError:
                    command = payload  # Não é JSON, usa o payload direto
                
                # Chama o callback do atuador se existir
                if self.actuator_callback:
                    self.actuator_callback(actuator_name, command)
                else:
                    self.logger.warning(f"Nenhum callback definido para comando: {actuator_name} -> {command}")
                    
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem MQTT: {e}")
    
    def _on_publish(self, client, userdata, mid):
        """Callback quando uma mensagem é publicada."""
        self.logger.debug(f"Mensagem publicada com ID: {mid}")
    
    def _attempt_reconnect(self):
        """Tenta reconectar ao broker."""
        if self.connection_attempts >= self.max_reconnect_attempts:
            self.logger.error(f"Máximo de tentativas de reconexão atingido ({self.max_reconnect_attempts})")
            return
        
        self.connection_attempts += 1
        wait_time = min(30, 2 ** self.connection_attempts)  # Backoff exponencial
        
        self.logger.info(f"Tentativa {self.connection_attempts} de reconexão em {wait_time}s")
        time.sleep(wait_time)
        
        try:
            self.client.connect(self.host, self.port, self.keepalive)
        except Exception as e:
            self.logger.error(f"Erro na tentativa de reconexão: {e}")
    
    def start(self):
        """Inicia a interface MQTT em uma thread separada."""
        if not self.enabled or not self.client:
            self.logger.info("Interface MQTT desabilitada")
            return
        
        self.running = True
        
        # Conecta ao broker
        try:
            self.client.connect(self.host, self.port, self.keepalive)
            
            # Inicia o loop em uma thread separada
            self.client.loop_start()
            self.logger.info("Interface MQTT iniciada")
            
        except Exception as e:
            self.logger.error(f"Erro ao iniciar interface MQTT: {e}")
            self.running = False
    
    def stop(self):
        """Para a interface MQTT."""
        if self.client:
            self.running = False
            self.client.loop_stop()
            self.client.disconnect()
            self.logger.info("Interface MQTT parada")
    
    def publish_sensor_data(self, sensor_name: str, data: Dict[str, Any]):
        """
        Publica dados de sensor via MQTT.
        
        Args:
            sensor_name: Nome do sensor
            data: Dicionário com dados do sensor
        """
        if not self.enabled or not self.connected or not self.client:
            return
        
        try:
            topic = f"{self.topic_prefix}/sensor/{sensor_name}"
            
            # Garante que os dados são JSON serializáveis
            payload = json.dumps(data, default=str)
            
            info = self.client.publish(topic, payload, qos=self.qos)
            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.debug(f"Dados publicados em {topic}")
            else:
                self.logger.warning(f"Falha ao publicar em {topic}, código: {info.rc}")
                
        except Exception as e:
            self.logger.error(f"Erro ao publicar dados MQTT: {e}")
    
    def publish_actuator_status(self, actuator_name: str, status: Dict[str, Any]):
        """
        Publica status de atuador via MQTT.
        
        Args:
            actuator_name: Nome do atuador
            status: Dicionário com status do atuador
        """
        if not self.enabled or not self.connected or not self.client:
            return
        
        try:
            topic = f"{self.topic_prefix}/actuator/{actuator_name}/status"
            payload = json.dumps(status, default=str)
            self.client.publish(topic, payload, qos=self.qos, retain=True)
            self.logger.debug(f"Status publicado em {topic}")
            
        except Exception as e:
            self.logger.error(f"Erro ao publicar status MQTT: {e}")
    
    def is_connected(self) -> bool:
        """Retorna o status da conexão."""
        return self.connected