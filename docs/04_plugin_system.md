# 4. O Sistema de Plugins (Ciclo de Vida)

## Visão Geral do Ciclo

O coração expansível do BrewStation vive em `src/core/plugin_manager.py`. Ele aplica transições restritas no Ciclo de Vida de um plugin, onde um plugin deve existir (`Draft/Discovered`), ser testado/ativado (`Active`) ou falhar e desativar.

## Máquina de Estados e Ciclo de Vida do Plugin

Todo Plugin no ecossistema passa por uma rígida transição de estados antes de assumir papéis e injetar rotas HTTP no Flask:

```mermaid
stateDiagram-v2
    [*] --> Discovered: Arquivos encontrados em src/plugins/
    
    state "Identificado e Válido" as Discovered
    state "Instalado no DB" as Installed
    state "Carregado & Roteado" as Active
    state "Inativo (Pausado)" as Inactive
    state "Erro de Dependência" as DependencyError
    
    Discovered --> Installed: call install_plugin()
    Discovered --> DependencyError: falha na validação do install.json
    
    Installed --> Active: call activate_plugin()
    Installed --> Inactive: Desativado manualmente pelo CLI
    
    Active --> Inactive: call deactivate_plugin()
    Inactive --> Active: call activate_plugin()
    
    Inactive --> Discovered: call uninstall_plugin()
```

## Fluxo de Carregamento na Inicialização da Estação

Ao iniciar a BrewStation (`python main.py`), este é o comportamento sequencial da Plataforma verificando suas extensões interconectadas:

```mermaid
sequenceDiagram
    participant App as Flask Application (main.py)
    participant PM as PluginManager
    participant PL as PluginLoader
    participant DB as SQLAlchemy DB
    participant Plugin as Plugin Modules (src/plugins/)
    
    App->>PM: Initialize(app, plugins_dir, config)
    activate PM
    
    PM->>PM: _load_config() (Leitura de install.json global)
    
    PM->>PL: discover_plugins()
    activate PL
    PL-->>PM: Lista de nomes detectados [pA, pB, pC...]
    deactivate PL
    
    loop Para cada plugin descoberto
        PM->>PL: load_plugin(name)
        PL->>Plugin: Importar classe PluginBase
        Plugin-->>PM: Retorna instância na memória
        
        alt is_installed AND (is_active OR is_core)
            PM->>Plugin: plugin.activate()
            PM->>PM: _register_plugin(plugin)
            PM->>App: Injecão de Flask Blueprints e Static Folders
        end
    end
    
    PM->>DB: _create_all_plugin_tables() (Cria/verificação SQL usando Auto-Prefixing)
    DB-->>PM: Prisão de Esquemas Realizada
    
    PM-->>App: Gerenciador Acoplado
    deactivate PM
```

## Fluxo de Mapeamento do Banco de Dados

O BrewStation evita confrontos de tabelas no banco de dados (`SQLite`/`PostgreSQL`) quando múltiplos plugins existem, utilizando o `Auto-Prefixing`.

```mermaid
erDiagram
    PLUGIN_YEAST_BANK {
        string table_prefix "Exemplo: yeastbk_"
    }
    
    PLUGIN_MASH_CONTROL {
        string table_prefix "Exemplo: mash_"
    }
    
    User ||--o{ yeastbk_YeastStrain : Registra
    yeastbk_YeastStrain ||--o{ yeastbk_YeastStarterLog : Avalia
    
    User ||--o{ mash_Session : Coordena
    mash_Session ||--o{ mash_StepLog : Gera Logging
```

Este mapa ER indica que mesmo o Módulo Core (Usuários) podendo relacionar-se com tabelas de plugins, essas tabelas carregam intrinsecamente um nome no banco (Ex: `yeastbk_`) que isola seus dados de corromper outros componentes, preservando independência em Drop/Upgrade/Downgrade de schema de banco.
