# Guia do Model Loader para Plugins

Este documento explica o que é o `model_loader`, por que usá-lo e como implementá-lo em seus plugins.

## O que é Model Loader?

O `model_loader` é um helper que garante que os modelos SQLAlchemy sejam sempre carregados com os prefixos corretos aplicados às tabelas. Ele resolve problemas de timing onde rotas são importadas antes dos prefixos serem aplicados aos modelos.

## Por que Usar Model Loader?

### O Problema

Quando você importa modelos diretamente em rotas API:

```python
# ❌ ERRADO
from plugins.meu_plugin.model.minha_tabela import MinhaTabela

@api_bp.route('/dados')
def get_dados():
    dados = MinhaTabela.query.all()  # Pode procurar tabela sem prefixo!
    return jsonify([d.to_dict() for d in dados])
```

**Problemas possíveis:**
- Rotas são importadas antes dos prefixos serem aplicados
- Queries podem procurar tabelas sem prefixo (`minha_tabela`) quando deveriam procurar com prefixo (`plugin_meu_plugin_minha_tabela`)
- Erros como `sqlite3.OperationalError: no such table: minha_tabela`

### A Solução

O `model_loader` garante que os modelos sempre tenham os prefixos corretos:

```python
# ✅ CORRETO
from plugins.meu_plugin.utils.model_loader import get_minha_tabela

@api_bp.route('/dados')
def get_dados():
    MinhaTabela = get_minha_tabela()  # Sempre usa tabela com prefixo correto
    dados = MinhaTabela.query.all()
    return jsonify([d.to_dict() for d in dados])
```

## Como Criar um Model Loader

### Estrutura Básica

Crie o arquivo `utils/model_loader.py` no seu plugin:

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
        model_class_name: Nome da classe do modelo (ex: 'MinhaTabela')
        
    Returns:
        Classe do modelo prefixado ou None se não encontrado
    """
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    # Fallback: importar diretamente do plugin
    try:
        from plugins.meu_plugin.model.minha_tabela import MinhaTabela
        
        model_map = {
            'MinhaTabela': MinhaTabela,
        }
        
        return model_map.get(model_class_name)
    except ImportError:
        return None

# Funções helper para obter modelos específicos
def get_minha_tabela():
    """Obtém o modelo MinhaTabela prefixado"""
    return _get_prefixed_model('MinhaTabela')

# Exportar modelos diretamente para uso nas rotas
# NOTA: Os modelos abaixo serão prefixados pelo plugin_manager quando o plugin for carregado.
from plugins.meu_plugin.model.minha_tabela import MinhaTabela
```

### Exemplo Completo com Múltiplos Modelos

```python
"""
Helper para carregar modelos prefixados do plugin.
"""

from flask import current_app
from core.plugin_model_registry import get_prefixed_model

PLUGIN_NAME = "meu_plugin"

def _get_prefixed_model(model_class_name: str):
    """Obtém um modelo prefixado do registry."""
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    # Fallback: importar diretamente do plugin
    try:
        from plugins.meu_plugin.model.produto import Produto
        from plugins.meu_plugin.model.categoria import Categoria
        from plugins.meu_plugin.model.venda import Venda
        
        model_map = {
            'Produto': Produto,
            'Categoria': Categoria,
            'Venda': Venda,
        }
        
        return model_map.get(model_class_name)
    except ImportError:
        return None

# Funções helper para cada modelo
def get_produto():
    """Obtém o modelo Produto prefixado"""
    return _get_prefixed_model('Produto')

def get_categoria():
    """Obtém o modelo Categoria prefixado"""
    return _get_prefixed_model('Categoria')

def get_venda():
    """Obtém o modelo Venda prefixado"""
    return _get_prefixed_model('Venda')

# Exportar modelos diretamente
from plugins.meu_plugin.model.produto import Produto
from plugins.meu_plugin.model.categoria import Categoria
from plugins.meu_plugin.model.venda import Venda
```

## Como Usar nas Rotas API

### Método 1: Usando Funções Helper (Recomendado)

```python
from plugins.meu_plugin.utils.model_loader import get_minha_tabela

@api_bp.route('/dados', methods=['GET'])
@login_required
def get_dados():
    MinhaTabela = get_minha_tabela()
    dados = MinhaTabela.query.all()
    return jsonify([d.to_dict() for d in dados]), 200
```

### Método 2: Importação Direta (Se Configurado)

Se o `model_loader` exporta modelos diretamente (como no exemplo acima):

```python
from plugins.meu_plugin.utils.model_loader import MinhaTabela

@api_bp.route('/dados', methods=['GET'])
@login_required
def get_dados():
    # MinhaTabela já está prefixado pelo plugin_manager
    dados = MinhaTabela.query.all()
    return jsonify([d.to_dict() for d in dados]), 200
```

**⚠️ IMPORTANTE**: Use o Método 1 se não tiver certeza. O Método 2 funciona apenas se os modelos forem exportados diretamente no `model_loader` e o plugin já tiver sido carregado.

## Exemplo Completo: Plugin com Model Loader

### Estrutura do Plugin

```
plugins/meu_plugin/
├── plugin.py
├── install.json
├── model/
│   └── produto.py
├── utils/
│   └── model_loader.py
└── api/
    └── routes/
        └── produtos_routes.py
```

### model/produto.py

```python
from sqlalchemy import Column, Integer, String, Float
from db.database import db

class Produto(db.Model):
    __tablename__ = 'produtos'  # Será prefixado automaticamente
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    preco = Column(Float, nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'preco': self.preco
        }
```

### utils/model_loader.py

```python
from core.plugin_model_registry import get_prefixed_model

PLUGIN_NAME = "meu_plugin"

def _get_prefixed_model(model_class_name: str):
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    try:
        from plugins.meu_plugin.model.produto import Produto
        return {'Produto': Produto}.get(model_class_name)
    except ImportError:
        return None

def get_produto():
    return _get_prefixed_model('Produto')

from plugins.meu_plugin.model.produto import Produto
```

### api/routes/produtos_routes.py

```python
from flask import Blueprint, jsonify
from flask_login import login_required
from plugins.meu_plugin.utils.model_loader import get_produto

produtos_bp = Blueprint('produtos_api', __name__)

@produtos_bp.route('/produtos', methods=['GET'])
@login_required
def listar_produtos():
    Produto = get_produto()
    produtos = Produto.query.all()
    return jsonify([p.to_dict() for p in produtos]), 200

@produtos_bp.route('/produtos/<int:produto_id>', methods=['GET'])
@login_required
def obter_produto(produto_id):
    Produto = get_produto()
    produto = Produto.query.get_or_404(produto_id)
    return jsonify(produto.to_dict()), 200
```

### plugin.py

```python
def register_models(self) -> List:
    """Registra os modelos SQLAlchemy do plugin."""
    from model.produto import Produto
    return [Produto]
```

## Boas Práticas

### 1. Sempre Use Model Loader em Rotas API

**❌ ERRADO:**
```python
from plugins.meu_plugin.model.produto import Produto
```

**✅ CORRETO:**
```python
from plugins.meu_plugin.utils.model_loader import get_produto
Produto = get_produto()
```

### 2. Crie Funções Helper para Cada Modelo

Facilita o uso e torna o código mais legível:

```python
def get_produto():
    return _get_prefixed_model('Produto')

def get_categoria():
    return _get_prefixed_model('Categoria')
```

### 3. Mantenha o PLUGIN_NAME Atualizado

Certifique-se de que `PLUGIN_NAME` no `model_loader.py` corresponde ao nome do plugin:

```python
PLUGIN_NAME = "meu_plugin"  # Deve corresponder ao nome no install.json ou diretório
```

### 4. Use Fallback para Desenvolvimento

O fallback permite que o código funcione mesmo se o registry não estiver disponível:

```python
def _get_prefixed_model(model_class_name: str):
    prefixed_model = get_prefixed_model(PLUGIN_NAME, model_class_name)
    if prefixed_model:
        return prefixed_model
    
    # Fallback para desenvolvimento/testes
    try:
        from plugins.meu_plugin.model.produto import Produto
        return {'Produto': Produto}.get(model_class_name)
    except ImportError:
        return None
```

### 5. Documente os Modelos Disponíveis

Adicione comentários no `model_loader.py` listando todos os modelos:

```python
"""
Helper para carregar modelos prefixados do plugin.

Modelos disponíveis:
- Produto: Produtos do sistema
- Categoria: Categorias de produtos
- Venda: Registros de vendas
"""
```

## Troubleshooting

### Erro "no such table" mesmo usando model_loader

**Possíveis causas:**
1. `PLUGIN_NAME` está incorreto no `model_loader.py`
2. Modelo não foi registrado em `register_models()`
3. Plugin não foi ativado após criar modelos

**Solução:**
1. Verifique que `PLUGIN_NAME` corresponde ao nome do plugin
2. Verifique que o modelo está em `register_models()`
3. Reative o plugin: `flask plugin deactivate meu_plugin && flask plugin activate meu_plugin`

### Model Loader retorna None

**Causa**: Modelo não encontrado no registry ou importação falhou

**Solução:**
1. Verifique que o modelo está registrado em `register_models()`
2. Verifique que o caminho de importação está correto no fallback
3. Verifique os logs para erros de importação

### Debug: Verificar qual tabela está sendo usada

Adicione logs temporários:

```python
from plugins.meu_plugin.utils.model_loader import get_produto

@api_bp.route('/produtos')
def listar_produtos():
    Produto = get_produto()
    print(f"DEBUG - Tabela usada: {Produto.__tablename__}")
    print(f"DEBUG - Total registros: {Produto.query.count()}")
    
    produtos = Produto.query.all()
    return jsonify([p.to_dict() for p in produtos])
```

## Referências

- [Sistema de Banco de Dados](PLUGIN_DATABASE.md) - Informações sobre prefixos de tabelas
- [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md) - Guia completo de desenvolvimento
- [Sistema de Plugins](PLUGIN_SYSTEM.md) - Visão geral do sistema

