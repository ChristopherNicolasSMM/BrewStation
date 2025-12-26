# Sistema de Banco de Dados para Plugins

Este documento descreve como o sistema de banco de dados funciona para plugins no BrewStation, incluindo o sistema de prefixos configuráveis para nomes de tabelas.

## Visão Geral

Os plugins podem definir modelos SQLAlchemy que serão automaticamente criados no banco de dados quando o plugin é instalado ou ativado. Para evitar conflitos de nomes e melhorar a organização, o sistema permite configurar prefixos para os nomes das tabelas.

## Configuração de Prefixos

### No install.json

O campo `table_prefix` pode ser especificado no arquivo `install.json` do plugin:

```json
{
  "name": "meu_plugin",
  "label": "Meu Plugin",
  "version": "1.0.0",
  "table_prefix": "meu_plugin_"
}
```

### Comportamento

- **Se `table_prefix` for especificado**: Usa o valor fornecido como prefixo
- **Se `table_prefix` for `null` ou não especificado**: Usa o nome do diretório do plugin como prefixo padrão
  - Exemplo: Plugin em `plugins/plugin_meu_plugin/` → prefixo `plugin_meu_plugin_`

### Exemplos

#### Exemplo 1: Prefixo Padrão (automático)
```json
{
  "name": "meu_plugin",
  "table_prefix": null
}
```
**Resultado**: Tabelas serão criadas como `plugin_meu_plugin_nome_tabela`

#### Exemplo 2: Prefixo Customizado
```json
{
  "name": "meu_plugin",
  "table_prefix": "custom_"
}
```
**Resultado**: Tabelas serão criadas como `custom_nome_tabela`

#### Exemplo 3: Sem Prefixo (não recomendado)
```json
{
  "name": "meu_plugin",
  "table_prefix": ""
}
```
**Resultado**: Tabelas serão criadas sem prefixo (pode causar conflitos)

## Criando Modelos em Plugins

### Estrutura Básica

Os modelos devem estar em `plugins/seu_plugin/model/` e serem retornados pelo método `register_models()`:

```python
# plugins/meu_plugin/model/minha_tabela.py
from sqlalchemy import Column, Integer, String
from db.database import db

class MinhaTabela(db.Model):
    __tablename__ = 'minha_tabela'  # Será prefixado automaticamente
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100))
    descricao = Column(String(255))
```

### Registrando Modelos

No arquivo `plugin.py`:

```python
def register_models(self) -> List:
    """Registra os modelos SQLAlchemy do plugin."""
    from model.minha_tabela import MinhaTabela
    
    return [MinhaTabela]
```

### Nomes de Tabelas Finais

Com o prefixo configurado, os nomes finais das tabelas serão:

- **Com prefixo padrão**: `plugin_meu_plugin_minha_tabela`
- **Com prefixo customizado "custom_"**: `custom_minha_tabela`

## ForeignKeys e Relacionamentos

### Atenção com ForeignKeys

Ao definir ForeignKeys em modelos de plugins, use strings com o nome completo da tabela (incluindo prefixo):

```python
from sqlalchemy import ForeignKey

class MinhaTabelaRelacionada(db.Model):
    __tablename__ = 'minha_tabela_relacionada'
    
    id = Column(Integer, primary_key=True)
    minha_tabela_id = Column(Integer, ForeignKey('plugin_meu_plugin_minha_tabela.id'))
```

**Nota**: O sistema não atualiza automaticamente ForeignKeys quando prefixos são aplicados. Você deve garantir que os nomes das tabelas referenciadas estejam corretos.

### Referenciando Tabelas Core

Para referenciar tabelas do core (sem prefixo de plugin):

```python
user_id = Column(Integer, ForeignKey('users.id'))  # Tabela core
```

## Processo de Criação de Tabelas

1. **Durante a instalação**: Quando `plugin.install()` é chamado, os modelos são registrados e as tabelas são criadas
2. **Durante a inicialização**: Quando o servidor inicia, modelos de plugins ativos são registrados e tabelas são criadas/atualizadas
3. **Ao ativar plugin**: Quando um plugin é ativado, seus modelos são registrados e prefixados automaticamente

**Importante**: Os modelos são prefixados **antes** das rotas serem carregadas, garantindo que quando as rotas importam os modelos, eles já têm os prefixos corretos aplicados.

## Boas Práticas

1. **Sempre use prefixos**: Evite conflitos de nomes usando prefixos apropriados
2. **Use nomes descritivos**: Nomes de tabelas devem ser claros e descritivos
3. **Documente ForeignKeys**: Documente quais tabelas são referenciadas
4. **Teste migrações**: Ao mudar prefixos, teste cuidadosamente as migrações de dados
5. **Considere o namespace**: Use prefixos que reflitam o propósito do plugin

## Exemplo Completo

### install.json
```json
{
  "name": "estoque_plugin",
  "label": "Plugin de Estoque",
  "version": "1.0.0",
  "table_prefix": "estoque_",
  "dependencies": [],
  "db_models": []
}
```

### model/produto.py
```python
from sqlalchemy import Column, Integer, String, Float
from db.database import db

class Produto(db.Model):
    __tablename__ = 'produtos'  # Será criado como 'estoque_produtos'
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    quantidade = Column(Integer, default=0)
    preco = Column(Float)
```

### plugin.py
```python
def register_models(self) -> List:
    from model.produto import Produto
    return [Produto]
```

**Tabela criada**: `estoque_produtos`

## Usando Modelos Prefixados nas Rotas

### O Problema

Quando você importa modelos diretamente em rotas API, pode haver um problema de timing: as rotas são importadas antes dos prefixos serem aplicados aos modelos, resultando em queries que procuram tabelas sem prefixo.

### A Solução: model_loader

O sistema fornece um helper `model_loader` que garante que os modelos sempre sejam carregados com os prefixos corretos. **Sempre use `model_loader` em suas rotas API em vez de importar modelos diretamente.**

### Criando um model_loader no Plugin

Crie um arquivo `utils/model_loader.py` no seu plugin:

```python
"""
Helper para carregar modelos prefixados do plugin.

Este módulo garante que os modelos sejam sempre carregados com os prefixos
corretos aplicados às tabelas.
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
from plugins.meu_plugin.model.minha_tabela import MinhaTabela
# Os modelos acima serão prefixados pelo plugin_manager quando o plugin for carregado.
```

### Usando model_loader nas Rotas API

**❌ ERRADO** - Importação direta:
```python
from plugins.meu_plugin.model.minha_tabela import MinhaTabela

@api_bp.route('/dados')
def get_dados():
    dados = MinhaTabela.query.all()  # Pode procurar tabela sem prefixo!
    return jsonify([d.to_dict() for d in dados])
```

**✅ CORRETO** - Usando model_loader:
```python
from plugins.meu_plugin.utils.model_loader import get_minha_tabela

@api_bp.route('/dados')
def get_dados():
    MinhaTabela = get_minha_tabela()
    dados = MinhaTabela.query.all()  # Sempre usa tabela com prefixo correto
    return jsonify([d.to_dict() for d in dados])
```

Ou usando importação direta do model_loader (se configurado corretamente):
```python
from plugins.meu_plugin.utils.model_loader import MinhaTabela

@api_bp.route('/dados')
def get_dados():
    dados = MinhaTabela.query.all()  # Modelo já prefixado
    return jsonify([d.to_dict() for d in dados])
```

Veja [Guia do Model Loader](PLUGIN_MODEL_LOADER.md) para mais detalhes.

## Comandos CLI para Diagnóstico e Migração

### Diagnóstico de Tabelas

Use o comando `flask diagnose-brewfather-tables` para verificar quais tabelas existem e se há necessidade de migração:

```bash
cd src
python -m flask diagnose-brewfather-tables
```

**Saída esperada:**
```
============================================================
DIAGNÓSTICO DE TABELAS BREWFATHER
============================================================

Tabelas encontradas relacionadas ao BrewFather:
  - brewfather_recipes: 10 registros
  - plugin_integ_bFather_brewfather_recipes: 0 registros

Verificando migração necessária:
  ⚠️  brewfather_recipes existe (10 registros) mas plugin_integ_bFather_brewfather_recipes não existe
     → Migração necessária!
```

### Recriar Tabelas com Prefixos

Se você precisa recriar todas as tabelas de plugins com os prefixos corretos:

```bash
cd src
python -m flask recreate-plugin-tables
```

Este comando:
- Remove tabelas antigas dos modelos de plugins
- Recria todas as tabelas (core e plugins) com os prefixos corretos
- Útil após mudanças em modelos ou prefixos

### Migrar Dados entre Tabelas

Se você tem dados em tabelas sem prefixo e precisa migrar para tabelas com prefixo:

```bash
cd src
python -m flask migrate-brewfather-tables
```

**⚠️ IMPORTANTE**: 
- Este comando migra dados de tabelas sem prefixo para tabelas com prefixo
- Execute `flask recreate-plugin-tables` primeiro para criar as tabelas com prefixo
- O comando pedirá confirmação se a tabela destino já tiver dados
- Após migração, verifique os dados antes de remover tabelas antigas

**Exemplo de uso:**
```bash
# 1. Diagnosticar situação
flask diagnose-brewfather-tables

# 2. Recriar tabelas com prefixos (se necessário)
flask recreate-plugin-tables

# 3. Migrar dados (se necessário)
flask migrate-brewfather-tables
```

## Migração de Tabelas sem Prefixo para com Prefixo

### Quando Migrar?

Migração é necessária quando:
- Você criou modelos antes do sistema de prefixos ser implementado
- Dados foram inseridos em tabelas sem prefixo
- Você mudou o `table_prefix` do plugin

### Processo de Migração

1. **Diagnosticar**: Execute `flask diagnose-brewfather-tables` para identificar tabelas que precisam migração

2. **Criar tabelas com prefixo**: Execute `flask recreate-plugin-tables` para garantir que as tabelas com prefixo existam

3. **Migrar dados**: Execute `flask migrate-brewfather-tables` para copiar dados

4. **Verificar**: Teste sua aplicação para garantir que os dados foram migrados corretamente

5. **Limpar** (opcional): Após verificar, você pode remover manualmente as tabelas antigas se desejar

### Migração Manual

Se preferir migrar manualmente via SQL:

```sql
-- Exemplo: Migrar dados de brewfather_recipes para plugin_integ_bFather_brewfather_recipes
INSERT INTO plugin_integ_bFather_brewfather_recipes 
SELECT * FROM brewfather_recipes;
```

**⚠️ CUIDADO**: Certifique-se de que:
- As estruturas das tabelas são compatíveis
- Não há conflitos de IDs
- ForeignKeys estão corretas

## Troubleshooting

### Tabelas não estão sendo criadas

1. Verifique se o plugin está instalado e ativo
2. Verifique se `register_models()` retorna uma lista não vazia
3. Verifique os logs para erros de importação
4. Verifique se o prefixo está configurado corretamente

### Conflitos de nomes

1. Use prefixos únicos para cada plugin
2. Verifique se não há outros plugins com o mesmo prefixo
3. Considere usar o nome completo do diretório como prefixo padrão

### ForeignKeys não funcionam

1. Verifique se o nome da tabela referenciada está correto (com prefixo)
2. Certifique-se de que a tabela referenciada existe
3. Use strings para nomes de tabelas em ForeignKeys, não classes

### Erro "no such table" nas rotas API

**Sintoma**: Rotas API retornam erro `sqlite3.OperationalError: no such table: nome_tabela`

**Causa comum**: Rotas estão importando modelos diretamente em vez de usar `model_loader`

**Solução**:
1. Crie `utils/model_loader.py` no seu plugin (veja seção acima)
2. Atualize suas rotas API para usar `model_loader`:
   ```python
   # Antes
   from plugins.meu_plugin.model.minha_tabela import MinhaTabela
   
   # Depois
   from plugins.meu_plugin.utils.model_loader import get_minha_tabela
   MinhaTabela = get_minha_tabela()
   ```
3. Reinicie a aplicação Flask

### Tabelas existem mas queries retornam vazias

**Sintoma**: Tabelas existem no banco, mas queries retornam resultados vazios

**Causa comum**: Query está procurando tabela sem prefixo, mas dados estão em tabela com prefixo

**Solução**:
1. Execute `flask diagnose-brewfather-tables` para verificar nomes das tabelas
2. Verifique qual tabela está sendo usada nas queries (adicionar logs de debug)
3. Use `model_loader` para garantir que o modelo correto seja usado

### Debug: Verificar qual tabela está sendo usada

Adicione logs temporários nas rotas para verificar:

```python
from plugins.meu_plugin.utils.model_loader import get_minha_tabela

@api_bp.route('/dados')
def get_dados():
    MinhaTabela = get_minha_tabela()
    print(f"DEBUG - Tabela usada: {MinhaTabela.__tablename__}")
    print(f"DEBUG - Total registros: {MinhaTabela.query.count()}")
    
    dados = MinhaTabela.query.all()
    return jsonify([d.to_dict() for d in dados])
```

## Referências

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)

