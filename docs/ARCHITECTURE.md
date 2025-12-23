# Arquitetura do BrewStation

Este documento descreve a arquitetura técnica do BrewStation, incluindo estrutura de diretórios, componentes principais e fluxos de dados.

## Visão Geral

O BrewStation é uma aplicação web modular construída com Flask, seguindo o padrão de arquitetura MVC (Model-View-Controller) com sistema de plugins extensível.

## Stack Tecnológica

### Backend
- **Flask 3.x**: Framework web Python
- **SQLAlchemy 2.x**: ORM para acesso a banco de dados
- **Flask-Login**: Gerenciamento de sessões e autenticação
- **Flask-Mail**: Envio de e-mails
- **Flask-CORS**: Suporte a CORS para APIs

### Frontend
- **Jinja2**: Engine de templates
- **Bootstrap 5**: Framework CSS
- **Bootstrap Icons**: Ícones
- **ApexCharts / ECharts**: Gráficos e visualizações
- **jQuery**: Manipulação DOM e AJAX

### Banco de Dados
- **SQLite**: Desenvolvimento e testes
- **PostgreSQL**: Produção (suporte a Neon)

### Utilitários
- **pandas**: Processamento de dados
- **openpyxl**: Manipulação de planilhas Excel
- **python-dotenv**: Gerenciamento de variáveis de ambiente

## Estrutura de Diretórios

```
BrewStation/
├── src/                          # Código-fonte principal
│   ├── api/                      # Rotas REST API
│   │   └── routes/              # Blueprints de API
│   ├── controller/               # Rotas web (server-side render)
│   │   ├── auth.py              # Autenticação
│   │   └── web.py               # Rotas web core
│   ├── core/                     # Sistema de plugins
│   │   ├── plugin_base.py       # Classe base de plugins
│   │   ├── plugin_loader.py     # Carregador de plugins
│   │   ├── plugin_manager.py    # Gerenciador de plugins
│   │   ├── plugin_installer.py  # Instalador automático
│   │   └── template_loader.py   # Loader de templates de plugins
│   ├── db/                       # Configuração de banco
│   │   ├── database.py          # Factory de conexão
│   │   ├── dev_database.py      # SQLite (dev)
│   │   └── prd_database.py      # PostgreSQL (prod)
│   ├── model/                    # Modelos SQLAlchemy
│   │   ├── user.py              # Usuários
│   │   ├── ingredientes.py      # Ingredientes
│   │   ├── estoque.py           # Estoque
│   │   ├── brewfather.py        # Integração BrewFather
│   │   └── ...
│   ├── plugins/                  # Plugins do sistema
│   │   ├── plugin_integ_bFather/ # Plugin core
│   │   └── plugins.json         # Configuração de plugins
│   ├── services/                 # Serviços de negócio
│   ├── templates/               # Templates HTML core
│   ├── static/                  # Arquivos estáticos
│   ├── utils/                   # Utilitários
│   ├── logs/                    # Configuração de logs
│   └── main.py                  # Application factory
├── docs/                         # Documentação
├── setup/                        # Scripts de deploy
└── requirements.txt              # Dependências Python
```

## Componentes Principais

### 1. Application Factory (`main.py`)

O ponto de entrada da aplicação usa o padrão Application Factory do Flask:

```python
def create_app():
    app = Flask(__name__)
    # Configurações
    # Inicialização de extensões
    # Registro de blueprints
    # Sistema de plugins
    return app
```

**Responsabilidades:**
- Configuração da aplicação
- Inicialização de extensões (LoginManager, CORS, etc.)
- Registro de blueprints core
- Inicialização do sistema de plugins
- Configuração de context processors

### 2. Sistema de Plugins

O BrewStation possui um sistema modular de plugins que permite adicionar funcionalidades dinamicamente.

#### Componentes do Sistema de Plugins

**PluginBase** (`core/plugin_base.py`):
- Classe abstrata base para todos os plugins
- Define interface comum (install, uninstall, activate, deactivate)
- Gerencia configuração e estado do plugin

**PluginLoader** (`core/plugin_loader.py`):
- Descobre plugins no diretório `src/plugins/`
- Carrega classes de plugins dinamicamente
- Valida estrutura de plugins

**PluginManager** (`core/plugin_manager.py`):
- Gerencia ciclo de vida dos plugins
- Registra rotas, templates e modelos
- Mantém estado de plugins instalados/ativos

**PluginInstaller** (`core/plugin_installer.py`):
- Instalação automática de plugins
- Descoberta de rotas API e web
- Registro de templates e static files

**PluginTemplateLoader** (`core/template_loader.py`):
- Loader customizado Jinja2
- Busca templates em plugins ativos
- Fallback para templates core

### 3. Camada de Modelos (`model/`)

Modelos SQLAlchemy representam entidades do domínio:

- **User**: Usuários e autenticação
- **Ingredientes**: Maltes, Lúpulos, Leveduras
- **Receita**: Receitas de cerveja
- **Estoque**: Movimentações e estoque atual
- **BrewFather**: Dados sincronizados do BrewFather
- **Notification**: Sistema de notificações
- **Config**: Configurações do sistema

### 4. Camada de Rotas

#### Rotas API (`api/routes/`)

Blueprints REST para operações CRUD e integrações:

- `ingredientes_routes.py`: CRUD de ingredientes
- `receitas_routes.py`: Gerenciamento de receitas
- `estoque_routes.py`: Movimentações de estoque
- `brewfather_routes.py`: Integração BrewFather
- `calculos_routes.py`: Cálculos de precificação
- `upload_routes.py`: Importação/exportação

**Padrão de URL:** `/api/<recurso>`

#### Rotas Web (`controller/`)

Rotas para renderização de páginas HTML:

- `auth.py`: Login, registro, perfil
- `web.py`: Dashboard, configurações

**Padrão de URL:** `/<página>`

### 5. Camada de Persistência (`db/`)

Abstração de banco de dados:

- **database.py**: Factory de conexão
- **dev_database.py**: Configuração SQLite
- **prd_database.py**: Configuração PostgreSQL/Neon

Suporta migração automática de modelos de plugins.

## Fluxos Principais

### 1. Fluxo de Autenticação

```
Usuário → /login → auth.login()
    ↓
Verificar credenciais → User.query.filter_by()
    ↓
Flask-Login → login_user()
    ↓
Redirect → /dashboard
```

### 2. Fluxo de Requisição API

```
Cliente → /api/ingredientes → ingredientes_bp.get_maltes()
    ↓
Validar autenticação (@login_required)
    ↓
Query → Malte.query.filter_by()
    ↓
Serializar → jsonify([malte.to_dict()])
    ↓
Response JSON
```

### 3. Fluxo de Renderização de Página

```
Usuário → /maltes → web_plugin_bp.maltes()
    ↓
Renderizar template → render_template("maltes.html")
    ↓
PluginTemplateLoader → Buscar em plugins/templates/
    ↓
Jinja2 → Processar template
    ↓
HTML → Response
```

### 4. Fluxo de Instalação de Plugin

```
Sistema → Descobrir plugins → PluginLoader.discover_plugins()
    ↓
Carregar plugin → PluginLoader.load_plugin()
    ↓
Instalar → plugin.install()
    ↓
Registrar rotas → PluginInstaller.discover_api_routes()
    ↓
Registrar templates → PluginTemplateLoader
    ↓
Ativar → plugin.activate()
    ↓
Salvar estado → plugins.json
```

## Padrões de Design

### 1. Application Factory

Permite criar múltiplas instâncias da aplicação para testes e diferentes ambientes.

### 2. Blueprint Pattern

Organiza rotas em módulos reutilizáveis e independentes.

### 3. Plugin Architecture

Sistema extensível que permite adicionar funcionalidades sem modificar o core.

### 4. Repository Pattern (implícito)

Modelos SQLAlchemy encapsulam acesso a dados.

### 5. Service Layer

Serviços em `services/` contêm lógica de negócio complexa.

## Segurança

### Autenticação
- Flask-Login para gerenciamento de sessões
- Hash de senhas com Werkzeug
- Proteção CSRF (via Flask-WTF, se configurado)

### Autorização
- Decorator `@login_required` para rotas protegidas
- Verificação de permissões de admin

### Validação
- Validação de entrada em rotas API
- Sanitização de dados antes de persistir

## Performance

### Otimizações
- Lazy loading de plugins
- Cache de templates Jinja2
- Queries otimizadas com SQLAlchemy
- Static files servidos diretamente pelo servidor web

### Escalabilidade
- Arquitetura stateless (sessões em cookies)
- Suporte a múltiplos workers (Gunicorn)
- Banco de dados pode ser escalado independentemente

## Extensibilidade

O sistema é extensível através de:

1. **Plugins**: Adicionar funcionalidades completas
2. **Blueprints**: Adicionar rotas API/web
3. **Templates**: Customizar interface
4. **Modelos**: Adicionar entidades ao banco
5. **Serviços**: Adicionar lógica de negócio

## Próximos Passos

- [Arquitetura de Plugins](PLUGIN_SYSTEM.md)
- [Guia de Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)
- [Referência da API](API_REFERENCE.md)

