# 3. A Arquitetura do Core (Hub de Integração)

## O Propósito do Core

O **BrewStation** evoluiu de uma simples ferramenta de cálculo cervejeiro para um modelo de Estação de Trabalho (*Workstation*). O sistema "Core" (nucleico) do BrewStation atua estritamente como uma plataforma de infraestrutura independente, análoga a um pequeno Sistema Operacional web, enquanto a inteligência e o domínio de negócios vivem inteiramente isolados em "Apps" acopláveis chamados de Plugins.

## Estrutura de Classes Principais do Core

Abaixo ilustramos as peças estáticas essenciais (Classes do Python) que dão vida a Arquitetura da Estação.

```mermaid
classDiagram
    class FlaskApp {
      +config Dictionary
      +blueprints Dictionary
    }
    
    class PluginManager {
      +app Flask
      +plugins_dir Path
      +loader PluginLoader
      +plugins Dict
      +active_plugins List
      +installed_plugins List
      +install_plugin(name) bool
      +activate_plugin(name) bool
      +get_menu_items() List
      -_create_all_plugin_tables()
    }
    
    class PluginLoader {
      +plugins_dir Path
      +discover_plugins() List
      +load_plugin(name) PluginBase
    }
    
    class PluginBase {
      <<abstract>>
      +name String
      +version String
      +config Dictionary
      +install() bool
      +uninstall() bool
      +activate() bool
      +deactivate() bool
      +register_routes() List
      +register_models() List
    }
    
    class PluginInstaller {
      +plugin_path Path
      +discover_all_routes() Tuple
      +get_static_folder() Path
    }

    FlaskApp "1" *-- "1" PluginManager : Inicializa na Application Factory
    PluginManager "1" *-- "1" PluginLoader : Delega Descoberta
    PluginManager "1" o-- "*" PluginBase : Gerencia Ciclo de Vida
    PluginBase <|-- "Herda" PluginMeuPlugin
    PluginInstaller "1" -- "1" PluginBase : Auxilia na Injeção Automática
```

## Separação em Camadas e o Encaixe dos Plugins

O ecossistema é estritamente separado em Camadas Lógicas para evitar espaguete de código.

```mermaid
flowchart LR
    subgraph ViewLayer [Camada de Apresentação]
        direction TB
        TemplatesCore[Templates Globais Base]
        TemplatesPlugin[Templates do Plugin]
        MenuInjector[Menu Config Injector]
    end

    subgraph DomainLayer [Camada de Domínio & Controladores]
        direction TB
        RoutesCore[Flask Blueprints Core]
        RoutesPlugin[Flask Blueprints Específicos]
        BusinessLogic[Regras Cervejeiras e Integrações]
    end

    subgraph InfraLayer [Camada de Infraestrutura]
        direction TB
        AuthSyst(Flask Login & Security)
        PluginEngine(Engine do PluginManager)
        SQLitePRD[(SQLAlchemy DB Factory)]
    end

    ViewLayer --> DomainLayer
    DomainLayer --> InfraLayer

    %% Conexões do Plugin
    TemplatesPlugin -. Injetado sobre .-> TemplatesCore
    RoutesPlugin -. Carregado pelo .-> PluginEngine
    BusinessLogic -. Persiste no .-> SQLitePRD
```

## Como a Plataforma Inicia (O Workflow do Application Factory)

A rotina em `src/main.py` levanta os pilares essenciais. O Flask orquestra e sobe os provedores necessários antes das rotas customizarem o comportamento:

1. **Environment Setup:** Definição de Secrets, Debug Flags, e pastas de static file globais.
2. **Database Factory:** Assinatura do `db.init_app`.
3. **Session & Auth Manager:** Definição do comportamento via `Flask-Login` garantindo que o Auth seja a única regra unânime.
4. **Boot do Gerenciador de Plugins:** A chamada central para instanciar o `PluginManager` que fará toda varredura, validação de JSON e `PluginLoader`.
5. **Comandos de Terminal:** A `cli.py` atrela as referências.
