# Sistema de Rotas de Plugins

Este documento descreve o sistema melhorado de registro de rotas para plugins do BrewStation.

## Visão Geral

O sistema de rotas de plugins permite que cada plugin registre suas próprias rotas (API e Web) de forma automática e organizada. O sistema garante que todas as rotas sejam descobertas, registradas e navegáveis de maneira fluida.

## Estrutura de Pastas

Cada plugin deve seguir a seguinte estrutura:

```
plugins/
  meu_plugin/
    api/
      routes/
        __init__.py          # Exporta all_blueprints
        ingredientes_routes.py
        receitas_routes.py
        ...
    controller/
      routes.py              # Blueprint web do plugin
    templates/
      ...
    static/
      ...
    install.json
    menu_config.json
```

## Criando Rotas de API

### Método 1: Usando o Helper (Recomendado)

```python
# plugins/meu_plugin/api/routes/__init__.py

from flask import Blueprint, jsonify
from flask_login import login_required
from core.plugin_routes_helper import create_plugin_api_blueprint, plugin_route

# Criar blueprint de API
api_bp = create_plugin_api_blueprint(
    plugin_name='meu_plugin',
    blueprint_name='meu_plugin_api'
)

# Registrar rotas usando o decorator simplificado
@plugin_route(api_bp, 'meu_plugin', '/maltes', methods=['GET'])
@login_required
def get_maltes():
    """Obter lista de maltes"""
    return jsonify({'maltes': []}), 200

@plugin_route(api_bp, 'meu_plugin', '/maltes', methods=['POST'])
@login_required
def create_malte():
    """Criar novo malte"""
    return jsonify({'message': 'Malte criado'}), 201

# Exportar blueprint
all_blueprints = [api_bp]
```

### Método 2: Blueprint Tradicional

```python
# plugins/meu_plugin/api/routes/ingredientes_routes.py

from flask import Blueprint, jsonify
from flask_login import login_required

ingredientes_bp = Blueprint('ingredientes', __name__)

@ingredientes_bp.route('/maltes', methods=['GET'])
@login_required
def get_maltes():
    return jsonify({'maltes': []}), 200

# Em __init__.py:
from .ingredientes_routes import ingredientes_bp
all_blueprints = [ingredientes_bp]
```

## Criando Rotas Web

### Método 1: Usando o Helper (Recomendado)

```python
# plugins/meu_plugin/controller/routes.py

from flask import Blueprint, render_template
from flask_login import login_required
from core.plugin_routes_helper import create_plugin_web_blueprint, plugin_route

# Criar blueprint web
web_bp = create_plugin_web_blueprint(
    plugin_name='meu_plugin',
    blueprint_name='plugin_meu_plugin_web'
)

# Registrar rotas
@plugin_route(web_bp, 'meu_plugin', '/maltes', methods=['GET'])
@login_required
def maltes_page():
    """Página de maltes"""
    return render_template('maltes.html')

# Exportar blueprint
web_plugin_bp = web_bp
```

### Método 2: Blueprint Tradicional

```python
# plugins/meu_plugin/controller/routes.py

from flask import Blueprint, render_template
from flask_login import login_required

web_plugin_bp = Blueprint('plugin_meu_plugin_web', __name__)

@web_plugin_bp.route('/maltes')
@login_required
def maltes():
    return render_template('maltes.html')
```

## Configuração de Prefixos de URL

Você pode configurar prefixos personalizados no `install.json`:

```json
{
  "name": "meu_plugin",
  "routes": {
    "api_prefix": "/api",
    "web_prefix": null
  }
}
```

- `api_prefix`: Prefixo para rotas de API (padrão: `/api`)
- `web_prefix`: Prefixo para rotas web (padrão: `null` - sem prefixo)

## Sistema de Registro de Rotas

O sistema mantém um registro centralizado de todas as rotas dos plugins, facilitando a navegação:

```python
from core.plugin_routes_helper import get_route_registry

route_registry = get_route_registry()

# Obter todas as rotas de um plugin
plugin_routes = route_registry.get_plugin_routes('meu_plugin')

# Construir URL para uma rota específica
url = route_registry.build_url('meu_plugin', 'meu_plugin_api.get_maltes')

# Obter informações sobre uma rota
route_info = route_registry.get_route('meu_plugin', 'meu_plugin_api.get_maltes')
```

## Descoberta Automática de Rotas

O sistema descobre automaticamente rotas de duas formas:

1. **Arquivo `__init__.py`**: Procura por `all_blueprints` ou blueprints individuais exportados
2. **Arquivos individuais**: Procura por arquivos `*_routes.py` que exportam blueprints

### Exemplo de `__init__.py`:

```python
# plugins/meu_plugin/api/routes/__init__.py

from .ingredientes_routes import ingredientes_bp
from .receitas_routes import receitas_bp

all_blueprints = [
    ingredientes_bp,
    receitas_bp
]
```

## Menu e Navegação

As rotas podem ser referenciadas no `menu_config.json` usando o nome do endpoint:

```json
{
  "main_items": [
    {
      "id": "maltes",
      "label": "Maltes",
      "icon": "bi bi-circle",
      "url": "plugin_meu_plugin_web.maltes_page"
    }
  ]
}
```

O sistema usa `url_for()` para construir URLs automaticamente, garantindo navegação fluida.

## Boas Práticas

1. **Use o helper quando possível**: O `plugin_route` facilita o registro e mantém consistência
2. **Organize rotas por funcionalidade**: Crie arquivos separados para diferentes áreas (ex: `ingredientes_routes.py`, `receitas_routes.py`)
3. **Exporte blueprints em `__init__.py`**: Facilita a descoberta automática
4. **Use nomes descritivos**: Nomes claros facilitam a manutenção e navegação
5. **Documente rotas**: Adicione docstrings explicando o propósito de cada rota

## Exemplo Completo

Veja `src/core/plugin_routes_example.py` para exemplos completos de uso do sistema.

## Troubleshooting

### Rotas não estão sendo registradas

1. Verifique se o plugin está ativo em `plugins.json`
2. Verifique se os blueprints estão sendo exportados corretamente
3. Verifique os logs da aplicação para mensagens de erro
4. Certifique-se de que o arquivo `__init__.py` existe e exporta `all_blueprints`

### URLs não estão funcionando

1. Verifique se o endpoint está correto no `menu_config.json`
2. Use `get_route_registry().get_all_routes()` para listar todas as rotas registradas
3. Verifique se o blueprint foi registrado corretamente no Flask

### Conflitos de nomes

1. Use nomes únicos para blueprints (ex: `plugin_meu_plugin_api`)
2. Evite nomes genéricos como `api` ou `web`
3. Use o nome do plugin como prefixo quando possível

