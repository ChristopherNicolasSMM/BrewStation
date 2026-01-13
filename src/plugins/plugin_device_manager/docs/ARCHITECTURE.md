# Arquitetura - Plugin Device Manager

## Visão Geral da Arquitetura

O Plugin Device Manager é construído sobre uma arquitetura modular que separa responsabilidades em camadas distintas: modelos de dados, lógica de negócio, APIs e interface de usuário.

## Componentes Principais

### 1. Camada de Modelos (`model/`)

#### DeviceMetadata
Armazena metadados básicos dos dispositivos no banco de dados. Configurações detalhadas são armazenadas em arquivos JSON.

**Tabela:** `dvmanage_device_metadata`

**Campos principais:**
- `id`: UUID do dispositivo
- `name`: Nome do dispositivo
- `device_type`: Tipo (sensor, actuator, gateway)
- `protocol`: Protocolo de comunicação (mqtt, http, websocket)
- `is_active`: Status ativo/inativo
- `port_config`: Configuração de portas (JSON)

#### DeviceFunction
Define funções que podem ser atribuídas a portas de dispositivos.

**Tabela:** `dvmanage_device_function`

**Campos principais:**
- `id`: ID único
- `name`: Nome único (slug)
- `display_name`: Nome para exibição
- `category`: Categoria (sensor, actuator, hybrid)
- `data_type`: Tipo de dado (float, int, bool, string)
- `unit`: Unidade de medida
- `is_predefined`: Se é função pré-definida do sistema

**Funções pré-definidas:**
Criadas automaticamente na instalação:
- temperature, humidity, pressure
- relay, pwm, adc
- gpio_digital

#### DeviceActor
Associa portas de dispositivos a funções, criando uma camada de abstração para outros plugins.

**Tabela:** `dvmanage_device_actor`

**Campos principais:**
- `id`: UUID do ator
- `device_id`: Referência ao dispositivo
- `port_name`: Nome da porta
- `function_id`: Referência à função
- `actor_type`: Tipo (sensor, actuator, rule_trigger)
- `plugin_name`: Plugin que usa este ator
- `plugin_entity_id`: ID da entidade no plugin
- `config_json`: Configuração específica (JSON)

### 2. Camada de Utilitários (`utils/`)

#### DeviceRegistry
Gerencia dispositivos, salvando configurações em JSON e mantendo apenas metadados no banco.

**Responsabilidades:**
- CRUD de dispositivos
- Gerenciamento de estados
- Armazenamento de configurações em arquivos JSON

**Estrutura de arquivos:**
```
data/
├── devices/
│   ├── configs/
│   │   └── {device_id}.json
│   └── states/
│       └── {device_id}.json
└── mqtt_broker.json
```

#### ActorManager
Gerencia atores com lógica de negócio completa.

**Responsabilidades:**
- CRUD de atores
- Execução de ações (publica comandos MQTT)
- Leitura de sensores (lê estados)
- Associação de atores a plugins

**Métodos principais:**
- `create_actor()`: Cria novo ator
- `execute_actor_action()`: Executa ação
- `read_actor_sensor()`: Lê valor do sensor
- `get_actors_by_device()`: Lista atores por dispositivo
- `get_actors_by_plugin()`: Lista atores por plugin

#### MQTTService
Gerencia comunicação MQTT e broker embutido.

**Responsabilidades:**
- Iniciar/parar broker MQTT
- Publicar mensagens
- Inscrever em tópicos
- Manter histórico de mensagens
- Gerenciar clientes MQTT

**Características:**
- Roda em thread separada (daemon)
- Suporta autenticação
- Histórico de mensagens para debugging
- Integração com paho-mqtt e hbmqtt

#### DeviceAPI
API pública para outros plugins usarem dispositivos.

**Características:**
- Métodos estáticos
- Interface simplificada
- Abstração de detalhes de implementação
- Thread-safe

### 3. Camada de API (`api/routes/`)

#### device_routes.py
Rotas para gerenciamento de dispositivos.

**Endpoints:**
- `GET /api/device_manager/devices`: Lista dispositivos
- `GET /api/device_manager/devices/<id>`: Obtém dispositivo
- `POST /api/device_manager/devices`: Cria dispositivo
- `PUT /api/device_manager/devices/<id>`: Atualiza dispositivo
- `DELETE /api/device_manager/devices/<id>`: Remove dispositivo

#### function_routes.py
Rotas para gerenciamento de funções.

**Endpoints:**
- `GET /api/device_manager/functions`: Lista funções
- `GET /api/device_manager/functions/predefined`: Lista pré-definidas
- `GET /api/device_manager/functions/<id>`: Obtém função
- `POST /api/device_manager/functions`: Cria função (customizada)
- `PUT /api/device_manager/functions/<id>`: Atualiza função
- `DELETE /api/device_manager/functions/<id>`: Remove função

#### actor_routes.py
Rotas para gerenciamento de atores.

**Endpoints:**
- `GET /api/device_manager/actors`: Lista atores
- `GET /api/device_manager/actors/<id>`: Obtém ator
- `POST /api/device_manager/actors`: Cria ator
- `PUT /api/device_manager/actors/<id>`: Atualiza ator
- `DELETE /api/device_manager/actors/<id>`: Remove ator
- `POST /api/device_manager/actors/<id>/execute`: Executa ação
- `GET /api/device_manager/actors/<id>/read`: Lê sensor
- `POST /api/device_manager/actors/<id>/link`: Associa a plugin

#### mqtt_test_routes.py
Rotas para testes do broker MQTT.

**Endpoints:**
- `POST /api/device_manager/mqtt/test/publish`: Publica mensagem
- `POST /api/device_manager/mqtt/test/subscribe`: Inscreve em tópico
- `GET /api/device_manager/mqtt/test/history`: Histórico de mensagens
- `GET /api/device_manager/mqtt/broker/status`: Status do broker
- `POST /api/device_manager/mqtt/test/unsubscribe`: Desinscreve

### 4. Camada de Interface (`controller/` e `templates/`)

#### Rotas Web
- `/device_manager`: Lista de dispositivos
- `/device_manager/add`: Formulário de cadastro
- `/device_manager/edit/<id>`: Formulário de edição
- `/device_manager/functions`: Gerenciador de funções
- `/device_manager/actors`: Gerenciador de atores
- `/device_manager/mqtt/monitor`: Monitor MQTT

#### Templates
- `device_manager.html`: Lista de dispositivos
- `device_form.html`: Formulário de dispositivos (com funções e atores)
- `function_manager.html`: Gerenciador de funções
- `actor_manager.html`: Gerenciador de atores
- `mqtt_monitor.html`: Monitor MQTT

## Fluxo de Dados

### Cadastro de Dispositivo com Ator

```
1. Usuário preenche formulário (device_form.html)
   ↓
2. JavaScript envia dados para API
   ↓
3. device_routes.py → DeviceRegistry.register_device()
   ↓
4. Cria DeviceMetadata no banco
   ↓
5. Salva configuração em JSON (data/devices/configs/)
   ↓
6. Cria estado inicial (data/devices/states/)
   ↓
7. Se ator criado:
   ↓
8. actor_routes.py → ActorManager.create_actor()
   ↓
9. Cria DeviceActor no banco
```

### Execução de Ação

```
1. Outro plugin chama DeviceAPI.execute_action()
   ↓
2. DeviceAPI → ActorManager.execute_actor_action()
   ↓
3. ActorManager obtém configuração do dispositivo
   ↓
4. Constrói tópico MQTT
   ↓
5. MQTTService.publish()
   ↓
6. Mensagem publicada no broker
   ↓
7. Dispositivo recebe comando
```

### Leitura de Sensor

```
1. Outro plugin chama DeviceAPI.read_sensor()
   ↓
2. DeviceAPI → ActorManager.read_actor_sensor()
   ↓
3. ActorManager obtém estado do dispositivo
   ↓
4. Lê valor da porta no estado
   ↓
5. Retorna valor
```

## Sistema de Prefixos

Todos os modelos são prefixados automaticamente com `dvmanage_`:

- `DeviceMetadata` → `dvmanage_device_metadata`
- `DeviceFunction` → `dvmanage_device_function`
- `DeviceActor` → `dvmanage_device_actor`

**Benefícios:**
- Evita conflitos de nomes
- Isolamento de dados
- Facilita migração/backup

**Implementação:**
- Prefixo aplicado pelo `plugin_db_helper`
- ForeignKeys usam nomes prefixados
- Model loader garante uso correto

## Integração com Flask

### Registro de Blueprints

Blueprints são registrados automaticamente durante ativação:

```python
# API
/api/device_manager/*

# Web
/device_manager/*
```

### Context Processors

Nenhum context processor específico é necessário (menu é gerenciado pelo sistema de plugins).

### Template Loader

Templates são carregados pelo `PluginTemplateLoader`, permitindo override de templates core.

## Segurança

### Autenticação
- Todas as rotas requerem `@login_required`
- Verificação de autenticação via Flask-Login

### Validação
- Validação de dados de entrada
- Verificação de permissões (ex: não editar funções pré-definidas)
- Validação de relacionamentos (ex: não deletar função em uso)

### Isolamento
- Prefixos de tabela evitam conflitos
- Cada plugin tem seu próprio namespace
- Configurações isoladas por arquivos JSON

## Extensibilidade

### Adicionar Novas Funções
1. Criar função via API ou interface
2. Função disponível imediatamente
3. Pode ser usada em novos atores

### Adicionar Novos Tipos de Atores
- Tipo `actor_type` é flexível
- Lógica específica pode ser adicionada em `ActorManager`
- Callbacks podem ser customizados

### Integração com Novos Protocolos
- Adicionar suporte em `MQTTService` ou criar novo serviço
- Atualizar `DeviceRegistry` para novo protocolo
- Adicionar campos de configuração em `DeviceMetadata`

## Performance

### Otimizações

1. **Cache de Estados:**
   - DeviceRegistry mantém cache de estados em memória
   - Reduz I/O de arquivos

2. **Queries Otimizadas:**
   - Índices em ForeignKeys
   - Queries com filtros eficientes

3. **MQTT Assíncrono:**
   - Broker roda em thread separada
   - Não bloqueia aplicação principal

### Considerações

1. **Histórico de Mensagens:**
   - Limitado a 1000 mensagens
   - Pode ser ajustado conforme necessário

2. **Múltiplas Subscrições:**
   - Cada subscrição adiciona overhead
   - Considere agregar quando possível

3. **Leituras Frequentes:**
   - Use subscrições para monitoramento contínuo
   - Use leituras diretas para valores pontuais

## Manutenibilidade

### Código Organizado
- Separação de responsabilidades clara
- Cada módulo tem responsabilidade única
- Fácil localizar e modificar funcionalidades

### Logging
- Logging abrangente em todas as operações
- Níveis apropriados (DEBUG, INFO, WARNING, ERROR)
- Facilita debugging e monitoramento

### Testabilidade
- Componentes isolados facilitam testes
- Dependências injetáveis
- Interfaces claras para mock

## Diagrama de Relacionamentos

```
DeviceMetadata (1) ──< (N) DeviceActor (N) >── (1) DeviceFunction
     │
     │ (has many)
     │
     └──> Config JSON File
     └──> State JSON File
```

```
Other Plugin
     │
     │ uses
     │
DeviceAPI ──> ActorManager ──> DeviceActor
                           └──> DeviceRegistry
                           └──> MQTTService
```

## Próximos Passos

Possíveis melhorias futuras:

1. **WebSockets:**
   - Atualizações em tempo real na UI
   - Notificações push

2. **Regras:**
   - Sistema de regras baseado em atores
   - Automação condicional

3. **Dashboards:**
   - Visualização de dados
   - Gráficos e métricas

4. **Histórico:**
   - Armazenamento de histórico de valores
   - Análise de tendências

5. **Grupos:**
   - Agrupamento de dispositivos
   - Ações em massa
