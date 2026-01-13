# Análise da Integração de Plugins com Flask

## Visão Geral

Este documento detalha como os plugins do BrewStation se integram com o Flask, cobrindo rotas, templates, modelos e sistema de menu. A integração é feita de forma automática e transparente, permitindo que plugins funcionem como extensões nativas da aplicação.

## 1. Integração de Rotas

### 1.1. Tipos de Rotas

O sistema suporta dois tipos de rotas:

#### Rotas API
- **Localização**: `api/routes/`
- **Prefixo Padrão**: `/api/{plugin_name}`
- **Uso**: Endpoints REST para comunicação frontend-backend
- **Exemplo**: `/api/device_manager/devices`

#### Rotas Web
- **Localização**: `controller/routes.py`
- **Prefixo Padrão**: Sem prefixo (configurável)
- **Uso**: Páginas HTML renderizadas
- **Exemplo**: `/devices`

### 1.2. Descoberta Automática de Rotas

O `PluginInstaller` descobre rotas automaticamente durante a ativação:

#### Descoberta de Rotas API

**Método 1: `__init__.py` com `all_blueprints`**

```python
# api/routes/__init__.py
from flask import Blueprint

device_bp = Blueprint('plugin_device_manager_api', __name__)
config_bp = Blueprint('plugin_device_manager_config_api', __name__)

all_blueprints = [device_bp, config_bp]
```

**Método 2: Arquivos `*_routes.py`**

```python
# api/routes/device_routes.py
from flask import Blueprint

device_bp = Blueprint('plugin_device_manager_api', __name__)

@device_bp.route('/devices', methods=['GET'])
def list_devices():
    return jsonify([])
```

#### Descoberta de Rotas Web

```python
# controller/routes.py
from flask import Blueprint

web_plugin_bp = Blueprint('plugin_device_manager_web', __name__)

@web_plugin_bp.route('/devices')
def devices_page():
    return render_template('device_manager.html')
```

### 1.3. Carregamento Dinâmico

O sistema usa `importlib.util` para carregar módulos dinamicamente:

**Processo:**
1. Constrói nome do módulo baseado no caminho
2. Usa `spec_from_file_location()` para criar spec
3. Executa módulo com `exec_module()`
4. Busca atributos que são instâncias de `Blueprint`

**Resolução de Nomes:**
- De: `src/plugins/plugin_name/api/routes/__init__.py`
- Para: `plugins.plugin_name.api.routes`

### 1.4. Registro de Blueprints

Durante `_register_plugin()`, os blueprints são registrados:

**Rotas API:**
```python
# Determina prefixo
url_prefix = self._get_api_url_prefix(plugin)
# Padrão: /api/{plugin_name}
# Configurável via install.json → routes.api_prefix

# Registra blueprint
app.register_blueprint(bp, url_prefix=url_prefix)

# Registra no route_registry para navegação
route_registry.register_blueprint(plugin.name, bp)
```

**Rotas Web:**
```python
# Determina prefixo
url_prefix = self._get_web_url_prefix(plugin)
# Padrão: None (sem prefixo)
# Configurável via install.json → routes.web_prefix

# Registra blueprint
app.register_blueprint(web_bp, url_prefix=url_prefix)
```

### 1.5. Verificação de Duplicatas

Antes de registrar, o sistema verifica se o blueprint já existe:

```python
if bp.name not in self.app.blueprints:
    app.register_blueprint(bp, url_prefix=url_prefix)
else:
    logger.debug(f"Blueprint {bp.name} já está registrado, pulando...")
```

### 1.6. Configuração de Prefixos

No `install.json`:
```json
{
  "routes": {
    "api_prefix": "/api/device_manager",
    "web_prefix": "/devices"
  }
}
```

**Lógica de Determinação:**
- Se `routes.api_prefix` especificado → usa esse valor
- Caso contrário → `/api/{plugin_name}` (remove prefixo `plugin_` se presente)

### 1.7. Exemplo Completo

**Estrutura:**
```
plugin_device_manager/
├── api/
│   └── routes/
│       ├── __init__.py
│       └── device_routes.py
└── controller/
    └── routes.py
```

**Rotas API:**
```python
# api/routes/device_routes.py
from flask import Blueprint, jsonify
from flask_login import login_required

device_bp = Blueprint('plugin_device_manager_api', __name__)

@device_bp.route('/device_manager/devices', methods=['GET'])
@login_required
def list_devices():
    return jsonify({'devices': []})
```

**Rotas Web:**
```python
# controller/routes.py
from flask import Blueprint, render_template

web_plugin_bp = Blueprint('plugin_device_manager_web', __name__)

@web_plugin_bp.route('/devices')
def devices():
    return render_template('device_manager.html')
```

**Resultado:**
- API: `/api/device_manager/device_manager/devices` (prefixo + rota)
- Web: `/devices` (sem prefixo)

## 2. Integração de Templates

### 2.1. Sistema de Template Loader

O `PluginTemplateLoader` é um loader customizado Jinja2 que permite override de templates.

**Características:**
- Herda de `BaseLoader` do Jinja2
- Busca templates em múltiplos diretórios
- Permite que plugins sobrescrevam templates core

### 2.2. Ordem de Busca

O loader busca templates na seguinte ordem:

1. **Templates dos plugins ativos** (por ordem de ativação)
   - Primeiro plugin ativado tem prioridade
   - Útil para override de templates core

2. **Templates do core** (`src/templates/`)
   - Fallback se não encontrado nos plugins

**Exemplo:**
```
Plugin A ativado primeiro
Plugin B ativado depois
Core

Busca por 'base.html':
1. Plugin A/templates/base.html
2. Plugin B/templates/base.html
3. Core/templates/base.html
```

### 2.3. Integração com Jinja2

O loader é integrado via `ChoiceLoader`:

```python
from jinja2 import ChoiceLoader

plugin_loader = PluginTemplateLoader(plugins_dir, active_plugins)
existing_loader = app.jinja_env.loader

# Combina loaders
app.jinja_env.loader = ChoiceLoader([plugin_loader, existing_loader])
```

### 2.4. Estrutura de Templates

**Plugin:**
```
plugin_name/
└── templates/
    ├── plugin_page.html
    └── partials/
        └── widget.html
```

**Core:**
```
src/
└── templates/
    ├── base.html
    └── components/
        └── navbar.html
```

### 2.5. Uso nos Blueprints

Templates são referenciados normalmente:

```python
@web_plugin_bp.route('/devices')
def devices():
    # Busca em: Plugin/templates/device_manager.html → Core/templates/device_manager.html
    return render_template('device_manager.html')
```

### 2.6. Override de Templates Core

Plugins podem sobrescrever templates core:

**Core:**
```
src/templates/components/navbar.html
```

**Plugin:**
```
plugin_custom_ui/templates/components/navbar.html
```

Se `plugin_custom_ui` for ativado primeiro, seu template será usado.

### 2.7. Atualização Dinâmica

Quando um plugin é ativado/desativado, o template loader é atualizado:

```python
def _update_template_loader(self):
    plugin_loader = PluginTemplateLoader(self.plugins_dir, self.active_plugins)
    existing_loader = self.app.jinja_env.loader
    self.app.jinja_env.loader = ChoiceLoader([plugin_loader, existing_loader])
```

## 3. Integração de Modelos

### 3.1. Sistema de Prefixação

Para evitar conflitos de nomes de tabelas, o sistema aplica prefixos:

**Configuração (`install.json`):**
```json
{
  "table_prefix": "dvmanage"  // ou null para usar nome do diretório
}
```

**Aplicação:**
- Durante `_register_plugin()`, modelos são prefixados
- Prefixo aplicado a `__tablename__` e `__table__.name`
- Tabelas criadas com nomes prefixados

**Exemplo:**
```python
# Modelo original
class DeviceMetadata(db.Model):
    __tablename__ = 'device_metadata'

# Após prefixação (prefixo: "dvmanage_")
class DeviceMetadata(db.Model):
    __tablename__ = 'dvmanage_device_metadata'
```

### 3.2. Registro de Modelos

**Processo:**
1. Plugin retorna lista de modelos via `register_models()`
2. Sistema aplica prefixos via `prefix_models()`
3. Modelos são registrados no `plugin_model_registry`
4. Tabelas são criadas com `db.create_all()`

**Código:**
```python
models = plugin.register_models()
if models:
    prefixed_models = prefix_models(models, plugin_name_for_prefix, plugin.table_prefix)
    
    # Registrar no registry
    for model in prefixed_models:
        register_prefixed_model(plugin_name, model, original_tablename)
    
    # Criar tabelas
    with app.app_context():
        db.create_all()
```

### 3.3. Acesso a Modelos Prefixados

**Problema:** Importação direta não garante uso de modelos prefixados.

**Solução:** Usar `model_loader` do plugin:

```python
# utils/model_loader.py
from core.plugin_model_registry import get_prefixed_model

PLUGIN_NAME = "plugin_device_manager"

def get_device_metadata():
    return get_prefixed_model(PLUGIN_NAME, 'DeviceMetadata')
```

**Uso nas Rotas:**
```python
# api/routes/device_routes.py
from plugins.plugin_device_manager.utils.model_loader import get_device_metadata

DeviceMetadata = get_device_metadata()

@device_bp.route('/devices', methods=['GET'])
def list_devices():
    devices = DeviceMetadata.query.all()
    return jsonify([d.to_dict() for d in devices])
```

### 3.4. Plugin Model Registry

O `plugin_model_registry` mantém registro global de modelos prefixados:

**Estrutura:**
```python
_prefixed_models_registry: Dict[str, Dict[str, Type]] = {}
# {plugin_name: {class_name: model_class}}
```

**Funções:**
- `register_prefixed_model()`: Registra modelo prefixado
- `get_prefixed_model()`: Obtém modelo prefixado
- `get_all_prefixed_models()`: Lista todos os modelos de um plugin

### 3.5. Relacionamentos entre Modelos

**Modelos Core:**
- Importados antes dos modelos de plugins
- Disponíveis para relacionamentos

**Exemplo:**
```python
# model/user.py (core)
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)

# model/device_metadata.py (plugin)
class DeviceMetadata(db.Model):
    __tablename__ = 'dvmanage_device_metadata'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='devices')
```

### 3.6. Importação de Modelos Core

Durante `_register_plugin()`, modelos core são importados primeiro:

```python
# Garantir que User está disponível para relacionamentos
from model.user import User
from db.database import db
with app.app_context():
    _ = User.__table__  # Força registro no metadata
```

## 4. Integração de Menu

### 4.1. Sistema de Menu

O sistema de menu permite que plugins adicionem itens à navegação principal.

### 4.2. Configuração do Menu

**Opção 1: Arquivo Separado (`menu_config.json`)**

```json
{
  "main_items": [
    {
      "id": "devices",
      "label": "Dispositivos",
      "icon": "bi bi-device-hdd",
      "url": "device_manager.devices",
      "children": [
        {
          "label": "Listar",
          "icon": "bi bi-list",
          "url": "device_manager.list_devices"
        },
        {
          "label": "Adicionar",
          "icon": "bi bi-plus",
          "url": "device_manager.add_device"
        }
      ]
    }
  ]
}
```

**Opção 2: Inline no `install.json`**

```json
{
  "menu": {
    "main_items": [
      {
        "id": "devices",
        "label": "Dispositivos",
        "icon": "bi bi-device-hdd",
        "url": "device_manager.devices"
      }
    ]
  }
}
```

**Referência no `install.json`:**
```json
{
  "menu_config_path": "menu_config.json"
}
```

### 4.3. Carregamento do Menu

Via `plugin.get_menu_config()`:

```python
def get_menu_config(self) -> Dict[str, Any]:
    # Verificar se há caminho para arquivo de menu separado
    menu_config_path = self.config.get('menu_config_path')
    if menu_config_path:
        menu_file = self.plugin_path / menu_config_path
        if menu_file.exists():
            with open(menu_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    
    # Fallback para menu inline no install.json
    return self.menu_config
```

### 4.4. Estrutura Hierárquica

O menu é estruturado hierarquicamente:

```
Plugin (label do install.json)
  ├── Item 1 (do menu_config.json)
  │   ├── Subitem 1.1
  │   └── Subitem 1.2
  └── Item 2
```

### 4.5. Injeção no Template

Via context processor `inject_plugin_menu()`:

```python
@app.context_processor
def inject_plugin_menu():
    def safe_url_for(endpoint, **values):
        """Helper para construir URLs de forma segura."""
        try:
            return url_for(endpoint, **values)
        except (BuildError, Exception) as e:
            logger.debug(f"Erro ao construir URL: {e}")
            return '#'
    
    if hasattr(app, 'plugin_manager'):
        menu_items = app.plugin_manager.get_menu_items()
        return {
            "plugin_menu_items": menu_items,
            "safe_url_for": safe_url_for
        }
    return {"plugin_menu_items": [], "safe_url_for": lambda x, **kwargs: '#'}
```

### 4.6. Formatação dos Itens

O `PluginManager.get_menu_items()` formata os itens:

```python
def get_menu_items(self) -> List[Dict]:
    menu_items = []
    
    for plugin_name in self.active_plugins:
        plugin = self.get_plugin(plugin_name)
        menu_config = plugin.get_menu_config()
        main_items = menu_config.get('main_items', [])
        
        # Criar item principal do plugin
        plugin_menu_item = {
            'id': f"plugin_{plugin_dir_name}",
            'label': plugin.label or plugin.name,
            'icon': 'bi bi-puzzle',
            'url': '',
            'children': []
        }
        
        # Adicionar itens do menu como sub-itens
        for item in main_items:
            formatted_item = {
                'id': item.get('id', ''),
                'label': item.get('label', ''),
                'icon': item.get('icon', 'bi bi-circle'),
                'url': item.get('url', ''),
                'children': []
            }
            
            # Processar children (submenu)
            if 'children' in item:
                for child in item['children']:
                    formatted_item['children'].append({
                        'label': child.get('label', ''),
                        'icon': child.get('icon', 'bi bi-circle'),
                        'url': child.get('url', '')
                    })
            
            plugin_menu_item['children'].append(formatted_item)
        
        menu_items.append(plugin_menu_item)
    
    return menu_items
```

### 4.7. Uso no Template

```html
<!-- templates/base.html -->
<nav>
  {% for plugin_item in plugin_menu_items %}
    <div class="plugin-menu">
      <h3>{{ plugin_item.label }}</h3>
      <ul>
        {% for item in plugin_item.children %}
          <li>
            <a href="{{ safe_url_for(item.url) }}">
              <i class="{{ item.icon }}"></i>
              {{ item.label }}
            </a>
            {% if item.children %}
              <ul>
                {% for child in item.children %}
                  <li>
                    <a href="{{ safe_url_for(child.url) }}">
                      {{ child.label }}
                    </a>
                  </li>
                {% endfor %}
              </ul>
            {% endif %}
          </li>
        {% endfor %}
      </ul>
    </div>
  {% endfor %}
</nav>
```

### 4.8. Construção de URLs

O `safe_url_for` trata erros graciosamente:

```python
def safe_url_for(endpoint, **values):
    if not endpoint:
        return '#'
    try:
        return url_for(endpoint, **values)
    except (BuildError, Exception) as e:
        logger.debug(f"Erro ao construir URL para '{endpoint}': {e}")
        return '#'
```

**URLs nos Menu Items:**
- Podem ser endpoints Flask (ex: `device_manager.devices`)
- Podem ser URLs absolutas (ex: `https://example.com`)
- Erros são tratados retornando `#`

## 5. Integração de Static Files

### 5.1. Registro de Static Files

Durante `_register_plugin()`, arquivos estáticos são registrados:

```python
static_folder = installer.get_static_folder()
if static_folder:
    static_bp = Blueprint(
        f'plugin_{plugin.name}_static',
        __name__,
        static_folder=str(static_folder),
        static_url_path=f'/plugin/{plugin.name}/static'
    )
    app.register_blueprint(static_bp)
```

### 5.2. Estrutura de Diretórios

```
plugin_name/
└── static/
    ├── css/
    │   └── styles.css
    ├── js/
    │   └── script.js
    └── images/
        └── logo.png
```

### 5.3. URLs Resultantes

```
/plugin/device_manager/static/css/styles.css
/plugin/device_manager/static/js/script.js
/plugin/device_manager/static/images/logo.png
```

### 5.4. Uso nos Templates

```html
<link rel="stylesheet" href="{{ url_for('plugin_device_manager_static', filename='css/styles.css') }}">
<script src="{{ url_for('plugin_device_manager_static', filename='js/script.js') }}"></script>
```

## 6. Fluxo de Integração Completo

### Durante Ativação de Plugin

```
activate_plugin(plugin_name)
    ↓
plugin.activate() → is_active = True
    ↓
_register_plugin(plugin)
    ↓
┌─────────────────────────────────────┐
│ 1. Importar modelos core            │
│    - Garantir User disponível       │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 2. Registrar e prefixar modelos    │
│    - plugin.register_models()       │
│    - prefix_models()                │
│    - register_prefixed_model()      │
│    - db.create_all()                │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 3. Descobrir rotas                 │
│    - discover_api_routes()          │
│    - discover_web_routes()          │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 4. Registrar blueprints            │
│    - API: /api/{plugin_name}        │
│    - Web: sem prefixo               │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 5. Registrar static files          │
│    - /plugin/{plugin_name}/static   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│ 6. Atualizar template loader       │
│    - Adicionar templates do plugin │
└─────────────────────────────────────┘
    ↓
Adicionar a active_plugins
    ↓
Salvar estado em plugins.json
```

### Durante Requisição

```
Cliente → Requisição HTTP
    ↓
Flask Router
    ↓
Blueprint do Plugin (se rota do plugin)
    ↓
@login_required (se protegida)
    ↓
Função da rota
    ↓
model_loader.get_modelo() → Modelo prefixado do registry
    ↓
Query SQLAlchemy → Tabela com prefixo
    ↓
Response (JSON ou HTML via template)
    ↓
Template Loader busca template:
    1. Plugin/templates/
    2. Core/templates/
```

## 7. Boas Práticas

1. **Rotas API**: Use `model_loader` para acessar modelos prefixados
2. **Rotas Web**: Use `render_template()` normalmente, loader busca automaticamente
3. **Menu**: Configure `menu_config.json` para melhor organização
4. **Static Files**: Use URLs geradas pelo Flask via `url_for()`
5. **Templates**: Plugins podem sobrescrever templates core se necessário
6. **Modelos**: Sempre use `model_loader` em vez de importação direta
7. **Prefixos**: Configure `table_prefix` para evitar conflitos
8. **Nomes Únicos**: Use nomes únicos para blueprints (ex: `plugin_{name}_api`)

## 8. Exemplo Completo de Integração

### Plugin Structure

```
plugin_exemplo/
├── plugin.py
├── install.json
├── menu_config.json
├── api/
│   └── routes/
│       └── exemplo_routes.py
├── controller/
│   └── routes.py
├── templates/
│   └── exemplo.html
├── static/
│   └── exemplo.css
├── model/
│   └── exemplo.py
└── utils/
    └── model_loader.py
```

### Rotas API

```python
# api/routes/exemplo_routes.py
from flask import Blueprint, jsonify
from flask_login import login_required
from plugins.plugin_exemplo.utils.model_loader import get_exemplo_model

exemplo_bp = Blueprint('plugin_exemplo_api', __name__)

@exemplo_bp.route('/exemplo/items', methods=['GET'])
@login_required
def list_items():
    ExemploModel = get_exemplo_model()
    items = ExemploModel.query.all()
    return jsonify([item.to_dict() for item in items])
```

### Rotas Web

```python
# controller/routes.py
from flask import Blueprint, render_template

web_plugin_bp = Blueprint('plugin_exemplo_web', __name__)

@web_plugin_bp.route('/exemplo')
def exemplo_page():
    return render_template('exemplo.html')
```

### Model Loader

```python
# utils/model_loader.py
from core.plugin_model_registry import get_prefixed_model

PLUGIN_NAME = "plugin_exemplo"

def get_exemplo_model():
    return get_prefixed_model(PLUGIN_NAME, 'ExemploModel')
```

### Template

```html
<!-- templates/exemplo.html -->
{% extends "base.html" %}

{% block content %}
<h1>Exemplo Plugin</h1>
<link rel="stylesheet" href="{{ url_for('plugin_exemplo_static', filename='exemplo.css') }}">
{% endblock %}
```

### Resultado

- **API**: `/api/exemplo/exemplo/items`
- **Web**: `/exemplo`
- **Static**: `/plugin/exemplo/static/exemplo.css`
- **Template**: `plugin_exemplo/templates/exemplo.html`
- **Modelo**: `exemplo_exemplo_model` (tabela prefixada)
