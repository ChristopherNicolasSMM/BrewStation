# 🍺 BrewStation — Prompt Mestre de Implementação: Dashboard SVG Operativo & Analítico

> **Instrução para Claude Code / Claude (modo agentic)**
> Projeto: https://github.com/ChristopherNicolasSMM/BrewStation
> Plugin alvo: `src/plugins/plugin_mash_control`
> Dependência principal: `src/plugins/plugin_device_manager`
> Versão deste prompt: 2.0

---

## ⚠️ PROTOCOLO DE TRABALHO — LEIA ANTES DE TUDO

Você é um engenheiro sênior Python/Flask. Vai implementar funcionalidades complexas de forma **incremental e segura**. Siga estas regras de trabalho sem exceção:

### Regra 1 — Uma Task por vez
Este prompt é organizado em **Tasks numeradas**. Implemente exatamente uma Task por sessão de trabalho. Ao finalizar cada Task:
1. Execute os testes manuais listados na Task
2. Faça commit com a mensagem padrão: `feat(task-XX): descrição curta em pt-BR`
3. Atualize o arquivo `docs/TASK_LOG.md` marcando a task como concluída
4. Informe ao usuário o que foi feito e o que vem a seguir

### Regra 2 — Reconhecimento antes de código
**NUNCA** escreva código antes de ler os arquivos relevantes. Para cada Task, o primeiro passo é sempre ler os arquivos que serão modificados.

### Regra 3 — Não quebre o que funciona
Antes de modificar qualquer arquivo existente, verifique se ele tem testes ou se é usado por outras partes do sistema. Use `grep -r "nome_do_arquivo"` para rastrear dependências.

### Regra 4 — Documentação junto com o código
Cada Task que adiciona funcionalidade **deve** atualizar o documento correspondente em `docs/`. Não deixe para "documentar depois".

### Regra 5 — Prefixo de tabelas
Todo modelo SQLAlchemy criado dentro de um plugin DEVE seguir a convenção de prefixo. Leia `docs/04_plugin_system.md` antes de criar qualquer modelo.

---

## 📋 MISSÃO GERAL

Implementar o **Dashboard de Brassagem SVG — Painel Operativo e Analítico** no plugin `plugin_mash_control`, com:

- Canvas SVG interativo com equipamentos do brewhouse
- Widgets de monitoramento em tempo real (temperatura, pressão, estado de atores)
- Componentes livres: texto, imagem, separadores, caixas de status
- Painel de log operacional ao vivo
- Motor de automação (regras "se sensor X → acionar ator Y")
- Emulador HTTP de dispositivos IoT (ESP32 / Raspberry Pi virtual)
- Modo Stand-by: rotação automática entre dashboards selecionados
- Execução de sessão de brassagem com controle PID e monitoramento

---

## 🗺️ MAPA DE TASKS

```
FASE 0 — Reconhecimento
  TASK-00  Leitura do projeto e GAP Analysis

FASE 1 — Fundação de Dados
  TASK-01  Modelos: DashboardLayout, DashboardWidget (novos tipos incluídos)
  TASK-02  Modelos: AutomationRule, AutomationRuleLog
  TASK-03  Modelos: BrewPlant, BrewPlantDeviceMapping
  TASK-04  Modelos: BrewSession expandido (steps, PID, log operacional)

FASE 2 — API Backend
  TASK-05  API: Layouts e Widgets (CRUD + batch save)
  TASK-06  API: Live Data (SSE + polling) e Sensor History
  TASK-07  API: Automation Rules (CRUD + toggle + logs)
  TASK-08  API: BrewPlant (CRUD + mapeamento de devices)
  TASK-09  API: Session Execution (iniciar, pausar, avançar step, finalizar)
  TASK-10  API: Emulador de Dispositivo IoT

FASE 3 — Assets SVG
  TASK-11  SVGs: Vessels (panelas, fermentadores, tanques)
  TASK-12  SVGs: Equipamentos (bombas, válvulas, canos, trocadores)
  TASK-13  SVGs: Sensores e indicadores
  TASK-14  catalog.json consolidado

FASE 4 — Frontend Canvas
  TASK-15  Canvas base: render de layout, zoom, pan
  TASK-16  Canvas: live data binding (atualização ao vivo nos widgets)
  TASK-17  Canvas: modo edit (drag, resize, rotate)
  TASK-18  Canvas: catálogo lateral + drag-to-canvas
  TASK-19  Canvas: widgets de conteúdo livre (texto, imagem, label, separador)
  TASK-20  Canvas: widgets de dados (gauge, semáforo, relay, chart, log panel)

FASE 5 — Modais e Configurações
  TASK-21  Modal de configuração de widget (4 abas)
  TASK-22  Painel lateral: sessão ativa, dispositivos, etapas, alarmes

FASE 6 — Automação
  TASK-23  AutomationEngine (backend, scheduler, avaliação de regras)
  TASK-24  Frontend: tela de gerenciamento de regras de automação

FASE 7 — Emulador IoT
  TASK-25  Emulador: backend (rotas HTTP, registro, simulação de valores)
  TASK-26  Emulador: frontend (painel de controle do emulador)

FASE 8 — Stand-by Mode
  TASK-27  Stand-by: backend (configuração de playlist de dashboards)
  TASK-28  Stand-by: frontend (rotação automática, overlay fullscreen)

FASE 9 — Fluxo Completo de Brassagem
  TASK-29  BrewPlant: fluxo de cadastro de planta e mapeamento de devices
  TASK-30  Session: execução com controle PID, steps, log operacional
  TASK-31  Session: tela de monitoramento analítico (gráficos, timeline, alarmes)

FASE 10 — Documentação Final
  TASK-32  Documentação completa de todos os plugins afetados
  TASK-33  Revisão final, estrutura de arquivos, checklist
```

---

## 🔍 TASK-00 — RECONHECIMENTO OBRIGATÓRIO DO PROJETO

**Objetivo:** Conhecer o estado atual do código antes de qualquer implementação.

### Passos obrigatórios:

```bash
# 1. Leia a arquitetura core em ordem
cat docs/03_core_architecture.md
cat docs/04_plugin_system.md      # CRÍTICO: convenções de prefixo de tabela
cat docs/05_plugin_views.md
cat docs/06_plugin_maker.md
cat docs/07_plugin_integration.md

# 2. Mapeie o Device Manager completamente
find src/plugins/plugin_device_manager -type f | sort
cat src/plugins/plugin_device_manager/models.py
cat src/plugins/plugin_device_manager/routes.py
# Identifique: como devices são criados, como sensores publicam valores,
# como atores recebem comandos, estrutura MQTT topics

# 3. Mapeie o Mash Control atual
find src/plugins/plugin_mash_control -type f | sort
cat src/plugins/plugin_mash_control/models.py
cat src/plugins/plugin_mash_control/routes.py
find src/plugins/plugin_mash_control/templates -name "*.html" | sort
# Leia todos os templates existentes

# 4. Rastreie integrações existentes entre os dois plugins
grep -r "device_manager\|DeviceManager\|get_sensor\|send_command\|mqtt" \
     src/plugins/plugin_mash_control --include="*.py"

# 5. Verifique bibliotecas JS já disponíveis no projeto
find src/static -name "*.js" | grep -v node_modules | sort
find src/static/vendors -type d 2>/dev/null
# Identifique: Chart.js, SVG.js, interact.js, d3, socket.io já presentes?

# 6. Verifique requirements.txt para bibliotecas Python disponíveis
cat requirements.txt
# Identifique: APScheduler, flask-socketio, paho-mqtt, etc.
```

### Entregável obrigatório desta Task:
Crie `docs/TASK_LOG.md` com o template:
```markdown
# BrewStation — Log de Tasks

| Task | Descrição | Status | Data | Commit |
|------|-----------|--------|------|--------|
| TASK-00 | Reconhecimento e GAP Analysis | ✅ | DD/MM/AAAA | abc1234 |
...
```

Crie `docs/plugin_mash_control/DASHBOARD_GAP_ANALYSIS.md` com:
- Lista de modelos existentes vs. necessários
- Lista de rotas existentes vs. necessárias
- Bibliotecas JS disponíveis vs. necessárias
- O que pode ser reutilizado do Device Manager
- Riscos e dependências identificadas

---

## 🏗️ ARQUITETURA CONCEITUAL DO SISTEMA

Antes das Tasks individuais, entenda o modelo mental do sistema:

```
┌─────────────────────────────────────────────────────────────────┐
│                    BREWSTATION — VISÃO GERAL                    │
├────────────────┬────────────────────┬───────────────────────────┤
│  Device Manager│   Mash Control     │  Dashboard SVG            │
│                │                   │                           │
│  Device        │   BrewPlant        │  DashboardLayout          │
│  (físico IoT)  │   (planta lógica)  │  (canvas salvo)           │
│       │        │        │           │        │                  │
│  Sensor/Actor  │   PlantMapping     │  DashboardWidget          │
│  (função)      │   (device→papel)   │  (elemento no canvas)     │
│       │        │        │           │        │                  │
│  MQTT Topics   │   BrewSession      │  LiveBinding              │
│  Readings      │   (execução)       │  (widget↔sensor/actor)    │
│                │   Steps + PID      │                           │
└────────────────┴────────────────────┴───────────────────────────┘
         ↕ MQTT / HTTP               ↕ SSE / polling
    Devices Físicos (ESP32,      Browser (dashboard ao vivo)
    Raspberry Pi, Emulador)
```

---

## 📐 FLUXO 1 — CADASTRO DE DEVICE (Device Manager)

> **Para a IA:** Este fluxo descreve como um dispositivo IoT é registrado no sistema. Entenda-o completamente antes de implementar qualquer Task das Fases 1–2.

### Conceitos fundamentais:

Um **Device** no BrewStation representa um hardware físico (ESP32, Raspberry Pi, sensor genérico) ou um **Emulador virtual**. Cada Device pode ter múltiplas **funções**:

- **Sensor**: lê um valor do ambiente (temperatura, pressão, nível, fluxo)
- **Atuador/Actor**: executa um comando (ligar/desligar relé, ajustar PWM, abrir válvula)
- **Gateway**: apenas roteia dados de outros devices

### Fluxo de cadastro:

```
1. Usuário acessa: Device Manager → Novo Device
2. Preenche:
   - Nome: "Sensor Temp Mostura" 
   - Tipo: ESP32 | Raspberry Pi | Emulador HTTP | Genérico MQTT
   - MQTT Client ID: "esp32_mostura_01" (único no broker)
   - IP / Endereço (opcional, para devices HTTP)
   
3. Adiciona Funções ao Device:
   ┌─────────────────────────────────────────────┐
   │ Função 1 — Sensor de Temperatura            │
   │   Papel: sensor                             │
   │   Métrica: temperature                      │
   │   Unidade: °C                               │
   │   MQTT Topic de leitura:                    │
   │   brewstation/devices/esp32_mostura_01/     │
   │              sensors/temperature            │
   │   Range: -20 a 150°C                       │
   │   Intervalo de publicação: 5s               │
   ├─────────────────────────────────────────────┤
   │ Função 2 — Relé de Aquecimento              │
   │   Papel: actor                              │
   │   Tipo de ação: ON/OFF                      │
   │   MQTT Topic de comando:                    │
   │   brewstation/devices/esp32_mostura_01/     │
   │              actors/relay_heat/set          │
   │   MQTT Topic de estado:                     │
   │   brewstation/devices/esp32_mostura_01/     │
   │              actors/relay_heat/state        │
   └─────────────────────────────────────────────┘

4. Sistema gera automaticamente:
   - ID único do device
   - Token de autenticação MQTT (se segurança habilitada)
   - Documentação dos tópicos MQTT para flash no firmware
   - QR Code com configuração (opcional)
```

### Convenção de tópicos MQTT:
```
Leitura de sensor:
  brewstation/devices/{client_id}/sensors/{metric}
  Payload: {"value": 65.3, "unit": "°C", "ts": 1717000000}

Estado de ator:
  brewstation/devices/{client_id}/actors/{actor_key}/state
  Payload: {"state": "ON", "ts": 1717000000}

Comando para ator:
  brewstation/devices/{client_id}/actors/{actor_key}/set
  Payload: {"action": "ON"} | {"action": "OFF"} | {"action": "SET", "value": 75.0}

Heartbeat / presença:
  brewstation/devices/{client_id}/status
  Payload: {"online": true, "firmware": "1.2.0", "ts": 1717000000}
```

### Modelos envolvidos (verificar/criar no Device Manager):
```python
Device:
  id, name, client_id (único), device_type (ENUM),
  ip_address, description, is_active,
  auth_token, created_at, last_seen_at

DeviceFunction:
  id, device_id (FK), role (ENUM: sensor|actor|gateway),
  metric (string), unit, label,
  mqtt_topic_read, mqtt_topic_cmd, mqtt_topic_state,
  min_value, max_value, publish_interval_s,
  actor_action_type (ENUM: ON_OFF|PWM|VALUE),
  is_active, config_json

DeviceReading:  # histórico de leituras
  id, function_id (FK), value (float), recorded_at (datetime, INDEX)
  # Purge automático após N dias (configurável)
```

---

## 🗺️ FLUXO 2 — MAPEAMENTO DEVICE → PLANTA DE BRASSAGEM

> **Para a IA:** Uma "Planta" (BrewPlant) é o modelo lógico de um equipamento de brassagem (ex: "Equipamento 120L — 3 Vessels"). Ela mapeia devices físicos a papéis lógicos do processo cervejeiro.

### Conceito de Planta:

```
BrewPlant "Equipamento Principal 120L"
├── Vessel: "Caldeirão de Mostura (HLT/MLT)"
│   ├── sensor_temp → Device: "esp32_mostura_01" / Function: temperature
│   ├── actor_heat  → Device: "esp32_mostura_01" / Function: relay_heat
│   └── actor_pump  → Device: "esp32_bomba_01"   / Function: relay_pump
├── Vessel: "Caldeirão de Fervura"
│   ├── sensor_temp → Device: "esp32_fervura_01" / Function: temperature
│   ├── actor_heat  → Device: "esp32_fervura_01" / Function: relay_heat
│   └── actor_pump  → Device: "esp32_bomba_02"   / Function: relay_pump
└── Fermentador: "Fermentador Cônico 50L"
    ├── sensor_temp → Device: "esp32_ferm_01"    / Function: temperature
    └── actor_cool  → Device: "esp32_ferm_01"    / Function: relay_cool
```

### Modelos necessários (criar no plugin_mash_control):

```python
BrewPlant:
  id, name, description, capacity_liters, vessel_count,
  is_active, created_at, updated_at,
  plant_schema_json  # descrição completa da planta em JSON

BrewPlantVessel:
  id, plant_id (FK), vessel_type (ENUM: mash_tun|boil_kettle|hlt|fermenter|bright_tank),
  label, position_order (int), description

BrewPlantMapping:
  id, vessel_id (FK), role_key (string: "sensor_temp"|"actor_heat"|"actor_pump"|...),
  device_function_id (FK → DeviceFunction no Device Manager),
  label, is_required (bool)
  # Exemplos de role_key padrão:
  # sensor_temp, sensor_pressure, sensor_level, sensor_flow
  # actor_heat, actor_cool, actor_pump_in, actor_pump_out, actor_valve
```

### Fluxo de cadastro de planta:

```
1. Usuário acessa: Mash Control → Plantas → Nova Planta
2. Define nome, capacidade, número de vessels
3. Para cada vessel: define tipo e label
4. Para cada vessel: mapeia roles a DeviceFunctions disponíveis
   (dropdown mostra apenas devices cadastrados e ativos no Device Manager)
5. Sistema valida se roles obrigatórios estão mapeados
6. Salva planta → disponível para vincular a sessões de brassagem
```

---

## 🍺 FLUXO 3 — EXECUÇÃO DE SESSÃO DE BRASSAGEM

> **Para a IA:** Uma sessão é a execução de uma receita em uma planta específica. O sistema controla automaticamente temperatura, aciona atores e registra tudo.

### Ciclo de vida de uma sessão:

```
Receita (Profile) → vinculada a → BrewPlant → inicia → BrewSession
                                                              │
                                                    ┌─────────┴─────────┐
                                                    │   Steps (etapas)   │
                                                    │                   │
                                                    │  Step 1: MashIn   │
                                                    │   target_temp: 52°C│
                                                    │   duration: 15min  │
                                                    │   PID: ativo       │
                                                    │                   │
                                                    │  Step 2: Sacch.   │
                                                    │   target_temp: 65°C│
                                                    │   duration: 60min  │
                                                    │                   │
                                                    │  Step N: Boil     │
                                                    │   target_temp:100°C│
                                                    │   duration: 60min  │
                                                    └───────────────────┘
```

### Modelos de sessão (verificar/expandir no plugin_mash_control):

```python
BrewSession:
  id, name, plant_id (FK), recipe_id (FK nullable),
  status (ENUM: draft|active|paused|completed|aborted),
  started_at, completed_at, notes,
  current_step_index (int),
  operator_id (FK → User)

BrewSessionStep:
  id, session_id (FK), step_index (int), name, step_type,
  target_temp (float), duration_seconds (int),
  vessel_id (FK → BrewPlantVessel),
  pid_enabled (bool), pid_kp, pid_ki, pid_kd,
  hop_addition_json,  # adições de lúpulo programadas
  status (ENUM: pending|active|completed|skipped),
  started_at, completed_at, actual_duration_s,
  notes

BrewSessionLog:  # log operacional da sessão
  id, session_id (FK), step_id (FK nullable),
  log_level (ENUM: info|warning|error|alarm),
  source (string: "pid_engine"|"automation"|"user"|"sensor"),
  message (string), detail_json,
  logged_at (datetime, INDEX)

BrewSessionAlarm:
  id, session_id (FK), alarm_type, severity (ENUM: low|medium|high|critical),
  message, is_acknowledged (bool),
  triggered_at, acknowledged_at, acknowledged_by
```

### Motor PID (criar em `services/pid_controller.py`):

```python
class PIDController:
    """
    Controle PID simples para manutenção de temperatura por step.
    Kp, Ki, Kd configuráveis por step.
    
    Ciclo de trabalho:
      1. Lê temperatura atual do sensor vinculado ao vessel do step
      2. Calcula output PID (0.0 a 1.0)
      3. Converte para duty cycle (PWM) ou ON/OFF com histerese
      4. Envia comando ao ator de aquecimento via Device Manager
      5. Registra em BrewSessionLog a cada ciclo
    """
    
    def __init__(self, kp, ki, kd, setpoint, output_limits=(0, 1))
    def compute(self, current_value, dt) -> float
    def reset()
    def set_setpoint(self, setpoint: float)
```

### Controle de sessão (serviço `services/session_engine.py`):

```python
class SessionEngine:
    """
    Gerencia a execução de uma BrewSession ativa.
    Roda em thread dedicada enquanto há sessão ativa.
    
    Responsabilidades:
    - Avançar steps automaticamente (ao atingir tempo ou temperatura alvo)
    - Executar PID em loop para o step atual
    - Avaliar AutomationRules associadas à sessão
    - Gerar BrewSessionLog e BrewSessionAlarm
    - Publicar estado via SSE para o dashboard
    """
    
    def start_session(self, session_id: int)
    def pause_session(self, session_id: int)
    def resume_session(self, session_id: int)
    def advance_step(self, session_id: int, force: bool = False)
    def abort_session(self, session_id: int, reason: str)
    def get_live_state(self, session_id: int) -> dict
    # Retorna: current_step, temps, actor_states, pid_output, elapsed, logs_recentes
```

---

## 📊 FLUXO 4 — DASHBOARD EM TEMPO REAL

### O que o dashboard operativo deve exibir:

```
┌──────────────────────────────────────────────────────────────────┐
│ TOPBAR: [Nome Layout ★ Padrão] [● Mostura Ao Vivo] [Editar]     │
│         [Gerenciar] [Stand-by ▶]                                │
├─────────────────────────────────────────────┬────────────────────┤
│                                             │ PAINEL LATERAL     │
│           CANVAS SVG                        │ ──────────────     │
│                                             │ 🔴 Sessão Ativa    │
│  [Panela SVG]──temp: 64.8°C──[Gauge]       │ Mostura Step 2     │
│       │                                     │ ⏱ 00:34:12        │
│  [Bomba SVG]──estado: ON──[Semáforo]       │ Target: 65°C       │
│       │                                     │ ──────────────     │
│  [Fermentador SVG]──temp: 18.2°C           │ 🌡 Dispositivos    │
│                                             │ • Mostura: 64.8°C  │
│  ┌──────────────────────────────────────┐  │ • Fervura: offline │
│  │  📊 Gráfico Temperatura (30min)      │  │ • Bomba: ON        │
│  │  ─────────────────────────────────  │  │ ──────────────     │
│  │  Mostura: ──────── 64.8°C           │  │ 📋 Etapas          │
│  │  Setpoint: - - - - 65.0°C           │  │ ✅ MashIn           │
│  └──────────────────────────────────────┘  │ 🔵 Sacch. 65°C     │
│                                             │ ⬜ Mash Out         │
│  ┌──────────────────────────────────────┐  │ ⬜ Boil             │
│  │  📋 LOG OPERACIONAL                  │  │ ──────────────     │
│  │  14:32:01 [PID] Relay ON (64.5°C)   │  │ 🔔 Alarmes (0)     │
│  │  14:32:06 [AUTO] Regra #3 avaliada  │  │ ──────────────     │
│  │  14:31:58 [USER] Step avançado      │  │ [⏸Pausar][▶Próx]  │
│  └──────────────────────────────────────┘  │                    │
│   [⊞] [🔍+] [🔍-] [↺] [⛶ Stand-by]       │                    │
└─────────────────────────────────────────────┴────────────────────┘
```

---

## 🗃️ TASK-01 — MODELOS: DashboardLayout e DashboardWidget

**Pré-requisito:** TASK-00 concluída.
**Arquivos a modificar:** `src/plugins/plugin_mash_control/models.py`

### Antes de implementar:
```bash
cat src/plugins/plugin_mash_control/models.py
cat docs/04_plugin_system.md  # convenção de prefixo
```

### Modelos a criar (verificar se já existem antes):

```python
class DashboardLayout(db.Model):
    __tablename__ = "mc_dashboard_layout"  # prefixo mc_ = mash_control
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    is_default = Column(Boolean, default=False)
    is_standby_enabled = Column(Boolean, default=False)  # incluso na rotação stand-by
    standby_duration_seconds = Column(Integer, default=30)  # tempo neste layout no stand-by
    canvas_width = Column(Integer, default=1600)   # dimensões do canvas em px
    canvas_height = Column(Integer, default=900)
    background_color = Column(String(20), default="#0f1117")
    background_image_url = Column(String(500))  # imagem de fundo opcional
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    created_by = Column(Integer, ForeignKey("user.id"))
    
    widgets = relationship("DashboardWidget", backref="layout", 
                           cascade="all, delete-orphan", order_by="DashboardWidget.z_index")


class DashboardWidget(db.Model):
    __tablename__ = "mc_dashboard_widget"
    
    id = Column(Integer, primary_key=True)
    layout_id = Column(Integer, ForeignKey("mc_dashboard_layout.id"), nullable=False)
    
    # Tipo do widget — define qual componente renderizar
    widget_type = Column(String(50), nullable=False)
    # Valores possíveis:
    #   SVG_VESSEL     — panela, fermentador, etc.
    #   SVG_EQUIPMENT  — bomba, válvula, cano
    #   SVG_SENSOR     — ícone de sensor
    #   GAUGE          — gauge circular de valor
    #   CHART          — gráfico de linha (histórico)
    #   TRAFFIC_LIGHT  — semáforo 3 estados
    #   RELAY_TOGGLE   — botão on/off de ator
    #   TEMP_DISPLAY   — display numérico de temperatura
    #   LOG_PANEL      — painel de log operacional ao vivo
    #   STEP_PROGRESS  — progresso das etapas da receita
    #   ALARM_PANEL    — painel de alarmes ativos
    #   TEXT           — texto livre (título, label, nota)
    #   IMAGE          — imagem externa ou upload
    #   SEPARATOR      — linha divisória ou moldura
    #   STATUS_BOX     — caixa de status geral do sistema
    
    label = Column(String(200))
    svg_asset_key = Column(String(100))  # chave no catalog.json, se tipo SVG
    
    # Posição e dimensões no canvas (px)
    x = Column(Float, default=100)
    y = Column(Float, default=100)
    width = Column(Float, default=120)
    height = Column(Float, default=140)
    rotation = Column(Float, default=0.0)  # graus
    z_index = Column(Integer, default=1)
    
    # Vínculos com devices (nullable — nem todo widget precisa)
    device_function_id = Column(Integer, ForeignKey("dm_device_function.id"), nullable=True)
    # dm_ = prefixo do Device Manager — confirme o prefixo real ao ler os modelos
    
    # Configurações específicas do tipo de widget (JSON flexível)
    config_json = Column(JSON, default={})
    # Exemplos por tipo:
    # GAUGE:        {"min": 0, "max": 100, "unit": "°C", "warn_above": 80, "critical_above": 95}
    # CHART:        {"history_minutes": 30, "show_setpoint": true, "color": "#00ff88"}
    # TEXT:         {"text": "Brewhouse Principal", "font_size": 24, "color": "#ffffff", "bold": true}
    # IMAGE:        {"src": "/static/img/logo.png", "object_fit": "contain", "opacity": 0.8}
    # SEPARATOR:    {"orientation": "horizontal", "color": "#334155", "thickness": 2}
    # LOG_PANEL:    {"max_lines": 20, "filter_levels": ["info","warning","error"]}
    # TRAFFIC_LIGHT:{"states": {"OFF": "gray", "STANDBY": "yellow", "ON": "green"}}
    # RELAY_TOGGLE: {"confirm_before_action": true, "show_label": true}
    # STATUS_BOX:   {"show_session": true, "show_devices": true, "show_time": true}
    
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### Testes manuais desta Task:
1. `flask shell` → importar os modelos → sem erros de importação
2. `flask recreate-plugin-tables` → tabelas criadas sem erro
3. Criar um layout via shell com 2 widgets e verificar persistência

### Documentação a atualizar:
- Criar `docs/plugin_mash_control/MODELS_DASHBOARD.md`

---

## 🗃️ TASK-02 — MODELOS: AutomationRule e AutomationRuleLog

**Arquivos a modificar:** `src/plugins/plugin_mash_control/models.py`

```python
class AutomationRule(db.Model):
    __tablename__ = "mc_automation_rule"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(String(1000))
    is_active = Column(Boolean, default=True)
    
    # Condição — SENSOR
    sensor_function_id = Column(Integer, ForeignKey("dm_device_function.id"), nullable=False)
    sensor_metric = Column(String(50), default="temperature")
    condition_operator = Column(String(5), nullable=False)
    # Valores: "<=", ">=", "==", "!=", "<", ">"
    condition_value = Column(Float, nullable=False)
    condition_unit = Column(String(20), default="°C")
    
    # Ação — ATOR
    actor_function_id = Column(Integer, ForeignKey("dm_device_function.id"), nullable=False)
    actor_action = Column(String(20), nullable=False)
    # Valores: "ON", "OFF", "TOGGLE", "SET_VALUE"
    actor_value = Column(Float, nullable=True)
    
    # Controle de execução
    cooldown_seconds = Column(Integer, default=30)
    last_triggered_at = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    
    # Escopo (opcional: regra ativa apenas durante uma sessão)
    session_id = Column(Integer, ForeignKey("mc_brew_session.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    logs = relationship("AutomationRuleLog", backref="rule", 
                        cascade="all, delete-orphan")


class AutomationRuleLog(db.Model):
    __tablename__ = "mc_automation_rule_log"
    
    id = Column(Integer, primary_key=True)
    rule_id = Column(Integer, ForeignKey("mc_automation_rule.id"), nullable=False)
    triggered_at = Column(DateTime, default=datetime.utcnow, index=True)
    sensor_value_at_trigger = Column(Float)
    action_taken = Column(String(100))
    success = Column(Boolean, default=True)
    error_message = Column(String(500))
```

### Exemplo de uso (documentar em `docs/plugin_mash_control/AUTOMATION_ENGINE.md`):

```
Cenário: Sensor "Mostura" ≤ 65°C → Acionar relé aquecimento ON

AutomationRule:
  name: "Aquecimento Mostura"
  sensor_function_id: 3     # DeviceFunction: esp32_mostura_01/temperature
  condition_operator: "<="
  condition_value: 65.0
  actor_function_id: 4      # DeviceFunction: esp32_mostura_01/relay_heat
  actor_action: "ON"
  cooldown_seconds: 10      # Não re-acionar por 10s após último trigger

Cenário inverso: Sensor "Mostura" > 66°C → Desligar relé aquecimento
  (segunda regra complementar para histerese manual)
```

---

## 🗃️ TASK-03 — MODELOS: BrewPlant e Mapeamento

**Arquivos a modificar:** `src/plugins/plugin_mash_control/models.py`

Implemente os modelos `BrewPlant`, `BrewPlantVessel` e `BrewPlantMapping` conforme especificado no **FLUXO 2** deste documento. Garanta FKs corretas para `DeviceFunction` do Device Manager.

### Testes manuais:
1. Criar planta com 2 vessels via Flask shell
2. Criar mapeamentos vinculando a DeviceFunctions existentes
3. Consultar planta com joins de vessels e mappings sem N+1 queries

---

## 🗃️ TASK-04 — MODELOS: BrewSession Expandido

**Arquivos a modificar:** `src/plugins/plugin_mash_control/models.py`

Implemente ou expanda os modelos `BrewSession`, `BrewSessionStep`, `BrewSessionLog` e `BrewSessionAlarm` conforme especificado no **FLUXO 3**.

Verifique se `BrewSession` já existe — se sim, adicione apenas os campos ausentes com `ALTER TABLE` via migração manual ou `flask recreate-plugin-tables` em dev.

---

## 🔌 TASK-05 — API: Layouts e Widgets

**Arquivo:** `src/plugins/plugin_mash_control/routes.py` (ou `routes/dashboard.py` separado)

### Antes de implementar:
```bash
cat src/plugins/plugin_mash_control/routes.py
# Verifique o blueprint existente, prefixo de URL, decoradores de auth
```

### Endpoints a implementar:

```
# Layouts
GET    /mash-control/api/dashboard/layouts
POST   /mash-control/api/dashboard/layouts
GET    /mash-control/api/dashboard/layouts/<id>
PUT    /mash-control/api/dashboard/layouts/<id>
DELETE /mash-control/api/dashboard/layouts/<id>
POST   /mash-control/api/dashboard/layouts/<id>/set-default

# Widgets
POST   /mash-control/api/dashboard/layouts/<id>/widgets
PUT    /mash-control/api/dashboard/layouts/<id>/widgets/<wid>
DELETE /mash-control/api/dashboard/layouts/<id>/widgets/<wid>
PUT    /mash-control/api/dashboard/layouts/<id>/widgets/batch
       # Body: {"widgets": [{id, x, y, width, height, rotation, z_index, config_json}...]}
       # Usado para salvar todo o estado do canvas de uma vez (drag/drop/resize)

# SVG Catalog
GET    /mash-control/api/dashboard/svg-catalog

# Stand-by config
GET    /mash-control/api/dashboard/standby-config
PUT    /mash-control/api/dashboard/standby-config
       # Body: {"layouts": [{id, duration_seconds}...], "transition": "fade|slide|instant"}
```

### Padrão de resposta:
```json
// Sucesso
{"data": {...}, "message": "Layout criado com sucesso"}

// Erro
{"error": "Layout não encontrado", "code": "NOT_FOUND"}
```

---

## 🔌 TASK-06 — API: Live Data e Sensor History

### Live Data (SSE preferencial, polling como fallback):

```python
# SSE endpoint — dados em tempo real via Server-Sent Events
GET /mash-control/api/dashboard/events

# Retorna stream SSE com eventos:
# event: live_data
# data: {"sensors": [{...}], "actors": [{...}], "session": {...}}

# Polling fallback
GET /mash-control/api/dashboard/live-data
# Retorna snapshot atual dos dados
```

**Estrutura do payload live_data:**
```json
{
  "sensors": [
    {
      "function_id": 3,
      "device_name": "esp32_mostura_01",
      "label": "Temperatura Mostura",
      "value": 64.8,
      "unit": "°C",
      "timestamp": "2024-01-15T14:32:01Z",
      "is_online": true,
      "is_alarm": false
    }
  ],
  "actors": [
    {
      "function_id": 4,
      "device_name": "esp32_mostura_01",
      "label": "Relé Aquecimento",
      "state": "ON",
      "timestamp": "2024-01-15T14:32:00Z",
      "is_online": true
    }
  ],
  "session": {
    "id": 12,
    "name": "Brassagem IPA #5",
    "status": "active",
    "current_step": {"name": "Sacarificação", "target_temp": 65.0, "elapsed_s": 1250, "duration_s": 3600},
    "recent_logs": [
      {"ts": "14:32:01", "level": "info", "source": "pid", "message": "Relay ON (64.5°C < 65.0°C)"}
    ],
    "active_alarms": []
  },
  "timestamp": "2024-01-15T14:32:05Z"
}
```

### Sensor History:
```
GET /mash-control/api/dashboard/sensor-history/<function_id>
    ?from=<ISO>&to=<ISO>&resolution=30s|1m|5m
    
Retorna: {"data": [{"ts": "...", "value": 64.8}, ...], "unit": "°C"}
```

---

## 🔌 TASK-07 — API: Automation Rules

Implemente os endpoints CRUD + toggle + logs para AutomationRule conforme especificado na versão anterior deste documento (Etapa 2.3).

Adicione também:
```
GET /mash-control/api/dashboard/rules/evaluate-now
    # Força avaliação imediata de todas as regras (útil para debug)
    # Retorna: lista de regras avaliadas com resultado de cada uma
```

---

## 🔌 TASK-08 — API: BrewPlant

```
GET    /mash-control/api/plants
POST   /mash-control/api/plants
GET    /mash-control/api/plants/<id>
PUT    /mash-control/api/plants/<id>
DELETE /mash-control/api/plants/<id>

GET    /mash-control/api/plants/<id>/vessels
POST   /mash-control/api/plants/<id>/vessels
DELETE /mash-control/api/plants/<id>/vessels/<vid>

GET    /mash-control/api/plants/<id>/vessels/<vid>/mappings
POST   /mash-control/api/plants/<id>/vessels/<vid>/mappings
DELETE /mash-control/api/plants/<id>/vessels/<vid>/mappings/<mid>

GET    /mash-control/api/plants/available-functions
    # Retorna DeviceFunctions disponíveis para mapeamento
    # (consultando Device Manager)
```

---

## 🔌 TASK-09 — API: Session Execution

```
POST   /mash-control/api/sessions               # inicia nova sessão
GET    /mash-control/api/sessions/<id>/state    # estado completo da sessão
POST   /mash-control/api/sessions/<id>/start
POST   /mash-control/api/sessions/<id>/pause
POST   /mash-control/api/sessions/<id>/resume
POST   /mash-control/api/sessions/<id>/advance-step
       # Body: {"force": false}
POST   /mash-control/api/sessions/<id>/abort
       # Body: {"reason": "texto"}
GET    /mash-control/api/sessions/<id>/logs
       # Querystring: ?level=info,warning&limit=100&offset=0
GET    /mash-control/api/sessions/<id>/alarms
POST   /mash-control/api/sessions/<id>/alarms/<aid>/acknowledge
```

---

## 🔌 TASK-10 — API: Emulador de Dispositivo IoT

> **Objetivo:** Criar um emulador HTTP que simula um ESP32 ou Raspberry Pi, publicando leituras de sensores e respondendo a comandos de atores — sem hardware físico. Fundamental para desenvolvimento e testes.

### Modelo do emulador:

```python
# Criar em plugin_device_manager ou como plugin próprio plugin_emulator
class EmulatedDevice(db.Model):
    __tablename__ = "dm_emulated_device"
    
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("dm_device.id"), nullable=False)
    # Device real que este emulador representa
    
    is_running = Column(Boolean, default=False)
    emulation_mode = Column(String(50), default="sine_wave")
    # Modos: sine_wave | random_walk | step_function | csv_replay | manual
    
    # Configuração por função emulada (JSON)
    functions_config = Column(JSON, default={})
    # Exemplo:
    # {
    #   "3": {  # function_id
    #     "mode": "sine_wave",
    #     "base_value": 65.0,
    #     "amplitude": 2.0,
    #     "period_seconds": 60,
    #     "noise": 0.3
    #   }
    # }
    
    publish_interval_seconds = Column(Integer, default=5)
    last_published_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
```

### Endpoints do emulador:

```
GET    /device-manager/api/emulator/devices
       # Lista devices com emulação disponível

POST   /device-manager/api/emulator/devices/<device_id>/start
       # Inicia emulação — começa a publicar via MQTT ou registrar leituras

POST   /device-manager/api/emulator/devices/<device_id>/stop
       # Para emulação

PUT    /device-manager/api/emulator/devices/<device_id>/config
       # Atualiza configuração de emulação (mode, amplitude, etc.)

POST   /device-manager/api/emulator/devices/<device_id>/publish
       # Força publicação manual de um valor específico
       # Body: {"function_id": 3, "value": 67.5}
       # Útil para simular manualmente uma leitura

POST   /device-manager/api/emulator/inject
       # Endpoint que o "hardware virtual" chama para injetar uma leitura
       # Simula o POST que um ESP32 real faria
       # Body: {"client_id": "esp32_mostura_01", "metric": "temperature", "value": 65.3}
       # Header: Authorization: Bearer <device_auth_token>
```

### Comportamento do emulador:

```
Modo sine_wave:
  valor(t) = base_value + amplitude * sin(2π * t / period_seconds) + noise * random()

Modo random_walk:
  valor(t) = valor(t-1) + step * random(-1, 1)
  (clamped entre min_value e max_value da função)

Modo step_function:
  Segue um array de {time_offset_s, value} para simular
  aquecimento realista: [(0, 20.0), (60, 35.0), (120, 55.0), ...]

Modo manual:
  Publicação apenas via endpoint /publish (controle total do usuário)
```

### Frontend do emulador (TASK-26):

```
Painel: Device Manager → Emulador

┌─────────────────────────────────────────────────────┐
│  🤖 Emulador de Dispositivos IoT                    │
├─────────────────────────────────────────────────────┤
│  Device: esp32_mostura_01  [▶ Iniciar] [⏹ Parar]   │
│  Status: ● Rodando  │  Último envio: 3s atrás       │
│                                                     │
│  Funções emuladas:                                  │
│  ┌──────────────────────────────────────────────┐  │
│  │ 🌡 Temperatura  │ Modo: sine_wave            │  │
│  │ Base: 65°C  Amp: ±2°C  Período: 60s         │  │
│  │ Valor atual: 64.7°C  [Enviar agora: 67.5°C] │  │
│  ├──────────────────────────────────────────────┤  │
│  │ ⚡ Relé Aquecimento  │ Estado: ON            │  │
│  │ [Forçar ON] [Forçar OFF]                    │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
│  Mini gráfico dos últimos 60s                       │
│  [─────────/\/\/───────────]  64.7°C               │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 TASK-11 — ASSETS SVG: Vessels

**Diretório:** `src/plugins/plugin_mash_control/static/svg/components/`

### Especificações técnicas de todos os SVGs:
- `viewBox="0 0 100 120"` (ou proporcional) — SEM width/height fixos
- Usar `currentColor` e variáveis CSS `--svg-body`, `--svg-accent`, `--svg-indicator`
- Classe na raiz: `class="bs-svg-component"`
- IDs semânticos nos grupos principais: `#body`, `#liquid-level`, `#temp-indicator`, etc.
- Tamanho de arquivo < 8KB
- Nenhuma dependência externa, SVG puro

### Componentes a criar:

**Vessels (recipientes):**
| Arquivo | Descrição | Detalhes |
|---------|-----------|----------|
| `mash_tun.svg` | Panela de mostura | Corpo cilíndrico, bocal de saída, indicador de agitador (#stirrer) |
| `boil_kettle.svg` | Panela de fervura | Corpo com indicador de chama/resistência (#heat-element) |
| `hlt.svg` | Hot Liquor Tank | Similar ao MLT, indica água quente |
| `fermenter_conical.svg` | Fermentador cônico | Corpo cônico, válvula na base, airlock no topo |
| `fermenter_carboy.svg` | Garrafão / Carboy | Formato arredondado, tampa com airlock |
| `bright_tank.svg` | Tanque de clarificação | Cilíndrico, conexões laterais |
| `keg.svg` | Barril / Keg | Formato característico de barril |

### Dica de implementação:
Use formas geométricas simples (rect, circle, ellipse, path) com stroke de 1.5px. O visual "industrial/técnico" é o objetivo — não precisa ser fotorrealista. Veja o estilo visual do CraftBeerPi como referência de linguagem.

---

## 🎨 TASK-12 — ASSETS SVG: Equipamentos

| Arquivo | Descrição |
|---------|-----------|
| `pump.svg` | Bomba centrífuga com seta de direção de fluxo e indicador de estado |
| `heat_exchanger.svg` | Trocador de calor / Chiller (serpentina) |
| `valve_ball.svg` | Válvula esfera (aberta/fechada via classe CSS) |
| `valve_solenoid.svg` | Válvula solenoide (elétrica) |
| `pipe_h.svg` | Segmento de cano horizontal (conectável) |
| `pipe_v.svg` | Segmento de cano vertical |
| `pipe_elbow.svg` | Cotovelo 90° |
| `pipe_tee.svg` | T de derivação |
| `resistencia.svg` | Resistência elétrica de imersão |
| `burner.svg` | Queimador a gás |

---

## 🎨 TASK-13 — ASSETS SVG: Sensores e Indicadores

| Arquivo | Descrição |
|---------|-----------|
| `thermometer.svg` | Termômetro (com nível animável via CSS) |
| `pressure_gauge.svg` | Manômetro circular (com ponteiro girável via JS) |
| `flow_meter.svg` | Medidor de fluxo |
| `level_sensor.svg` | Sensor de nível (boia) |
| `ph_probe.svg` | Eletrodo de pH |

---

## 🎨 TASK-14 — catalog.json Consolidado

```json
{
  "version": "1.0",
  "categories": [
    {
      "id": "vessel",
      "label": "Recipientes",
      "icon": "🫙",
      "components": [
        {
          "key": "mash_tun",
          "label": "Panela de Mostura",
          "file": "mash_tun.svg",
          "widget_type": "SVG_VESSEL",
          "default_size": [100, 120],
          "tags": ["mostura", "mlt", "hlt"],
          "compatible_roles": ["sensor_temp", "actor_heat", "actor_pump_out"],
          "description": "Panela principal para mostura com indicador de temperatura"
        }
      ]
    },
    {
      "id": "equipment",
      "label": "Equipamentos",
      "icon": "⚙️",
      "components": [...]
    },
    {
      "id": "sensor",
      "label": "Sensores",
      "icon": "📡",
      "components": [...]
    },
    {
      "id": "display",
      "label": "Displays e Widgets",
      "icon": "📊",
      "components": [
        { "key": "gauge_temp", "label": "Gauge de Temperatura", "widget_type": "GAUGE", ... },
        { "key": "chart_temp", "label": "Gráfico de Temperatura", "widget_type": "CHART", ... },
        { "key": "traffic_light", "label": "Semáforo de Estado", "widget_type": "TRAFFIC_LIGHT", ... },
        { "key": "relay_toggle", "label": "Botão de Ator", "widget_type": "RELAY_TOGGLE", ... },
        { "key": "log_panel", "label": "Painel de Log", "widget_type": "LOG_PANEL", ... },
        { "key": "step_progress", "label": "Progresso de Etapas", "widget_type": "STEP_PROGRESS", ... },
        { "key": "alarm_panel", "label": "Painel de Alarmes", "widget_type": "ALARM_PANEL", ... }
      ]
    },
    {
      "id": "content",
      "label": "Conteúdo Livre",
      "icon": "✏️",
      "components": [
        { "key": "text_label", "label": "Texto / Título", "widget_type": "TEXT", "default_size": [200, 50] },
        { "key": "image_box", "label": "Imagem", "widget_type": "IMAGE", "default_size": [150, 100] },
        { "key": "separator_h", "label": "Separador Horizontal", "widget_type": "SEPARATOR", "default_size": [300, 4] },
        { "key": "status_box", "label": "Caixa de Status", "widget_type": "STATUS_BOX", "default_size": [250, 150] }
      ]
    }
  ]
}
```

---

## 🖥️ TASK-15 — Canvas Base: Render e Viewport

**Arquivo novo:** `src/plugins/plugin_mash_control/static/js/dashboard_canvas.js`
**Template:** `src/plugins/plugin_mash_control/templates/plugin_mash_control/dashboard.html`

### Classe BrewCanvas — esqueleto:

```javascript
class BrewCanvas {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.layoutId = options.layoutId;
        this.mode = 'view'; // 'view' | 'edit'
        this.zoom = 1.0;
        this.panX = 0;
        this.panY = 0;
        this.widgets = new Map(); // widgetId → WidgetInstance
        this.liveData = {};
        this._liveDataInterval = null;
        this._sseSource = null;
        
        this._initCanvas();
        this._bindEvents();
    }
    
    // INICIALIZAÇÃO
    _initCanvas() { /* cria elemento SVG/div principal */ }
    _bindEvents() { /* mouse wheel zoom, middle-click pan */ }
    
    // CARREGAMENTO
    async loadLayout(layoutId) { /* GET /api/dashboard/layouts/<id> → renderiza widgets */ }
    
    // RENDERIZAÇÃO
    renderWidget(widgetData) {
        // Instancia a classe correta baseado em widgetData.widget_type:
        const WidgetClass = WidgetRegistry.get(widgetData.widget_type);
        const instance = new WidgetClass(widgetData, this);
        instance.render(this.canvas);
        this.widgets.set(widgetData.id, instance);
    }
    
    // PERSISTÊNCIA
    async saveLayout() { /* PUT /api/dashboard/layouts/batch com estado atual */ }
    
    // LIVE DATA
    startLiveUpdates() { /* SSE ou polling → chama applyLiveData */ }
    stopLiveUpdates() { /* fecha SSE ou clearInterval */ }
    applyLiveData(data) {
        // Distribui dados para cada widget registrado
        this.widgets.forEach(widget => widget.onLiveData(data));
    }
    
    // VIEWPORT
    setZoom(level) { this.zoom = level; this._applyTransform(); }
    resetView() { this.zoom = 1; this.panX = 0; this.panY = 0; this._applyTransform(); }
    fitToScreen() { /* calcula zoom para caber na janela */ }
    _applyTransform() { /* aplica scale + translate no canvas */ }
    
    // MODO EDIT
    enableEditMode() { this.mode = 'edit'; this.widgets.forEach(w => w.enableEdit()); }
    disableEditMode() { this.mode = 'view'; this.widgets.forEach(w => w.disableEdit()); }
}
```

### Registro de widgets:

```javascript
// dashboard_widget_registry.js
const WidgetRegistry = {
    _registry: new Map(),
    register(type, cls) { this._registry.set(type, cls); },
    get(type) { return this._registry.get(type) || UnknownWidget; }
};

// Cada widget registra a si mesmo ao ser importado:
WidgetRegistry.register('SVG_VESSEL', SVGVesselWidget);
WidgetRegistry.register('GAUGE', GaugeWidget);
WidgetRegistry.register('CHART', ChartWidget);
WidgetRegistry.register('TRAFFIC_LIGHT', TrafficLightWidget);
WidgetRegistry.register('RELAY_TOGGLE', RelayToggleWidget);
WidgetRegistry.register('LOG_PANEL', LogPanelWidget);
WidgetRegistry.register('STEP_PROGRESS', StepProgressWidget);
WidgetRegistry.register('ALARM_PANEL', AlarmPanelWidget);
WidgetRegistry.register('TEXT', TextWidget);
WidgetRegistry.register('IMAGE', ImageWidget);
WidgetRegistry.register('SEPARATOR', SeparatorWidget);
WidgetRegistry.register('STATUS_BOX', StatusBoxWidget);
```

---

## 🖥️ TASK-16 — Canvas: Live Data Binding

### Classe base de widget:

```javascript
class BaseWidget {
    constructor(data, canvas) {
        this.id = data.id;
        this.data = data;         // dados do banco
        this.canvas = canvas;
        this.el = null;           // elemento DOM/SVG do widget
        this.deviceFunctionId = data.device_function_id;
        this.config = data.config_json || {};
    }
    
    render(parent) { /* implementar em subclasses */ }
    onLiveData(livePayload) { /* chamar updateValue se function_id bate */ }
    updateValue(value, meta) { /* implementar em subclasses */ }
    enableEdit() { /* adiciona handles de drag/resize */ }
    disableEdit() { /* remove handles */ }
    destroy() { this.el?.remove(); }
    
    // Helpers compartilhados
    _positionStyle() {
        return `left:${this.data.x}px; top:${this.data.y}px; 
                width:${this.data.width}px; height:${this.data.height}px;
                transform: rotate(${this.data.rotation}deg);
                z-index: ${this.data.z_index};`;
    }
}
```

### Implementação de widgets críticos:

#### `GaugeWidget` (gauge circular SVG nativo):
```javascript
class GaugeWidget extends BaseWidget {
    render(parent) {
        // SVG gauge circular desenhado via arc path
        // - Arco de fundo cinza (0° a 270°)
        // - Arco de valor colorido (0° a X° proporcional)
        // - Linha de setpoint (ponteiro vermelho)
        // - Texto central com valor atual
        // - Cores: azul(frio) → verde(ok) → amarelo(alerta) → vermelho(crítico)
        // baseado em config.warn_above e config.critical_above
    }
    updateValue(value) {
        const pct = (value - this.config.min) / (this.config.max - this.config.min);
        const degrees = pct * 270; // arco de 270°
        this._updateArc(degrees);
        this._updateText(value);
        this._updateColor(value);
    }
}
```

#### `LogPanelWidget` (painel de log ao vivo):
```javascript
class LogPanelWidget extends BaseWidget {
    // Exibe os logs recentes da sessão ativa
    // Atualiza via livePayload.session.recent_logs
    // Auto-scroll para o log mais recente
    // Filtra por nível (info/warning/error/alarm)
    // Cores por nível: cinza/amarelo/vermelho/vermelho piscante
    render(parent) { /* div com overflow-y: auto e lista de log entries */ }
    onLiveData(data) {
        if (data.session?.recent_logs) {
            this._appendLogs(data.session.recent_logs);
        }
    }
}
```

#### `TextWidget` (texto livre):
```javascript
class TextWidget extends BaseWidget {
    render(parent) {
        // div com texto, tamanho de fonte e cor configuráveis
        // No modo edit: clique duplo abre input inline para editar texto
        // Suporte a markdown básico: **negrito**, *itálico*
    }
}
```

#### `ImageWidget` (imagem livre):
```javascript
class ImageWidget extends BaseWidget {
    render(parent) {
        // <img> com src = config.src (URL ou base64)
        // No modo edit: clique abre modal para inserir URL ou fazer upload
        // object-fit configurável (contain/cover/fill)
        // Opacidade configurável
    }
}
```

---

## 🖥️ TASK-17 — Canvas: Modo Edit (Drag, Resize, Rotate)

### Biblioteca recomendada: `interact.js`

Verifique se já está no projeto: `find src/static/vendors -name "interact*"`
Se não: adicionar em `src/static/vendors/interact.min.js`

### Implementação no `enableEdit()` de BaseWidget:

```javascript
enableEdit() {
    this.el.classList.add('widget-editable');
    
    // Drag
    interact(this.el).draggable({
        listeners: {
            move: (e) => {
                this.data.x += e.dx / this.canvas.zoom;
                this.data.y += e.dy / this.canvas.zoom;
                this.el.style.left = this.data.x + 'px';
                this.el.style.top  = this.data.y + 'px';
            },
            end: () => this.canvas._onWidgetMoved(this)
        }
    });
    
    // Resize (handles nos cantos)
    interact(this.el).resizable({
        edges: { right: true, bottom: true, left: true, top: true },
        listeners: {
            move: (e) => {
                this.data.width  = e.rect.width  / this.canvas.zoom;
                this.data.height = e.rect.height / this.canvas.zoom;
                this.el.style.width  = this.data.width + 'px';
                this.el.style.height = this.data.height + 'px';
            },
            end: () => this.canvas._onWidgetResized(this)
        }
    });
    
    // Rotate handle (SVG overlay no topo do widget)
    this._addRotateHandle();
}

_addRotateHandle() {
    const handle = document.createElement('div');
    handle.className = 'rotate-handle';
    // Posiciona acima do widget; drag circular calcula ângulo relativo ao centro
    handle.addEventListener('mousedown', this._startRotate.bind(this));
    this.el.appendChild(handle);
}
```

### Toolbar de edição (exibida no canvas em modo edit):
```html
<div id="edit-toolbar">
  <button onclick="canvas.saveLayout()">💾 Salvar</button>
  <button onclick="canvas.disableEditMode()">✕ Cancelar</button>
  <hr>
  <!-- para widget selecionado: -->
  <button onclick="selectedWidget.bringToFront()">⬆ Frente</button>
  <button onclick="selectedWidget.sendToBack()">⬇ Fundo</button>
  <button onclick="selectedWidget.duplicate()">⧉ Duplicar</button>
  <button onclick="selectedWidget.openConfig()">⚙ Configurar</button>
  <button onclick="selectedWidget.remove()">🗑 Excluir</button>
  <hr>
  <label>Rot: <input type="number" id="rotation-input" step="5" min="0" max="360"></label>
  <label>Z: <input type="number" id="zindex-input"></label>
</div>
```

---

## 🖥️ TASK-18 — Canvas: Catálogo Lateral e Drag-to-Canvas

### Sidebar de catálogo (modo edit):

```html
<div id="catalog-sidebar" class="hidden">
  <input type="search" id="catalog-search" placeholder="🔍 Buscar componente...">
  
  <div id="catalog-categories">
    <!-- Gerado via /api/dashboard/svg-catalog -->
    <details open>
      <summary>🫙 Recipientes</summary>
      <div class="catalog-grid">
        <div class="catalog-item" 
             draggable="true"
             data-widget-type="SVG_VESSEL"
             data-svg-key="mash_tun">
          <img src="/static/svg/components/mash_tun.svg" alt="Panela de Mostura">
          <span>Mostura</span>
        </div>
        <!-- ... outros itens ... -->
      </div>
    </details>
    <!-- ... outras categorias ... -->
  </div>
</div>
```

### Drag-to-canvas:
```javascript
// Ao soltar item do catálogo no canvas:
canvas.addEventListener('drop', (e) => {
    const widgetType = e.dataTransfer.getData('widget-type');
    const svgKey = e.dataTransfer.getData('svg-key');
    const pos = canvas.screenToCanvas(e.clientX, e.clientY);
    
    // Abre modal de configuração antes de inserir
    openWidgetConfigModal({
        widget_type: widgetType,
        svg_asset_key: svgKey,
        x: pos.x, y: pos.y,
        isNew: true,
        onConfirm: (config) => canvas.addWidget(config)
    });
});
```

---

## 🖥️ TASK-19 — Canvas: Widgets de Conteúdo Livre

Implemente os seguintes widgets adicionais que não dependem de dispositivos IoT mas enriquecem o painel operativo:

### `StatusBoxWidget`
Caixa de status geral configurável:
- Linha de sessão ativa (nome, status, duração)
- Lista de devices online/offline
- Relógio atual
- IP/hostname do servidor (útil em TVs de monitoramento)

### `TextWidget`
- Texto configurável, tamanho, cor, alinhamento, negrito/itálico
- Modo edit: clique duplo → edição inline
- Suporte a `{HORA}`, `{DATA}`, `{SESSAO}` como variáveis dinâmicas

### `ImageWidget`
- Fonte: URL externa ou arquivo estático do servidor
- Opacidade, object-fit configuráveis
- Útil para: logo da cervejaria, foto da receita, diagramas de processo

### `SeparatorWidget`
- Linha horizontal ou vertical (configurável)
- Espessura, cor, estilo (sólido/tracejado/pontilhado)
- Útil para organizar visualmente o canvas em seções

---

## 🖥️ TASK-20 — Canvas: Widgets Analíticos e Operacionais

### `AlarmPanelWidget`
```javascript
class AlarmPanelWidget extends BaseWidget {
    // Lista de alarmes ativos da sessão
    // Cada alarme: ícone de severidade + mensagem + botão "Reconhecer"
    // Cores: low=azul, medium=amarelo, high=laranja, critical=vermelho piscante
    // Badge de contagem visível mesmo quando o widget está minimizado
    onLiveData(data) {
        this._renderAlarms(data.session?.active_alarms || []);
    }
}
```

### `StepProgressWidget` expandido:
```javascript
class StepProgressWidget extends BaseWidget {
    // Lista vertical de etapas com estados visuais
    // Etapa atual: destaque com borda colorida + timer regressivo
    // Temperatura atual vs. setpoint em cada etapa
    // Botões: [⏸ Pausar] [▶ Próxima Etapa] apenas se user tem permissão
    onLiveData(data) {
        if (data.session) {
            this._updateCurrentStep(data.session.current_step);
        }
    }
}
```

### `ChartWidget` completo:
```javascript
class ChartWidget extends BaseWidget {
    render(parent) {
        // Canvas Chart.js ou SVG nativo
        // Linha de temperatura real (cor configurável)
        // Linha de setpoint tracejada (vermelho)
        // Eixo X: últimos N minutos (configurável: 15/30/60/120)
        // Tooltip ao hover
        // Botão de expandir → modal com gráfico maior + download CSV
    }
    async loadHistory() {
        // GET /api/dashboard/sensor-history/<function_id>?from=...
        // Popula o gráfico com dados históricos
    }
    onLiveData(data) {
        // Adiciona novo ponto ao gráfico ao vivo
        const sensor = data.sensors.find(s => s.function_id === this.deviceFunctionId);
        if (sensor) this._pushDataPoint(sensor.value, sensor.timestamp);
    }
}
```

---

## ⚙️ TASK-21 — Modal de Configuração de Widget

Arquivo: `dashboard_config_modal.js` + seção no template `dashboard.html`

### Estrutura do modal (4 abas):

```html
<div id="widget-config-modal" class="modal">
  <div class="modal-header">
    <h3 id="modal-title">⚙ Configurar Widget</h3>
    <button onclick="closeModal()">✕</button>
  </div>
  
  <div class="modal-tabs">
    <button class="tab-btn active" data-tab="general">Geral</button>
    <button class="tab-btn" data-tab="device">Dispositivo</button>
    <button class="tab-btn" data-tab="display">Visual</button>
    <button class="tab-btn" data-tab="position">Posição</button>
  </div>
  
  <!-- ABA GERAL -->
  <div class="tab-panel active" id="tab-general">
    <label>Label: <input id="cfg-label" type="text"></label>
    <label>Visível: <input id="cfg-visible" type="checkbox"></label>
    <!-- Para TEXT: textarea com suporte a variáveis dinâmicas -->
    <!-- Para IMAGE: input de URL + preview -->
  </div>
  
  <!-- ABA DISPOSITIVO (só para widgets que usam dados ao vivo) -->
  <div class="tab-panel" id="tab-device">
    <label>Sensor/Ator vinculado:
      <select id="cfg-function-id">
        <option value="">-- Nenhum --</option>
        <!-- preenchido via /api/dashboard/live-data -->
      </select>
    </label>
    <div id="device-preview">
      <!-- Mostra valor atual do sensor selecionado -->
    </div>
  </div>
  
  <!-- ABA VISUAL -->
  <div class="tab-panel" id="tab-display">
    <!-- GAUGE: min, max, warn_above, critical_above, cor -->
    <!-- CHART: history_minutes, show_setpoint, cor -->
    <!-- TEXT: font_size, color, bold, align -->
    <!-- IMAGE: object_fit, opacity -->
    <!-- TRAFFIC_LIGHT: mapeamento estado → cor -->
    <!-- LOG_PANEL: max_lines, filter_levels -->
  </div>
  
  <!-- ABA POSIÇÃO -->
  <div class="tab-panel" id="tab-position">
    <label>X: <input id="cfg-x" type="number"></label>
    <label>Y: <input id="cfg-y" type="number"></label>
    <label>Largura: <input id="cfg-w" type="number"></label>
    <label>Altura: <input id="cfg-h" type="number"></label>
    <label>Rotação: <input id="cfg-rot" type="number" min="0" max="360" step="5"></label>
    <label>Z-index: <input id="cfg-z" type="number"></label>
  </div>
  
  <div class="modal-footer">
    <button onclick="closeModal()">Cancelar</button>
    <button onclick="saveWidgetConfig()" class="btn-primary">Salvar</button>
  </div>
</div>
```

---

## ⚙️ TASK-22 — Painel Lateral Operativo

O painel lateral direito do dashboard deve ser um componente React-like (ou template Jinja com atualizações via JS) com as seguintes seções colapsáveis:

```javascript
class SidePanel {
    // Seção: Sessão Ativa
    renderSessionSection(sessionData) {
        // Nome, status badge, timer, step atual, setpoint vs real, botões pause/next
    }
    
    // Seção: Dispositivos
    renderDevicesSection(sensorsData, actorsData) {
        // Card por device function: nome, valor, unidade, status online/offline
        // Indicador visual de alarme se valor fora do range
    }
    
    // Seção: Etapas da Receita
    renderStepsSection(stepsData) {
        // Lista de steps: ✅ concluído / 🔵 ativo / ⬜ pendente
        // Step ativo com timer regressivo e barra de progresso
    }
    
    // Seção: Alarmes Ativos
    renderAlarmsSection(alarmsData) {
        // Badge de contagem no header da seção
        // Lista de alarmes com severity e botão de reconhecimento
    }
    
    update(liveData) {
        // Chamado a cada tick do live data
        // Atualiza apenas o que mudou (diff mínimo)
    }
}
```

---

## 🤖 TASK-23 — AutomationEngine (Backend)

**Arquivo:** `src/plugins/plugin_mash_control/services/automation_engine.py`

```python
class AutomationEngine:
    """
    Avalia AutomationRules periodicamente e aciona atores quando condições são satisfeitas.
    Roda em thread APScheduler. Instanciado no __init__.py do plugin.
    
    IMPORTANTE: Consume Device Manager via API interna Python.
    Não fazer HTTP interno. Use a interface pública do DeviceManager plugin.
    """
    
    _instance = None  # Singleton
    _scheduler = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AutomationEngine()
        return cls._instance
    
    def start(self, interval_seconds: int = 5):
        """Inicia o scheduler. Chamar no __init__.py do plugin."""
    
    def stop(self):
        """Para o scheduler. Chamar no shutdown do plugin."""
    
    def evaluate_all_rules(self):
        """Job executado periodicamente."""
        with app.app_context():
            rules = AutomationRule.query.filter_by(is_active=True).all()
            for rule in rules:
                try:
                    self.evaluate_rule(rule)
                except Exception as e:
                    logger.error(f"Erro ao avaliar regra {rule.id}: {e}")
    
    def evaluate_rule(self, rule: AutomationRule) -> bool:
        # 1. Verificar cooldown
        if rule.last_triggered_at:
            elapsed = (datetime.utcnow() - rule.last_triggered_at).total_seconds()
            if elapsed < rule.cooldown_seconds:
                return False
        
        # 2. Obter valor atual do sensor via Device Manager
        sensor_value = self._get_sensor_value(rule.sensor_function_id)
        if sensor_value is None:
            return False
        
        # 3. Avaliar condição
        ops = {"<=": operator.le, ">=": operator.ge, "==": operator.eq,
               "!=": operator.ne, "<": operator.lt, ">": operator.gt}
        condition_met = ops[rule.condition_operator](sensor_value, rule.condition_value)
        
        if condition_met:
            # 4. Acionar ator
            success = self._trigger_actor(rule.actor_function_id, 
                                          rule.actor_action, rule.actor_value)
            # 5. Logar
            self._log_trigger(rule, sensor_value, success)
            if success:
                rule.last_triggered_at = datetime.utcnow()
                rule.trigger_count += 1
                db.session.commit()
            return success
        return False
    
    def _get_sensor_value(self, function_id: int) -> Optional[float]:
        """Busca última leitura do Device Manager (não via HTTP, via query direta)."""
        # Consulte como o Device Manager armazena leituras recentes
        # Geralmente: DeviceReading.query.filter_by(function_id=...).order_by(desc).first()
    
    def _trigger_actor(self, function_id: int, action: str, value=None) -> bool:
        """Envia comando ao ator via Device Manager (publicação MQTT ou registro)."""
        # Consulte a API interna do Device Manager para envio de comandos
    
    def _log_trigger(self, rule, sensor_value, success, error=None):
        log = AutomationRuleLog(
            rule_id=rule.id,
            sensor_value_at_trigger=sensor_value,
            action_taken=f"{rule.actor_action} on function {rule.actor_function_id}",
            success=success,
            error_message=str(error) if error else None
        )
        db.session.add(log)
        db.session.commit()
```

---

## 🤖 TASK-24 — Frontend: Tela de Regras de Automação

**Rota:** `/mash-control/automacao`
**Template:** `automation_rules.html`

### Layout da tela:

```
┌─────────────────────────────────────────────────────┐
│ ⚙ Regras de Automação           [+ Nova Regra]      │
├─────────────────────────────────────────────────────┤
│ 🟢 Aquecimento Mostura                         [⚙][🗑]│
│    SE Temp Mostura ≤ 65°C → Relé Aquecimento ON    │
│    Cooldown: 10s  │  Disparos: 142  │  Há 3min     │
├─────────────────────────────────────────────────────┤
│ 🔴 Desligamento por Superaquecimento (inativo) [⚙][🗑]│
│    SE Temp Mostura > 68°C → Relé Aquecimento OFF   │
│    Cooldown: 5s   │  Disparos: 0    │  Nunca       │
└─────────────────────────────────────────────────────┘
```

Modal de criação (conforme especificado na versão anterior + campos de sessão específica).

---

## 🌀 TASK-27 — Stand-by Mode: Backend

O modo stand-by permite que o dashboard fique em exibição contínua (ex: TV na cervejaria) alternando automaticamente entre layouts selecionados.

### Configuração de stand-by:

```python
# Em DashboardLayout, campos já incluídos na TASK-01:
# is_standby_enabled (bool) — se este layout entra na rotação
# standby_duration_seconds (int) — tempo neste layout

# Configuração global (armazenar em chave/valor do BrewStation ou JSON):
# standby_transition: "fade" | "slide" | "instant"
# standby_active: bool
```

### Endpoint de configuração:
```
GET /mash-control/api/dashboard/standby-config
    → {"layouts": [{id, name, duration_s, order}], "transition": "fade", "active": false}

PUT /mash-control/api/dashboard/standby-config
    Body: {"layouts": [{id, duration_seconds, order}...], "transition": "fade"}

GET /mash-control/api/dashboard/standby-playlist
    → Lista ordenada de layouts habilitados para stand-by com duração de cada um
```

---

## 🌀 TASK-28 — Stand-by Mode: Frontend

### Comportamento:

```javascript
class StandbyManager {
    constructor(canvas) {
        this.canvas = canvas;
        this.playlist = [];    // lista de {layoutId, durationMs}
        this.currentIndex = 0;
        this.timer = null;
        this.isActive = false;
    }
    
    async loadPlaylist() {
        const data = await fetch('/mash-control/api/dashboard/standby-playlist').then(r => r.json());
        this.playlist = data.layouts;
    }
    
    start() {
        this.isActive = true;
        document.body.classList.add('standby-mode');
        // Oculta sidebar, topbar, toolbar
        // Mostra overlay fullscreen com o canvas
        this._showCurrent();
    }
    
    stop() {
        this.isActive = false;
        clearTimeout(this.timer);
        document.body.classList.remove('standby-mode');
        // Restaura UI normal
    }
    
    _showCurrent() {
        const current = this.playlist[this.currentIndex];
        this.canvas.loadLayout(current.layoutId);
        this.timer = setTimeout(() => this._advance(), current.durationMs);
    }
    
    _advance() {
        this.currentIndex = (this.currentIndex + 1) % this.playlist.length;
        this._transition(() => this._showCurrent());
    }
    
    _transition(callback) {
        // fade: opacity 0 → carregar → opacity 1
        // slide: translate-x → carregar → translate-x back
        // instant: direto
    }
}
```

### Botão stand-by na topbar:
```html
<button id="btn-standby" onclick="standbyManager.start()" title="Modo Stand-by">
  ⛶ Stand-by
</button>
<!-- Pressionar ESC sai do modo stand-by -->
```

---

## 📋 TASK-29 — BrewPlant: Fluxo Completo de Cadastro

**Rota:** `/mash-control/plantas`
**Template:** `brew_plant.html`

### Wizard de cadastro em 3 passos:

```
PASSO 1: Identificação da Planta
  - Nome: "Equipamento Principal 120L"
  - Capacidade (litros): 120
  - Número de vessels: 3
  - Descrição opcional

PASSO 2: Configuração dos Vessels
  Para cada vessel:
  - Tipo: [Mostura/HLT | Fervura | Fermentador | Bright Tank | Outro]
  - Label: "Caldeirão 1 — Mostura"
  - Ordem no processo

PASSO 3: Mapeamento de Dispositivos
  Para cada vessel, para cada role possível:
  ┌─────────────────────────────────────────────────────┐
  │ Vessel: Caldeirão 1 — Mostura                       │
  ├─────────────────────────────────────────────────────┤
  │ 🌡 Sensor de Temperatura (obrigatório)              │
  │    [Dropdown: esp32_mostura_01 / temperature  ▼]   │
  │    Testando... ✅ Último valor: 22.3°C             │
  │                                                     │
  │ ⚡ Ator de Aquecimento                             │
  │    [Dropdown: esp32_mostura_01 / relay_heat   ▼]   │
  │    Estado atual: OFF                               │
  │                                                     │
  │ 💧 Bomba de Saída (opcional)                       │
  │    [Dropdown: esp32_bomba_01 / relay_pump     ▼]   │
  └─────────────────────────────────────────────────────┘

RESULTADO: Planta cadastrada e disponível para vincular a sessões
```

---

## 📋 TASK-30 — Session Engine: Execução com PID e Steps

Implemente `src/plugins/plugin_mash_control/services/session_engine.py` conforme especificado no **FLUXO 3**.

### Loop de execução do step ativo:

```python
def _step_loop(self, session: BrewSession):
    """
    Executa em thread dedicada enquanto há step ativo.
    Ciclo: lê temperatura → calcula PID → aciona ator → aguarda → repete
    """
    step = session.current_step
    vessel = step.vessel
    
    # Obtém mappings do vessel
    temp_mapping = self._get_mapping(vessel, "sensor_temp")
    heat_mapping = self._get_mapping(vessel, "actor_heat")
    
    pid = PIDController(step.pid_kp, step.pid_ki, step.pid_kd, step.target_temp)
    
    last_time = time.time()
    while step.status == "active" and session.status == "active":
        now = time.time()
        dt = now - last_time
        last_time = now
        
        # Lê temperatura
        temp = self._get_sensor_value(temp_mapping.device_function_id)
        if temp is None:
            self._log(session, "error", "pid", f"Sensor offline: {temp_mapping.label}")
            time.sleep(5)
            continue
        
        # Calcula PID
        output = pid.compute(temp, dt)
        
        # Aciona ator (PWM ou ON/OFF com histerese)
        if step.pid_enabled:
            self._set_actor_pwm(heat_mapping.device_function_id, output)
        else:
            # Histerese simples: ±0.5°C
            if temp < step.target_temp - 0.5:
                self._set_actor_onoff(heat_mapping.device_function_id, "ON")
            elif temp > step.target_temp + 0.5:
                self._set_actor_onoff(heat_mapping.device_function_id, "OFF")
        
        # Loga ciclo
        self._log(session, "info", "pid", 
                  f"T={temp:.1f}°C SP={step.target_temp}°C PID={output:.2f}")
        
        # Verifica se step deve avançar (tempo atingido)
        elapsed = (datetime.utcnow() - step.started_at).total_seconds()
        if elapsed >= step.duration_seconds:
            self.advance_step(session.id)
            break
        
        time.sleep(5)  # intervalo do ciclo PID (configurável)
```

---

## 📋 TASK-31 — Tela de Monitoramento Analítico de Sessão

**Rota:** `/mash-control/sessoes/<id>/monitoramento`

### Layout da tela analítica:

```
┌────────────────────────────────────────────────────────────────┐
│ 📊 Análise da Sessão: IPA Tropical #5   Status: ● Ativa        │
├────────────────────────────────────────────────────────────────┤
│ LINHA 1: Indicadores Gerais                                    │
│ [🌡64.8°C Mostura] [⏱ 01:23:45 Total] [🔵 Step 2/6: Sacch.] │
├────────────────────────────────────────────────────────────────┤
│ LINHA 2: Gráfico Principal (temperatura vs. tempo da sessão)   │
│ ┌──────────────────────────────────────────────────────────┐  │
│ │  °C 100                                           ─ ─ ─ │  │
│ │      80                                                  │  │
│ │      60  ────────────────────────────────────────────    │  │
│ │      40  /                                               │  │
│ │      20 /                                                │  │
│ │         └─────────────────────────────────────── tempo  │  │
│ │  ● Real  - - Setpoint  ▲ Adição de Lúpulo               │  │
│ └──────────────────────────────────────────────────────────┘  │
├────────────────────────────────────────────────────────────────┤
│ LINHA 3: Timeline de Etapas e Log                              │
│ ┌──────────────────┐  ┌──────────────────────────────────┐   │
│ │ Timeline         │  │ Log Operacional                  │   │
│ │ ✅ MashIn 15min  │  │ 14:32:01 [PID] Relay ON 64.5°C  │   │
│ │ 🔵 Sacch. 60min  │  │ 14:31:58 [USR] Step avançado    │   │
│ │ ⬜ MashOut 10min  │  │ 14:28:33 [AUTO] Regra disparada │   │
│ │ ⬜ Boil 60min    │  │ [Exportar CSV]                  │   │
│ └──────────────────┘  └──────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
```

---

## 📝 TASK-32 — Documentação Completa dos Plugins

### Após cada fase implementada, atualizar/criar os seguintes arquivos:

```
docs/
├── TASK_LOG.md                              # Log de progresso das tasks
├── plugin_device_manager/
│   ├── DEVICE_REGISTRATION.md              # Fluxo completo de cadastro de device
│   ├── MQTT_TOPICS.md                      # Convenção de tópicos MQTT
│   ├── EMULATOR_GUIDE.md                   # Como usar o emulador IoT
│   └── API_REFERENCE.md                    # Endpoints do Device Manager
└── plugin_mash_control/
    ├── DASHBOARD_GAP_ANALYSIS.md            # Análise inicial (TASK-00)
    ├── DASHBOARD_ARCHITECTURE.md           # Diagrama de componentes e fluxo
    ├── DASHBOARD_WIDGETS.md                # Catálogo de widgets com config e exemplos
    ├── AUTOMATION_ENGINE.md                # Como criar regras, exemplos, limitações
    ├── BREW_PLANT_GUIDE.md                 # Fluxo de cadastro de planta
    ├── SESSION_EXECUTION.md                # Como executar uma sessão, PID, steps
    ├── STANDBY_MODE.md                     # Configuração do modo stand-by
    ├── SVG_COMPONENTS.md                   # Guia para criar novos SVGs
    ├── MODELS_DASHBOARD.md                 # Documentação dos modelos de dados
    └── DEVELOPMENT_GUIDE.md               # Como adicionar widgets e funcionalidades
```

### Template padrão para cada documento:

```markdown
# [Nome do Documento]

> Plugin: plugin_xxx
> Versão: 1.0
> Última atualização: DD/MM/AAAA

## Sumário
- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Configuração](#configuração)
- [Uso](#uso)
- [Exemplos](#exemplos)
- [Referência de API](#referência-de-api)
- [Solução de Problemas](#solução-de-problemas)

## Visão Geral
[2-3 parágrafos descrevendo a funcionalidade]

## Diagrama
[Diagrama Mermaid quando aplicável]

## Exemplos
[Exemplos concretos e executáveis]
```

---

## 📁 TASK-33 — Estrutura Final de Arquivos e Revisão

Ao finalizar toda a implementação, a estrutura deve ser:

```
src/plugins/plugin_device_manager/
├── __init__.py
├── models.py                          # + EmulatedDevice
├── routes.py                          # + rotas do emulador
├── services/
│   ├── mqtt_service.py               # existente
│   └── emulator_service.py           # NOVO
└── templates/
    └── plugin_device_manager/
        └── emulator.html              # NOVO

src/plugins/plugin_mash_control/
├── __init__.py                        # + AutomationEngine.start() + SessionEngine
├── models.py                          # + todos os novos modelos
├── routes.py                          # + todas as novas rotas (ou routes/ dividido)
├── services/
│   ├── automation_engine.py           # NOVO
│   ├── session_engine.py              # NOVO
│   └── pid_controller.py             # NOVO
├── static/
│   ├── css/
│   │   └── dashboard.css
│   ├── js/
│   │   ├── dashboard_canvas.js
│   │   ├── dashboard_widget_registry.js
│   │   ├── dashboard_widgets.js       # todas as classes de widget
│   │   ├── dashboard_config_modal.js
│   │   ├── dashboard_side_panel.js
│   │   ├── automation_rules.js
│   │   └── standby_manager.js
│   └── svg/
│       ├── components/               # todos os SVGs
│       └── catalog.json
└── templates/
    └── plugin_mash_control/
        ├── dashboard.html
        ├── automation_rules.html
        ├── brew_plant.html
        └── session_monitor.html
```

---

## ✅ CHECKLIST FINAL DE IMPLEMENTAÇÃO

### Fase 0 — Reconhecimento
- [ ] TASK-00: GAP Analysis concluída, TASK_LOG.md criado

### Fase 1 — Modelos
- [ ] TASK-01: DashboardLayout + DashboardWidget (com todos os widget_types)
- [ ] TASK-02: AutomationRule + AutomationRuleLog
- [ ] TASK-03: BrewPlant + BrewPlantVessel + BrewPlantMapping
- [ ] TASK-04: BrewSession expandido + Steps + Log + Alarm
- [ ] Todas as tabelas com prefixo correto do sistema de plugins

### Fase 2 — API Backend
- [ ] TASK-05: CRUD Layouts + Widgets + batch save
- [ ] TASK-06: SSE live data + polling fallback + sensor history
- [ ] TASK-07: CRUD AutomationRules + toggle + logs
- [ ] TASK-08: CRUD BrewPlant + vessels + mappings
- [ ] TASK-09: Session execution (start/pause/resume/advance/abort)
- [ ] TASK-10: Emulador IoT (start/stop/config/inject)

### Fase 3 — SVGs
- [ ] TASK-11: 7 vessels SVG
- [ ] TASK-12: 10 equipamentos SVG
- [ ] TASK-13: 5 sensores SVG
- [ ] TASK-14: catalog.json completo

### Fase 4 — Canvas Frontend
- [ ] TASK-15: Canvas base (render, zoom, pan)
- [ ] TASK-16: Live data binding em todos os widgets
- [ ] TASK-17: Modo edit (drag, resize, rotate)
- [ ] TASK-18: Catálogo lateral + drag-to-canvas
- [ ] TASK-19: Widgets de conteúdo livre (TEXT, IMAGE, SEPARATOR, STATUS_BOX)
- [ ] TASK-20: Widgets analíticos (GAUGE, CHART, LOG_PANEL, ALARM_PANEL, STEP_PROGRESS)

### Fase 5 — Modais e UX
- [ ] TASK-21: Modal de configuração (4 abas)
- [ ] TASK-22: Painel lateral operativo

### Fase 6 — Automação
- [ ] TASK-23: AutomationEngine rodando em background
- [ ] TASK-24: Tela de gerenciamento de regras

### Fase 7 — Emulador
- [ ] TASK-25: Backend do emulador (modelos + serviço)
- [ ] TASK-26: Painel de controle do emulador

### Fase 8 — Stand-by
- [ ] TASK-27: Backend stand-by (playlist, config)
- [ ] TASK-28: Frontend stand-by (rotação, fullscreen, ESC para sair)

### Fase 9 — Fluxo de Brassagem
- [ ] TASK-29: BrewPlant wizard de cadastro
- [ ] TASK-30: SessionEngine com PID e steps
- [ ] TASK-31: Tela de monitoramento analítico

### Fase 10 — Documentação
- [ ] TASK-32: Todos os docs criados/atualizados
- [ ] TASK-33: Estrutura de arquivos revisada, TASK_LOG.md completo

---

## 🔒 REGRAS E RESTRIÇÕES GLOBAIS

1. **Não modificar o core** (`src/core/`, `src/main.py`). Use apenas interfaces de plugin.
2. **Não duplicar infraestrutura** do Device Manager. Sempre consuma sua API interna.
3. **Prefixo de tabelas** obrigatório. `mc_` para Mash Control, confirme prefixo do Device Manager.
4. **Uma Task por sessão** de trabalho. Não misture Tasks no mesmo commit.
5. **Ler antes de escrever.** Sempre leia os arquivos existentes antes de modificar.
6. **Documentação junto.** Cada Task atualiza o documento correspondente em `docs/`.
7. **Erros HTTP.** Retorne sempre `{"error": "mensagem", "code": "SNAKE_CODE"}` com HTTP status correto.
8. **CSRF.** Proteger todas as rotas POST/PUT/DELETE com o mecanismo já existente no projeto.
9. **Compatibilidade visual.** Usar Bootstrap + tema escuro + paleta de cores do BrewStation existente.
10. **Commits.** Mensagem: `feat(task-XX): descrição curta em pt-BR`. Um commit por Task.
11. **Sem bibliotecas desnecessárias.** Antes de adicionar uma biblioteca ao requirements.txt ou vendors, verificar se algo equivalente já está no projeto.
12. **Thread safety.** AutomationEngine e SessionEngine rodam em threads. Usar `app.app_context()` e cuidado com SQLAlchemy sessions.

---

*BrewStation — Grupo S2M / S2M Bebidas*
*Prompt v2.0 — Do grão ao copo, com operação rastreável e precificação sob controle. 🍻⚙️*