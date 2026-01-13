# API Reference - Plugin Device Manager

## Visão Geral

O Plugin Device Manager expõe uma API REST completa para gerenciamento de dispositivos, funções e atores. Todas as rotas estão prefixadas com `/api/device_manager/`.

## Autenticação

Todas as rotas requerem autenticação via Flask-Login. O usuário deve estar logado para acessar os endpoints.

## Endpoints de Dispositivos

### Listar Dispositivos

```
GET /api/device_manager/devices
```

**Query Parameters:**
- `type` (opcional): Filtrar por tipo (sensor, actuator, gateway)
- `protocol` (opcional): Filtrar por protocolo (mqtt, http, websocket)

**Resposta:**
```json
{
  "success": true,
  "devices": [
    {
      "device_id": "uuid",
      "name": "Sensor de Temperatura",
      "type": "sensor",
      "protocol": "mqtt",
      "state": {
        "status": "online",
        "last_seen": "2024-01-01T12:00:00"
      }
    }
  ],
  "total": 1
}
```

### Obter Dispositivo

```
GET /api/device_manager/devices/<device_id>
```

**Resposta:**
```json
{
  "success": true,
  "device": {
    "device_id": "uuid",
    "name": "Sensor de Temperatura",
    "type": "sensor",
    "protocol": "mqtt",
    "connection": {...},
    "topics": {...},
    "ports": {...},
    "state": {...}
  }
}
```

### Criar Dispositivo

```
POST /api/device_manager/devices
```

**Body:**
```json
{
  "name": "Sensor de Temperatura",
  "type": "sensor",
  "protocol": "mqtt",
  "connection": {
    "broker": "localhost:1883",
    "client_id": "sensor_001"
  },
  "topics": {
    "command": "brewstation/devices/sensor_001/command",
    "telemetry": "brewstation/devices/sensor_001/telemetry"
  },
  "ports": {
    "GPIO1": {
      "type": "sensor",
      "direction": "input"
    }
  }
}
```

### Atualizar Dispositivo

```
PUT /api/device_manager/devices/<device_id>
```

### Deletar Dispositivo

```
DELETE /api/device_manager/devices/<device_id>
```

## Endpoints de Funções

### Listar Funções

```
GET /api/device_manager/functions
```

**Query Parameters:**
- `category` (opcional): Filtrar por categoria (sensor, actuator, hybrid)
- `is_predefined` (opcional): Filtrar por tipo (true, false)
- `search` (opcional): Buscar por nome ou descrição

**Resposta:**
```json
{
  "success": true,
  "functions": [
    {
      "id": 1,
      "name": "temperature",
      "display_name": "Temperatura",
      "description": "Sensor de temperatura",
      "category": "sensor",
      "unit": "°C",
      "data_type": "float",
      "min_value": -50.0,
      "max_value": 150.0,
      "is_predefined": true,
      "icon": "bi-thermometer-half"
    }
  ],
  "total": 1
}
```

### Listar Funções Pré-definidas

```
GET /api/device_manager/functions/predefined
```

### Obter Função

```
GET /api/device_manager/functions/<function_id>
```

### Criar Função

```
POST /api/device_manager/functions
```

**Body:**
```json
{
  "name": "my_custom_function",
  "display_name": "Minha Função Customizada",
  "description": "Descrição da função",
  "category": "sensor",
  "data_type": "float",
  "unit": "V",
  "min_value": 0.0,
  "max_value": 5.0,
  "icon": "bi-speedometer"
}
```

**Nota:** Apenas funções customizadas podem ser criadas via API. Funções pré-definidas são criadas automaticamente na instalação.

### Atualizar Função

```
PUT /api/device_manager/functions/<function_id>
```

**Nota:** Apenas funções customizadas podem ser atualizadas.

### Deletar Função

```
DELETE /api/device_manager/functions/<function_id>
```

**Nota:** Apenas funções customizadas podem ser deletadas. Funções em uso por atores não podem ser deletadas.

## Endpoints de Atores

### Listar Atores

```
GET /api/device_manager/actors
```

**Query Parameters:**
- `device_id` (opcional): Filtrar por dispositivo
- `actor_type` (opcional): Filtrar por tipo (sensor, actuator, rule_trigger)
- `plugin_name` (opcional): Filtrar por plugin

**Resposta:**
```json
{
  "success": true,
  "actors": [
    {
      "id": "uuid",
      "device_id": "device_uuid",
      "port_name": "GPIO1",
      "function_id": 1,
      "actor_type": "sensor",
      "name": "Sensor de Temperatura - GPIO1",
      "description": "Sensor de temperatura no GPIO1",
      "config": {},
      "plugin_name": null,
      "plugin_entity_id": null,
      "is_active": true
    }
  ],
  "total": 1
}
```

### Listar Atores por Dispositivo

```
GET /api/device_manager/actors/device/<device_id>
```

### Listar Atores por Plugin

```
GET /api/device_manager/actors/plugin/<plugin_name>?plugin_entity_id=<entity_id>
```

### Obter Ator

```
GET /api/device_manager/actors/<actor_id>
```

### Criar Ator

```
POST /api/device_manager/actors
```

**Body:**
```json
{
  "device_id": "device_uuid",
  "port_name": "GPIO1",
  "function_id": 1,
  "actor_type": "sensor",
  "name": "Sensor de Temperatura - GPIO1",
  "description": "Sensor de temperatura no GPIO1",
  "config": {}
}
```

### Atualizar Ator

```
PUT /api/device_manager/actors/<actor_id>
```

**Body:**
```json
{
  "name": "Novo Nome",
  "description": "Nova descrição",
  "actor_type": "actuator",
  "is_active": true,
  "plugin_name": "plugin_mash_control",
  "plugin_entity_id": "recipe_123",
  "config": {}
}
```

### Deletar Ator

```
DELETE /api/device_manager/actors/<actor_id>
```

### Executar Ação do Ator

```
POST /api/device_manager/actors/<actor_id>/execute
```

**Body:**
```json
{
  "value": true
}
```

**Nota:** Apenas atores do tipo `actuator` ou `rule_trigger` podem executar ações.

**Resposta:**
```json
{
  "success": true,
  "message": "Ação executada com sucesso"
}
```

### Ler Valor do Sensor

```
GET /api/device_manager/actors/<actor_id>/read
```

**Nota:** Apenas atores do tipo `sensor` podem ser lidos.

**Resposta:**
```json
{
  "success": true,
  "value": 25.5
}
```

### Associar Ator a Plugin

```
POST /api/device_manager/actors/<actor_id>/link
```

**Body:**
```json
{
  "plugin_name": "plugin_mash_control",
  "plugin_entity_id": "recipe_123"
}
```

## Endpoints de Teste MQTT

### Publicar Mensagem

```
POST /api/device_manager/mqtt/test/publish
```

**Body:**
```json
{
  "topic": "brewstation/test/topic",
  "payload": "mensagem de teste",
  "qos": 1,
  "retain": false
}
```

### Inscrever em Tópico

```
POST /api/device_manager/mqtt/test/subscribe
```

**Body:**
```json
{
  "topic": "brewstation/test/topic",
  "qos": 1
}
```

### Histórico de Mensagens

```
GET /api/device_manager/mqtt/test/history?limit=100&topic=brewstation/test/topic
```

**Query Parameters:**
- `limit` (opcional): Número máximo de mensagens (padrão: 100)
- `topic` (opcional): Filtrar por tópico

**Resposta:**
```json
{
  "success": true,
  "messages": [
    {
      "topic": "brewstation/test/topic",
      "payload": "mensagem",
      "direction": "outgoing",
      "qos": 1,
      "retain": false,
      "timestamp": "2024-01-01T12:00:00"
    }
  ],
  "total": 1,
  "limit": 100
}
```

### Status do Broker

```
GET /api/device_manager/mqtt/broker/status
```

**Resposta:**
```json
{
  "success": true,
  "status": "running",
  "is_running": true,
  "subscriptions_count": 5,
  "subscriptions": ["topic1", "topic2"],
  "config": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 1883
  }
}
```

### Desinscrever de Tópico

```
POST /api/device_manager/mqtt/test/unsubscribe
```

**Body:**
```json
{
  "topic": "brewstation/test/topic"
}
```

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Dados inválidos
- `401 Unauthorized`: Não autenticado
- `403 Forbidden`: Operação não permitida (ex: editar função pré-definida)
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno do servidor

## Exemplos de Uso

### Criar um dispositivo com porta e ator

```bash
# 1. Criar dispositivo
curl -X POST http://localhost:5000/api/device_manager/devices \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sensor de Temperatura",
    "type": "sensor",
    "protocol": "mqtt",
    "ports": {
      "GPIO1": {"type": "sensor", "direction": "input"}
    }
  }'

# 2. Criar ator
curl -X POST http://localhost:5000/api/device_manager/actors \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_uuid",
    "port_name": "GPIO1",
    "function_id": 1,
    "actor_type": "sensor",
    "name": "Temperatura GPIO1"
  }'

# 3. Ler valor do sensor
curl http://localhost:5000/api/device_manager/actors/actor_uuid/read
```

### Executar ação em ator

```bash
curl -X POST http://localhost:5000/api/device_manager/actors/actor_uuid/execute \
  -H "Content-Type: application/json" \
  -d '{"value": true}'
```

## Notas Importantes

1. Todos os modelos são prefixados com `dvmanage_` no banco de dados
2. Funções pré-definidas não podem ser editadas ou deletadas
3. Atores só podem executar ações se forem do tipo `actuator` ou `rule_trigger`
4. Sensores só podem ser lidos se forem do tipo `sensor`
5. O broker MQTT deve estar rodando para executar ações ou ler sensores via MQTT
