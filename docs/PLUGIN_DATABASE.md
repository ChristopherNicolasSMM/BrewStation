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
3. **Ao ativar plugin**: Quando um plugin é ativado, seus modelos são registrados

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

## Referências

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)

