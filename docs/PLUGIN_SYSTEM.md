# Sistema de Plugins do BrewStation

## Visão Geral

O BrewStation é um sistema modular que permite adicionar funcionalidades através de plugins. Cada plugin é um módulo independente que pode ser instalado, ativado, desativado e desinstalado dinamicamente.

## Plugins Disponíveis

### Device Manager

Plugin completo de gerenciamento de dispositivos IoT com servidor MQTT embutido.

- **Documentação**: `docs/PLUGIN_DEVICE_MANAGER.md`
- **API para Plugins**: `docs/PLUGIN_DEVICE_MANAGER_API.md`
- **Funcionalidades**:
  - Gerenciamento de dispositivos IoT (sensores, atuadores, gateways)
  - Servidor MQTT embutido
  - Sistema de portas configuráveis
  - Monitoramento em tempo real
  - API pública para outros plugins

### Mash Control

Plugin completo de automação de processos de brassagem com dashboard visual interativo.

- **Documentação**: `docs/PLUGIN_MASH_CONTROL.md`
- **API**: `docs/PLUGIN_MASH_CONTROL_API.md`
- **Funcionalidades**:
  - Dashboard visual com representação SVG do brewhouse
  - Controle automático e manual de processos de brassagem
  - Editor visual de receitas (profiles)
  - Sistema de logging e histórico de sessões
  - Integração bidirecional em tempo real com dispositivos via Device Manager
  - Importação de receitas do BrewFather
- **Dependências**: Requer `device_manager` instalado e ativo

## Estrutura de um Plugin

Cada plugin deve estar localizado em `src/plugins/<nome_do_plugin>/` e conter a seguinte estrutura:

```
src/plugins/<nome_do_plugin>/
├── plugin.py              # Classe principal do plugin (herda de PluginBase)
├── install.json           # Configuração do plugin (nome, versão, etc.)
├── menu_config.json       # Configuração do menu de navegação (opcional)
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

O arquivo `install.json` é obrigatório e contém a configuração básica do plugin:

```json
{
  "name": "nome_do_plugin",
  "label": "Nome Exibido no Menu",
  "version": "1.0.0",
  "description": "Descrição do plugin",
  "author": "Nome do Autor",
  "menu_config_path": "menu_config.json",
  "dependencies": [],
  "db_models": [
    "model.nome_modelo"
  ],
  "table_prefix": null
}
```

### Campos do install.json

- **name**: Nome único do plugin (usado para identificação interna)
- **label**: Nome exibido no menu (opcional, prioridade sobre `name`)
  - Se não existir, usa `name`
  - Se `name` também não existir, usa o nome do diretório formatado
- **version**: Versão do plugin (formato semântico)
- **description**: Descrição do que o plugin faz
- **author**: Nome do autor/equipe
- **menu_config_path**: Caminho relativo para o arquivo de configuração do menu (opcional)
  - Padrão: `"menu_config.json"`
  - Se não especificado, o sistema procura por `menu_config.json` na raiz do plugin
- **dependencies**: Lista de nomes de outros plugins necessários
- **db_models**: Lista de módulos de modelos SQLAlchemy (opcional)
- **table_prefix**: Prefixo para nomes de tabelas (opcional)
  - Se `null` ou não especificado: usa o nome do diretório do plugin como prefixo padrão (ex: `plugin_meu_plugin_`)
  - Se especificado: usa o valor fornecido (ex: `"meu_plugin_"`)
  - Veja [Sistema de Banco de Dados](PLUGIN_DATABASE.md) para mais detalhes

## menu_config.json

O arquivo `menu_config.json` contém a estrutura do menu de navegação do plugin. Este arquivo é separado do `install.json` para melhor organização:

```json
{
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
          "url": "blueprint_name.subroute",
          "children": [
            {
              "label": "Sub-subitem",
              "icon": "bi bi-icon",
              "url": "blueprint_name.subsubroute"
            }
          ]
        }
      ]
    }
  ]
}
```

### Campos do menu_config.json

- **main_items**: Lista de itens principais do menu
  - **id**: Identificador único do item
  - **label**: Texto exibido no menu
  - **icon**: Classe do ícone Bootstrap Icons (ex: "bi bi-house")
  - **url**: Endpoint do Flask para `url_for()` (ex: "plugin_web.maltes")
  - **children**: Lista opcional de subitens (suporta múltiplos níveis)

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

**⚠️ IMPORTANTE**: Se suas rotas API usam modelos SQLAlchemy, **sempre use `model_loader`** em vez de importar modelos diretamente. Isso garante que os modelos prefixados sejam usados corretamente.

**Exemplo correto:**
```python
# api/routes/minhas_rotas.py
from flask import Blueprint, jsonify
from flask_login import login_required
from plugins.meu_plugin.utils.model_loader import get_meu_modelo

minha_api_bp = Blueprint('minha_api', __name__)

@minha_api_bp.route('/dados', methods=['GET'])
@login_required
def get_dados():
    MeuModelo = get_meu_modelo()  # Usa model_loader
    dados = MeuModelo.query.all()
    return jsonify([d.to_dict() for d in dados]), 200
```

Veja [Guia do Model Loader](PLUGIN_MODEL_LOADER.md) para mais detalhes.

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

O menu é construído automaticamente a partir do `menu_config.json` de todos os plugins ativos. A estrutura do menu é hierárquica:

### Estrutura Hierárquica

```
📦 Nome do Plugin (do campo "label" ou "name" do install.json)
  ├── 📄 Item 1 (do menu_config.json)
  │   ├── Subitem 1.1
  │   └── Subitem 1.2
  │       └── Sub-subitem 1.2.1
  ├── 📄 Item 2
  └── 📄 Item 3
```

### Prioridade do Nome do Plugin

O nome exibido no menu segue esta prioridade:

1. **`label`** (campo no `install.json`) - **Prioridade máxima**
2. **`name`** (campo no `install.json`) - Se `label` não existir
3. **Nome do diretório formatado** - Se nenhum dos dois existir

### Carregamento do Menu

- O sistema carrega o menu do arquivo especificado em `menu_config_path` (padrão: `menu_config.json`)
- Se o arquivo não existir, o plugin não terá itens no menu
- O menu é injetado no template `base.html` através do context processor `inject_plugin_menu()`
- Endpoints inválidos são tratados automaticamente (links apontam para `#` sem quebrar o template)

## Comandos CLI

O sistema fornece comandos para gerenciar plugins através do `run.py` e Flask CLI:

### Comandos via run.py (Recomendado)

```bash
# Criar plugin template (modo interativo)
python run.py plugin -c

# Criar plugin template (modo direto)
python run.py plugin -c meu_plugin "Meu Plugin"

# Instalar um plugin
python run.py plugin -i <nome_do_plugin>

# Ativar um plugin
python run.py plugin -a <nome_do_plugin>

# Desativar um plugin
python run.py plugin -d <nome_do_plugin>

# Ajuda sobre comandos de plugin
python run.py plugin -h
```

### Comandos via Flask CLI

```bash
cd src

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

### Gerador de Plugins

O comando `python run.py plugin -c` cria automaticamente:

- ✅ Estrutura completa de diretórios
- ✅ `install.json` configurado
- ✅ `menu_config.json` básico
- ✅ `plugin.py` com implementação mínima
- ✅ Rota API de exemplo funcional
- ✅ Rota web de exemplo funcional
- ✅ Template HTML básico

Veja [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md) para mais detalhes.

## Exemplo Completo

Veja o plugin `plugin_integ_bFather` em `src/plugins/plugin_integ_bFather/` como referência completa de um plugin funcional.

## Sistema de Prefixos de Tabelas

O BrewStation aplica automaticamente prefixos aos nomes das tabelas dos modelos de plugins para evitar conflitos e melhorar a organização. O prefixo pode ser configurado no campo `table_prefix` do `install.json`.

**Comportamento:**
- Se `table_prefix` for `null` ou não especificado: usa o nome do diretório do plugin (ex: `plugin_meu_plugin_`)
- Se `table_prefix` for especificado: usa o valor fornecido (ex: `"meu_plugin_"`)

**Exemplo:**
- Modelo com `__tablename__ = 'produtos'`
- Plugin com `table_prefix: null` → Tabela criada como `plugin_meu_plugin_produtos`
- Plugin com `table_prefix: "estoque_"` → Tabela criada como `estoque_produtos`

Veja [Sistema de Banco de Dados](PLUGIN_DATABASE.md) para mais detalhes.

## Model Loader

Para garantir que as rotas API sempre usem modelos com os prefixos corretos, o sistema recomenda o uso de `model_loader` em vez de importar modelos diretamente.

**Por que usar model_loader:**
- Garante que modelos prefixados sejam sempre usados
- Evita erros de "tabela não encontrada"
- Facilita manutenção e migrações

Veja [Guia do Model Loader](PLUGIN_MODEL_LOADER.md) para mais detalhes e exemplos.

## Notas Importantes

1. O nome do plugin no `install.json` deve ser único
2. O nome do diretório do plugin pode ser diferente do nome no `install.json`
3. O sistema descobre plugins pelo nome do diretório, mas usa o nome do `install.json` internamente
4. Templates são buscados primeiro nos plugins, depois no core
5. Rotas API sempre usam prefixo `/api`
6. Rotas web não usam prefixo (são registradas diretamente)
7. O menu é construído dinamicamente a partir do `install.json` de todos os plugins ativos
8. **Sempre use `model_loader` nas rotas API que acessam modelos SQLAlchemy**
9. Modelos são prefixados automaticamente durante o registro do plugin
10. Use comandos CLI (`flask diagnose-brewfather-tables`, `flask migrate-brewfather-tables`) para diagnosticar e migrar tabelas
