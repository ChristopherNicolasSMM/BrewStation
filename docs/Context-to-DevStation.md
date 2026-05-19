# BrewStation — Especificação para IA: Addon do DevStation

> **Versão:** 3.0 — Revisão Arquitetural "DevStation Integration"
> **Data:** 2026-05
> **Gerado para uso por agentes de IA, desenvolvedores e geradores de código**

---

## 1. Visão Geral da Nova Arquitetura

O BrewStation **deixa de ser uma aplicação standalone** e passa a ser um **Addon de primeiro nível do DevStation**. Toda a lógica de negócio cervejeiro (catálogo, estoque, precificação, IoT, brassagem) é encapsulada dentro de um único addon chamado `addon_brewstation`, que convive com outros addons no ecossistema DevStation.

Os **antigos plugins do BrewStation** (device_manager, mash_control, yeast_bank, integ_bFather, maker) passam a ser chamados de **Features** (ou Sub-Addons), e seguem o padrão de addons do DevStation, mas com escopo restrito ao domínio BrewStation.

```
DevStation (Hub Principal — Application Factory)
│
├── core/                     ← Infraestrutura DevStation (auth, DB, addon lifecycle)
│   ├── addon_manager.py      ← Orquestrador de Addons (equivale ao PluginManager)
│   ├── addon_loader.py
│   ├── addon_base.py         ← Classe base para todos os Addons
│   └── event_bus.py          ← Sistema de eventos inter-addons (ver seção 6)
│
└── addons/
    ├── addon_brewstation/    ← BrewStation como Addon do DevStation
    │   ├── addon.json        ← Manifesto do Addon (substitui install.json)
    │   ├── addon.py          ← Classe BrewStationAddon(AddonBase)
    │   ├── core/             ← Núcleo BrewStation (catálogo, estoque, dashboard)
    │   ├── features/         ← Sub-Addons / Features habilitáveis
    │   │   ├── feature_device_manager/
    │   │   ├── feature_mash_control/
    │   │   ├── feature_yeast_bank/
    │   │   ├── feature_integ_bfather/
    │   │   └── feature_maker/
    │   ├── model/
    │   ├── services/
    │   ├── templates/
    │   ├── static/
    │   └── menu_config.json
    │
    └── addon_outro/          ← Outros addons DevStation (futuro)
```

---

## 2. Hierarquia de Conceitos

| Nível | Nome Antigo | Nome Novo | Quem Gerencia |
|-------|-------------|-----------|---------------|
| 1 | Aplicação Flask | **DevStation** | Application Factory |
| 2 | — | **Addon** | `AddonManager` (DevStation core) |
| 3 | Plugin BrewStation | **Feature / Sub-Addon** | `FeatureManager` (BrewStation addon) |
| 4 | — | **Hook/Event** | `EventBus` (DevStation core) |

- **Addon**: módulo de alto nível que estende o DevStation. Ex: `addon_brewstation`, `addon_crm`, `addon_financeiro`.
- **Feature**: módulo de médio nível que estende um Addon específico. Ex: `feature_device_manager` estende `addon_brewstation`. São o que antes se chamava de "plugins" do BrewStation.
- **Feature ≠ Plugin independente**: features não têm ciclo de vida próprio no DevStation — elas dependem do addon pai estar ativo.

---

## 3. Manifesto do Addon (`addon.json`)

Substitui o `install.json`. Adiciona campos de contrato com o DevStation:

```json
{
  "name": "brewstation",
  "label": "BrewStation",
  "version": "3.0.0",
  "description": "Plataforma de gestão para cervejarias artesanais",
  "author": "S2M Tech",
  "type": "addon",
  "table_prefix": "brew",
  "devstation_min_version": "1.0.0",
  "dependencies": [],
  "features": [
    {
      "name": "feature_device_manager",
      "label": "Device Manager",
      "table_prefix": "brew_dvm",
      "enabled_by_default": true,
      "requires": []
    },
    {
      "name": "feature_mash_control",
      "label": "Mash Control",
      "table_prefix": "brew_mash",
      "enabled_by_default": false,
      "requires": ["feature_device_manager"]
    },
    {
      "name": "feature_yeast_bank",
      "label": "Yeast Bank",
      "table_prefix": "brew_yeast",
      "enabled_by_default": false,
      "requires": []
    },
    {
      "name": "feature_integ_bfather",
      "label": "BrewFather Integration",
      "table_prefix": "brew_bf",
      "enabled_by_default": false,
      "requires": []
    },
    {
      "name": "feature_maker",
      "label": "Feature Maker",
      "table_prefix": "brew_maker",
      "enabled_by_default": true,
      "requires": []
    }
  ],
  "env_keys": [
    "BREWFATHER_USER_ID",
    "BREWFATHER_API_KEY"
  ]
}
```

**Diferenças em relação ao `install.json` antigo:**
- Campo `"type": "addon"` obrigatório para o DevStation distinguir addons de outras coisas
- Campo `"features"` lista todas as features disponíveis com seus prefixos de tabela **compostos** (`brew_dvm`, `brew_mash`, etc.)
- Campo `"devstation_min_version"` para compatibilidade
- O `table_prefix` do addon (`brew`) é o namespace raiz; features usam `brew_[sigla]`

---

## 4. Prefixo de Tabelas — Hierarquia Tri-nível

```
devstation_[tabela]           ← Tabelas do core DevStation (usuários, sessões, addons)
brew_[tabela]                 ← Tabelas do núcleo BrewStation (maltes, receitas, estoque)
brew_dvm_[tabela]             ← Tabelas da feature Device Manager
brew_mash_[tabela]            ← Tabelas da feature Mash Control
brew_yeast_[tabela]           ← Tabelas da feature Yeast Bank
brew_bf_[tabela]              ← Tabelas da feature BrewFather Integration
```

**Regra de ouro para IAs:** Nunca crie uma tabela sem prefixo. O prefixo deve ser declarado no `addon.json` sob o campo `features[n].table_prefix` e aplicado automaticamente pelo `FeatureManager`.

---

## 5. Classe Base do Addon

```python
# devstation/core/addon_base.py
from abc import ABC, abstractmethod

class AddonBase(ABC):
    """Classe base que todo Addon do DevStation deve herdar."""

    name: str = None           # Identificador único (snake_case)
    label: str = None          # Nome legível
    version: str = "1.0.0"
    table_prefix: str = None   # Prefixo de tabelas do addon

    def __init__(self, app, db, config: dict):
        self.app = app
        self.db = db
        self.config = config
        self._feature_manager = None

    @abstractmethod
    def register_routes(self):
        """Registra Blueprints Flask do addon core."""
        pass

    @abstractmethod
    def register_models(self):
        """Registra/cria tabelas do addon core."""
        pass

    def setup(self):
        """Ponto de entrada chamado pelo AddonManager após instância criada."""
        self.register_models()
        self.register_routes()
        if self._feature_manager:
            self._feature_manager.load_active_features()

    def get_menu_config(self) -> dict:
        """Retorna config de menu do addon + features ativas."""
        pass

    def install(self):
        """Chamado na primeira ativação: cria tabelas, seeds iniciais."""
        pass

    def uninstall(self):
        """Chamado ao desinstalar: remove tabelas (com cuidado)."""
        pass
```

```python
# addons/addon_brewstation/addon.py
from devstation.core.addon_base import AddonBase
from .core.feature_manager import FeatureManager

class BrewStationAddon(AddonBase):
    name = "brewstation"
    label = "BrewStation"
    version = "3.0.0"
    table_prefix = "brew"

    def __init__(self, app, db, config):
        super().__init__(app, db, config)
        self._feature_manager = FeatureManager(self)

    def register_routes(self):
        from .core.controllers import brew_core_bp
        self.app.register_blueprint(brew_core_bp, url_prefix="/brew")

    def register_models(self):
        from .model import init_core_models
        init_core_models(self.db, self.table_prefix)
```

---

## 6. Sistema de Features (Sub-Addons)

### 6.1 Estrutura de uma Feature

```
addons/addon_brewstation/features/feature_device_manager/
├── feature.json          ← Manifesto da feature (substitui install.json do plugin)
├── feature.py            ← Classe FeatureDeviceManager(FeatureBase)
├── model/                ← Modelos SQLAlchemy com prefixo brew_dvm_
├── controller/           ← Blueprints Flask da feature
├── services/             ← Serviços de negócio
├── templates/            ← Templates Jinja2 da feature
├── static/               ← JS/CSS específicos
├── menu_config.json      ← Itens de menu injetados quando ativa
└── docs/
```

### 6.2 `feature.json` — Manifesto da Feature

```json
{
  "name": "feature_device_manager",
  "label": "Device Manager",
  "version": "1.0.0",
  "description": "Gerenciamento de dispositivos IoT com broker MQTT embutido",
  "table_prefix": "brew_dvm",
  "enabled": true,
  "requires": [],
  "provides": ["mqtt_broker", "device_api"],
  "settings": {
    "mqtt_port": 1883,
    "mqtt_host": "localhost"
  }
}
```

**Campo `provides`**: declara capacidades que outras features podem requisitar via EventBus (ver seção 8).

### 6.3 Classe Base de Feature

```python
# addons/addon_brewstation/core/feature_base.py
from abc import ABC, abstractmethod

class FeatureBase(ABC):
    name: str = None
    label: str = None
    table_prefix: str = None
    enabled: bool = False

    def __init__(self, addon: 'BrewStationAddon'):
        self.addon = addon
        self.app = addon.app
        self.db = addon.db

    @abstractmethod
    def register_routes(self):
        pass

    @abstractmethod
    def register_models(self):
        pass

    def setup(self):
        self.register_models()
        self.register_routes()
 
    def enable(self):
        """Ativa a feature — persiste no DB, registra blueprints."""
        pass

    def disable(self):
        """Desativa a feature — marca inativa no DB, unregistra rotas na próxima carga."""
        pass

    def get_menu_items(self) -> list:
        pass
```

### 6.4 Exemplo: Feature Device Manager

```python
# features/feature_device_manager/feature.py
from ...core.feature_base import FeatureBase

class FeatureDeviceManager(FeatureBase):
    name = "feature_device_manager"
    label = "Device Manager"
    table_prefix = "brew_dvm"

    def register_routes(self):
        from .controller.device_web import device_web_bp
        from .controller.device_api import device_api_bp
        self.app.register_blueprint(device_web_bp, url_prefix="/brew/devices")
        self.app.register_blueprint(device_api_bp, url_prefix="/api/brew/devices")

    def register_models(self):
        from .model import DeviceMetadata, DeviceLog
        # Auto-prefix aplicado pelo FeatureManager
```

---

## 7. FeatureManager — Orquestrador das Features

O `FeatureManager` reside dentro do BrewStation (não no DevStation core), e é responsável pelo ciclo de vida das features:

```python
# addons/addon_brewstation/core/feature_manager.py
import json, importlib
from pathlib import Path

class FeatureManager:
    """
    Gerencia o ciclo de vida das Features do BrewStation.
    Equivale ao antigo PluginManager, mas scoped ao addon_brewstation.
    """

    FEATURES_DIR = Path(__file__).parent.parent / "features"

    def __init__(self, addon):
        self.addon = addon
        self._registry: dict[str, FeatureBase] = {}

    def discover(self) -> list[dict]:
        """Descobre todas as features disponíveis no diretório /features."""
        features = []
        for d in self.FEATURES_DIR.iterdir():
            if d.is_dir() and (d / "feature.json").exists():
                with open(d / "feature.json") as f:
                    features.append(json.load(f))
        return features

    def load_active_features(self):
        """Carrega e inicializa apenas features marcadas como enabled no DB."""
        active = self._get_active_from_db()
        for feature_name in active:
            self._load_feature(feature_name)

    def _load_feature(self, name: str):
        module = importlib.import_module(
            f"addons.addon_brewstation.features.{name}.feature"
        )
        cls = module.__feature__   # variável __feature__ obrigatória no feature.py
        instance = cls(self.addon)
        instance.setup()
        self._registry[name] = instance

    def enable_feature(self, name: str) -> bool:
        """Habilita uma feature e persiste no DB. Requer reload da aplicação."""
        # 1. Valida dependências
        # 2. Persiste enabled=True no DB
        # 3. Retorna True + flag "reload_required"
        pass

    def disable_feature(self, name: str) -> bool:
        """Desabilita. Marca no DB. Blueprints desregistrados no próximo boot."""
        pass

    def get_all_menu_items(self) -> list:
        """Coleta menu_config.json de todas as features ativas."""
        items = []
        for feature in self._registry.values():
            items.extend(feature.get_menu_items())
        return items

    def _get_active_from_db(self) -> list[str]:
        from ..model.brew_feature_state import BrewFeatureState
        return [f.name for f in BrewFeatureState.query.filter_by(enabled=True).all()]
```

**Tabela de controle de features (persistência):**

```python
# model/brew_feature_state.py
class BrewFeatureState(db.Model):
    __tablename__ = "brew_feature_state"   # prefixo brew_ aplicado
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    enabled = db.Column(db.Boolean, default=False)
    version = db.Column(db.String(20))
    installed_at = db.Column(db.DateTime)
    settings_json = db.Column(db.Text)     # JSON de configurações por feature
```

---

## 8. Sistema de Eventos (EventBus) — Integração Flask-Plugins

### 8.1 Análise da Biblioteca Flask-Plugins 2.0.0

**Status atual (maio 2026):** versão 2.0.0 foi lançada em 11/05/2026. Requer Python ≥ 3.10. Licença BSD-3.

**O que a biblioteca oferece:**
- `PluginManager` — gerencia plugins por pasta com arquivos `DISABLED`
- `EventManager` — sistema de eventos `emit_event` / `connect_event`
- Suporte a templates Jinja2 com `{{ emit_event("nome") }}`
- Padrão `info.json` para metadados

**Veredicto — O que ADOTAR vs REJEITAR:**

| Componente | Decisão | Motivo |
|------------|---------|--------|
| `PluginManager` | ❌ **NÃO USAR** | O DevStation já possui AddonManager mais sofisticado; Flask-Plugins usa arquivo `DISABLED` em disco, requer restart, sem resolução de dependências, sem prefixo de tabelas |
| `EventManager` / `EventBus` | ✅ **ADOTAR** | Sistema de `emit_event` / `connect_event` é elegante, desacopla addons, suporta templates Jinja2 — exatamente o que o BrewStation precisa para comunicação inter-features |
| `info.json` | ⚠️ **INSPIRAÇÃO** | O `addon.json` / `feature.json` do DevStation já é mais rico, mas a estrutura de campos é compatível |

### 8.2 Implementação do EventBus no DevStation

```python
# devstation/core/event_bus.py
# Wrapper sobre flask_plugins.EventManager para uso no DevStation
from flask_plugins import connect_event, emit_event, iter_listeners

class DevStationEventBus:
    """
    Barramento de eventos para comunicação desacoplada entre Addons e Features.
    Usa o EventManager do Flask-Plugins 2.0.0 como backend.
    """

    @staticmethod
    def on(event_name: str, callback, position='after'):
        """Registra um handler para um evento."""
        connect_event(event_name, callback, position)

    @staticmethod
    def emit(event_name: str, *args, **kwargs) -> list:
        """Dispara um evento e retorna lista de resultados."""
        return emit_event(event_name, *args, **kwargs)

    @staticmethod
    def listeners(event_name: str):
        """Itera sobre handlers de um evento."""
        return iter_listeners(event_name)

# Instância global
event_bus = DevStationEventBus()
```

### 8.3 Uso de Eventos entre Features

```python
# feature_device_manager: publica evento quando dispositivo muda de estado
from devstation.core.event_bus import event_bus

def on_device_status_change(device_id, status):
    event_bus.emit("brew.device.status_changed", device_id=device_id, status=status)

# feature_mash_control: reage ao evento sem importar device_manager diretamente
event_bus.on("brew.device.status_changed", handle_device_status)

def handle_device_status(device_id, status):
    # Atualiza dashboard de brassagem
    pass
```

**Convenção de nomes de eventos BrewStation:**
```
brew.[domínio].[ação]

brew.device.status_changed
brew.device.reading_received
brew.session.started
brew.session.step_completed
brew.session.finished
brew.inventory.low_stock
brew.brewfather.sync_completed
brew.feature.enabled
brew.feature.disabled
```

### 8.4 Eventos em Templates Jinja2

Flask-Plugins injeta `emit_event` no contexto Jinja2 automaticamente. Isso permite que features injetem conteúdo em templates do addon core:

```html
<!-- templates/brew/dashboard.html (addon core) -->
<div class="dashboard-widgets">
  {{ emit_event("brew.dashboard.widgets") | safe }}
</div>
```

```python
# feature_mash_control conecta ao evento de template
def render_mash_widget():
    return render_template("feature_mash_control/dashboard_widget.html")

event_bus.on("brew.dashboard.widgets", render_mash_widget)
```

---

## 9. Regras para IAs — Geração de Código

### 9.1 Regras Absolutas

1. **Nunca modifique `devstation/core/`** — toda lógica nova vai em `addons/addon_brewstation/` ou em suas features.

2. **Nunca crie tabelas sem prefixo tri-nível**: core BrewStation usa `brew_`, features usam `brew_[sigla]_`. Exemplos:
   - ✅ `brew_recipe` — tabela do core BrewStation
   - ✅ `brew_dvm_device` — tabela da feature device_manager
   - ❌ `device` — proibido
   - ❌ `brew_device` — pertence ao core, não à feature

3. **Toda feature deve declarar `__feature__`** no arquivo `feature.py`:
   ```python
   __feature__ = "FeatureDeviceManager"
   ```

4. **Blueprints devem usar `url_prefix` com `/brew/`** para rotas web e `/api/brew/` para REST.

5. **Features não se importam diretamente entre si** — usam `event_bus.emit` / `event_bus.on` ou o `model_loader` para acesso a dados.

6. **Não use `flask_plugins.PluginManager`** — use apenas `flask_plugins.connect_event`, `emit_event`, `iter_listeners`.

### 9.2 Estrutura Obrigatória de uma Nova Feature

```
features/feature_[nome]/
├── __init__.py
├── feature.json           ← OBRIGATÓRIO: metadados, table_prefix, requires, provides
├── feature.py             ← OBRIGATÓRIO: classe + __feature__ = "ClasseName"
├── menu_config.json       ← OBRIGATÓRIO: itens de menu (pode ser lista vazia [])
├── model/
│   ├── __init__.py
│   └── [nome]_models.py   ← Modelos com __tablename__ = f"{table_prefix}_[entidade]"
├── controller/
│   ├── __init__.py
│   ├── [nome]_web.py      ← Blueprint web (url_prefix="/brew/[nome]")
│   └── [nome]_api.py      ← Blueprint REST (url_prefix="/api/brew/[nome]")
├── services/
│   └── [nome]_service.py
├── templates/
│   └── feature_[nome]/
│       └── index.html
└── docs/
    └── README.md
```

### 9.3 Checklist de Validação

Antes de gerar código para uma feature, verificar:

- [ ] `feature.json` existe com `name`, `table_prefix`, `version`, `requires`, `provides`
- [ ] `__feature__` declarado no `feature.py`
- [ ] Todos os `__tablename__` usam o `table_prefix` correto
- [ ] Blueprints registrados em `register_routes()` da feature
- [ ] Eventos emitidos/consumidos declarados na documentação da feature
- [ ] `menu_config.json` presente (mesmo que vazio)
- [ ] Sem imports diretos de outras features (usar event_bus ou model_loader)

---

## 10. Feature Maker — Gerador de Sub-Addons

O antigo `plugin_maker` torna-se `feature_maker` e continua gerando scaffolding, agora adaptado ao novo padrão:

```bash
# CLI DevStation
devstation brew feature create [nome]    # Gera estrutura completa de uma feature
devstation brew feature list             # Lista features e status
devstation brew feature enable [nome]    # Habilita feature (persiste no DB)
devstation brew feature disable [nome]   # Desabilita feature
devstation brew feature info [nome]      # Detalhes e dependências

# Compatibilidade legada (mantida para transição)
flask plugin list          → devstation brew feature list
flask plugin install       → devstation brew feature enable
flask plugin activate      → devstation brew feature enable
```

**Template gerado pelo Maker:**

O Maker lê um template interno e gera todos os arquivos da estrutura obrigatória (seção 9.2) com os nomes corretos, `table_prefix` calculado, classe base herdada, e documentação inicial. Equivale ao antigo `python run.py plugin -c` mas agora via `devstation brew feature create`.

---

## 11. Compatibilidade e Migração

### 11.1 Renomeações de Artefatos

| Antigo (BrewStation standalone) | Novo (BrewStation como Addon) |
|--------------------------------|-------------------------------|
| `src/plugins/plugin_[nome]/` | `addons/addon_brewstation/features/feature_[nome]/` |
| `install.json` | `feature.json` |
| `PluginBase` | `FeatureBase` |
| `PluginManager` | `FeatureManager` |
| `flask plugin list` | `devstation brew feature list` |
| `table_prefix: "dvmanage"` | `table_prefix: "brew_dvm"` |
| `dvmanage_device_metadata` | `brew_dvm_device_metadata` |

### 11.2 O que NÃO muda

- Estrutura interna MVC de cada feature (model, controller, services, templates)
- Auto-prefixing de tabelas SQLAlchemy (mecânica idêntica, prefixos diferentes)
- Template precedence loader (feature > addon core > devstation global)
- `menu_config.json` (formato idêntico)
- Integração BrewFather, MQTT, SMTP (encapsulados nas features correspondentes)

---

## 12. Variáveis de Ambiente

```env
# DevStation Core (gerenciado pelo DevStation)
SECRET_KEY=
FLASK_ENV=DEV|PRD
DATABASE_URL=

# Addon BrewStation (adicionadas ao .env quando addon instalado)
BREWFATHER_USER_ID=
BREWFATHER_API_KEY=

# Feature Device Manager (adicionadas quando feature habilitada)
MQTT_HOST=localhost
MQTT_PORT=1883

# Feature Notificações/SMTP (compartilhado com DevStation)
MAIL_SERVER=
MAIL_PORT=
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_USE_TLS=true
```

---

## 13. Logs

```
logs/
├── devstation.log          ← Core DevStation
├── errors.log              ← Erros globais
├── brew_core.log           ← Addon BrewStation (núcleo)
├── brew_devices.log        ← Feature device_manager
├── brew_sessions.log       ← Feature mash_control
└── brew_sync.log           ← Feature integ_bfather
```

---

## 14. Resumo para Agentes de IA

Se você é uma IA gerando código para o BrewStation integrado ao DevStation:

1. **BrewStation é um Addon** → sua classe está em `addons/addon_brewstation/addon.py` herdando `AddonBase`.
2. **Os antigos "plugins" são Features** → ficam em `addons/addon_brewstation/features/feature_[nome]/`.
3. **Prefixo de tabelas é tri-nível**: `devstation_` (core), `brew_` (addon), `brew_[sigla]_` (feature).
4. **Comunicação entre features via EventBus** → `event_bus.emit()` / `event_bus.on()` usando Flask-Plugins 2.0.0 apenas para o sistema de eventos (não use o PluginManager do Flask-Plugins).
5. **Feature Maker** gera scaffolding via `devstation brew feature create [nome]`.
6. **Habilitação de features é persistida em banco** na tabela `brew_feature_state`, não por arquivo DISABLED em disco.
7. **Nunca modifique `devstation/core/`** — todo código novo fica dentro do addon ou das features.
8. **`__feature__` é obrigatório** no `feature.py` de cada feature (equivale ao `__plugin__` do Flask-Plugins).
9. **Blueprints usam url_prefix `/brew/`** (web) e `/api/brew/` (REST).
10. **Imports cruzados entre features são proibidos** — use event_bus ou model_loader.