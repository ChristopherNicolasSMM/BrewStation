# BrewStation - Documentação v2.0

Bem-vindo à documentação oficial consolidada v2.0 do **BrewStation**.
Atualmente o BrewStation opera como uma **Estação de Trabalho Inteligente**, não sendo um simples software monolítico. Sua missão central é atuar como plataforma web modular (um Hub) que roteia fluxos, armazena configurações persistentes e suporta a instalação e ativação dinâmica de plugins independentes (como Mash Control, Device Manager e Yeast Bank).

## 🚀 Como Navegar por Esta Documentação

Esta pasta `docs_v2.0` consolida informações sobre as arquiteturas, fluxos e processo de criação do ecossistema BrewStation. 
Escolha seu destino abaixo:

### 📖 Manuais e Uso Geral
- [**Apresentação e Requisitos**](01_apresentacao_requisitos.md) - Propósito do projeto, requisitos mínimos e processos gerais da Estação.
- [**Backlog Geral**](02_backlog_geral.md) - Nossas próximas entregas e roadmap consolidado.

### 🏗️ Arquitetura e Integração Core
- [**A Arquitetura do Core (Hub de Integração)**](03_core_architecture.md) - Como a Plataforma em si funciona sem nenhum plugin, estrutura das classes principais e onde a plataforma entra (Autenticação, Sessões e Bootstrap DB).

### 🔌 Ecossistema de Plugins
- [**O Sistema de Plugins (Ciclo de Vida)**](04_plugin_system.md) - Entendendo a `PluginManager`, como plugins são descobertos, instalados e inicializados. Inclui regras de Auto-Prefixing do SQLAlchemy.
- [**Gerenciamento de Menus e Views**](05_plugin_views.md) - Como a árvore de `menu_config.json` constrói o UI da plataforma em tempo de execução e a precedência do `TemplateLoader`.

### 🛠️ Criação e Integração
- [**O Gerador "Maker" e Estrutura dos Plugins**](06_plugin_maker.md) - Entendendo a anatomia formal (MVC) exigida de um plugin e como utilizar o Maker para scaffolding de novos módulos em minutos.
- [**Comunicação Cíclica (Dependências Inter-Plugin)**](07_plugin_integration.md) - Entendendo a resolução de conflitos e injeção de dependência de plugins maduros.

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
