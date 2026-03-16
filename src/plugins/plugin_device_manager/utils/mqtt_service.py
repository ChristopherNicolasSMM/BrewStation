"""
Serviço MQTT para comunicação com dispositivos IoT.

Gerencia servidor MQTT embutido rodando em thread separada.
"""

import json
import threading
import logging
from pathlib import Path
from typing import Dict, Optional, Callable, Any, List
import time

logger = logging.getLogger(__name__)

# Tentar importar bibliotecas MQTT
try:
    import paho.mqtt.client as mqtt
    PAHO_MQTT_AVAILABLE = True
except ImportError:
    PAHO_MQTT_AVAILABLE = False
    logger.warning("paho-mqtt não está instalado. Instale com: pip install paho-mqtt")

try:
    from hbmqtt.broker import Broker
    from hbmqtt.client import MQTTClient, ClientException
    HBMQTT_AVAILABLE = True
except ImportError:
    HBMQTT_AVAILABLE = False
    logger.warning("hbmqtt não está instalado. Instale com: pip install hbmqtt")


class MQTTService:
    """
    Serviço para gerenciar servidor MQTT embutido.
    
    O servidor roda em uma thread daemon separada, permitindo comunicação
    assíncrona com dispositivos IoT sem bloquear a aplicação principal.
    """
    
    def __init__(self):
        """Inicializa o serviço MQTT."""
        self.broker = None
        self.thread = None
        self._is_running = False
        self._stop_event = threading.Event()
        self._config = None
        self._clients: Dict[str, Any] = {}  # Clientes MQTT por device_id
        self._subscriptions: Dict[str, list] = {}  # Callbacks por tópico
        self._monitor_subscriptions: Dict[str, int] = {}  # Tópicos de monitoramento e seus QoS
        self._message_history: List[Dict[str, Any]] = []  # Histórico de mensagens para monitoramento
        self._max_history = 1000  # Limite de mensagens no histórico
    
    def start_broker(self, config_path: str):
        """
        Inicia o servidor MQTT em thread separada.
        
        Args:
            config_path: Caminho para arquivo de configuração JSON do broker
        """
        if self._is_running:
            logger.warning("Servidor MQTT já está rodando")
            return
        
        try:
            # Carregar configuração
            config_file = Path(config_path)
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            else:
                # Usar configuração padrão
                self._config = {
                    "enabled": True,
                    "host": "0.0.0.0",
                    "port": 1883,
                    "authentication": {"enabled": False},
                    "topics": {"base": "brewstation/devices"}
                }
            
            if not self._config.get('enabled', True):
                logger.info("Servidor MQTT desabilitado na configuração")
                return
            
            # Criar thread daemon (para automaticamente quando app parar)
            self._stop_event.clear()
            self.thread = threading.Thread(
                target=self._run_broker,
                args=(config_path,),
                daemon=True,  # IMPORTANTE: thread daemon para parar com aplicação
                name="MQTTBrokerThread"
            )
            self._is_running = True
            self.thread.start()
            
            logger.info("Servidor MQTT iniciado em thread separada")
            
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor MQTT: {e}", exc_info=True)
    
    def stop_broker(self):
        """Para o servidor MQTT graciosamente."""
        if not self._is_running:
            return
        
        try:
            self._stop_event.set()
            self._is_running = False
            
            # Desconectar todos os clientes
            for client_id, client in self._clients.items():
                try:
                    if client and hasattr(client, 'disconnect'):
                        client.disconnect()
                except Exception as e:
                    logger.warning(f"Erro ao desconectar cliente {client_id}: {e}")
            
            self._clients.clear()
            self._subscriptions.clear()
            
            logger.info("Servidor MQTT parado")
            
        except Exception as e:
            logger.error(f"Erro ao parar servidor MQTT: {e}", exc_info=True)
    
    #def _run_broker(self, config_path: str):
    #    """
    #    Método interno que roda o broker em thread separada.
    #    
    #    Args:
    #        config_path: Caminho para arquivo de configuração
    #    """
    #    try:
    #        self._is_running = True
    #        logger.info(f"Thread do servidor MQTT iniciada")
    #        
    #        # Por enquanto, implementação básica usando paho-mqtt como cliente
    #        # Para um broker completo, seria necessário usar hbmqtt ou mosquitto
    #        
    #        # Verificar se hbmqtt está disponível para broker completo
    #        if HBMQTT_AVAILABLE:
    #            self._run_hbmqtt_broker()
    #        else:
    #            # Modo simplificado: apenas gerenciar clientes conectados
    #            logger.info("Modo simplificado: gerenciando clientes MQTT (broker externo necessário)")
    #            self._run_simple_mode()
    #        
    #    except Exception as e:
    #        logger.error(f"Erro na thread do servidor MQTT: {e}", exc_info=True)
    #        self._is_running = False
    
    def _run_broker(self, config_path: str):
        
        self._is_running = True
        logger.info("MQTT Service rodando em modo cliente")
        
        while not self._stop_event.is_set():
            time.sleep(1)
            
        self._is_running = False    
    
    def _run_hbmqtt_broker(self):
        """Executa broker usando hbmqtt."""
        try:
            config = {
                'listeners': {
                    'default': {
                        'type': 'tcp',
                        'bind': f"{self._config.get('host', '0.0.0.0')}:{self._config.get('port', 1883)}"
                    }
                },
                'sys_interval': 10,
                'auth': {
                    'allow-anonymous': not self._config.get('authentication', {}).get('enabled', False)
                }
            }
            
            # Criar e iniciar broker
            self.broker = Broker(config)
            
            # Rodar broker até receber sinal de parada
            while not self._stop_event.is_set():
                # O broker precisa ser executado de forma assíncrona
                # Por enquanto, apenas logar que está rodando
                time.sleep(1)
            
            logger.info("Broker hbmqtt parado")
            
        except Exception as e:
            logger.error(f"Erro ao executar broker hbmqtt: {e}", exc_info=True)
    
    def _run_simple_mode(self):
        """Modo simplificado: apenas gerencia conexões de clientes."""
        # Neste modo, assumimos que há um broker MQTT externo rodando
        # O serviço apenas gerencia clientes que se conectam a esse broker
        
        while not self._stop_event.is_set():
            time.sleep(1)
            # Manter thread viva para gerenciar clientes
    
    def connect_device(self, device_config: Dict[str, Any]) -> bool:
        """
        Conecta um dispositivo ao broker MQTT.
        
        Args:
            device_config: Configuração do dispositivo
            
        Returns:
            True se conectado com sucesso
        """
        if not PAHO_MQTT_AVAILABLE:
            logger.error("paho-mqtt não está disponível. Instale com: pip install paho-mqtt")
            return False
        
        try:
            device_id = device_config.get('device_id')
            connection = device_config.get('connection', {})
            topics = device_config.get('topics', {})
            
            # Criar cliente MQTT
            client_id = connection.get('client_id', f"brewstation_{device_id}")
            client = mqtt.Client(client_id=client_id)
            
            # Configurar autenticação se necessário
            username = connection.get('username')
            password = connection.get('password')
            if username and password:
                client.username_pw_set(username, password)
            
            # Configurar callbacks
            def on_connect(client, userdata, flags, rc):
                if rc == 0:
                    logger.info(f"Dispositivo {device_id} conectado ao broker MQTT")
                    # Inscrever em tópicos
                    if topics.get('command'):
                        client.subscribe(topics['command'])
                    if topics.get('status'):
                        client.subscribe(topics['status'])
                else:
                    logger.error(f"Falha ao conectar dispositivo {device_id}: código {rc}")
            
            def on_message(client, userdata, msg):
                topic = msg.topic
                payload = msg.payload.decode('utf-8')
                qos = msg.qos
                retain = msg.retain
                
                logger.debug(f"Mensagem recebida no tópico {topic}: {payload}")
                
                # Adicionar ao histórico
                self.add_message_to_history(topic, payload, 'incoming', qos, retain)
                
                # Chamar callbacks registrados para este tópico
                # Também verificar wildcards
                for sub_topic, callbacks in list(self._subscriptions.items()):
                    if self._topic_matches(topic, sub_topic):
                        for callback in callbacks:
                            try:
                                callback(device_id, topic, payload)
                            except Exception as e:
                                logger.error(f"Erro ao executar callback para tópico {topic}: {e}")
            
            client.on_connect = on_connect
            client.on_message = on_message
            
            # Conectar ao broker
            broker_host = connection.get('broker', 'localhost:1883').split(':')
            host = broker_host[0]
            port = int(broker_host[1]) if len(broker_host) > 1 else 1883
            keepalive = connection.get('keepalive', 60)
            
            client.connect(host, port, keepalive)
            client.loop_start()
            
            # Armazenar cliente
            self._clients[device_id] = client
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao conectar dispositivo {device_id}: {e}", exc_info=True)
            return False
    
    def publish(self, topic: str, payload: str, qos: int = 1, retain: bool = False) -> bool:
        """
        Publica mensagem em um tópico MQTT.
        
        Args:
            topic: Tópico MQTT
            payload: Mensagem a publicar
            qos: Nível de qualidade de serviço (0, 1 ou 2)
            retain: Se a mensagem deve ser retida pelo broker
            
        Returns:
            True se publicado com sucesso
        """
        try:
            # Adicionar ao histórico antes de publicar
            self.add_message_to_history(topic, payload, 'outgoing', qos, retain)
            
            # Publicar usando primeiro cliente disponível ou criar cliente temporário
            if self._clients:
                # Usar primeiro cliente disponível
                client = list(self._clients.values())[0]
                result = client.publish(topic, payload, qos=qos, retain=retain)
                return result.rc == mqtt.MQTT_ERR_SUCCESS
            else:
                # Criar cliente temporário para publicação
                if not PAHO_MQTT_AVAILABLE:
                    return False
                
                temp_client = mqtt.Client()
                broker_host = self._config.get('host', 'localhost')
                broker_port = self._config.get('port', 1883)
                temp_client.connect(broker_host, broker_port)
                result = temp_client.publish(topic, payload, qos=qos, retain=retain)
                temp_client.disconnect()
                return result.rc == mqtt.MQTT_ERR_SUCCESS
            
        except Exception as e:
            logger.error(f"Erro ao publicar mensagem no tópico {topic}: {e}", exc_info=True)
            return False
    
    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """
        Verifica se um tópico corresponde a um padrão (suporta wildcards MQTT).
        
        Args:
            topic: Tópico real
            pattern: Padrão com wildcards (+ para nível único, # para multinível)
            
        Returns:
            True se corresponde
        """
        if pattern == topic:
            return True
        
        # Substituir wildcards por regex
        pattern_regex = pattern.replace('+', '[^/]+').replace('#', '.*')
        import re
        return bool(re.match(f'^{pattern_regex}$', topic))
    
    def subscribe(self, topic: str, callback: Callable[[str, str, str], None] = None, qos: int = 1) -> bool:
        """
        Inscreve em um tópico MQTT.
        
        Args:
            topic: Tópico MQTT
            callback: Função callback(device_id, topic, payload) (opcional)
            qos: Nível de qualidade de serviço (0, 1 ou 2)
            
        Returns:
            True se inscrito com sucesso
        """
        try:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            
            if callback:
                self._subscriptions[topic].append(callback)
            
            # Registrar para monitoramento
            self._monitor_subscriptions[topic] = qos
            
            # Inscrever em todos os clientes conectados
            for client in self._clients.values():
                if client and hasattr(client, 'subscribe'):
                    client.subscribe(topic, qos=qos)
            
            logger.info(f"Inscrito no tópico {topic} com QoS {qos}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inscrever no tópico {topic}: {e}", exc_info=True)
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Desinscreve de um tópico MQTT.
        
        Args:
            topic: Tópico MQTT
            
        Returns:
            True se desinscrito com sucesso
        """
        try:
            # Remover callbacks
            if topic in self._subscriptions:
                del self._subscriptions[topic]
            
            # Remover do monitoramento
            if topic in self._monitor_subscriptions:
                del self._monitor_subscriptions[topic]
            
            # Desinscrever em todos os clientes conectados
            for client in self._clients.values():
                if client and hasattr(client, 'unsubscribe'):
                    client.unsubscribe(topic)
            
            logger.info(f"Desinscrito do tópico {topic}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao desinscrever do tópico {topic}: {e}", exc_info=True)
            return False
    
    def get_subscriptions(self) -> Dict[str, int]:
        """
        Obtém lista de tópicos inscritos.
        
        Returns:
            Dicionário com tópicos e seus QoS
        """
        return self._monitor_subscriptions.copy()
    
    def add_message_to_history(self, topic: str, payload: str, direction: str = 'incoming', qos: int = 0, retain: bool = False):
        """
        Adiciona mensagem ao histórico para monitoramento.
        
        Args:
            topic: Tópico MQTT
            payload: Payload da mensagem
            direction: 'incoming' ou 'outgoing'
            qos: QoS da mensagem
            retain: Se a mensagem foi marcada como retain
        """
        from datetime import datetime
        
        message = {
            'topic': topic,
            'payload': payload,
            'direction': direction,
            'qos': qos,
            'retain': retain,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self._message_history.insert(0, message)
        
        # Limitar histórico
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[:self._max_history]
    
    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Obtém histórico de mensagens.
        
        Args:
            limit: Número máximo de mensagens a retornar
            
        Returns:
            Lista de mensagens
        """
        return self._message_history[:limit]
    
    def is_running(self) -> bool:
        """
        Verifica se o servidor está rodando.
        
        Returns:
            True se está rodando
        """
        return self._is_running

