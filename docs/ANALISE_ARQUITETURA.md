# Análise da Arquitetura do Sistema BrewStation

## Visão Geral

O BrewStation é uma aplicação Flask modular para controle de brassagens artesanais, projetada com arquitetura extensível baseada em plugins. O sistema permite adicionar funcionalidades dinamicamente sem modificar o código core, facilitando manutenção e expansão.

## Componentes Principais

### 1. Application Factory (`src/main.py`)

O ponto de entrada da aplicação utiliza o padrão Application Factory do Flask, permitindo criação flexível de instâncias da aplicação.

#### Responsabilidades:

- **Criação da Aplicação Flask**: Configuração inicial com `Flask(__name__)`
- **Configuração de Ambiente**: Carregamento de variáveis de ambiente via `dotenv`
- **Inicialização de Extensões**:
  - `LoginManager`: Gerenciamento de autenticação de usuários
  - `CORS`: Suporte a requisições cross-origin
- **Inicialização do Banco de Dados**: Chamada a `init_db(app)` para configurar SQLAlchemy
- **Inicialização do Sistema de Plugins**: Criação e configuração do `PluginManager`
- **Registro de Blueprints Core**: Apenas funcionalidades essenciais (auth, web básico, registro, notificações)
- **Registro de Context Processors**: Injeção de dados globais nos templates
- **Registro de Comandos CLI**: Comandos personalizados para administração

#### Fluxo de Inicialização:

```python
create_app()
  ↓
Configuração Flask
  ↓
init_db() → Configuração SQLAlchemy
  ↓
PluginManager() → Descoberta e carregamento de plugins
  ↓
Garantir plugin core instalado e ativo
  ↓
Registrar blueprints core
  ↓
Registrar context processors
  ↓
Registrar comandos CLI
```

### 2. Sistema de Plugins (`src/core/`)

O sistema de plugins é o coração da arquitetura extensível, composto por vários módulos especializados:

#### 2.1. PluginBase (`plugin_base.py`)

Classe abstrata base que define a interface que todos os plugins devem implementar.

**Propriedades Principais:**
- `plugin_path`: Caminho do diretório do plugin
- `config`: Configuração carregada do `install.json`
- `name`: Nome do plugin (do install.json)
- `label`: Label para exibição (prioridade sobre name)
- `version`: Versão do plugin
- `description`: Descrição do plugin
- `author`: Autor do plugin
- `dependencies`: Lista de dependências
- `table_prefix`: Prefixo para nomes de tabelas (opcional)
- `is_active`: Estado de ativação
- `is_installed`: Estado de instalação

**Métodos Abstratos:**
- `install()`: Lógica de instalação do plugin
- `uninstall()`: Lógica de desinstalação
- `register_routes()`: Registro de blueprints (usado como fallback)
- `register_models()`: Retorna lista de modelos SQLAlchemy do plugin

**Métodos Concretos:**
- `activate()` / `deactivate()`: Controle de estado básico
- `get_menu_config()`: Carrega configuração de menu (menu_config.json ou inline)
- `get_static_folder()` / `get_templates_folder()`: Helpers para caminhos

#### 2.2. PluginLoader (`plugin_loader.py`)

Responsável pela descoberta e carregamento dinâmico de plugins.

**Funcionalidades:**

1. **Descoberta de Plugins** (`discover_plugins()`):
   - Escaneia `src/plugins/` procurando diretórios
   - Valida presença de `install.json` e `plugin.py`
   - Ignora diretórios iniciados com `_`

2. **Carregamento de Configuração** (`load_plugin_config()`):
   - Lê e valida `install.json`
   - Retorna dicionário com configuração

3. **Carregamento de Classe** (`load_plugin_class()`):
   - Importa dinamicamente o módulo `plugins.{nome}.plugin`
   - Busca classe que herda de `PluginBase`
   - Suporta múltiplos padrões de nomenclatura:
     - `Plugin{PluginName}` (ex: `PluginDeviceManager`)
     - `Plugin{PluginNameCamelCase}` (ex: `PluginIntegBrewFather`)
     - Busca automática por subclasse de `PluginBase`

4. **Instanciação** (`load_plugin()`):
   - Carrega configuração e classe
   - Instancia plugin com `plugin_path` e `config`
   - Cacheia instâncias em `loaded_plugins`

#### 2.3. PluginManager (`plugin_manager.py`)

Gerenciador central que coordena o ciclo de vida completo dos plugins.

**Estados do Plugin:**
1. **Descoberto**: Plugin encontrado no diretório
2. **Instalado**: Método `install()` executado, estado salvo em `plugins.json`
3. **Ativo**: Método `activate()` executado, rotas/templates registrados
4. **Desativado**: Rotas removidas, templates não carregados
5. **Desinstalado**: Método `uninstall()` executado, dados removidos

**Persistência de Estado:**

O estado é persistido em `src/plugins/plugins.json`:
```json
{
  "installed_plugins": ["plugin_name1", "plugin_name2"],
  "active_plugins": ["plugin_name1"],
  "plugin_configs": {
    "plugin_name1": {"version": "1.0.0"}
  }
}
```

**Métodos Principais:**

- `install_plugin()`: Verifica dependências, chama `plugin.install()`, salva estado
- `uninstall_plugin()`: Desativa antes de desinstalar, chama `plugin.uninstall()`
- `activate_plugin()`: Chama `plugin.activate()`, registra na aplicação via `_register_plugin()`
- `deactivate_plugin()`: Chama `plugin.deactivate()`, remove blueprints, atualiza template loader
- `_register_plugin()`: **Método crítico** que integra plugin na aplicação Flask

**Processo de Registro (`_register_plugin()`):**

1. **Importação de Modelos Core**: Garante que modelos base (ex: `User`) estão disponíveis para relacionamentos
2. **Registro e Prefixação de Modelos**:
   - Chama `plugin.register_models()`
   - Aplica prefixos via `plugin_db_helper.prefix_models()`
   - Registra modelos prefixados no `plugin_model_registry`
   - Cria tabelas com `db.create_all()`
3. **Descoberta de Rotas**:
   - Usa `PluginInstaller` para descobrir rotas automaticamente
   - Rotas API: `api/routes/`
   - Rotas Web: `controller/routes.py`
4. **Registro de Blueprints**:
   - API: Prefixo `/api/{plugin_name}` (configurável)
   - Web: Sem prefixo por padrão (configurável)
   - Verifica duplicatas antes de registrar
5. **Registro de Static Files**:
   - Cria blueprint para servir arquivos estáticos
   - URL: `/plugin/{plugin_name}/static`
6. **Atualização do Template Loader**:
   - Adiciona templates do plugin ao Jinja2

#### 2.4. PluginInstaller (`plugin_installer.py`)

Sistema de instalação automática que descobre e registra componentes do plugin.

**Descoberta de Rotas API** (`discover_api_routes()`):
- Procura em `api/routes/`
- Método 1: `__init__.py` que exporta `all_blueprints`
- Método 2: Arquivos `*_routes.py` que exportam blueprints

**Descoberta de Rotas Web** (`discover_web_routes()`):
- Procura `controller/routes.py`
- Prioridade: `web_plugin_bp` ou qualquer blueprint exportado

**Carregamento Dinâmico** (`_load_blueprints_from_module()`):
- Usa `importlib.util` para carregar módulos dinamicamente
- Resolve nomes de módulos baseado no caminho
- Busca atributos que são instâncias de `Blueprint`

#### 2.5. PluginTemplateLoader (`template_loader.py`)

Loader customizado Jinja2 que permite override de templates.

**Ordem de Busca:**
1. Templates dos plugins ativos (por ordem de ativação)
2. Templates do core (`src/templates/`)

**Integração:**
- Usa `ChoiceLoader` do Jinja2 para combinar múltiplos loaders
- Permite que plugins sobrescrevam templates core

#### 2.6. PluginDBHelper (`plugin_db_helper.py`)

Sistema de prefixação de tabelas para isolamento de dados.

**Funcionamento:**

1. **Configuração** (`install.json`):
   - Campo `table_prefix` (opcional)
   - `null` ou não especificado → usa nome do diretório (ex: `plugin_meu_plugin_`)
   - Especificado → usa valor fornecido (ex: `"estoque_"`)

2. **Aplicação de Prefixo** (`prefix_table_name()`):
   - Modifica `__tablename__` da classe
   - Atualiza `__table__.name` se já foi criado
   - Evita duplicação de prefixos

3. **Registro** (`prefix_models()`):
   - Aplica prefixo a lista de modelos
   - Registra no `plugin_model_registry` para acesso posterior

**Exemplo:**
```python
# Modelo original
class DeviceMetadata(db.Model):
    __tablename__ = 'device_metadata'

# Após prefixação (prefixo: "dvmanage_")
class DeviceMetadata(db.Model):
    __tablename__ = 'dvmanage_device_metadata'
```

#### 2.7. PluginModelRegistry (`plugin_model_registry.py`)

Registry global para modelos prefixados, garantindo acesso correto nas rotas.

**Funcionalidades:**
- `register_prefixed_model()`: Registra modelo prefixado por plugin
- `get_prefixed_model()`: Obtém modelo prefixado do registry
- `get_all_prefixed_models()`: Lista todos os modelos de um plugin

**Uso nas Rotas:**
```python
# utils/model_loader.py no plugin
from core.plugin_model_registry import get_prefixed_model

def get_device_metadata():
    return get_prefixed_model('plugin_device_manager', 'DeviceMetadata')
```

### 3. Estrutura de Diretórios

```
BrewStation/
├── src/
│   ├── main.py                 # Application Factory
│   ├── core/                    # Sistema de plugins
│   │   ├── plugin_base.py
│   │   ├── plugin_loader.py
│   │   ├── plugin_manager.py
│   │   ├── plugin_installer.py
│   │   ├── template_loader.py
│   │   ├── plugin_db_helper.py
│   │   └── plugin_model_registry.py
│   ├── plugins/                  # Plugins instalados
│   │   ├── plugins.json         # Estado dos plugins
│   │   └── {plugin_name}/
│   │       ├── plugin.py        # Classe do plugin
│   │       ├── install.json     # Configuração
│   │       ├── menu_config.json # Menu (opcional)
│   │       ├── api/
│   │       │   └── routes/      # Rotas API
│   │       ├── controller/
│   │       │   └── routes.py    # Rotas Web
│   │       ├── templates/       # Templates HTML
│   │       ├── static/          # CSS, JS, imagens
│   │       ├── model/           # Modelos SQLAlchemy
│   │       └── utils/           # Utilitários
│   ├── templates/               # Templates core
│   ├── static/                 # Arquivos estáticos core
│   ├── model/                  # Modelos core
│   ├── controller/             # Controllers core
│   └── api/                    # APIs core
```

## Padrões de Design Utilizados

### 1. Application Factory Pattern
Permite criação flexível de instâncias Flask, facilitando testes e configuração.

### 2. Plugin Pattern
Sistema extensível onde funcionalidades são adicionadas como plugins independentes.

### 3. Registry Pattern
`PluginModelRegistry` mantém registro centralizado de modelos prefixados.

### 4. Template Method Pattern
`PluginBase` define estrutura, plugins implementam detalhes específicos.

### 5. Strategy Pattern
`PluginInstaller` usa diferentes estratégias para descobrir rotas.

## Fluxo de Requisição Completo

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
```

## Integrações Flask

### Blueprints
- Cada plugin registra seus próprios blueprints
- Verificação de duplicatas antes do registro
- Registro no `route_registry` para navegação

### Context Processors
- `inject_notifications_count()`: Contador de notificações não lidas
- `inject_plugin_menu()`: Menu de navegação dos plugins ativos

### CLI Commands
- `flask plugin list`: Lista plugins
- `flask plugin install <name>`: Instala plugin
- `flask plugin activate <name>`: Ativa plugin
- `flask recreate-plugin-tables`: Recria tabelas com prefixos
- `flask migrate-brewfather-tables`: Migra dados entre tabelas

## Segurança e Isolamento

- **Isolamento por Diretório**: Cada plugin em seu próprio diretório
- **Prefixos de Tabela**: Evitam conflitos de nomes no banco
- **Verificação de Dependências**: Antes da instalação
- **Autenticação Uniforme**: Flask-Login aplicado consistentemente
- **Validação de Configuração**: Antes do carregamento

## Pontos Fortes da Arquitetura

1. **Modularidade**: Separação clara entre core e plugins
2. **Extensibilidade**: Fácil adicionar novas funcionalidades
3. **Manutenibilidade**: Código organizado e bem estruturado
4. **Isolamento**: Plugins não interferem entre si
5. **Flexibilidade**: Sistema de prefixos e configuração extensível

## Considerações de Design

1. **Nomes de Plugins**: Sistema suporta nome do diretório e nome do install.json
2. **Ordem de Ativação**: Importante para templates (primeiro ativado tem prioridade)
3. **Dependências**: Verificadas antes da instalação, mas não há resolução automática
4. **Estado Persistente**: plugins.json mantém estado entre reinicializações
5. **Hot Reload**: Não suportado - requer reinicialização para mudanças
