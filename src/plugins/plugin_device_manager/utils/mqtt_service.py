"""
Serviço MQTT para comunicação com dispositivos IoT.

Modos de operação (definido em mqtt_broker.json):
  - use_embedded_broker: true  → sobe broker amqtt em thread própria
  - use_embedded_broker: false → conecta como cliente paho a broker externo

NOTAS DE COMPATIBILIDADE:
  - paho-mqtt 2.x exige CallbackAPIVersion no construtor → tratado automaticamente
  - Host de bind "0.0.0.0" é convertido para "127.0.0.1" nas conexões de cliente
"""

import json
import threading
import logging
import re
import time
from pathlib import Path
from typing import Dict, Optional, Callable, Any, List

logger = logging.getLogger(__name__)

# ── paho-mqtt ──────────────────────────────────────────────────────────────────
try:
    import paho.mqtt.client as mqtt

    # paho 2.x introduziu CallbackAPIVersion — detectar e adaptar
    if hasattr(mqtt, 'CallbackAPIVersion'):
        _PAHO_V2 = True
    else:
        _PAHO_V2 = False

    PAHO_MQTT_AVAILABLE = True
except ImportError:
    PAHO_MQTT_AVAILABLE = False
    _PAHO_V2 = False
    logger.warning("paho-mqtt não instalado. Execute: pip install paho-mqtt")

# ── amqtt (broker embutido) ────────────────────────────────────────────────────
try:
    from amqtt.broker import Broker
    AMQTT_AVAILABLE = True
except ImportError:
    AMQTT_AVAILABLE = False
    try:
        from hbmqtt.broker import Broker
        AMQTT_AVAILABLE = True
        logger.warning("hbmqtt está descontinuado. Prefira: pip install amqtt")
    except ImportError:
        logger.warning(
            "Broker embutido indisponível. "
            "Para modo embutido execute: pip install amqtt"
        )


def _make_paho_client(client_id: str = "") -> Any:
    """
    Cria um cliente paho compatível com versões 1.x e 2.x.

    Args:
        client_id: ID do cliente MQTT

    Returns:
        Instância de mqtt.Client pronta para uso
    """
    if not PAHO_MQTT_AVAILABLE:
        raise RuntimeError("paho-mqtt não está instalado")

    if _PAHO_V2:
        # paho 2.x — exige CallbackAPIVersion
        return mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id=client_id
        )
    else:
        # paho 1.x — API clássica
        return mqtt.Client(client_id=client_id)


def _connect_host(bind_host: str) -> str:
    """
    Converte endereço de bind em endereço de conexão.
    '0.0.0.0' não é um destino válido para clientes — usa '127.0.0.1'.

    Args:
        bind_host: Host configurado no broker (pode ser '0.0.0.0')

    Returns:
        Host para uso em client.connect()
    """
    if bind_host in ('0.0.0.0', '::'):
        return '127.0.0.1'
    return bind_host


class MQTTService:
    """
    Serviço de comunicação MQTT para o BrewStation.

    Gerencia broker embutido (amqtt) ou cliente externo (paho),
    histórico de mensagens e subscriptions para monitoramento.
    """

    def __init__(self):
        self.broker = None
        self.thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._config: Optional[Dict] = None
        self._clients: Dict[str, Any] = {}
        self._subscriptions: Dict[str, list] = {}
        self._monitor_subscriptions: Dict[str, int] = {}
        self._message_history: List[Dict[str, Any]] = []
        self._max_history = 1000
        self._loop = None
        self._lock = threading.Lock()
        self.__is_running = False

    # ── Propriedade is_running ─────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        """True se o serviço está ativo."""
        with self._lock:
            return self.__is_running

    @is_running.setter
    def is_running(self, value: bool):
        with self._lock:
            self.__is_running = value

    # ── Ciclo de vida ──────────────────────────────────────────────────────────

    def start_broker(self, config_path: str):
        """
        Inicia o serviço MQTT em thread daemon separada.

        Args:
            config_path: Caminho para o arquivo mqtt_broker.json
        """
        if self.is_running:
            logger.warning("MQTTService já está rodando")
            return

        try:
            cfg_file = Path(config_path)
            if cfg_file.exists():
                with open(cfg_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"Config MQTT carregada de {config_path}")
            else:
                logger.warning(f"Arquivo {config_path} não encontrado — usando padrão")
                self._config = {
                    "enabled": True,
                    "host": "127.0.0.1",
                    "port": 1883,
                    "use_embedded_broker": False,
                    "authentication": {"enabled": False},
                    "topics": {"base": "brewstation/devices"}
                }

            if not self._config.get('enabled', True):
                logger.info("MQTTService desabilitado na configuração")
                return

            self._stop_event.clear()
            self.thread = threading.Thread(
                target=self._run_broker,
                daemon=True,
                name="MQTTBrokerThread"
            )
            self.thread.start()

            # Aguarda confirmação de boot (até 10 s para broker embutido)
            timeout = 10.0 if self._config.get('use_embedded_broker') else 2.0
            deadline = time.time() + timeout
            while time.time() < deadline:
                if self.is_running:
                    break
                time.sleep(0.1)

            if self.is_running:
                mode = "embutido (amqtt)" if self._config.get('use_embedded_broker') else "cliente externo"
                logger.info(f"MQTTService iniciado — modo: {mode}")
            else:
                logger.warning("MQTTService: thread iniciou mas ainda não confirmou boot")

        except Exception as e:
            logger.error(f"Erro ao iniciar MQTTService: {e}", exc_info=True)

    def stop_broker(self):
        """Para o serviço MQTT de forma graciosa."""
        if not self.is_running:
            return

        try:
            self._stop_event.set()

            # Para o loop asyncio do broker embutido
            if self._loop and self._loop.is_running():
                self._loop.call_soon_threadsafe(self._loop.stop)

            # Desconecta clientes paho
            for cid, client in list(self._clients.items()):
                try:
                    client.disconnect()
                    client.loop_stop()
                except Exception as e:
                    logger.warning(f"Erro ao desconectar cliente {cid}: {e}")

            self._clients.clear()
            self._subscriptions.clear()
            self._monitor_subscriptions.clear()

            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=8)

        except Exception as e:
            logger.error(f"Erro ao parar MQTTService: {e}", exc_info=True)
        finally:
            self.is_running = False
            logger.info("MQTTService parado")

    # ── Threads internas ───────────────────────────────────────────────────────

    def _run_broker(self):
        """Decide o modo de execução com base na configuração."""
        use_embedded = self._config.get('use_embedded_broker', False)

        if use_embedded:
            if AMQTT_AVAILABLE:
                self._run_embedded_broker()
            else:
                logger.error(
                    "use_embedded_broker=True mas amqtt não está instalado. "
                    "Execute: pip install amqtt"
                )
                self.is_running = True   # marca como rodando para não travar o boot
                while not self._stop_event.is_set():
                    time.sleep(1)
                self.is_running = False
        else:
            self._run_client_mode()

    def _run_embedded_broker(self):
        """
        Sobe o broker amqtt nesta thread via asyncio.
        O loop é criado aqui e destruído ao encerrar.
        """
        import asyncio

        host = self._config.get('host', '0.0.0.0')
        port = self._config.get('port', 1883)

        config = {
            'listeners': {
                'default': {
                    'type': 'tcp',
                    'bind': f"{host}:{port}"
                }
            },
            'sys_interval': 10,
            'auth': {
                'allow-anonymous': not self._config.get(
                    'authentication', {}
                ).get('enabled', False)
            },
            'topic-check': {'enabled': False}
        }

        async def run():
            self.broker = Broker(config)
            await self.broker.start()
            self.is_running = True
            logger.info(f"Broker amqtt ouvindo em {host}:{port}")

            while not self._stop_event.is_set():
                await asyncio.sleep(0.5)

            logger.info("Encerrando broker amqtt...")
            await self.broker.shutdown()

        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(run())
        except Exception as e:
            logger.error(f"Erro no broker embutido: {e}", exc_info=True)
        finally:
            try:
                if self._loop and not self._loop.is_closed():
                    self._loop.close()
            except Exception:
                pass
            self.is_running = False
            logger.info("Thread do broker embutido encerrada")

    def _run_client_mode(self):
        """
        Modo cliente externo: mantém a thread viva para gerenciar callbacks.
        O broker deve estar rodando externamente (ex: Mosquitto).
        """
        self.is_running = True
        connect_host = _connect_host(self._config.get('host', '127.0.0.1'))
        logger.info(
            f"MQTTService em modo cliente externo — "
            f"broker esperado em {connect_host}:{self._config.get('port', 1883)}"
        )
        while not self._stop_event.is_set():
            time.sleep(1)
        self.is_running = False

    # ── Dispositivos ───────────────────────────────────────────────────────────

    def connect_device(self, device_config: Dict[str, Any]) -> bool:
        """
        Conecta um dispositivo ao broker via paho.

        Args:
            device_config: Configuração do dispositivo

        Returns:
            True se conectado com sucesso
        """
        if not PAHO_MQTT_AVAILABLE:
            logger.error("paho-mqtt não disponível")
            return False

        try:
            device_id = device_config.get('device_id')
            connection = device_config.get('connection', {})
            topics = device_config.get('topics', {})

            client_id = connection.get('client_id', f"brewstation_{device_id}")
            client = _make_paho_client(client_id)

            username = connection.get('username')
            password = connection.get('password')
            if username and password:
                client.username_pw_set(username, password)

            def on_connect(cl, userdata, flags, rc):
                if rc == 0:
                    logger.info(f"Dispositivo {device_id} conectado ao broker")
                    for t in [topics.get('command'), topics.get('status')]:
                        if t:
                            cl.subscribe(t)
                    for t, qos in self._monitor_subscriptions.items():
                        cl.subscribe(t, qos=qos)
                else:
                    logger.error(f"Falha ao conectar dispositivo {device_id}: rc={rc}")

            def on_message(cl, userdata, msg):
                topic = msg.topic
                try:
                    payload = msg.payload.decode('utf-8')
                except UnicodeDecodeError:
                    payload = str(msg.payload)

                self.add_message_to_history(
                    topic, payload, 'incoming', msg.qos, msg.retain
                )

                for sub_topic, callbacks in list(self._subscriptions.items()):
                    if self._topic_matches(topic, sub_topic):
                        for cb in callbacks:
                            try:
                                cb(device_id, topic, payload)
                            except Exception as e:
                                logger.error(f"Erro no callback {topic}: {e}")

            client.on_connect = on_connect
            client.on_message = on_message

            # Determina broker de destino
            if connection.get('broker'):
                parts = connection['broker'].split(':')
                broker_host = _connect_host(parts[0])
                broker_port = int(parts[1]) if len(parts) > 1 else 1883
            else:
                broker_host = _connect_host(
                    self._config.get('host', '127.0.0.1') if self._config else '127.0.0.1'
                )
                broker_port = self._config.get('port', 1883) if self._config else 1883

            keepalive = connection.get('keepalive', 60)
            logger.info(f"Conectando dispositivo {device_id} → {broker_host}:{broker_port}")
            client.connect(broker_host, broker_port, keepalive)
            client.loop_start()

            self._clients[device_id] = client
            return True

        except Exception as e:
            logger.error(f"Erro ao conectar dispositivo {device_id}: {e}", exc_info=True)
            return False

    # ── Publish / Subscribe ────────────────────────────────────────────────────

    def publish(
        self,
        topic: str,
        payload: str,
        qos: int = 1,
        retain: bool = False
    ) -> bool:
        """
        Publica mensagem em um tópico MQTT.

        Args:
            topic:   Tópico MQTT
            payload: Mensagem (string)
            qos:     Qualidade de serviço (0, 1 ou 2)
            retain:  Se o broker deve reter a mensagem

        Returns:
            True se publicado com sucesso
        """
        try:
            self.add_message_to_history(topic, payload, 'outgoing', qos, retain)

            # ── usa cliente permanente se disponível ───────────────────────────
            if self._clients:
                client = list(self._clients.values())[0]
                result = client.publish(topic, payload, qos=qos, retain=retain)
                if hasattr(result, 'rc'):
                    return result.rc == mqtt.MQTT_ERR_SUCCESS
                return True

            # ── sem clientes: cria temporário ──────────────────────────────────
            if not PAHO_MQTT_AVAILABLE or not self._config:
                logger.error("Não é possível publicar: paho indisponível ou sem config")
                return False

            broker_host = _connect_host(self._config.get('host', '127.0.0.1'))
            broker_port = self._config.get('port', 1883)

            temp_client = _make_paho_client()
            try:
                logger.debug(f"Cliente temporário conectando em {broker_host}:{broker_port}")
                temp_client.connect(broker_host, broker_port, keepalive=10)
                result = temp_client.publish(topic, payload, qos=qos, retain=retain)
                temp_client.disconnect()

                if hasattr(result, 'rc'):
                    ok = result.rc == mqtt.MQTT_ERR_SUCCESS
                    if not ok:
                        logger.error(f"Publish falhou: rc={result.rc}")
                    return ok
                return True

            except Exception as e:
                logger.error(f"Erro no cliente temporário: {e}")
                return False

        except Exception as e:
            logger.error(f"Erro ao publicar em {topic}: {e}", exc_info=True)
            return False

    def subscribe(
        self,
        topic: str,
        callback: Optional[Callable[[str, str, str], None]] = None,
        qos: int = 1
    ) -> bool:
        """
        Inscreve em um tópico MQTT.

        Args:
            topic:    Tópico (suporta wildcards + e #)
            callback: callback(device_id, topic, payload) — opcional
            qos:      Qualidade de serviço

        Returns:
            True se inscrito com sucesso
        """
        try:
            if topic not in self._subscriptions:
                self._subscriptions[topic] = []
            if callback:
                self._subscriptions[topic].append(callback)

            self._monitor_subscriptions[topic] = qos

            for client in self._clients.values():
                try:
                    client.subscribe(topic, qos=qos)
                except Exception as e:
                    logger.warning(f"Erro ao inscrever cliente em {topic}: {e}")

            logger.info(f"Inscrito no tópico {topic} com QoS {qos}")
            return True

        except Exception as e:
            logger.error(f"Erro ao inscrever em {topic}: {e}", exc_info=True)
            return False

    def unsubscribe(self, topic: str) -> bool:
        """
        Desinscreve de um tópico MQTT.

        Args:
            topic: Tópico a desinscrever

        Returns:
            True se desinscrito com sucesso
        """
        try:
            self._subscriptions.pop(topic, None)
            self._monitor_subscriptions.pop(topic, None)

            for client in self._clients.values():
                try:
                    client.unsubscribe(topic)
                except Exception as e:
                    logger.warning(f"Erro ao desinscrever cliente de {topic}: {e}")

            logger.info(f"Desinscrito de {topic}")
            return True

        except Exception as e:
            logger.error(f"Erro ao desinscrever de {topic}: {e}", exc_info=True)
            return False

    # ── Histórico e consultas ──────────────────────────────────────────────────

    def get_subscriptions(self) -> Dict[str, int]:
        """Retorna dict {tópico: qos} dos tópicos inscritos."""
        return self._monitor_subscriptions.copy()

    def add_message_to_history(
        self,
        topic: str,
        payload: str,
        direction: str = 'incoming',
        qos: int = 0,
        retain: bool = False
    ):
        """
        Adiciona mensagem ao histórico em memória.

        Args:
            topic:     Tópico MQTT
            payload:   Conteúdo da mensagem
            direction: 'incoming' ou 'outgoing'
            qos:       Nível QoS
            retain:    Flag retain
        """
        from datetime import datetime, timezone
        entry = {
            'topic': topic,
            'payload': payload,
            'direction': direction,
            'qos': qos,
            'retain': retain,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        self._message_history.insert(0, entry)
        if len(self._message_history) > self._max_history:
            self._message_history = self._message_history[:self._max_history]

    def get_message_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retorna histórico de mensagens, mais recente primeiro.

        Args:
            limit: Quantidade máxima de mensagens

        Returns:
            Lista de mensagens
        """
        return self._message_history[:limit]

    # ── Utilitário de tópicos ──────────────────────────────────────────────────

    def _topic_matches(self, topic: str, pattern: str) -> bool:
        """
        Verifica se um tópico corresponde a um padrão MQTT.

        Suporte a wildcards:
          +  → qualquer segmento único (sem /)
          #  → qualquer sequência de segmentos (deve ser o último)

        Args:
            topic:   Tópico real recebido
            pattern: Padrão com wildcards

        Returns:
            True se corresponde
        """
        if pattern == topic:
            return True
        if '#' in pattern and not pattern.endswith('#'):
            return False
        regex = pattern.replace('+', '[^/]+').replace('#', '.*')
        return bool(re.match(f'^{regex}$', topic))
