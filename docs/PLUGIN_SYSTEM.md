# Sistema de Plugins do BrewStation

## Visão Geral

O BrewStation é um sistema modular que permite adicionar funcionalidades através de plugins. Cada plugin é um módulo independente que pode ser instalado, ativado, desativado e desinstalado dinamicamente.

## Estrutura de um Plugin

Cada plugin deve estar localizado em `src/plugins/<nome_do_plugin>/` e conter a seguinte estrutura:

```
src/plugins/<nome_do_plugin>/
├── plugin.py              # Classe principal do plugin (herda de PluginBase)
├── install.json           # Configuração do plugin (nome, versão, menu, etc.)
├── api/
│   └── routes/           # Rotas API (blueprints Flask)
│       ├── __init__.py   # Exporta todos os blueprints
│       └── *.py          # Arquivos de rotas individuais
├── controller/
│   └── routes.py         # Rotas web (blueprint Flask para páginas HTML)
├── templates/            # Templates HTML do plugin
│   └── *.html
├── static/              # Arquivos estáticos (CSS, JS, imagens) - opcional
├── model/               # Modelos SQLAlchemy do plugin - opcional
├── utils/               # Utilitários do plugin - opcional
└── logs/                # Logs do plugin - opcional
```

## install.json

O arquivo `install.json` é obrigatório e contém a configuração do plugin:

```json
{
  "name": "nome_do_plugin",
  "version": "1.0.0",
  "description": "Descrição do plugin",
  "author": "Nome do Autor",
  "menu": {
    "main_items": [
      {
        "id": "item_id",
        "label": "Nome do Item",
        "icon": "bi bi-icon-name",
        "url": "blueprint_name.route_name",
        "children": [
          {
            "label": "Subitem",
            "icon": "bi bi-icon",
            "url": "blueprint_name.subroute"
          }
        ]
      }
    ]
  },
  "dependencies": [],
  "db_models": [
    "model.nome_modelo"
  ]
}
```

### Campos do install.json

- **name**: Nome único do plugin (usado para identificação)
- **version**: Versão do plugin (formato semântico)
- **description**: Descrição do que o plugin faz
- **author**: Nome do autor/equipe
- **menu**: Configuração do menu de navegação
  - **main_items**: Lista de itens principais do menu
    - **id**: Identificador único do item
    - **label**: Texto exibido no menu
    - **icon**: Classe do ícone Bootstrap Icons (ex: "bi bi-house")
    - **url**: Endpoint do Flask para `url_for()` (ex: "plugin_web.maltes")
    - **children**: Lista opcional de subitens (submenu)
- **dependencies**: Lista de nomes de outros plugins necessários
- **db_models**: Lista de módulos de modelos SQLAlchemy (opcional)

## Classe do Plugin (plugin.py)

Cada plugin deve ter uma classe que herda de `PluginBase`:

```python
from core.plugin_base import PluginBase
from flask import Blueprint
from typing import List

class PluginMeuPlugin(PluginBase):
    def install(self) -> bool:
        """Instala o plugin (cria tabelas, configurações, etc.)"""
        # Implementar lógica de instalação
        return True
    
    def uninstall(self) -> bool:
        """Desinstala o plugin (remove dados, etc.)"""
        # Implementar lógica de desinstalação
        return True
    
    def register_routes(self, app) -> List[Blueprint]:
        """Registra as rotas do plugin"""
        # Retornar lista de blueprints
        return []
    
    def register_models(self) -> List:
        """Registra os modelos SQLAlchemy do plugin"""
        # Retornar lista de modelos
        return []
```

## Sistema de Instalação Automática

O BrewStation possui um sistema de instalação automática que:

1. **Descobre plugins**: Escaneia `src/plugins/` procurando por diretórios com `plugin.py` e `install.json`
2. **Carrega configuração**: Lê o `install.json` de cada plugin
3. **Registra rotas API**: Descobre automaticamente blueprints em `api/routes/__init__.py`
4. **Registra rotas web**: Descobre blueprint em `controller/routes.py`
5. **Registra templates**: Adiciona `templates/` ao template loader do Jinja2
6. **Registra menu**: Extrai itens de menu do `install.json` e injeta no template base
7. **Registra modelos**: Chama `register_models()` para criar tabelas no banco

## Rotas

### Rotas API

As rotas API devem estar em `api/routes/` e serem exportadas em `__init__.py`:

```python
# api/routes/__init__.py
from .minhas_rotas import minha_api_bp

all_blueprints = [minha_api_bp]
```

As rotas API são registradas com prefixo `/api`.

### Rotas Web

As rotas web devem estar em `controller/routes.py`:

```python
from flask import Blueprint, render_template

web_plugin_bp = Blueprint('plugin_meu_plugin_web', __name__)

@web_plugin_bp.route("/minha-pagina")
def minha_pagina():
    return render_template("minha_pagina.html")
```

As rotas web são registradas **sem prefixo** (acessíveis diretamente como `/minha-pagina`).

## Templates

Os templates devem estar em `templates/` e são carregados automaticamente pelo `PluginTemplateLoader`. O sistema busca templates na seguinte ordem:

1. Templates dos plugins ativos (por ordem de ativação)
2. Templates do core (`src/templates/`)

## Menu de Navegação

O menu é construído automaticamente a partir do `install.json` de todos os plugins ativos. Cada item pode ser:

- **Item simples**: Link direto para uma rota
- **Item com submenu**: Item que expande mostrando subitens

O menu é injetado no template `base.html` através do context processor `inject_plugin_menu()`.

## Comandos CLI

O sistema fornece comandos Flask CLI para gerenciar plugins:

```bash
# Listar todos os plugins
flask plugin list

# Descobrir novos plugins
flask plugin discover

# Instalar um plugin
flask plugin install <nome_do_plugin>

# Desinstalar um plugin
flask plugin uninstall <nome_do_plugin>

# Ativar um plugin
flask plugin activate <nome_do_plugin>

# Desativar um plugin
flask plugin deactivate <nome_do_plugin>

# Informações de um plugin
flask plugin info <nome_do_plugin>
```

## Exemplo Completo

Veja o plugin `plugin_integ_bFather` em `src/plugins/plugin_integ_bFather/` como referência completa de um plugin funcional.

## Notas Importantes

1. O nome do plugin no `install.json` deve ser único
2. O nome do diretório do plugin pode ser diferente do nome no `install.json`
3. O sistema descobre plugins pelo nome do diretório, mas usa o nome do `install.json` internamente
4. Templates são buscados primeiro nos plugins, depois no core
5. Rotas API sempre usam prefixo `/api`
6. Rotas web não usam prefixo (são registradas diretamente)
7. O menu é construído dinamicamente a partir do `install.json` de todos os plugins ativos
