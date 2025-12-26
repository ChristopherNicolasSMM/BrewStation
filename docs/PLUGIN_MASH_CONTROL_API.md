# Referência da API - Plugin Mash Control

## Visão Geral

Esta documentação descreve todas as rotas API REST disponíveis no plugin Mash Control. Todas as rotas requerem autenticação (`@login_required`).

**Base URL**: `/api/mash_control`

## Rotas de Dashboard

### Obter Layout do Dashboard

```http
GET /api/mash_control/dashboard/layout?layout_id={layout_id}
```

Obtém um layout salvo do dashboard. Se `layout_id` não for fornecido, retorna o layout padrão do usuário.

**Resposta**:
```json
{
  "id": "layout_001",
  "name": "Layout Padrão",
  "layout_data": [
    {
      "type": "kettle",
      "id": "kettle_1",
      "x": 100,
      "y": 50,
      "device_id": "device_001",
      "properties": {
        "fill_color": "#4CAF50",
        "show_temp": true
      }
    }
  ],
  "is_default": true
}
```

### Salvar Layout do Dashboard

```http
POST /api/mash_control/dashboard/layout
```

Salva um layout do dashboard.

**Corpo da Requisição**:
```json
{
  "id": "layout_001",
  "name": "Meu Layout",
  "elements": [
    {
      "type": "kettle",
      "id": "kettle_1",
      "x": 100,
      "y": 50,
      "device_id": "device_001",
      "properties": {
        "fill_color": "#4CAF50",
        "show_temp": true
      }
    }
  ],
  "is_default": false
}
```

**Resposta**:
```json
{
  "id": "layout_001",
  "message": "Layout salvo"
}
```

### Listar Dispositivos Disponíveis

```http
GET /api/mash_control/dashboard/devices?device_type={type}&protocol={protocol}&is_active={true|false}
```

Lista dispositivos disponíveis com filtros opcionais.

**Resposta**:
```json
[
  {
    "id": "device_001",
    "name": "Mash Tun",
    "type": "sensor",
    "protocol": "MQTT",
    "is_active": true,
    "ports": {
      "GPIO_32": {
        "type": "sensor",
        "function": "temperature",
        "current_value": 52.5
      }
    }
  }
]
```

### Status do Dashboard

```http
GET /api/mash_control/dashboard/status
```

Obtém status atual do dashboard (sessões ativas, pausadas, etc.).

**Resposta**:
```json
{
  "active_sessions": 1,
  "paused_sessions": 0,
  "total_sessions": 1
}
```

## Rotas de Sessões

### Listar Sessões

```http
GET /api/mash_control/sessions?status={status}
```

Lista sessões com filtro opcional por status.

**Parâmetros de Query**:
- `status` (opcional): Filtrar por status (pending/running/paused/completed/error)

**Resposta**:
```json
[
  {
    "id": "session_001",
    "recipe_id": "recipe_001",
    "name": "American IPA - 2024-01-15",
    "status": "running",
    "current_step": 2,
    "start_time": "2024-01-15T10:00:00",
    "end_time": null,
    "user_id": 1
  }
]
```

### Obter Sessão Específica

```http
GET /api/mash_control/sessions/{session_id}
```

Obtém detalhes de uma sessão específica.

**Resposta**:
```json
{
  "id": "session_001",
  "recipe_id": "recipe_001",
  "name": "American IPA - 2024-01-15",
  "status": "running",
  "current_step": 2,
  "start_time": "2024-01-15T10:00:00",
  "end_time": null,
  "session_data": {
    "equipment_mapping": {
      "mash_tun": "device_001",
      "boil_kettle": "device_002"
    },
    "events": [
      {
        "type": "session_started",
        "data": {},
        "timestamp": "2024-01-15T10:00:00"
      }
    ],
    "telemetry": []
  },
  "equipment_used": ["device_001", "device_002"]
}
```

### Criar Nova Sessão

```http
POST /api/mash_control/sessions
```

Inicia uma nova sessão de brassagem.

**Corpo da Requisição**:
```json
{
  "recipe_id": "recipe_001",
  "equipment_mapping": {
    "mash_tun": "device_001",
    "boil_kettle": "device_002",
    "pump_1": "device_003"
  },
  "name": "Sessão Personalizada"
}
```

**Resposta**:
```json
{
  "id": "session_001",
  "message": "Sessão iniciada"
}
```

### Pausar Sessão

```http
POST /api/mash_control/sessions/{session_id}/pause
```

Pausa uma sessão em execução.

**Resposta**:
```json
{
  "message": "Sessão pausada"
}
```

### Retomar Sessão

```http
POST /api/mash_control/sessions/{session_id}/resume
```

Retoma uma sessão pausada.

**Resposta**:
```json
{
  "message": "Sessão retomada"
}
```

### Parar Sessão

```http
POST /api/mash_control/sessions/{session_id}/stop
```

Para uma sessão em execução.

**Resposta**:
```json
{
  "message": "Sessão parada"
}
```

### Enviar Comando Manual

```http
POST /api/mash_control/sessions/{session_id}/command
```

Envia um comando manual para um dispositivo durante a sessão.

**Corpo da Requisição**:
```json
{
  "device_id": "device_001",
  "command": "set_port",
  "payload": {
    "port": "GPIO_25",
    "value": true
  }
}
```

**Resposta**:
```json
{
  "message": "Comando enviado"
}
```

### Obter Logs da Sessão

```http
GET /api/mash_control/sessions/{session_id}/logs
```

Obtém logs de eventos da sessão.

**Resposta**:
```json
{
  "events": [
    {
      "type": "session_started",
      "data": {},
      "timestamp": "2024-01-15T10:00:00"
    },
    {
      "type": "step_started",
      "data": {
        "step_index": 0,
        "step_name": "Protein Rest"
      },
      "timestamp": "2024-01-15T10:00:05"
    }
  ]
}
```

### Obter Telemetria da Sessão

```http
GET /api/mash_control/sessions/{session_id}/telemetry
```

Obtém telemetria atualizada da sessão (valores de sensores, etc.).

**Resposta**:
```json
{
  "telemetry": [
    {
      "timestamp": "2024-01-15T10:00:00",
      "device_id": "device_001",
      "port": "GPIO_32",
      "value": 52.5
    }
  ],
  "current_values": {
    "device_001": {
      "GPIO_32": {
        "type": "sensor",
        "function": "temperature",
        "current_value": 52.5,
        "last_update": "2024-01-15T10:00:00"
      }
    }
  }
}
```

## Rotas de Receitas

### Listar Receitas

```http
GET /api/mash_control/recipes?is_active={true|false}&brewfather_recipe_id={id}
```

Lista receitas com filtros opcionais.

**Resposta**:
```json
[
  {
    "id": "recipe_001",
    "name": "American IPA",
    "description": "Receita clássica de IPA",
    "recipe_data": {
      "steps": [
        {
          "type": "mash",
          "name": "Protein Rest",
          "target_temp": 52,
          "duration": 15
        }
      ]
    },
    "equipment_mapping": {
      "mash_tun": "device_001"
    },
    "brewfather_recipe_id": "bf_12345",
    "is_active": true
  }
]
```

### Obter Receita Específica

```http
GET /api/mash_control/recipes/{recipe_id}
```

Obtém detalhes de uma receita específica.

**Resposta**: Mesmo formato da lista de receitas, mas com um único objeto.

### Criar Nova Receita

```http
POST /api/mash_control/recipes
```

Cria uma nova receita.

**Corpo da Requisição**:
```json
{
  "name": "Nova Receita",
  "description": "Descrição da receita",
  "recipe_data": {
    "steps": [
      {
        "type": "mash",
        "name": "Protein Rest",
        "target_temp": 52,
        "duration": 15,
        "devices": {
          "heater": "device_001_heater",
          "sensor": "device_001_temp"
        },
        "actions": [
          {"type": "set_temperature", "target": 52, "tolerance": 1},
          {"type": "wait", "duration": 15}
        ]
      }
    ]
  },
  "equipment_mapping": {
    "mash_tun": "device_001"
  }
}
```

**Resposta**:
```json
{
  "id": "recipe_001",
  "message": "Receita criada"
}
```

### Atualizar Receita

```http
PUT /api/mash_control/recipes/{recipe_id}
```

Atualiza uma receita existente.

**Corpo da Requisição**: Mesmo formato da criação, mas apenas campos a serem atualizados.

**Resposta**:
```json
{
  "message": "Receita atualizada"
}
```

### Remover Receita

```http
DELETE /api/mash_control/recipes/{recipe_id}
```

Remove uma receita.

**Resposta**:
```json
{
  "message": "Receita removida"
}
```

### Importar Receita do BrewFather

```http
POST /api/mash_control/recipes/import/brewfather
```

Importa uma receita do BrewFather.

**Corpo da Requisição**:
```json
{
  "brewfather_recipe_id": "bf_12345"
}
```

**Resposta**:
```json
{
  "id": "recipe_001",
  "message": "Receita importada do BrewFather"
}
```

### Listar Receitas do BrewFather

```http
GET /api/mash_control/recipes/brewfather/list
```

Lista receitas disponíveis no BrewFather para importação.

**Resposta**:
```json
[
  {
    "brewfather_id": "bf_12345",
    "name": "American IPA",
    "style": "American IPA",
    "abv": 6.5,
    "ibu": 65
  }
]
```

### Validar Receita

```http
POST /api/mash_control/recipes/{recipe_id}/validate
```

Valida uma receita (estrutura e equipamento necessário).

**Resposta**:
```json
{
  "valid": true,
  "structure_valid": true,
  "equipment_validation": {
    "valid": true,
    "missing_devices": [],
    "required_devices": ["device_001"],
    "available_devices": ["device_001", "device_002"]
  }
}
```

### Calcular Timeline da Receita

```http
GET /api/mash_control/recipes/{recipe_id}/timeline
```

Calcula a timeline completa da receita.

**Resposta**:
```json
[
  {
    "step_name": "Protein Rest",
    "start_time": 0,
    "end_time": 15,
    "duration": 15,
    "target_temp": 52,
    "type": "mash"
  },
  {
    "step_name": "Saccharification Rest",
    "start_time": 15,
    "end_time": 75,
    "duration": 60,
    "target_temp": 65,
    "type": "mash"
  }
]
```

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Erro na requisição (dados inválidos)
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro interno do servidor

## Tratamento de Erros

Todas as rotas retornam erros no seguinte formato:

```json
{
  "error": "Mensagem de erro descritiva"
}
```

## Autenticação

Todas as rotas requerem autenticação via Flask-Login. O token de sessão deve ser incluído automaticamente pelo navegador ou fornecido via cabeçalho `Cookie`.

## Exemplos de Uso

### Criar e Executar uma Receita

```javascript
// 1. Criar receita
const recipeResponse = await fetch('/api/mash_control/recipes', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    name: 'Minha Receita',
    recipe_data: {
      steps: [
        {
          type: 'mash',
          name: 'Protein Rest',
          target_temp: 52,
          duration: 15
        }
      ]
    },
    equipment_mapping: {
      mash_tun: 'device_001'
    }
  })
});
const recipe = await recipeResponse.json();

// 2. Iniciar sessão
const sessionResponse = await fetch('/api/mash_control/sessions', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    recipe_id: recipe.id,
    equipment_mapping: {
      mash_tun: 'device_001'
    }
  })
});
const session = await sessionResponse.json();

// 3. Monitorar sessão
setInterval(async () => {
  const statusResponse = await fetch(`/api/mash_control/sessions/${session.id}`);
  const status = await statusResponse.json();
  console.log('Status:', status.status, 'Etapa:', status.current_step);
}, 2000);
```

## Referências

- [Documentação Técnica](PLUGIN_MASH_CONTROL.md)
- [Manual do Usuário](PLUGIN_MASH_CONTROL_MANUAL.md)
- [Device Manager API](PLUGIN_DEVICE_MANAGER_API.md)

