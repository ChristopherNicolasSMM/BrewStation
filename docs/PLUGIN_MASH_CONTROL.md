# Plugin Mash Control - Documentação Técnica

## Visão Geral

O **Mash Control** é um plugin completo de automação de processos de brassagem para o BrewStation. Ele fornece um sistema visual interativo para controlar e monitorar processos de brassagem em tempo real, integrando-se com dispositivos IoT através do plugin Device Manager.

## Características Principais

- **Dashboard Visual Interativo**: Representação SVG do brewhouse com elementos arrastáveis
- **Controle Automático**: Execução automática de receitas com controle PID de temperatura
- **Controle Manual**: Override para operação direta de dispositivos
- **Editor de Receitas**: Criação e edição visual de perfis de brassagem
- **Sistema de Logging**: Histórico completo de sessões com eventos e telemetria
- **Integração com Device Manager**: Acesso completo a sensores e atuadores
- **Importação do BrewFather**: Importação automática de receitas sincronizadas

## Requisitos

- **BrewStation** versão 1.0 ou superior
- **Plugin Device Manager** instalado e ativo (dependência obrigatória)
- **Python 3.11+**
- **Dependências**: Todas as dependências do BrewStation

## Instalação

### Via CLI

```bash
# Instalar o plugin
flask plugin install mash_control

# Ativar o plugin
flask plugin activate mash_control
```

### Verificação

Após a instalação, o plugin deve aparecer no menu lateral do BrewStation como "Controle de Brassagem" com os seguintes subitens:
- Dashboard
- Receitas
- Nova Receita
- Sessões Ativas
- Histórico
- Configurações

## Estrutura do Plugin

```
src/plugins/plugin_mash_control/
├── plugin.py                    # Classe principal do plugin
├── install.json                 # Configuração (table_prefix: mash_ctrl)
├── menu_config.json             # Menu de navegação
├── model/
│   └── mash_models.py          # Modelos SQLAlchemy (MashRecipe, BrewSession, DashboardLayout)
├── api/
│   └── routes/
│       ├── mash_routes.py       # Rotas API REST para dashboard e sessões
│       └── recipe_routes.py     # Rotas API REST para receitas
├── controller/
│   └── routes.py                # Rotas web (páginas HTML)
├── services/
│   ├── device_integration.py    # Integração com device_manager
│   ├── process_control.py       # Controle de processos automáticos
│   ├── dashboard_builder.py     # Gerenciamento de layouts SVG
│   └── recipe_editor.py         # Editor e gerenciamento de receitas
├── templates/
│   └── mash_control/
│       ├── dashboard.html       # Dashboard principal
│       ├── recipe_list.html      # Lista de receitas
│       ├── recipe_editor.html    # Editor de receitas
│       ├── session_control.html # Controle de sessão
│       └── session_history.html # Histórico de sessões
├── static/
│   └── mash_control/
│       ├── dashboard.js         # JavaScript do dashboard
│       ├── recipe-editor.js     # JavaScript do editor
│       ├── svg-components.js    # Componentes SVG reutilizáveis
│       └── styles.css           # Estilos específicos
└── data/                        # DENTRO do plugin
    ├── recipes/                 # Receitas JSON
    ├── dashboards/              # Layouts JSON
    └── sessions/                # Logs de sessões JSON
```

## Modelos de Dados

### MashRecipe

Armazena perfis de brassagem reutilizáveis.

**Tabela**: `mash_ctrl_mash_recipe`

**Campos principais**:
- `id` (String, PK)
- `name` (String)
- `description` (Text)
- `recipe_data` (Text/JSON) - Estrutura completa da receita
- `equipment_mapping` (Text/JSON) - Mapeamento dispositivo → função
- `brewfather_recipe_id` (String, nullable) - ID da receita no BrewFather
- `created_by` (Integer, FK para User)
- `is_active` (Boolean)
- `created_at`, `updated_at` (DateTime)

### BrewSession

Registra execuções de receitas.

**Tabela**: `mash_ctrl_brew_session`

**Campos principais**:
- `id` (String, PK)
- `recipe_id` (String, FK para MashRecipe)
- `name` (String)
- `status` (String) - pending/running/paused/completed/error
- `current_step` (Integer)
- `start_time`, `end_time` (DateTime, nullable)
- `session_data` (Text/JSON) - Logs, telemetria, eventos
- `user_id` (Integer, FK para User)
- `equipment_used` (Text/JSON) - Lista de dispositivos usados
- `created_at`, `updated_at` (DateTime)

### DashboardLayout

Salva configurações visuais do dashboard.

**Tabela**: `mash_ctrl_dashboard_layout`

**Campos principais**:
- `id` (String, PK)
- `name` (String)
- `user_id` (Integer, FK para User)
- `layout_data` (Text/JSON) - Posicionamento SVG, dispositivos vinculados
- `is_default` (Boolean)
- `created_at`, `updated_at` (DateTime)

## Serviços Principais

### DeviceIntegrationService

Bridge entre `mash_control` e `device_manager` para acesso a sensores e atuadores.

**Localização**: `services/device_integration.py`

**Métodos principais**:
- `get_available_devices(filters)` - Lista dispositivos disponíveis
- `get_sensors()` - Lista apenas sensores
- `get_actuators()` - Lista apenas atuadores
- `send_command(device_id, command, payload)` - Envia comando
- `get_port_value(device_id, port)` - Obtém valor de porta
- `set_port_value(device_id, port, value)` - Define valor de porta

### ProcessControlService

Gerencia execução de receitas, controle PID de temperatura e transições entre etapas.

**Localização**: `services/process_control.py`

**Métodos principais**:
- `start_session(recipe_id, equipment_mapping)` - Inicia sessão
- `pause_session(session_id)` - Pausa sessão
- `resume_session(session_id)` - Retoma sessão
- `stop_session(session_id)` - Para sessão
- `control_temperature(device_id, target_temp, tolerance)` - Controle PID
- `log_event(session_id, event_type, data)` - Registra evento

### DashboardBuilderService

Gerencia layouts SVG, posicionamento de elementos e vinculação com dispositivos.

**Localização**: `services/dashboard_builder.py`

**Métodos principais**:
- `load_layout(layout_id)` - Carrega layout salvo
- `save_layout(layout_data, user_id, is_default)` - Salva layout
- `get_default_layout(user_id)` - Obtém layout padrão
- `create_element(element_type, position, device_id)` - Cria elemento SVG
- `get_svg_components()` - Retorna biblioteca de componentes

### RecipeEditorService

Gerencia criação, edição, validação e importação de receitas.

**Localização**: `services/recipe_editor.py`

**Métodos principais**:
- `create_recipe(recipe_data)` - Cria nova receita
- `update_recipe(recipe_id, updates)` - Atualiza receita
- `delete_recipe(recipe_id)` - Remove receita
- `import_from_brewfather(brewfather_recipe_id)` - Importa do BrewFather
- `validate_recipe(recipe_data)` - Valida estrutura
- `calculate_timeline(recipe_data)` - Calcula timeline

## Estrutura de Dados JSON

### Receita (`data/recipes/{recipe_id}.json`)

```json
{
  "id": "recipe_001",
  "name": "American IPA",
  "version": "1.0",
  "brewfather_recipe_id": "bf_12345",
  "equipment": {
    "mash_tun": "device_001",
    "boil_kettle": "device_002",
    "pump_1": "device_003"
  },
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
}
```

### Layout de Dashboard (`data/dashboards/{layout_id}.json`)

```json
{
  "id": "layout_default",
  "name": "Layout Padrão",
  "elements": [
    {
      "type": "kettle",
      "id": "kettle_1",
      "x": 100,
      "y": 50,
      "device_id": "device_001",
      "properties": {
        "fill_color": "#4CAF50",
        "show_temp": true,
        "show_level": true
      }
    }
  ]
}
```

## Integração com Device Manager

O Mash Control utiliza a API pública do Device Manager para:

1. **Listar Dispositivos**: Obter lista de sensores e atuadores disponíveis
2. **Ler Valores**: Obter valores de portas de sensores (temperatura, etc.)
3. **Controlar Dispositivos**: Enviar comandos para atuadores (aquecedores, bombas, válvulas)
4. **Telemetria**: Inscrever-se em atualizações em tempo real

**Exemplo de uso**:

```python
from plugins.plugin_mash_control.services.device_integration import DeviceIntegrationService

device_service = DeviceIntegrationService()

# Obter sensores disponíveis
sensors = device_service.get_sensors()

# Ler temperatura
temp = device_service.get_port_value('device_001', 'GPIO_32')

# Controlar aquecedor
device_service.set_port_value('device_001', 'GPIO_25', True)
```

## Integração com BrewFather

O plugin pode importar receitas do BrewFather através do plugin `integ_bFather`:

1. **Listar Receitas**: Obter lista de receitas sincronizadas do BrewFather
2. **Importar Receita**: Converter formato BrewFather para formato Mash Control
3. **Mapear Equipamento**: Associar dispositivos IoT às funções da receita

**Fluxo de importação**:

1. Usuário seleciona receita do BrewFather na interface
2. Sistema converte etapas de mostura e fervura
3. Receita é salva no formato Mash Control
4. Usuário pode editar e executar a receita importada

## Segurança

- Todas as rotas API requerem autenticação (`@login_required`)
- Validação de comandos enviados aos dispositivos
- Limites de temperatura/operação configuráveis
- Log de todas as ações de controle
- Validação de equipamento antes de iniciar sessão

## Troubleshooting

### Plugin não aparece no menu

1. Verifique se o plugin está instalado: `flask plugin list`
2. Verifique se o plugin está ativo: `flask plugin activate mash_control`
3. Verifique se `device_manager` está instalado e ativo (dependência obrigatória)

### Dispositivos não aparecem

1. Verifique se o Device Manager está funcionando
2. Verifique se os dispositivos estão cadastrados e ativos
3. Verifique os logs do sistema

### Sessão não inicia

1. Verifique se todos os dispositivos necessários estão disponíveis
2. Verifique se o mapeamento de equipamento está correto
3. Verifique os logs da sessão para erros específicos

## Desenvolvimento

Para contribuir com o desenvolvimento do plugin:

1. Clone o repositório
2. Instale as dependências de desenvolvimento
3. Siga os padrões de código do BrewStation
4. Use `model_loader` para acessar modelos prefixados
5. Teste todas as funcionalidades antes de submeter

## Referências

- [Manual do Usuário](PLUGIN_MASH_CONTROL_MANUAL.md)
- [Referência da API](PLUGIN_MASH_CONTROL_API.md)
- [Device Manager API](PLUGIN_DEVICE_MANAGER_API.md)
- [Sistema de Plugins](PLUGIN_SYSTEM.md)

