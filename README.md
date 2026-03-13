
![Logo do BrewStation](src/static/img/nova_logo.png)

# BrewStation 🍺

Plataforma web modular para controle de brassagens artesanais, classificação de ingredientes, precificação, estoque e relatórios – construída com Flask, SQLAlchemy e integração nativa com o BrewFather.

## Índice

- [Visão Geral](#visão-geral)
- [Funcionalidades Principais](#funcionalidades-principais)
- [Instalação Rápida](#instalação-rápida)
- [Guia Debian](instalacao_debian.md)  
- [Documentação Completa](#documentação-completa)
- [Variáveis de Ambiente Essenciais](#variáveis-de-ambiente-essenciais)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Integração com o BrewFather](#integração-com-o-brewfather)
- [Sistema de Plugins](#sistema-de-plugins)

## Visão Geral

- **Público-alvo**: cervejarias artesanais, laboratórios de testes e homebrewers avançados.
- **Pilares**: catálogo de insumos, cálculo de custos, sincronização BrewFather, rastreabilidade de envase, notificações e painéis operacionais.
- **Stack**: Python 3.11+, Flask 3, SQLAlchemy 2, SQLite/PostgreSQL (Neon), Flask-Login, Flask-Mail, Pandas/OpenPyXL para importação/exportação.
- **Arquitetura**: Sistema modular com plugins extensíveis para adicionar funcionalidades dinamicamente.

## Funcionalidades Principais

### Catálogo e precificação
- CRUD completo de maltes, lúpulos e leveduras, com importação via planilhas-modelo (`/upload/modelo/<tipo>`).
- Criação de receitas locais ou a partir de sincronizações BrewFather.
- Motor de cálculo configurável (margens, impostos, custo de envase, sanitização, taxa de cartão).
- Relatórios consolidados com preço sugerido, custo por litro e margens previstas.

### Estoque, envase e custos
- Movimentações (entrada/saída/ajuste) com custo médio e alerta por estoque mínimo.
- Módulo de envase vinculado a lotes do BrewFather, incluindo embalagens, SKUs e quantidades produzidas.
- Cálculo de custo de produção (ingredientes + embalagens + operacionais) e sugestão de preço final.

### Operação e monitoramento
- Dashboard com indicadores de produção, notificações e status das integrações.
- Sistema de notificações com filtros (todas/lidas/não lidas/lixeira) e ações rápidas.
- Perfil de usuário completo (dados pessoais, redes sociais, preferências de alertas, troca de senha).

### Integrações
- **BrewFather**: sincronização de receitas, lotes e inventário, com cadastro automático dos insumos faltantes.
- **E-mail (SMTP)**: envio de notificações administrativas e workflow de solicitações de acesso.
- **Uploads/Relatórios**: importação e exportação em Excel com ajustes automáticos de layout.

### Sistema de Plugins
- Arquitetura modular extensível
- Gerador de plugins template (`python run.py plugin -c`)
- Instalação e ativação dinâmica de plugins
- Menu de navegação hierárquico configurável por plugin
- Configuração de menu separada em `menu_config.json`
- Templates e rotas isolados por plugin
- Suporte a múltiplos níveis de submenu
- CLI completo para gerenciamento de plugins

## Instalação Rápida

```bash
git clone <url>
cd BrewStation
python -m venv vEnvStation
.\vEnvStation\Scripts\activate   # Windows
source vEnvStation/bin/activate  # Linux/Mac
pip install -r requirements.txt
copy src\config.env.modelo src\.env   # Windows
cp src/config.env.modelo src/.env     # Linux/Mac
cd src
python main.py
```

Acesse `http://localhost:5000` com `admin / 123` (troque a senha no primeiro login via `Perfil > Segurança`).

Para instalação detalhada, veja a documentação oficial abaixo ou o guia específico para Debian em [instalacao_debian.md](instalacao_debian.md).

## Documentação Completa

Bem-vindo à documentação oficial consolidada v2.0 do **BrewStation**.
Atualmente o BrewStation opera como uma **Estação de Trabalho Inteligente**, não sendo um simples software monolítico. Sua missão central é atuar como plataforma web modular (um Hub) que roteia fluxos, armazena configurações persistentes e suporta a instalação e ativação dinâmica de plugins independentes (como Mash Control, Device Manager e Yeast Bank).

### 📖 Manuais e Uso Geral
- [**Apresentação e Requisitos**](docs/01_apresentacao_requisitos.md) - Propósito do projeto, requisitos mínimos e processos gerais da Estação.
- [**Backlog Geral**](docs/02_backlog_geral.md) - Nossas próximas entregas e roadmap consolidado.

### 🏗️ Arquitetura e Integração Core
- [**A Arquitetura do Core (Hub de Integração)**](docs/03_core_architecture.md) - Como a Plataforma em si funciona sem nenhum plugin, estrutura das classes principais e onde a plataforma entra (Autenticação, Sessões e Bootstrap DB).

### 🔌 Ecossistema de Plugins
- [**O Sistema de Plugins (Ciclo de Vida)**](docs/04_plugin_system.md) - Entendendo a `PluginManager`, como plugins são descobertos, instalados e inicializados. Inclui regras de Auto-Prefixing do SQLAlchemy.
- [**Gerenciamento de Menus e Views**](docs/05_plugin_views.md) - Como a árvore de `menu_config.json` constrói o UI da plataforma em tempo de execução e a precedência do `TemplateLoader`.

### 🛠️ Criação e Integração
- [**O Gerador "Maker" e Estrutura dos Plugins**](docs/06_plugin_maker.md) - Entendendo a anatomia formal (MVC) exigida de um plugin e como utilizar o Maker para scaffolding de novos módulos em minutos.
- [**Comunicação Cíclica (Dependências Inter-Plugin)**](docs/07_plugin_integration.md) - Entendendo a resolução de conflitos e injeção de dependência de plugins maduros.
- [**📖 Manual do Usuário: Plugin Maker**](docs/08_maker_manual_usuario.md) - Manual completo de como operar a fábrica de extensões e usufruir da arquitetura de segurança (Guarded Blocks).

---
## 🗺️ Mapa Macro da Arquitetura BrewStation

```mermaid
flowchart TD
    User([Usuário Final]) <--> WebInterface[Painel Dashboard V2]
    Hardware([Dispositivos IoT]) <--> Dmgr[Plugin Device Manager]
    
    subgraph CorePlatform [BrewStation Core (A Plataforma)]
        direction TB
        MainApp(Application Factory)
        DB[(DB SQLite / PostgreSQL)]
        Auth[Autenticação & Sessões]
        PM[Plugin Manager Orquestrador]
    end

    subgraph PluginsEcossystem [Ecossistema de Plugins]
        direction LR
        P1[Plugin Integrador BrewFather]
        P2[Plugin Mash Control]
        P3[Plugin Yeast Bank]
        Dmgr
    end

    WebInterface --> MainApp
    MainApp <--> DB
    MainApp <--> Auth
    MainApp --> PM
    
    PM -->|Discovery & Load| PluginsEcossystem
    P1 .->|Consome DB via Core| CorePlatform
    P2 .->|Depende via interface| Dmgr
```

## Variáveis de Ambiente Essenciais

| Chave | Descrição |
|-------|-----------|
| `SECRET_KEY` | Chave Flask para sessões |
| `FLASK_ENV` | `DEV` (SQLite local) ou `PRD` (PostgreSQL/Neon) |
| `DATABASE_URL` ou `NEON_*` | Parâmetros de banco em produção |
| `BREWFATHER_USER_ID` / `BREWFATHER_API_KEY` | Credenciais API BrewFather |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS` | SMTP |
| `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH` | Controle de uploads |

Veja a documentação oficial para detalhes completos sobre configuração do sistema.

## Estrutura de Pastas

```
BrewStation/
├── src/
│   ├── api/              # Rotas REST API
│   ├── controller/       # Rotas web (server-side render)
│   ├── core/             # Sistema de plugins
│   ├── db/               # Configuração SQLite/PostgreSQL
│   ├── model/            # Modelos SQLAlchemy
│   ├── plugins/          # Plugins do sistema
│   ├── services/         # Serviços de negócio
│   ├── templates/        # Templates HTML core
│   ├── static/           # CSS, JS, vendors, uploads
│   ├── utils/            # Utilitários
│   └── main.py           # Application factory
├── docs/                 # Documentação completa
└── requirements.txt      # Dependências Python
```

## Integração com o BrewFather

1. Configure `BREWFATHER_USER_ID` e `BREWFATHER_API_KEY` em `Configurações`.
2. Use as rotas `/api/brewfather/sync/*` para sincronizar receitas, lotes, inventário ou tudo de uma vez.
3. Cadastre automaticamente os ingredientes faltantes por receita (`/api/brewfather/recipe/<id>/cadastrar-insumos`).
4. Gere relatórios filtrados por lote, status ou intervalo de datas e exporte para Excel com métricas de OG, FG, ABV, IBU e eficiência.

## Sistema de Plugins

O BrewStation possui um sistema modular de plugins que permite:

- ✅ Adicionar funcionalidades sem modificar o core
- ✅ Instalar/desinstalar plugins dinamicamente
- ✅ Configurar menu de navegação via JSON
- ✅ Isolar rotas, templates e modelos por plugin
- ✅ Prefixos automáticos para tabelas de banco de dados
- ✅ Sistema de model_loader para garantir modelos prefixados corretos

### Plugins Disponíveis

#### Device Manager

Sistema completo de gerenciamento de dispositivos IoT com servidor MQTT embutido.

**Funcionalidades:**
- Gerenciamento de dispositivos IoT (sensores, atuadores, gateways)
- Servidor MQTT embutido rodando em thread separada
- Monitoramento de mensagens MQTT em tempo real
- API pública para outros plugins

#### Mash Control

Sistema completo de automação de processos de brassagem com dashboard visual interativo.

**Funcionalidades:**
- Dashboard visual com representação SVG do brewhouse
- Controle automático e manual de processos de brassagem
- Editor visual de receitas (profiles)
- Sistema de logging e histórico de sessões
- Integração bidirecional em tempo real com dispositivos via Device Manager
- Importação de receitas do BrewFather

### Comandos CLI de Plugins

```bash
# Listar plugins
flask plugin list

# Instalar plugin
flask plugin install <nome>

# Ativar plugin
flask plugin activate <nome>

# Informações do plugin
flask plugin info <nome>
```

### Comandos CLI de Diagnóstico e Migração

```bash
# Diagnosticar tabelas de plugins
flask diagnose-brewfather-tables

# Recriar tabelas de plugins com prefixos corretos
flask recreate-plugin-tables

# Migrar dados entre tabelas (sem prefixo → com prefixo)
flask migrate-brewfather-tables
```

Veja a documentação atualizada do [Sistema de Plugins](docs/04_plugin_system.md) para mais informações sobre manipulação estrita via CLI.

## Observabilidade e Logs

- Estrutura sugerida: `logs/application.log`, `logs/errors.log`, `logs/devices.log`, `logs/brew_sessions.log`.
- A aplicação imprime no console os principais eventos (registro de blueprints, criação de admin, testes de conexão).
- Use `flask test-db` para validar rapidamente a camada de dados após implantações.

## Roadmap

- ✅ Catálogo completo de ingredientes e cálculo de preço.
- ✅ Integração BrewFather com cadastro automático de insumos.
- ✅ Relatórios exportáveis (BrewFather, ingredientes, estoque).
- ✅ Sistema de plugins modular.
- ✅ Gerenciamento de dispositivos IoT com MQTT (Device Manager).
- ✅ Automação de processos de brassagem (Mash Control).
- 🔜 Fluxo de aprovação/rejeição das solicitações de acesso.
- 🔜 Alertas automáticos (e-mail/Push) para estoque crítico e falhas de sincronização.
- 🔜 Interface de gerenciamento de plugins via web.

## Contribuindo

Contribuições são bem-vindas!
Veja nossa [Documentação Completa](#documentação-completa)

## Suporte

- 📖 Consulte nossa **[Documentação Completa](#documentação-completa)**
- 🐛 Reporte bugs abrindo uma issue

---

**BrewStation** — do grão ao copo, com operação rastreável e precificação sob controle. 🍻⚙️
