# 7. Comunicação Cíclica (Dependências Inter-Plugin)

Assim como em sistemas maduros (e.g., WordPress, HomeAssistant), a nova versão da Plataforma BrewStation implementa o conceito de resoluções de dependências estruturais entre os "Apps".

Por exemplo: O "Mash Control" (Controle de Brassagem Rápida) precisa se comunicar com Atuadores/Sensores (Termômetros, Relés). Em vez de implementar a complexidade IoT do zero, o `install.json` do `plugin_mash_control` declarará dependência direta do `device_manager`.

## Resolução Formal e Proteções do Sistema

Quando o desenvolvedor (ou `Admin`) requisita a inicialização de um pacote, o `PluginManager._check_dependencies(plugin)` avalia uma lista cruzada do que o novo pacote quer e o que o hub está orquestrando.

```mermaid
flowchart TD
    Start([Admin Solicitou Ativação do Plugin P])
    
    Start --> L1{Tem 'dependencies' no install.json?}
    L1 -- Não --> A[Sucesso: Módulo Ativo]
    
    L1 -- Sim --> LoopNode[Para cada dependência 'D']
    LoopNode --> L2{O plugin 'D' está Instalado?}
    
    L2 -- Não --> Erro1[Erro de Dependência: Aborta Inicialização]
    L2 -- Sim --> L3{O plugin 'D' está Ativo?}
    
    L3 -- Não --> Erro2[Erro de Dependência Lógica: Habilitar D primeiro]
    L3 -- Sim --> ValidaVersao{A Versão de 'D' satisfaz P?}
    
    ValidaVersao -- Sim --> L4{Existem mais dependências?}
    L4 -- Sim --> LoopNode
    L4 -- Não --> A
    
    ValidaVersao -- Não --> ErroVersion[Erro: Requer Atualização de D]
```

## Como a Integração entre Plugins Funciona no Python

No ecossistema atual, o Flask atua como o mediador (`event bus`):
A comunicação *intra-plugin* (Python p/ Python) não ocorre de forma fracamente tipada. O ideal do sistema é exportar Classes/Modelos, acessados via `model_loader` do Plugin B dentro do escopo do Plugin A.

```mermaid
graph LR
    subgraph Plugin B: Device Manager
        DevInterface(API Interna Servidor MQTT)
        DevModel[(SQLite prefix: 'dt_manager_')]
    end

    subgraph Plugin A: Mash Control
        MashCore(Business Logic Controller)
        MashRoute(Flask Blueprints)
    end

    MashCore -. "1. Importa via model_loader.py" .-> DevModel
    MashRoute -. "2. Dispara Request p/ Endpoint de B" .-> DevInterface
```

Isso garante duas frentes oficiais para "Programação Orientada a Módulos" na **BrewStation Platform v2.0**:
1. Chamadas de REST Enfileiradas Localmente (onde A chama o EndPoint Web de B).
2. Agenciamento do Database via Import do Repositório do vizinho. 
