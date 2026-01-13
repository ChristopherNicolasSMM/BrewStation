# Análise do Sistema de Plugins do BrewStation

## Visão Geral

O sistema de plugins do BrewStation permite adicionar funcionalidades dinamicamente sem modificar o código core. Este documento detalha o processo completo de descoberta, carregamento, instalação e ativação de plugins.

## Ciclo de Vida de um Plugin

### Estados do Plugin

1. **Descoberto**: Plugin encontrado no diretório `src/plugins/`
2. **Carregado**: Classe do plugin instanciada em memória
3. **Instalado**: Método `install()` executado, estado persistido
4. **Ativo**: Método `activate()` executado, integrado na aplicação Flask
5. **Desativado**: Removido da aplicação, mas mantém instalação
6. **Desinstalado**: Método `uninstall()` executado, dados removidos

## 1. Descoberta de Plugins

### Processo de Descoberta

O `PluginLoader.discover_plugins()` escaneia o diretório `src/plugins/` procurando por:

**Critérios de Validação:**
- Diretório existe e não é arquivo
- Nome não inicia com `_` (ignorado)
- Contém `install.json`
- Contém `plugin.py`

**Fluxo:**
```
PluginLoader.discover_plugins()
    ↓
Itera sobre src/plugins/
    ↓
Para cada diretório:
    - Verifica se é diretório
    - Verifica se não começa com _
    - Verifica existência de install.json
    - Verifica existência de plugin.py
    ↓
Adiciona nome do diretório à lista
    ↓
Retorna lista de nomes de plugins
```

### Estrutura Mínima de um Plugin

```
plugin_name/
├── install.json    # Obrigatório: Configuração do plugin
└── plugin.py       # Obrigatório: Classe do plugin
```

## 2. Carregamento de Plugins

### 2.1. Carregamento de Configuração

O `PluginLoader.load_plugin_config()` carrega o arquivo `install.json`:

**Estrutura Esperada:**
```json
{
  "name": "device_manager",
  "label": "Device Manager",
  "version": "1.0.0",
  "description": "Descrição do plugin",
  "author": "Autor",
  "dependencies": [],
  "table_prefix": "dvmanage",
  "menu_config_path": "menu_config.json",
  "routes": {
    "api_prefix": "/api/device_manager",
    "web_prefix": null
  }
}
```

**Validação:**
- Arquivo deve ser JSON válido
- Campos obrigatórios: `name`, `version`
- Campos opcionais têm valores padrão

### 2.2. Carregamento da Classe

O `PluginLoader.load_plugin_class()` importa dinamicamente a classe do plugin:

**Processo:**
1. Constrói nome do módulo: `plugins.{plugin_name}.plugin`
2. Adiciona `src/` ao `sys.path` se necessário
3. Importa módulo usando `importlib`
4. Busca classe que herda de `PluginBase`

**Padrões de Nomenclatura Suportados:**
- `Plugin{PluginName}` (ex: `PluginDeviceManager`)
- `Plugin{PluginNameCamelCase}` (ex: `PluginIntegBrewFather`)
- Busca automática por qualquer subclasse de `PluginBase`

**Exemplo de Classe:**
```python
from core.plugin_base import PluginBase

class DeviceManagerPlugin(PluginBase):
    def install(self) -> bool:
        # Lógica de instalação
        return True
    
    def uninstall(self) -> bool:
        # Lógica de desinstalação
        return True
    
    def register_routes(self, app) -> List[Blueprint]:
        # Fallback se descoberta automática falhar
        return []
    
    def register_models(self) -> List:
        # Retorna lista de modelos SQLAlchemy
        from plugins.plugin_device_manager.model.device_metadata import DeviceMetadata
        return [DeviceMetadata]
```

### 2.3. Instanciação

O `PluginLoader.load_plugin()` instancia o plugin:

**Processo:**
1. Carrega configuração via `load_plugin_config()`
2. Valida e aplica valores padrão
3. Carrega classe via `load_plugin_class()`
4. Instancia com `plugin_class(plugin_dir, config)`
5. Cacheia em `loaded_plugins` para evitar recarregamento

**Parâmetros da Instanciação:**
- `plugin_path`: Caminho do diretório do plugin (`Path`)
- `config`: Dicionário com configuração do `install.json`

## 3. Instalação de Plugins

### Processo de Instalação

O `PluginManager.install_plugin()` executa a instalação:

**Fluxo:**
```
install_plugin(plugin_name)
    ↓
Verifica se plugin existe
    ↓
Verifica dependências
    - Para cada dependência em plugin.dependencies
    - Verifica se está em installed_plugins
    - Verifica tanto por nome do diretório quanto por nome do install.json
    ↓
Chama plugin.install()
    ↓
Marca plugin.is_installed = True
    ↓
Adiciona a installed_plugins
    ↓
Salva estado em plugins.json
```

### Verificação de Dependências

**Lógica:**
- Para cada dependência em `plugin.dependencies`:
  - Busca em `installed_plugins` pelo nome do diretório
  - Busca pelo nome do install.json
  - Se não encontrar, falha a instalação

**Exemplo:**
```json
{
  "name": "mash_control",
  "dependencies": ["device_manager"]
}
```

### Método install() do Plugin

Cada plugin implementa sua própria lógica de instalação:

**Responsabilidades Típicas:**
- Criar estrutura de diretórios necessária
- Criar arquivos de configuração padrão
- Registrar modelos no banco (prefixados automaticamente)
- Salvar estado no banco de dados (opcional)

**Exemplo:**
```python
def install(self) -> bool:
    try:
        # Criar estrutura de pastas
        plugin_data_path = self.plugin_path / "data"
        plugin_data_path.mkdir(parents=True, exist_ok=True)
        
        # Registrar modelos
        models = self.register_models()
        if models:
            db.create_all()
        
        # Salvar no banco
        plugin_db = PluginModel.query.filter_by(name=self.name).first()
        if not plugin_db:
            plugin_db = PluginModel(...)
            db.session.add(plugin_db)
        db.session.commit()
        
        return True
    except Exception as e:
        logger.error(f"Erro ao instalar: {e}")
        db.session.rollback()
        return False
```

### Persistência de Estado

Após instalação bem-sucedida, o estado é salvo em `src/plugins/plugins.json`:

```json
{
  "installed_plugins": ["plugin_device_manager", "plugin_mash_control"],
  "active_plugins": [],
  "plugin_configs": {
    "plugin_device_manager": {
      "version": "1.0.0"
    }
  }
}
```

## 4. Ativação de Plugins

### Processo de Ativação

O `PluginManager.activate_plugin()` integra o plugin na aplicação Flask:

**Fluxo:**
```
activate_plugin(plugin_name)
    ↓
Verifica se plugin existe
    ↓
Verifica se está instalado
    ↓
Chama plugin.activate()
    - Marca plugin.is_active = True
    ↓
Chama _register_plugin(plugin)
    ↓
Adiciona a active_plugins
    ↓
Salva estado em plugins.json
```

### Registro na Aplicação (`_register_plugin()`)

Este é o método mais complexo, responsável por integrar o plugin:

#### 4.1. Importação de Modelos Core

**Motivo:** Garantir que modelos base (ex: `User`) estão disponíveis para relacionamentos.

```python
from model.user import User
from db.database import db
with app.app_context():
    _ = User.__table__  # Força registro no metadata
```

#### 4.2. Registro e Prefixação de Modelos

**Processo:**
1. Chama `plugin.register_models()` para obter lista de modelos
2. Aplica prefixos via `plugin_db_helper.prefix_models()`
3. Registra modelos prefixados no `plugin_model_registry`
4. Cria tabelas com `db.create_all()`

**Prefixação:**
- Se `table_prefix` especificado no install.json → usa esse valor
- Se `null` ou não especificado → usa nome do diretório (ex: `plugin_device_manager_`)
- Modifica `__tablename__` e `__table__.name`

**Registro:**
```python
from core.plugin_model_registry import register_prefixed_model
register_prefixed_model(plugin_name, prefixed_model, original_tablename)
```

#### 4.3. Descoberta de Rotas

Usa `PluginInstaller` para descobrir rotas automaticamente:

**Rotas API** (`discover_api_routes()`):
- Procura em `api/routes/`
- Método 1: `__init__.py` que exporta `all_blueprints`
- Método 2: Arquivos `*_routes.py` que exportam blueprints

**Rotas Web** (`discover_web_routes()`):
- Procura `controller/routes.py`
- Prioridade: `web_plugin_bp` ou qualquer blueprint exportado

**Carregamento Dinâmico:**
- Usa `importlib.util` para carregar módulos
- Resolve nomes de módulos baseado no caminho
- Busca atributos que são instâncias de `Blueprint`

#### 4.4. Registro de Blueprints

**Rotas API:**
- Prefixo padrão: `/api/{plugin_name}`
- Configurável via `install.json` → `routes.api_prefix`
- Verifica duplicatas antes de registrar

**Rotas Web:**
- Sem prefixo por padrão
- Configurável via `install.json` → `routes.web_prefix`
- Verifica duplicatas antes de registrar

**Exemplo:**
```python
# API: /api/device_manager/devices
app.register_blueprint(api_bp, url_prefix='/api/device_manager')

# Web: /devices (sem prefixo)
app.register_blueprint(web_bp, url_prefix=None)
```

#### 4.5. Registro de Static Files

Cria blueprint dedicado para servir arquivos estáticos:

```python
static_bp = Blueprint(
    f'plugin_{plugin.name}_static',
    __name__,
    static_folder=str(static_folder),
    static_url_path=f'/plugin/{plugin.name}/static'
)
app.register_blueprint(static_bp)
```

**URL Resultante:** `/plugin/device_manager/static/css/styles.css`

#### 4.6. Atualização do Template Loader

Atualiza o Jinja2 loader para incluir templates do plugin:

```python
plugin_loader = PluginTemplateLoader(plugins_dir, active_plugins)
existing_loader = app.jinja_env.loader
app.jinja_env.loader = ChoiceLoader([plugin_loader, existing_loader])
```

**Ordem de Busca:**
1. Templates dos plugins ativos (por ordem de ativação)
2. Templates do core (`src/templates/`)

## 5. Desativação de Plugins

### Processo de Desativação

O `PluginManager.deactivate_plugin()` remove o plugin da aplicação:

**Fluxo:**
```
deactivate_plugin(plugin_name)
    ↓
Verifica se plugin existe
    ↓
Chama plugin.deactivate()
    - Marca plugin.is_active = False
    ↓
Remove blueprints (via _unregister_plugin_blueprints)
    ↓
Remove de active_plugins
    ↓
Atualiza template loader
    ↓
Salva estado em plugins.json
```

**Nota:** Flask não permite remover blueprints diretamente após registro. A verificação de duplicatas no `_register_plugin()` previne re-registro.

## 6. Desinstalação de Plugins

### Processo de Desinstalação

O `PluginManager.uninstall_plugin()` remove completamente o plugin:

**Fluxo:**
```
uninstall_plugin(plugin_name)
    ↓
Verifica se plugin existe
    ↓
Desativa antes de desinstalar (se ativo)
    ↓
Chama plugin.uninstall()
    ↓
Marca plugin.is_installed = False
    ↓
Remove de installed_plugins
    ↓
Salva estado em plugins.json
```

### Método uninstall() do Plugin

Cada plugin implementa sua própria lógica de desinstalação:

**Responsabilidades Típicas:**
- Remover dados do banco (opcional)
- Limpar arquivos temporários (opcional)
- Atualizar estado no banco de dados

## 7. Sistema de Prefixos de Tabelas

### Configuração

No `install.json`:
```json
{
  "table_prefix": "dvmanage"  // ou null para usar nome do diretório
}
```

### Aplicação

Durante `_register_plugin()`:
1. Obtém modelos via `plugin.register_models()`
2. Aplica prefixo via `prefix_models()`
3. Modifica `__tablename__` e `__table__.name`
4. Registra no `plugin_model_registry`

### Uso nas Rotas

**Problema:** Rotas precisam usar modelos prefixados, mas importação direta não garante isso.

**Solução:** Usar `model_loader` do plugin:

```python
# utils/model_loader.py
from core.plugin_model_registry import get_prefixed_model

def get_device_metadata():
    return get_prefixed_model('plugin_device_manager', 'DeviceMetadata')

# api/routes/device_routes.py
from plugins.plugin_device_manager.utils.model_loader import get_device_metadata

DeviceMetadata = get_device_metadata()
```

## 8. Sistema de Menu

### Configuração

**Opção 1:** Arquivo separado (`menu_config.json`):
```json
{
  "main_items": [
    {
      "id": "devices",
      "label": "Dispositivos",
      "icon": "bi bi-device-hdd",
      "url": "device_manager.devices",
      "children": []
    }
  ]
}
```

**Opção 2:** Inline no `install.json`:
```json
{
  "menu": {
    "main_items": [...]
  }
}
```

### Carregamento

Via `plugin.get_menu_config()`:
- Se `menu_config_path` especificado → carrega arquivo
- Caso contrário → usa `menu` inline do install.json

### Injeção no Template

Via context processor `inject_plugin_menu()`:
- Carrega menu de todos os plugins ativos
- Estrutura hierárquica: Plugin → Itens → Sub-itens
- Injeta `plugin_menu_items` e `safe_url_for` no contexto

## 9. Tratamento de Erros

### Durante Descoberta
- Diretório não existe → retorna lista vazia
- `install.json` inválido → loga erro, ignora plugin
- `plugin.py` não encontrado → loga erro, ignora plugin

### Durante Carregamento
- Classe não encontrada → retorna `None`
- Erro na instanciação → loga exceção, retorna `None`

### Durante Instalação
- Dependência não instalada → falha, retorna `False`
- Erro em `install()` → loga exceção, retorna `False`

### Durante Ativação
- Plugin não instalado → falha, retorna `False`
- Erro em `_register_plugin()` → loga exceção, continua (plugin marcado como ativo)

## 10. Boas Práticas

1. **Sempre use model_loader** nas rotas API que acessam modelos
2. **Configure table_prefix** para evitar conflitos de nomes
3. **Documente dependências** no `install.json`
4. **Use nomes únicos** para blueprints (ex: `plugin_meu_plugin_api`)
5. **Teste instalação/ativação** antes de distribuir
6. **Trate erros graciosamente** nos métodos `install()` e `uninstall()`
7. **Use logging** para debug e troubleshooting

## 11. Exemplo Completo

### Estrutura do Plugin

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

### install.json

```json
{
  "name": "exemplo",
  "label": "Plugin Exemplo",
  "version": "1.0.0",
  "description": "Plugin de exemplo",
  "author": "Autor",
  "dependencies": [],
  "table_prefix": "exemplo_",
  "menu_config_path": "menu_config.json",
  "routes": {
    "api_prefix": "/api/exemplo",
    "web_prefix": null
  }
}
```

### plugin.py

```python
from core.plugin_base import PluginBase
from typing import List

class ExemploPlugin(PluginBase):
    def install(self) -> bool:
        # Lógica de instalação
        return True
    
    def uninstall(self) -> bool:
        # Lógica de desinstalação
        return True
    
    def register_routes(self, app) -> List:
        return []
    
    def register_models(self) -> List:
        from plugins.plugin_exemplo.model.exemplo import ExemploModel
        return [ExemploModel]
```

### Fluxo Completo

1. **Descoberta**: Sistema encontra `plugin_exemplo/`
2. **Carregamento**: Carrega `install.json` e `plugin.py`, instancia `ExemploPlugin`
3. **Instalação**: Executa `install()`, salva estado
4. **Ativação**: 
   - Prefixa modelos → `exemplo_exemplo_model`
   - Descobre rotas em `api/routes/` e `controller/routes.py`
   - Registra blueprints com prefixos apropriados
   - Registra static files
   - Atualiza template loader
5. **Uso**: Rotas acessíveis, templates carregáveis, modelos prefixados disponíveis
