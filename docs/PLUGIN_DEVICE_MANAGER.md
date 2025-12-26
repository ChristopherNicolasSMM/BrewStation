# Plugin Device Manager - Documentação Completa

## Visão Geral

O Plugin Device Manager é um sistema completo de gerenciamento de dispositivos IoT para o BrewStation. Ele fornece:

- Gerenciamento de dispositivos IoT (sensores, atuadores, gateways)
- Servidor MQTT embutido para comunicação com dispositivos
- Sistema de portas configuráveis (GPIO, entradas, saídas)
- API pública para outros plugins acessarem dispositivos
- Interface web completa para gerenciamento e monitoramento
- Sistema de monitoramento MQTT em tempo real

## Instalação

### Pré-requisitos

```bash
pip install paho-mqtt
# Opcional: para broker completo
pip install hbmqtt
```

### Instalação do Plugin

```bash
python run.py plugin -i device_manager
```

### Ativação

O plugin pode ser ativado via interface web ou CLI:

```bash
python run.py plugin -a device_manager
```

## Estrutura do Plugin

```
src/plugins/plugin_device_manager/
├── plugin.py                    # Classe principal do plugin
├── install.json                 # Configuração do plugin
├── menu_config.json             # Configuração de menu
├── model/
│   └── device_metadata.py       # Modelo SQLAlchemy (metadados)
├── api/
│   └── routes/
│       └── device_routes.py     # Rotas API REST
├── controller/
│   └── routes.py                # Rotas web (páginas HTML)
├── utils/
│   ├── device_registry.py       # Gerenciamento de dispositivos
│   ├── mqtt_service.py          # Servidor MQTT
│   ├── device_api.py            # API pública para outros plugins
│   └── model_loader.py          # Helper para modelos prefixados
├── templates/
│   ├── device_manager.html      # Lista de dispositivos
│   ├── device_form.html         # Formulário de cadastro/edição
│   ├── mqtt_config.html         # Configuração do broker MQTT
│   ├── mqtt_monitor.html        # Monitoramento MQTT
│   └── status_logs.html         # Logs e status
├── static/
│   └── device_manager/
│       ├── device.js            # JavaScript frontend
│       └── styles.css           # Estilos CSS
└── data/                        # Dados do plugin
    ├── devices/
    │   ├── configs/              # Configurações JSON dos dispositivos
    │   └── states/               # Estados JSON dos dispositivos
    └── mqtt_broker.json          # Configuração do broker MQTT
```

## Conceitos Principais

### Dispositivos

Um dispositivo IoT é representado por:

- **Metadados no Banco de Dados**: Informações básicas (nome, tipo, protocolo)
- **Configuração em JSON**: Detalhes completos salvos em `data/devices/configs/{device_id}.json`
- **Estado em JSON**: Estado atual salvo em `data/devices/states/{device_id}.json`

### Portas IoT

Cada dispositivo pode ter múltiplas portas configuradas:

- **Tipo**: `sensor` ou `actuator`
- **Direção**: `input` (entrada) ou `output` (saída)
- **Função**: Descrição da função (ex: `temperature`, `humidity`, `relay`)

Exemplo de configuração de portas:

```json
{
  "GPIO_32": {
    "type": "sensor",
    "direction": "input",
    "function": "temperature",
    "unit": "celsius"
  },
  "GPIO_25": {
    "type": "actuator",
    "direction": "output",
    "function": "relay",
    "default": false
  }
}
```

### Servidor MQTT

O plugin inclui um servidor MQTT embutido que:

- Roda em thread daemon separada
- Para automaticamente quando a aplicação principal para
- Suporta autenticação configurável
- Gerencia conexões de dispositivos automaticamente

## Uso da Interface Web

### Gerenciar Dispositivos

1. **Acessar**: Menu "Dispositivos IoT > Todos Dispositivos"
2. **Adicionar**: Clique em "Adicionar Dispositivo"
3. **Configurar**:
   - Nome e tipo do dispositivo
   - Protocolo (MQTT, HTTP, WebSocket)
   - Configuração MQTT (se aplicável)
   - Portas IoT (GPIO, função, direção)

### Configurar Broker MQTT

1. **Acessar**: Menu "Dispositivos IoT > Brokers MQTT"
2. **Configurar**:
   - Host e porta do broker
   - Autenticação (se necessário)
   - Tópicos base permitidos
3. **Iniciar/Parar**: Use os botões para controlar o servidor

### Monitorar Mensagens MQTT

1. **Acessar**: Menu "Dispositivos IoT > Monitoramento MQTT"
2. **Inscrever-se**: Digite um tópico e clique em "Inscrever"
3. **Publicar**: Use o formulário para enviar mensagens de teste
4. **Monitorar**: Mensagens aparecem automaticamente na área de mensagens

## API REST

### Dispositivos

#### Listar Dispositivos

```http
GET /api/device_manager/devices
```

**Query Parameters:**
- `type`: Filtrar por tipo (sensor, actuator, gateway)
- `protocol`: Filtrar por protocolo (mqtt, http, websocket)

**Resposta:**
```json
{
  "success": true,
  "devices": [
    {
      "device_id": "esp32-sensor-001",
      "name": "Sensor de Temperatura",
      "type": "sensor",
      "protocol": "mqtt",
      "ports": {...},
      "state": {...}
    }
  ],
  "total": 1
}
```

#### Obter Dispositivo

```http
GET /api/device_manager/devices/{device_id}
```

#### Criar Dispositivo

```http
POST /api/device_manager/devices
Content-Type: application/json

{
  "name": "Sensor de Temperatura",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "localhost:1883",
    "client_id": "brewstation_sensor_001"
  },
  "topics": {
    "command": "brewstation/devices/001/command",
    "status": "brewstation/devices/001/status",
    "telemetry": "brewstation/devices/001/telemetry"
  },
  "ports": {
    "GPIO_32": {
      "type": "sensor",
      "direction": "input",
      "function": "temperature"
    }
  }
}
```

#### Atualizar Dispositivo

```http
PUT /api/device_manager/devices/{device_id}
Content-Type: application/json

{
  "name": "Novo Nome",
  "ports": {...}
}
```

#### Remover Dispositivo

```http
DELETE /api/device_manager/devices/{device_id}
```

### Portas

#### Obter Todas as Portas

```http
GET /api/device_manager/devices/{device_id}/ports/all
```

**Resposta:**
```json
{
  "success": true,
  "ports": {
    "GPIO_32": {
      "type": "sensor",
      "direction": "input",
      "function": "temperature",
      "current_value": 68.5,
      "last_update": "2024-01-01T12:00:00Z",
      "status": "active"
    }
  },
  "total": 1
}
```

#### Configurar Portas

```http
POST /api/device_manager/devices/{device_id}/ports
Content-Type: application/json

{
  "ports": {
    "GPIO_32": {
      "type": "sensor",
      "direction": "input",
      "function": "temperature"
    }
  }
}
```

### MQTT

#### Status do Broker

```http
GET /api/device_manager/mqtt/status
```

#### Configuração do Broker

```http
GET /api/device_manager/mqtt/config
POST /api/device_manager/mqtt/config
```

#### Inscrever-se em Tópico

```http
POST /api/device_manager/mqtt/subscribe
Content-Type: application/json

{
  "topic": "brewstation/devices/+/telemetry",
  "qos": 1
}
```

#### Desinscrever-se de Tópico

```http
POST /api/device_manager/mqtt/unsubscribe
Content-Type: application/json

{
  "topic": "brewstation/devices/+/telemetry"
}
```

#### Publicar Mensagem

```http
POST /api/device_manager/mqtt/publish
Content-Type: application/json

{
  "topic": "brewstation/test/message",
  "payload": "{\"test\": \"message\"}",
  "qos": 1,
  "retain": false
}
```

#### Obter Histórico de Mensagens

```http
GET /api/device_manager/mqtt/messages?limit=100
```

## API para Outros Plugins

O `DeviceAPIService` fornece uma interface simples para outros plugins acessarem dispositivos:

### Importar o Serviço

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService
```

### Obter Status de um Dispositivo

```python
status = DeviceAPIService.get_device_status('esp32-sensor-001')
# Retorna: {
#   'device_id': 'esp32-sensor-001',
#   'name': 'Sensor de Temperatura',
#   'status': 'online',
#   'ports': {...},
#   'telemetry': {...}
# }
```

### Obter Valor de uma Porta

```python
temperature = DeviceAPIService.get_port_value('esp32-sensor-001', 'GPIO_32')
# Retorna: 68.5
```

### Obter Todas as Portas

```python
all_ports = DeviceAPIService.get_all_ports('esp32-sensor-001')
# Retorna: {
#   'GPIO_32': {
#     'type': 'sensor',
#     'direction': 'input',
#     'function': 'temperature',
#     'current_value': 68.5,
#     'last_update': '2024-01-01T12:00:00Z'
#   }
# }
```

### Definir Valor de uma Porta

```python
success = DeviceAPIService.set_port_value('esp32-sensor-001', 'GPIO_25', True)
# Envia comando para ativar/desativar porta
```

### Enviar Comando

```python
success = DeviceAPIService.send_command(
    'esp32-sensor-001',
    'set_temperature',
    {'target': 70.0}
)
```

### Inscrever-se em Telemetria

```python
def handle_telemetry(device_id, data):
    print(f"Telemetria de {device_id}: {data}")

DeviceAPIService.subscribe_telemetry('esp32-sensor-001', handle_telemetry)
```

### Listar Dispositivos por Tipo de Porta

```python
# Obter todos os dispositivos com sensores
sensor_devices = DeviceAPIService.list_devices_by_port_type('sensor')

# Obter todos os dispositivos com atuadores
actuator_devices = DeviceAPIService.list_devices_by_port_type('actuator')
```

### Obter Configuração de Portas

```python
# Obter configuração de uma porta específica
port_config = DeviceAPIService.get_port_config('esp32-sensor-001', 'GPIO_32')

# Obter configuração de todas as portas
all_ports_config = DeviceAPIService.get_port_config('esp32-sensor-001')
```

## Estrutura de Dados

### Configuração de Dispositivo

Arquivo: `data/devices/configs/{device_id}.json`

```json
{
  "device_id": "esp32-sensor-001",
  "name": "Sensor de Temperatura da Mostura",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "localhost:1883",
    "client_id": "brewstation_sensor_001",
    "username": null,
    "password": null,
    "keepalive": 60,
    "qos": 1
  },
  "topics": {
    "command": "brewstation/devices/001/command",
    "status": "brewstation/devices/001/status",
    "telemetry": "brewstation/devices/001/telemetry"
  },
  "ports": {
    "GPIO_32": {
      "type": "sensor",
      "function": "temperature",
      "direction": "input",
      "unit": "celsius",
      "min": 0,
      "max": 100
    },
    "GPIO_33": {
      "type": "sensor",
      "function": "humidity",
      "direction": "input",
      "unit": "percent"
    },
    "GPIO_25": {
      "type": "actuator",
      "function": "relay",
      "direction": "output",
      "default": false
    }
  },
  "properties": {
    "firmware": "1.0.0",
    "location": "Sala de Brassagem"
  },
  "created_at": "2024-01-01T12:00:00Z",
  "updated_at": "2024-01-01T12:00:00Z"
}
```

### Estado de Dispositivo

Arquivo: `data/devices/states/{device_id}.json`

```json
{
  "device_id": "esp32-sensor-001",
  "status": "online",
  "last_seen": "2024-01-01T12:00:00Z",
  "ports": {
    "GPIO_32": {
      "value": 68.5,
      "timestamp": "2024-01-01T12:00:00Z"
    },
    "GPIO_33": {
      "value": 45.2,
      "timestamp": "2024-01-01T12:00:00Z"
    },
    "GPIO_25": {
      "value": false,
      "timestamp": "2024-01-01T12:00:00Z"
    }
  },
  "telemetry": {
    "temperature": 68.5,
    "humidity": 45.2,
    "voltage": 3.8
  },
  "last_error": null
}
```

### Configuração do Broker MQTT

Arquivo: `data/mqtt_broker.json`

```json
{
  "enabled": true,
  "host": "0.0.0.0",
  "port": 1883,
  "authentication": {
    "enabled": false,
    "username": null,
    "password": null
  },
  "topics": {
    "base": "brewstation/devices",
    "allowed_patterns": ["brewstation/devices/+/+"]
  },
  "ssl": {
    "enabled": false,
    "cert_file": null,
    "key_file": null
  }
}
```

## Exemplos de Uso

### Exemplo 1: Criar um Dispositivo Sensor

```python
from plugins.plugin_device_manager.utils.device_registry import DeviceRegistry
from flask import current_app

# Obter registry
plugin_manager = current_app.plugin_manager
plugin = plugin_manager.get_plugin('device_manager')
registry = DeviceRegistry(plugin.plugin_path)

# Criar dispositivo
device_config = {
    "name": "Sensor de Temperatura",
    "type": "sensor",
    "protocol": "mqtt",
    "connection": {
        "broker": "localhost:1883",
        "client_id": "brewstation_temp_001"
    },
    "topics": {
        "command": "brewstation/devices/temp001/command",
        "status": "brewstation/devices/temp001/status",
        "telemetry": "brewstation/devices/temp001/telemetry"
    },
    "ports": {
        "GPIO_32": {
            "type": "sensor",
            "direction": "input",
            "function": "temperature",
            "unit": "celsius"
        }
    }
}

device_id = registry.register_device(device_config)
```

### Exemplo 2: Ler Temperatura de um Sensor

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService

# Obter valor da porta de temperatura
temperature = DeviceAPIService.get_port_value('esp32-sensor-001', 'GPIO_32')

if temperature is not None:
    print(f"Temperatura atual: {temperature}°C")
else:
    print("Sensor não disponível")
```

### Exemplo 3: Controlar um Atuador

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService

# Ativar relé
success = DeviceAPIService.set_port_value('esp32-sensor-001', 'GPIO_25', True)

if success:
    print("Relé ativado")
else:
    print("Erro ao ativar relé")
```

### Exemplo 4: Monitorar Telemetria

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService

def handle_telemetry(device_id, data):
    if 'temperature' in data:
        print(f"Temperatura: {data['temperature']}°C")
    if 'humidity' in data:
        print(f"Umidade: {data['humidity']}%")

# Inscrever-se em telemetria
DeviceAPIService.subscribe_telemetry('esp32-sensor-001', handle_telemetry)
```

## Troubleshooting

### Servidor MQTT não inicia

1. Verifique se `paho-mqtt` está instalado: `pip install paho-mqtt`
2. Verifique se a porta 1883 está disponível
3. Verifique os logs em `logs/brewstation.log`

### Dispositivo não conecta

1. Verifique a configuração do broker MQTT
2. Verifique se o dispositivo está configurado corretamente
3. Verifique os tópicos MQTT no monitoramento

### Mensagens não aparecem no monitoramento

1. Verifique se está inscrito no tópico correto
2. Verifique se o broker está rodando
3. Verifique os logs para erros

## Segurança

- **Autenticação MQTT**: Configure usuário e senha no broker
- **TLS/SSL**: Habilite SSL para comunicação segura
- **Tópicos**: Use padrões de tópicos restritivos
- **Permissões**: Configure permissões adequadas no broker

## Limitações

- O histórico de mensagens é limitado a 1000 mensagens em memória
- Para produção, considere usar Redis ou banco de dados para histórico
- O broker MQTT embutido é básico; para recursos avançados, use Mosquitto ou similar

## Suporte

Para problemas ou dúvidas:
1. Verifique os logs em `logs/brewstation.log`
2. Consulte a documentação do sistema de plugins: `docs/PLUGIN_SYSTEM.md`
3. Verifique a documentação da API: `docs/PLUGIN_DEVICE_MANAGER.md`

