# Documentação das Classes

## ConfigManager

Gerencia o armazenamento persistente de configurações usando Preferences do ESP32.

### Estruturas de Dados

#### WiFiConfig

```cpp
struct WiFiConfig {
    char ssid[64];           // SSID da rede WiFi
    char password[64];        // Senha da rede
    bool useStaticIP;         // Usar IP estático (true) ou DHCP (false)
    IPAddress ip;             // IP estático
    IPAddress gateway;        // Gateway
    IPAddress subnet;         // Máscara de sub-rede
    IPAddress dns1;           // DNS primário
    IPAddress dns2;           // DNS secundário
};
```

#### MQTTConfig

```cpp
struct MQTTConfig {
    bool enabled;             // MQTT habilitado
    char host[128];           // Host do broker
    uint16_t port;            // Porta do broker
    char username[64];        // Usuário (opcional)
    char password[64];        // Senha (opcional)
    char deviceId[64];        // ID único do dispositivo
    char topicBase[128];      // Tópico base MQTT
};
```

### Métodos Principais

#### `bool begin()`
Inicializa o Preferences com namespace "brewstation".

#### `void end()`
Fecha o Preferences.

#### `bool loadWiFiConfig(WiFiConfig& config)`
Carrega configuração WiFi salva. Retorna `false` se não houver configuração.

#### `bool saveWiFiConfig(const WiFiConfig& config)`
Salva configuração WiFi.

#### `bool hasWiFiConfig()`
Verifica se existe configuração WiFi salva.

#### `bool loadMQTTConfig(MQTTConfig& config)`
Carrega configuração MQTT. Retorna `false` se não houver ou se estiver desabilitado.

#### `bool saveMQTTConfig(const MQTTConfig& config)`
Salva configuração MQTT.

#### `bool hasMQTTConfig()`
Verifica se existe configuração MQTT válida.

#### `void resetAll()`
Remove todas as configurações.

#### `void resetWiFi()`
Remove apenas configurações WiFi.

#### `void resetMQTT()`
Remove apenas configurações MQTT.

#### `String generateDeviceId()`
Gera um ID único baseado no MAC do ESP32 (formato: `ESP32_XXXXXXXX`).

---

## WiFiManager

Gerencia conexões WiFi, modo AP e lógica de fallback.

### Constantes

- `AP_SSID`: "ND_BrewStation"
- `AP_IP`: 192.168.4.1
- `AP_SUBNET`: 255.255.255.0
- `CONNECTION_TIMEOUT`: 30000ms (30 segundos)
- `STATUS_CHECK_INTERVAL`: 10000ms (10 segundos)

### Métodos Principais

#### `bool begin()`
Inicializa WiFi no modo AP+Station.

#### `void update()`
Deve ser chamado no loop principal. Verifica status e executa fallback se necessário.

#### `bool startAP()`
Inicia modo Access Point. Retorna `false` em caso de erro.

#### `void stopAP()`
Para o modo Access Point.

#### `bool isAPMode()`
Retorna `true` se estiver em modo AP.

#### `bool connectToWiFi(const WiFiConfig& config)`
Tenta conectar à rede WiFi configurada. Timeout de 30 segundos.

#### `bool isConnected()`
Verifica se está conectado à rede WiFi.

#### `IPAddress getIP()`
Retorna IP atual (AP_IP se em modo AP, ou localIP se conectado).

#### `String getSSID()`
Retorna SSID da rede atual.

#### `int getRSSI()`
Retorna força do sinal WiFi (0 se em modo AP).

#### `bool shouldFallbackToAP()`
Verifica se deve fazer fallback para modo AP (baseado em timeout).

#### `void handleFallback()`
Executa fallback: desconecta WiFi e inicia modo AP.

#### `wl_status_t getStatus()`
Retorna status WiFi atual.

---

## WebConfigServer

Servidor HTTP para configuração do dispositivo.

### Rotas

- `GET /`: Página de configuração (index.html ou HTML inline)
- `POST /config`: Salva configurações WiFi e MQTT
- `GET /status`: Retorna status JSON
- `GET /reset`: Reseta todas as configurações
- `*`: Serve arquivos do SPIFFS ou 404

### Métodos Principais

#### `bool begin()`
Inicializa SPIFFS e configura rotas do servidor.

#### `void handleClient()`
Deve ser chamado no loop principal. Processa requisições HTTP.

#### `void handleRoot()`
Serve página de configuração (tenta SPIFFS, depois HTML inline).

#### `void handleConfig()`
Processa POST /config: salva WiFi e MQTT, reinicia dispositivo.

#### `void handleStatus()`
Processa GET /status: retorna JSON com status atual.

#### `void handleReset()`
Processa GET /reset: reseta configurações e reinicia.

#### `void handleNotFound()`
Lida com rotas não encontradas (tenta servir do SPIFFS, depois 404).

### Métodos Privados

#### `String getContentType(String filename)`
Retorna Content-Type baseado na extensão do arquivo.

#### `bool handleFileRead(String path)`
Tenta servir arquivo do SPIFFS. Suporta arquivos .gz comprimidos.

#### `void sendJSON(int code, const JsonDocument& doc)`
Envia resposta JSON.

#### `void sendError(const String& message)`
Envia erro JSON.

#### `void parseIPAddress(const String& ipStr, IPAddress& ip)`
Converte string IP para IPAddress.

#### `String IPAddressToString(const IPAddress& ip)`
Converte IPAddress para string.

---

## MQTTClientManager

Gerencia conexão e comunicação MQTT.

### Tópicos MQTT

#### Publicados

- `{topicBase}/{deviceId}/status`: Status do dispositivo (online/offline)
- `{topicBase}/{deviceId}/sensor/{port}`: Leituras de sensores
- `{topicBase}/{deviceId}/actuator/{port}/state`: Estado dos atuadores

#### Subscritos

- `{topicBase}/{deviceId}/actuator/{port}/set`: Comandos para atuadores

### Métodos Principais

#### `bool begin()`
Inicializa cliente MQTT. Retorna `false` se MQTT não estiver configurado/enabled.

#### `void loop()`
Deve ser chamado no loop principal. Processa mensagens MQTT e reconecta se necessário.

#### `bool connect()`
Tenta conectar ao broker. Publica status "online" se bem-sucedido.

#### `void disconnect()`
Desconecta do broker e publica status "offline".

#### `bool isConnected()`
Verifica se está conectado ao broker.

#### `bool publishStatus(const String& status)`
Publica status do dispositivo (QoS 1, retained).

#### `bool publishSensor(const String& port, const String& value)`
Publica leitura de sensor.

#### `bool publishActuatorState(const String& port, const String& state)`
Publica estado de atuador (QoS 1, retained).

#### `bool subscribeToActuator(const String& port)`
Subscreve em tópico de comando de atuador (QoS 1).

#### `void setActuatorCallback(void (*callback)(const String& port, const String& value))`
Define callback para quando comando de atuador for recebido.

### Métodos Privados

#### `String getStatusTopic()`
Retorna tópico de status.

#### `String getSensorTopic(const String& port)`
Retorna tópico de sensor.

#### `String getActuatorSetTopic(const String& port)`
Retorna tópico de comando de atuador.

#### `String getActuatorStateTopic(const String& port)`
Retorna tópico de estado de atuador.

#### `String getDeviceId()`
Retorna Device ID da configuração.

#### `String getTopicBase()`
Retorna tópico base da configuração.

#### `bool reconnect()`
Tenta reconectar ao broker. Retorna `true` se bem-sucedido.

#### `static void mqttCallback(char* topic, byte* payload, unsigned int length)`
Callback estático do PubSubClient. Processa mensagens recebidas.

---

## StatusLED

Gerencia LED de status do dispositivo.

### Estados

- **Modo 0 (Off)**: LED desligado
- **Modo 1 (Fast Blink)**: Piscando rápido (200ms) - Modo AP
- **Modo 2 (Slow Blink)**: Piscando lento (1000ms) - Conectando
- **Modo 3 (On)**: LED ligado - Conectado

### Métodos

#### `StatusLED(int pin = LED_BUILTIN_PIN)`
Construtor. GPIO padrão: 2 (LED built-in do ESP32).

#### `void begin()`
Configura GPIO como OUTPUT e desliga LED.

#### `void setAPMode()`
Define modo 1 (piscando rápido).

#### `void setConnecting()`
Define modo 2 (piscando lento).

#### `void setConnected()`
Define modo 3 (ligado).

#### `void setError()`
Define modo 0 (desligado).

#### `void update()`
Deve ser chamado no loop principal. Atualiza estado do LED.

---

## main.cpp

Arquivo principal que orquestra todos os componentes.

### Variáveis Globais

- `ConfigManager configManager`: Gerenciador de configurações
- `WiFiManager wifiManager`: Gerenciador WiFi
- `WebConfigServer webServer`: Servidor web
- `WiFiClient wifiClient`: Cliente WiFi para MQTT
- `MQTTClientManager mqttClient`: Cliente MQTT
- `StatusLED statusLED`: LED de status

### Funções

#### `void setup()`

1. Inicializa Serial (115200 baud)
2. Verifica reset de fábrica (botão BOOT por 10s)
3. Inicializa ConfigManager
4. Inicializa WiFiManager
5. Tenta conectar WiFi ou inicia AP
6. Inicializa WebServer
7. Inicializa MQTT (se configurado)
8. Configura LED de status

#### `void loop()`

1. Atualiza LED de status
2. Atualiza WiFiManager (verifica fallback)
3. Atualiza LED baseado no estado WiFi
4. Tenta conectar MQTT se necessário
5. Processa requisições web
6. Processa loop MQTT
7. Delay de 10ms

### Reset de Fábrica

Se o botão BOOT (GPIO 0) estiver pressionado por 10 segundos durante o boot, todas as configurações são apagadas.
