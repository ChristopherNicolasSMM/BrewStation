# Guia de Desenvolvimento de Plugins

Este guia fornece instruções detalhadas para criar plugins para o BrewStation.

## Visão Geral

Plugins permitem estender o BrewStation com novas funcionalidades sem modificar o código core. Cada plugin é um módulo independente que pode ser instalado, ativado, desativado e desinstalado dinamicamente.

## Pré-requisitos

- Conhecimento de Python 3.11+
- Familiaridade com Flask e Blueprints
- Conhecimento básico de SQLAlchemy
- Entendimento de HTML/CSS/JavaScript

## Estrutura de um Plugin

Crie um novo diretório em `src/plugins/<nome_do_plugin>/`:

```
src/plugins/meu_plugin/
├── plugin.py              # Classe principal (obrigatório)
├── install.json           # Configuração (obrigatório)
├── api/
│   └── routes/           # Rotas API (opcional)
│       ├── __init__.py
│       └── minhas_rotas.py
├── controller/
│   └── routes.py         # Rotas web (opcional)
├── templates/            # Templates HTML (opcional)
│   └── minha_pagina.html
├── static/              # Arquivos estáticos (opcional)
│   ├── css/
│   ├── js/
│   └── img/
├── model/               # Modelos SQLAlchemy (opcional)
│   └── meu_modelo.py
└── utils/               # Utilitários (opcional)
    └── helpers.py
```

## Passo 1: Criar install.json

Crie o arquivo `install.json` com a configuração básica do plugin:

```json
{
  "name": "meu_plugin",
  "label": "Meu Plugin",
  "version": "1.0.0",
  "description": "Descrição do que o plugin faz",
  "author": "Seu Nome",
  "menu_config_path": "menu_config.json",
  "dependencies": [],
  "db_models": [],
  "table_prefix": null
}
```

### Campos Importantes

- **`name`**: Identificador único interno do plugin
- **`label`**: Nome exibido no menu (opcional, mas recomendado)
  - Se não especificado, usa `name`
  - Se `name` também não existir, usa o nome do diretório formatado
- **`menu_config_path`**: Caminho para o arquivo de menu (padrão: `"menu_config.json"`)
- **`table_prefix`**: Prefixo para nomes de tabelas (opcional)
  - Se `null` ou não especificado: usa o nome do diretório do plugin como prefixo (ex: `plugin_meu_plugin_`)
  - Se especificado: usa o valor fornecido (ex: `"meu_plugin_"`)
  - Veja [Sistema de Banco de Dados](PLUGIN_DATABASE.md) para mais detalhes

## Passo 1.1: Criar menu_config.json

Crie o arquivo `menu_config.json` com a estrutura do menu:

```json
{
  "main_items": [
    {
      "id": "meu_item",
      "label": "Meu Item",
      "icon": "bi bi-star",
      "url": "meu_plugin_web.minha_pagina",
      "children": [
        {
          "label": "Subitem",
          "icon": "bi bi-circle",
          "url": "meu_plugin_web.subpagina"
        }
      ]
    }
  ]
}
```

**Nota**: O nome do plugin (do campo `label` ou `name` do `install.json`) aparecerá como item principal no menu, e os itens do `menu_config.json` aparecerão como subitens.

## Passo 2: Criar plugin.py

Crie a classe do plugin herdando de `PluginBase`:

```python
from pathlib import Path
from typing import List
from flask import Blueprint

from core.plugin_base import PluginBase
from db.database import db


class PluginMeuPlugin(PluginBase):
    """Plugin de exemplo."""
    
    def install(self) -> bool:
        """Instala o plugin."""
        try:
            # Criar tabelas do banco
            models = self.register_models()
            if models:
                db.create_all()
            
            # Registrar no banco de dados
            from model.plugin import Plugin as PluginModel
            
            plugin_db = PluginModel.query.filter_by(name=self.name).first()
            if not plugin_db:
                plugin_db = PluginModel(
                    name=self.name,
                    version=self.version,
                    description=self.description,
                    author=self.author,
                    is_installed=True,
                    is_active=False,
                    config_json=self.config
                )
                db.session.add(plugin_db)
            else:
                plugin_db.is_installed = True
                plugin_db.version = self.version
            
            db.session.commit()
            return True
        except Exception as e:
            print(f"Erro ao instalar plugin {self.name}: {e}")
            db.session.rollback()
            return False
    
    def uninstall(self) -> bool:
        """Desinstala o plugin."""
        try:
            from model.plugin import Plugin as PluginModel
            
            plugin_db = PluginModel.query.filter_by(name=self.name).first()
            if plugin_db:
                plugin_db.is_installed = False
                plugin_db.is_active = False
                db.session.commit()
            
            return True
        except Exception as e:
            print(f"Erro ao desinstalar plugin {self.name}: {e}")
            db.session.rollback()
            return False
    
    def register_routes(self, app) -> List[Blueprint]:
        """Registra as rotas do plugin."""
        # O sistema descobre automaticamente rotas em api/routes/ e controller/routes.py
        # Este método é usado apenas como fallback
        return []
    
    def register_models(self) -> List:
        """Registra os modelos SQLAlchemy do plugin."""
        models = []
        
        # Importar e retornar modelos do plugin
        # Exemplo:
        # from model.meu_modelo import MeuModelo
        # models.append(MeuModelo)
        
        return models
```

## Passo 3: Criar Rotas API (Opcional)

Se seu plugin precisa de rotas API, crie em `api/routes/`:

**api/routes/minhas_rotas.py:**
```python
from flask import Blueprint, request, jsonify
from flask_login import login_required
from db.database import db

minha_api_bp = Blueprint('minha_api', __name__)

@minha_api_bp.route('/minha-rota', methods=['GET'])
@login_required
def minha_rota():
    """Exemplo de rota API."""
    return jsonify({'message': 'Hello from plugin!'}), 200
```

**⚠️ IMPORTANTE**: Se seu plugin usa modelos SQLAlchemy, **sempre use `model_loader`** nas rotas API em vez de importar modelos diretamente. Veja a seção "Usando Modelos nas Rotas API" abaixo.

**api/routes/__init__.py:**
```python
from .minhas_rotas import minha_api_bp

all_blueprints = [minha_api_bp]
```

As rotas API são registradas automaticamente com prefixo `/api`.

### Usando Modelos nas Rotas API

Se suas rotas API precisam acessar modelos do banco de dados, você **deve** usar o `model_loader` para garantir que os modelos prefixados sejam usados corretamente.

**❌ ERRADO** - Importação direta (pode causar erros de "tabela não encontrada"):
```python
from plugins.meu_plugin.model.meu_modelo import MeuModelo

@minha_api_bp.route('/dados', methods=['GET'])
@login_required
def get_dados():
    dados = MeuModelo.query.all()  # Pode procurar tabela sem prefixo!
    return jsonify([d.to_dict() for d in dados]), 200
```

**✅ CORRETO** - Usando model_loader:
```python
from plugins.meu_plugin.utils.model_loader import get_meu_modelo

@minha_api_bp.route('/dados', methods=['GET'])
@login_required
def get_dados():
    MeuModelo = get_meu_modelo()
    dados = MeuModelo.query.all()  # Sempre usa tabela com prefixo correto
    return jsonify([d.to_dict() for d in dados]), 200
```

Veja a seção "Passo 3.1: Criar model_loader" abaixo para criar o arquivo `utils/model_loader.py`.

### Passo 3.1: Criar model_loader (Recomendado se usar modelos)

Se seu plugin define modelos SQLAlchemy, crie `utils/model_loader.py`:

**utils/model_loader.py:**
```python
"""
Helper para carregar modelos prefixados do plugin.

Este módulo garante que os modelos sejam sempre carregados com os prefixos
corretos aplicados às tabelas. Use este helper em vez de importar diretamente
de model.* para garantir que os modelos prefixados sejam usados.
"""

from flask import current_app
from core.plugin_model_registry import get_prefixed_model

# Nome do plugin (ajuste conforme necessário)
PLUGIN_NAME = "meu_plugin"

def _get_prefixed_model(model_class_name: str):
    """
    Obtém um modelo prefixado do registry.
    
    Args:
        model_class_name: Nome da classe do modelo (ex: 'MeuModelo')
        
    Returns:
        Classe do modelo prefixado ou None se não encontrado
    """
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    # Fallback: importar diretamente do plugin
    try:
        from plugins.meu_plugin.model.meu_modelo import MeuModelo
        
        model_map = {
            'MeuModelo': MeuModelo,
        }
        
        return model_map.get(model_class_name)
    except ImportError:
        return None

# Funções helper para obter modelos específicos
def get_meu_modelo():
    """Obtém o modelo MeuModelo prefixado"""
    return _get_prefixed_model('MeuModelo')

# Exportar modelos diretamente para uso nas rotas
# NOTA: Os modelos abaixo serão prefixados pelo plugin_manager quando o plugin for carregado.
from plugins.meu_plugin.model.meu_modelo import MeuModelo
```

**Uso nas rotas:**
```python
from plugins.meu_plugin.utils.model_loader import get_meu_modelo

@minha_api_bp.route('/dados', methods=['GET'])
@login_required
def get_dados():
    MeuModelo = get_meu_modelo()
    dados = MeuModelo.query.all()
    return jsonify([d.to_dict() for d in dados]), 200
```

Veja [Guia do Model Loader](PLUGIN_MODEL_LOADER.md) para mais detalhes.

## Passo 4: Criar Rotas Web (Opcional)

Crie rotas web em `controller/routes.py`:

```python
from flask import Blueprint, render_template
from flask_login import login_required

web_plugin_bp = Blueprint('meu_plugin_web', __name__)

@web_plugin_bp.route("/minha-pagina")
@login_required
def minha_pagina():
    """Renderiza página do plugin."""
    return render_template("minha_pagina.html")
```

As rotas web são registradas **sem prefixo** (acessíveis diretamente como `/minha-pagina`).

## Passo 5: Criar Templates (Opcional)

Crie templates HTML em `templates/`:

**templates/minha_pagina.html:**
```html
{% extends "base.html" %}

{% block content %}
<div class="container">
    <h1>Minha Página do Plugin</h1>
    <p>Conteúdo do plugin aqui.</p>
</div>
{% endblock %}
```

Templates herdam de `base.html` e têm acesso a todas as variáveis do contexto.

## Passo 6: Criar Modelos (Opcional)

Se seu plugin precisa de tabelas no banco, crie modelos:

**model/meu_modelo.py:**
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from db.database import db

class MeuModelo(db.Model):
    __tablename__ = 'meu_modelo'  # Será prefixado automaticamente
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
```

**⚠️ IMPORTANTE**: O `__tablename__` será automaticamente prefixado pelo sistema. Se seu `install.json` tem `table_prefix: null`, a tabela será criada como `plugin_meu_plugin_meu_modelo`. Se tiver `table_prefix: "custom_"`, será `custom_meu_modelo`.

Registre o modelo em `plugin.py`:

```python
def register_models(self) -> List:
    """Registra os modelos SQLAlchemy do plugin."""
    from model.meu_modelo import MeuModelo
    
    return [MeuModelo]
```

**Nota**: Os modelos são prefixados automaticamente durante o registro. Não é necessário especificar o prefixo no `__tablename__` do modelo.

### Configurando Prefixo de Tabelas

No `install.json`, você pode configurar o prefixo:

```json
{
  "name": "meu_plugin",
  "table_prefix": null  // Usa "plugin_meu_plugin_" como padrão
}
```

ou

```json
{
  "name": "meu_plugin",
  "table_prefix": "custom_"  // Usa "custom_" como prefixo
}
```

Veja [Sistema de Banco de Dados](PLUGIN_DATABASE.md) para mais detalhes sobre prefixos.

## Passo 7: Testar o Plugin

### 1. Descobrir Plugin

```bash
cd src
flask plugin discover
```

### 2. Instalar Plugin

```bash
flask plugin install meu_plugin
```

### 3. Ativar Plugin

```bash
flask plugin activate meu_plugin
```

### 4. Verificar Status

```bash
flask plugin list
flask plugin info meu_plugin
```

### 5. Testar Funcionalidades

- Acesse as rotas web criadas
- Teste as rotas API via Postman/curl
- Verifique se o menu aparece na sidebar
- Confirme que templates são renderizados

## Boas Práticas

### 1. Nomenclatura

- Use nomes descritivos e únicos para plugins
- Siga convenções Python (snake_case)
- Evite conflitos com plugins existentes

### 2. Estrutura de Código

- Mantenha código organizado e documentado
- Use type hints
- Siga PEP 8

### 3. Tratamento de Erros

```python
def install(self) -> bool:
    try:
        # Lógica de instalação
        return True
    except Exception as e:
        logger.error(f"Erro ao instalar: {e}")
        db.session.rollback()
        return False
```

### 4. Dependências

Declare dependências no `install.json`:

```json
{
  "dependencies": ["plugin_base", "outro_plugin"]
}
```

### 5. Versionamento

Use versionamento semântico (MAJOR.MINOR.PATCH):

- **MAJOR**: Mudanças incompatíveis
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs

### 6. Documentação

Documente seu plugin:
- README.md no diretório do plugin
- Docstrings em funções e classes
- Comentários em código complexo

## Exemplo Completo

Veja o plugin `plugin_integ_bFather` em `src/plugins/plugin_integ_bFather/` como referência completa de um plugin funcional.

## Troubleshooting

### Plugin não aparece na lista

**Verifique:**
- `install.json` e `plugin.py` existem
- Estrutura JSON válida
- Nome do plugin único

### Rotas não funcionam

**Verifique:**
- Blueprints exportados em `api/routes/__init__.py`
- Nome do blueprint em `controller/routes.py` é `web_plugin_bp`
- Plugin está ativo

### Menu não aparece ou está incorreto

**Verifique:**
- `menu_config.json` existe na raiz do plugin
- Campo `menu_config_path` no `install.json` aponta para o arquivo correto
- Estrutura JSON do `menu_config.json` está válida
- Endpoints nas URLs do menu existem (use `safe_url_for` no template para evitar erros)
- Plugin está ativo

### Templates não encontrados

**Verifique:**
- Templates em `templates/`
- Nome do template correto
- Plugin está ativo
- Template loader está configurado corretamente

### Modelos não criados

**Verifique:**
- Modelos importados em `register_models()`
- Tabelas criadas após instalação
- Migrações aplicadas
- Prefixo configurado corretamente no `install.json`

**Comandos úteis:**
```bash
# Recriar tabelas de plugins
flask recreate-plugin-tables

# Diagnosticar tabelas
flask diagnose-brewfather-tables
```

### Erro "no such table" nas rotas API

**Causa**: Rotas estão importando modelos diretamente em vez de usar `model_loader`

**Solução**:
1. Crie `utils/model_loader.py` no seu plugin (veja Passo 3.1)
2. Atualize suas rotas para usar `model_loader`
3. Reinicie a aplicação

### Migração de Dados entre Tabelas

Se você precisa migrar dados de tabelas sem prefixo para tabelas com prefixo:

```bash
# 1. Diagnosticar
flask diagnose-brewfather-tables

# 2. Recriar tabelas com prefixos
flask recreate-plugin-tables

# 3. Migrar dados
flask migrate-brewfather-tables
```

Veja [Sistema de Banco de Dados](PLUGIN_DATABASE.md) para mais detalhes sobre migração.

## Recursos Adicionais

- [Sistema de Plugins](PLUGIN_SYSTEM.md)
- [Estrutura do install.json](PLUGIN_INSTALL_JSON.md)
- [Arquitetura do Sistema](ARCHITECTURE.md)
- [Referência da API](API_REFERENCE.md)

## Suporte

Para dúvidas sobre desenvolvimento de plugins:
- Consulte a documentação existente
- Veja exemplos em `src/plugins/`
- Abra uma issue no repositório

