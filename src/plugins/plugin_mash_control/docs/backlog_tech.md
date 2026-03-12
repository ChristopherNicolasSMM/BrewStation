# MASH Control Plugin

## Backlog Técnico

Projeto: **BrewStation**
Plugin: **mash_control**

Objetivo do plugin:

Controlar processos de brassagem com suporte a:

* execução manual
* execução semi-automática
* execução automática
* integração com hardware via `device_manager`
* importação opcional de receitas via `plugin_integ_bFather`

O plugin deve permitir:

* modelagem completa de rampas de mostura
* controle de atuadores
* dashboard visual por planta
* persistência de sessão
* recuperação após reinício
* fail-safe operacional

---

# Arquitetura Funcional

O plugin é dividido em três camadas principais:

### 1 — Configuração

Define o ambiente operacional.

Inclui:

* plantas
* papéis funcionais
* parâmetros de segurança
* dashboard

---

### 2 — Receita / Rampas

Define:

* temperaturas
* tempos
* condições de avanço
* uso de atuadores

Importante:

**Receitas não salvam device IDs**

Receitas salvam **papéis funcionais**, permitindo reutilização entre plantas.

---

### 3 — Sessão

Executa uma brassagem real.

Inclui:

* estado atual
* telemetria
* comandos
* logs
* checkpoints
* recuperação

---

# Conceito de Papéis Funcionais

O sistema utiliza **roles (papéis)** em vez de IDs de dispositivos.

Exemplos:

```
mash_temp_sensor
mash_heater
recirculation_pump
transfer_pump
hlt_temp_sensor
hlt_heater
boil_heater
alarm_buzzer
```

A **planta** faz o mapeamento:

```
role → device_manager.device_id
```

Exemplo:

```
mash_temp_sensor → sensor_18
mash_heater → relay_panel_3
recirculation_pump → pump_01
```

A **sessão salva um snapshot desse mapeamento**.

---

# Modos de Operação

O sistema deve suportar:

### Manual

Operador controla atuadores manualmente.

### Semi-automático

Sistema sugere ações.

### Automático

Sistema executa etapas automaticamente.

---

# Integrações

## device_manager

Dependência operacional.

Sem ele:

Permitido:

* cadastrar receitas
* cadastrar plantas
* editar dashboards
* simulação

Bloqueado:

* execução real
* automação
* envio de comandos

---

## plugin_integ_bFather

Integração opcional.

Aba BrewFather:

* visível
* desabilitada quando plugin não ativo
* mensagem explicativa

---

# Persistência e Recuperação

Sessões devem:

Salvar em:

* banco de dados
* log local

Ao reiniciar BrewStation:

Sistema deve:

1 detectar sessão interrompida
2 carregar último checkpoint
3 oferecer opções:

* retomar
* abortar
* finalizar seguro

---

# Classificação de Comandos

## Nível 1 — Seguro

Executado automaticamente

Exemplos:

* leitura de sensor
* atualização de estado

---

## Roadmap de Desenvolvimento
As fases iniciais do plugin já estão implementadas conforme o roteiro
MVP. O trabalho procede da seguinte forma:

1. **Plants** – cadastro e gerenciamento de plantas (concluído).
2. **Recipes** – criação e edição de receitas com mash steps (concluído).
3. **Mash Schedule** – gerar cronograma a partir da receita; próxima
   etapa.
4. **Brew Session / Batch** – controlar execução, gravar telemetria,
   suportar manual/semi/automático.
5. **Hardware Integration** – mapear roles para devices, enviar comandos
   via `device_manager`.
6. **Analytics & Sharing** – visualizações e integração com serviços
   externos.

Cada fase repete o padrão arquitetural descrito anteriormente: modelo
SQLAlchemy, serviço com CRUD, endpoints REST, template HTML + JS,
registro no plugin e rota web.

Consulte também `docs/MASH_CONTROL_BACKLOG.md` e a pasta `docs/backlog`
para orientações e histórico.

---

## Nível 2 — Sensível

Configurável

Exemplos:

* ligar aquecimento
* ativar bomba

---

## Nível 3 — Crítico

Requer confirmação ou política explícita.

Exemplos:

* fervura
* transferência
* drenagem
* reset de falha

---

# Estrutura de Dados

## recipe

```
id
name
description
steps
required_roles
origin
created_at
```

---

## plant

```
id
name
dashboard_layout
role_mapping
safety_limits
created_at
```

---

## session

```
id
recipe_id
plant_id
role_resolution_snapshot
current_step
status
started_at
paused_at
recovered_at
fail_safe_state
checkpoint_version
```

---

## session_log

```
id
session_id
timestamp
event_type
source
payload
```

---

# BACKLOG

---

# EPIC 1 — Sistema de Configuração do Plugin

Prioridade: **Alta**

Objetivo:

Criar sistema completo de configurações.

---

## História 1.1

Criar modelo `MashControlSettings`

Prioridade: Alta

Descrição:

Persistir configurações gerais do plugin.

Critérios de aceite:

* modelo salvo em DB
* valores padrão definidos
* versão de configuração suportada

Dependências:

* nenhuma

---

## História 1.2

Implementar UI de Configurações

Prioridade: Alta

Descrição:

Criar tela `/mash_control/settings`.

Abas:

* Geral
* Integrações
* Papéis
* Segurança
* Sessões
* BrewFather

Critérios de aceite:

* configuração persistida
* validação de campos
* salvamento funcional

Dependências:

História 1.1

---

## História 1.3

Detecção de plugins dependentes

Prioridade: Alta

Descrição:

Detectar:

* `device_manager`
* `plugin_integ_bFather`

Critérios de aceite:

* status visível na UI
* integração refletida no sistema

Dependências:

* sistema de plugins BrewStation

---

# EPIC 2 — Sistema de Papéis Funcionais

Prioridade: **Alta**

Objetivo:

Desacoplar receita de hardware.

---

## História 2.1

Criar entidade `device_role`

Prioridade: Alta

Descrição:

Cadastrar papéis funcionais.

Critérios de aceite:

* roles cadastráveis
* roles editáveis
* roles removíveis

---

## História 2.2

Mapeamento de roles na planta

Prioridade: Alta

Descrição:

Associar roles a dispositivos do `device_manager`.

Critérios de aceite:

* UI para mapear
* validação de dispositivo
* persistência correta

Dependências:

device_manager

---

## História 2.3

Validação de roles obrigatórias

Prioridade: Alta

Descrição:

Receita não pode executar sem roles resolvidas.

Critérios de aceite:

* erro claro na criação da sessão
* validação automática

---

# EPIC 3 — Sistema de Plantas

Prioridade: **Alta**

Objetivo:

Modelar estrutura física da brassagem.

---

## História 3.1

Cadastro de planta

Critérios de aceite:

* CRUD completo
* persistência correta

---

## História 3.2

Dashboard por planta

Critérios de aceite:

* layout salvo
* componentes persistidos

---

## História 3.3

Componentes visuais vinculados a roles

Critérios de aceite:

* elemento SVG vinculado a role
* estado refletido visualmente

---

# EPIC 4 — Sistema de Receitas e Rampas

Prioridade: **Alta**

Objetivo:

Criar motor de receitas independente.

---

## História 4.1

Modelo de receita

Critérios de aceite:

* salvar etapas
* salvar temperatura
* salvar tempo

---

## História 4.2

Modelo de rampas

Critérios de aceite:

* múltiplas rampas
* edição fácil

---

## História 4.3

Uso de roles nas receitas

Critérios de aceite:

* receita referencia roles
* não referencia device IDs

---

## História 4.4

Edição manual de rampas

Critérios de aceite:

* operador pode alterar parâmetros

---

# EPIC 5 — Sessão de Brassagem

Prioridade: **Alta**

Objetivo:

Executar produção real.

---

## História 5.1

Wizard de criação de sessão

Critérios:

1 selecionar planta
2 selecionar receita
3 validar roles

---

## História 5.2

Snapshot de resolução de roles

Critérios:

* role → device salvo na sessão

---

## História 5.3

Persistência de sessão

Critérios:

* estado salvo
* recuperação possível

---

# EPIC 6 — Motor de Execução

Prioridade: **Alta**

Objetivo:

Controlar processo.

---

## História 6.1

Executor de etapas

Critérios:

* iniciar etapa
* finalizar etapa

---

## História 6.2

Controle de temperatura

Critérios:

* leitura de sensor
* acionamento de aquecimento

---

## História 6.3

Controle de tempo

Critérios:

* contagem correta
* avanço automático

---

## História 6.4

Modo manual

Critérios:

* operador pode ligar atuadores

---

# EPIC 7 — Fail-Safe e Segurança

Prioridade: **Alta**

---

## História 7.1

Limites de segurança

Critérios:

* temperatura máxima
* tempo máximo

---

## História 7.2

Perda de sensor

Critérios:

* desligar aquecimento

---

## História 7.3

Parada de emergência

Critérios:

* desligar todos atuadores

---

# EPIC 8 — Persistência e Recuperação

Prioridade: **Alta**

---

## História 8.1

Checkpoint de sessão

Critérios:

* checkpoint periódico

---

## História 8.2

Log local

Critérios:

* eventos registrados

---

## História 8.3

Recuperação após reinício

Critérios:

* sessão restaurada

---

# EPIC 9 — Integração BrewFather

Prioridade: **Média**

---

## História 9.1

Detectar plugin BrewFather

Critérios:

* aba desabilitada quando ausente

---

## História 9.2

Importar receita

Critérios:

* converter mash steps

---

## História 9.3

Conversão para receita interna

Critérios:

* rampas geradas corretamente

---

# EPIC 10 — Dashboard Operacional

Prioridade: **Média**

---

## História 10.1

Atualização de telemetria

---

## História 10.2

Status visual de atuadores

---

## História 10.3

Comandos rápidos

---

# Sequência Recomendada de Implementação

Ordem ideal:

```
1 Configuração do plugin
2 Papéis funcionais
3 Sistema de plantas
4 Sistema de receitas
5 Sessões
6 Motor de execução
7 Fail-safe
8 Persistência
9 Dashboard
10 BrewFather
```

---

# Resultado Esperado

Ao final o `mash_control` será capaz de:

* operar brassagem completa
* trabalhar com múltiplas plantas
* executar rampas configuráveis
* suportar operação manual
* recuperar sessão após falha
* operar com segurança industrial básica
