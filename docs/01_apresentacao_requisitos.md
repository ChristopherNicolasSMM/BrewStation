# 1. Apresentação, Propósito e Requisitos

## Qual a Missão da BrewStation v2.0?

A **BrewStation** renasce nesta segunda versão não apenas como um calculador de volumes ou precificador de receitas, mas sim como uma verdadeira **Estação de Trabalho Modular para Cervejeiros (Workstation Hub)**. 

Seu arquétipo fundacional inspira-se no formato de plataformas consolidadas de mercado (ex: HomeAssistant ou ecossistemas de IDEs empresariais). Na prática orgânica, isso significa que:
**O Núcleo (*Core*) da aplicação nunca cresce ou "incha" o código.** Todo poder cervejeiro real está na capacidade das extensões inter-reguláveis - conhecidas no mercado como Plugins, Mods ou Apps.

### Razões Específicas do Design Em Camadas (Hub + Plugins)
1. **Estabilidade Monolítica Limitada:** A lógica de automação de termostatos em um ESP32 (Mash Control/Device) é assíncrona, frágil com hardware limitante e propensa a crash. Ao isolá-la inteiramente em um Plugin, se ele falhar, o Dashboard de Finanças e o Envase Core do usuário permanecerão no ar ininterruptos.
2. **Experimentação sem Culpa:** O gerador interno do sistema (`Maker Engine`) permite fabricar rascunhos de extensões rapidamente, sem medo de corromper o Flask e suas rotas.

## ⚙️ Requisitos Fundamentais da Estação Base

Para erguer esse Hub são necessários pouquíssimos componentes do ecossistema infraestrutural:

### Infraestrutura & Server
- **Interpretador:** Python 3.11+ (Maturidade de bibliotecas analíticas como *Pandas* no plugin bFather).
- **Roteador HTTP / Framework:** Flask 3+ acoplado de forma agnóstica sem amarras excessivas a bibliotecas Opinionionted. 
- **DB Driver (RDBMS):** SQLAlchemy 2 acenando para SQLite (Local/Teste/IoT) ou PostgresSQL Neon (Cloud/Production).

### Mapeamento das Extensões Base
Os recursos essenciais listados pelo time desenvolvedor devem rodar como módulos adjacentes. Atualmente:
- `plugin_integ_bFather`: (Auto-intitulado *brewstation_core* internamente). Trata de usuários, estoques primários, precificação crua e integração de planilhas.
- `plugin_device_manager`: Servidor WebSockets/MQTT embarcado para IoT.
- `plugin_mash_control`: Cronômetros, Steps, PID e PID tunning.
- `plugin_yeast_bank`: Congelamento de cepas, slants e cálculo real do decaimento vital de laboratórios de repicagem local.
