A seguir está a **especificação (design doc)** do *Plugin Maker* (com ALV-like grids) e, ao final, um **backlog em `.md`** pronto para você salvar como arquivo.

---

## DESIGN DOC — Plugin Maker (Plugin Forge) para BrewStation

### Objetivo

Criar um plugin “maker” que:

1. **Lista plugins existentes** e seus status (instalado/ativo).
2. Permite **criar/editar um “projeto de plugin”**: tabelas, colunas, relações, telas, seções e campos.
3. Permite **importar Excel** (schema) e gerar tabelas/colunas automaticamente.
4. Gera plugins no padrão BrewStation: **models + API + templates NiceAdmin + JS separado + menu + export/import**.
5. Inclui um **Grid estilo ALV (SAP)**: filtros, ordenação, agrupamento, agregações (sum/avg/min/max/count), variantes de layout e export.

---

# 1) Metamodelo completo (tabelas Maker)

> **Nota:** estas são as tabelas internas do plugin maker. Elas descrevem “o plugin-alvo” (o que será gerado). O Maker pode gerenciar **vários projetos**.

## 1.1 Entidades do projeto e geração

### `maker_project`

* `id` (PK)
* `plugin_dir` (ex: `plugin_sales`)
* `plugin_name` (nome lógico em `install.json`, ex: `sales`)
* `label` (ex: “Vendas”)
* `version`
* `description`
* `author`
* `license`
* `table_prefix` (ex: `sales`)
* `menu_config_path` (default `menu_config.json`)
* `status` enum: `draft | generated | synced | error`
* `generation_mode` enum: `full_overwrite | guarded_blocks`
* `created_at`, `updated_at`

### `maker_generation_run`

* `id` (PK)
* `project_id` (FK)
* `run_type` enum: `preview | generate | rebuild | sync`
* `result` enum: `success | warning | error`
* `diff_summary` (text/json)
* `log` (text)
* `created_at`

---

## 1.2 Modelo de dados (tabelas/colunas/relações)

### `maker_table`

* `id` (PK)
* `project_id` (FK)
* `name` (snake_case) — nome lógico (ex: `customer`)
* `db_table_name` (opcional) — se quiser fixar `__tablename__` diferente
* `label` (humano) — “Clientes”
* `description`
* `pk_strategy` enum: `int | uuid`
* `timestamps` bool (created_at/updated_at)
* `soft_delete` bool (deleted_at)
* `default_order_by` (ex: `created_at desc`)
* `created_at`, `updated_at`

### `maker_column`

* `id` (PK)
* `table_id` (FK)
* `name` (snake_case)
* `label`
* `description/help_text`
* `data_type` enum:

  * `string, text, int, float, decimal, bool, date, datetime, json, enum, uuid`
* `length` (para string)
* `precision`, `scale` (decimal)
* `required` bool
* `unique` bool
* `indexed` bool
* `default_value` (string; interpretado por tipo)
* `is_primary_key` bool
* `is_foreign_key` bool
* `fk_target_table_id` (FK maker_table)
* `fk_target_column_name` (string; default `id`)
* `on_delete` enum: `restrict | cascade | set_null`
* `ui_widget_hint` enum:

  * `text, textarea, number, money, percent, date, datetime, checkbox, select, multiselect`
* `ui_options_json` (ex: options de select)
* `created_at`, `updated_at`

### `maker_relation`

* `id` (PK)
* `project_id` (FK)
* `relation_type` enum: `many_to_one | one_to_many | many_to_many`
* `from_table_id`, `to_table_id`
* `fk_column_id` (quando many_to_one)
* `backref_name` (string)
* `join_table_name` (many_to_many)
* `created_at`

**MVP recomendação:** suportar bem `many_to_one` (FK) + backref automático. `many_to_many` fica v2.

---

## 1.3 UI: telas, seções, campos, abas

### `maker_screen`

* `id` (PK)
* `project_id` (FK)
* `name` (slug) — `customers`
* `title` — “Clientes”
* `screen_type` enum: `crud | dashboard | custom`
* `base_table_id` (FK maker_table) — para CRUD
* `route_path` (ex: `/customers`)
* `menu_group` (ex: “Cadastros”)
* `menu_label`
* `menu_icon` (Bootstrap icon class, ex: `bi bi-people`)
* `enabled` bool
* `created_at`, `updated_at`

### `maker_tab_group`

* `id` (PK)
* `screen_id` (FK)
* `label` — “Detalhes”
* `icon`
* `order`
* `enabled`

### `maker_tab`

* `id` (PK)
* `tab_group_id` (FK)
* `label`
* `icon`
* `order`
* `enabled`

### `maker_section`

* `id` (PK)
* `screen_id` (FK)
* `tab_id` (nullable) — se section fica dentro de uma aba
* `title`
* `icon`
* `order`
* `width_12` int 1..12 (layout do container)
* `layout_type` enum:

  * `form_card | table_card | kpi_card | text_card | grid_card`
* `style_variant` (ex: `info-card`, `revenue-card`, etc.)
* `description`
* `enabled`

### `maker_field_placement`

* `id` (PK)
* `section_id` (FK)
* `column_id` (FK maker_column) **ou** `computed_field_id` (FK)
* `label_override`
* `icon`
* `help_text_override`
* `order`
* `width_12` int 1..12
* `visible_on` enum flags: `list, create, edit, details`
* `editable` bool
* `required_override` bool/nullable
* `widget_override` enum/nullable
* `format_override` enum: `money, percent, date, datetime`
* `enabled`

---

## 1.4 Campos calculados (primeira classe)

### `maker_computed_field`

* `id` (PK)
* `project_id`
* `table_id` (FK maker_table) — onde ele “vive”
* `name` (snake_case)
* `label`
* `data_type` (mesmo enum)
* `mode` enum:

  * `ui` (JS-only)
  * `api` (calculado no backend ao ler)
  * `persisted` (gravado em coluna real / mantido em write)
* `expression` (string)
* `deps_json` (lista de colunas de dependência)
* `cache_policy` enum:

  * `none | request | persisted`
* `enabled`

---

## 1.5 ALV-like Grid (layout, agrupamento, agregações, variantes)

> Isto é o diferencial para “tabelas” (list screens) e export.

### `maker_grid_view`

* `id` (PK)
* `screen_id` (FK maker_screen) — normalmente screen_type=crud/list
* `label` — “Lista padrão”
* `default_variant_id` (FK maker_grid_variant)
* `enable_grouping` bool
* `enable_aggregations` bool
* `enable_column_freeze` bool (v2)
* `enable_column_reorder` bool
* `enable_multi_sort` bool
* `enable_export` bool
* `created_at`

### `maker_grid_column`

* `id` (PK)
* `grid_view_id` (FK)
* `source_type` enum: `column | computed`
* `column_id` / `computed_field_id`
* `label_override`
* `order`
* `width_px` (nullable)
* `align` enum: `left | right | center`
* `format` enum: `text | money | percent | date | datetime`
* `visible` bool
* `sortable` bool
* `filterable` bool
* `groupable` bool
* `aggregatable` bool
* `created_at`

### `maker_grid_aggregation`

* `id` (PK)
* `grid_view_id` (FK)
* `column_ref` (grid_column_id)
* `agg_type` enum: `sum | avg | min | max | count`
* `show_in_footer` bool
* `show_in_group_header` bool

### `maker_grid_variant`

* `id` (PK)
* `grid_view_id`
* `name` — “Minha visão”
* `owner` (user_id/email, opcional)
* `is_shared` bool
* `config_json` (col order/visibility/sort/group/filters)
* `created_at`

**MVP**: variantes armazenadas no banco do Maker (por usuário), export CSV/JSON respeitando “visão atual”.

---

# 2) Contratos de geração (como sai um CRUD padrão)

## 2.1 Estrutura de pastas gerada para o plugin-alvo

Para um plugin gerado `plugin_sales` (name=`sales`):

* `src/plugins/plugin_sales/install.json`
* `src/plugins/plugin_sales/menu_config.json`
* `src/plugins/plugin_sales/plugin.py`
* `src/plugins/plugin_sales/model/<tables>.py`
* `src/plugins/plugin_sales/utils/model_loader.py`
* `src/plugins/plugin_sales/api/routes/__init__.py`
* `src/plugins/plugin_sales/api/routes/<crud>_routes.py`
* `src/plugins/plugin_sales/controller/routes.py`
* `src/plugins/plugin_sales/templates/<slug>/*.html`
* `src/plugins/plugin_sales/static/js/*.js`
* `src/plugins/plugin_sales/static/css/*.css` (opcional)

## 2.2 Padrão de CRUD

Para cada tabela marcada como “CRUD screen”:

### API

* `GET    /<entity>` list
* `POST   /<entity>` create
* `GET    /<entity>/<id>` details (v2 opcional)
* `PUT    /<entity>/<id>` update
* `DELETE /<entity>/<id>` delete (com bloqueios 409 quando houver dependências)
* `GET /<entity>/export/csv`
* `GET /<entity>/export/json`
* `POST /<entity>/import/json` (v2; por ora import no front via POST item a item)

### Web

* Template list com:

  * toolbar (Novo / Export CSV / Export JSON / Import JSON)
  * filtros (colunas configuradas como filterable)
  * tabela com actions (edit/delete)
  * modal bootstrap (create/edit)
* JS separado em:

  * `/plugin/<plugin_name>/static/js/<screen>.js`

### Data grid

No MVP vocês já usam Simple-DataTables. Para ALV-like, o Maker pode:

* continuar Simple-DataTables para base
* adicionar camada de:

  * agrupamento + agregação + variantes (controlada por JS + API)
    Se quiser “ALV forte”, no futuro pode migrar para Tabulator/AG Grid, mas MVP fica com Simple + extensão própria.

---

# 3) Padrões obrigatórios (prefixos API, static, model_loader)

## 3.1 Prefixo API

**Regra:** rotas dentro do blueprint **NUNCA** incluem o nome do plugin.

* Blueprint define `/items`, `/strains`, etc.
* O core aplica prefixo: `/api/<plugin_name>` (via PluginManager). ([raw.githubusercontent.com](https://raw.githubusercontent.com/ChristopherNicolasSMM/BrewStation/main/src/core/plugin_manager.py))

✅ Gerador deve criar:

* `@bp.get("/items")`, etc.

## 3.2 Static por plugin

**Regra:** JS/CSS do plugin fica em `static/` do plugin e é servido por:

* `/plugin/<plugin_name>/static/...` ([raw.githubusercontent.com](https://raw.githubusercontent.com/ChristopherNicolasSMM/BrewStation/main/src/core/plugin_manager.py))

✅ Templates devem carregar:

```html
<script src="/plugin/<plugin_name>/static/js/<file>.js"></script>
```

## 3.3 model_loader e prefixos de tabela

O BrewStation prefixa tabelas para evitar conflitos. (`plugin_db_helper`) e usa registry.
✅ Regra para gerador:

* `PLUGIN_NAME` no model_loader = **plugin_name do install.json** (ex: `yeast_bank`)
* CRUD/rotas devem usar `get_prefixed_model()` ao invés de importar model “cru” diretamente.

---

# 4) Especificação de computed fields (modes + grammar + deps)

## 4.1 Modos

* `ui`: calculado no JS (melhor UX, sem persistência)
* `api`: calculado no backend no `GET list/details`
* `persisted`: calculado no backend ao salvar e armazenado em coluna real

## 4.2 Grammar (expressões seguras)

Sem `eval`. Use gramática limitada:

### Tokens permitidos

* números: `123`, `12.5`
* campos: `row.<field>`
* config: `cfg.<key>`
* funções: `min(a,b)`, `max(a,b)`, `round(x,2)`, `abs(x)`
* operadores: `+ - * / ( )`
* condicionais (v2): `if(cond, a, b)`

Exemplos:

* `row.prepared_date + cfg.expiry_work_days`
* `round(row.price * row.qty, 2)`
* `max(row.a, row.b)`

## 4.3 Dependências

* `deps_json`: lista de colunas usadas.
* O Maker valida:

  * campo existe
  * tipo compatível
  * não há ciclo (grafo acíclico)

## 4.4 Eficiência

* `ui`: recalcular apenas ao mudar dependências (event listeners nos inputs)
* `api`: compute em lote no backend (uma passagem por linha)
* `persisted`: recalcular somente se dependências mudarem (diff no update)

---

# 5) Mapa de telas do Maker (fluxo completo)

## 5.1 Navegação principal

**Maker Home**

* Lista plugins existentes (lidos do FS)
* Lista projetos do Maker (draft/generated)
* Botões: Novo Projeto, Rebuild, Ver Logs

## 5.2 Wizard de projeto

**Projeto**

* campos: plugin_dir, plugin_name, label, prefix, version
* validação: nomes, conflito, diretório existente

## 5.3 Dados

**Tabelas**

* lista tabelas, criar, excluir, importar Excel

**Tabela → Colunas**

* criar coluna
* definir tipo, required, etc.
* criar FK
* preview do model

## 5.4 UI

**Telas**

* criar tela CRUD
* escolher tabela base
* menu label/icon/group
* tabs (opcional)
* sections (cards/forms)
* field placements (grid 12 col)

## 5.5 Grid ALV

**Grid**

* escolher colunas visíveis
* habilitar sort/filter/group
* definir agregações (sum/avg/…)
* salvar variantes

## 5.6 Geração

**Rebuild**

* preview de arquivos
* aplicar geração
* log/diff

---

# 6) ALV-like (agrupamento, soma, export) — como encaixar sem “muito trabalho”

### MVP ALV-like (realista)

* Agrupar por 1 coluna (v1), multi-group (v2)
* Agregações por coluna (sum/count) no footer
* “Variant” salva no Maker (por usuário)
* Export CSV/JSON respeitando:

  * colunas visíveis
  * ordem
  * filtros (opcional v2)
  * agregações não entram no export (exporta dados; agrega no final opcional)

### Implementação sugerida (eficiente)

* Para datasets pequenos/médios: agregação no JS (rápido)
* Para datasets grandes: endpoint `/grid/query` com:

  * filtros
  * sort
  * group
  * aggregation server-side
    (MVP pode ficar client-side e evoluir depois.)

---

# 7) Backlog (salvar como `BACKLOG_PLUGIN_MAKER.md`)

```md
# Backlog — Plugin Maker (Plugin Forge) BrewStation

## Épico 0 — Fundamentos e segurança
- [ ] Criar plugin `plugin_maker` com estrutura padrão (install.json, menu, templates, static, api)
- [ ] Adicionar controle de acesso (somente admin) para geração em filesystem
- [ ] Logs de geração (maker_generation_run) com diff/resumo
- [ ] Dry-run (preview) antes de gerar

## Épico 1 — Metamodelo (banco do Maker)
- [ ] Criar modelos SQLAlchemy do Maker: project, table, column, relation
- [ ] Criar modelos UI: screens, sections, fields, tab_groups/tabs
- [ ] Criar modelos de computed fields (mode/expression/deps)
- [ ] Criar modelos ALV: grid_view, grid_column, aggregations, variants

## Épico 2 — UI do Maker (fluxo principal)
- [ ] Tela: Home (listar plugins existentes + projetos Maker)
- [ ] Tela: Criar/Editar Projeto (plugin_dir, name, prefix, label, version)
- [ ] Tela: Tabelas (CRUD de MakerTable)
- [ ] Tela: Colunas (CRUD de MakerColumn, validações de tipo/size)
- [ ] Tela: Relações (FK many-to-one, backref)
- [ ] Tela: Telas (MakerScreen) com menu label/icon/group
- [ ] Tela: Abas (TabGroup/Tab) e Seções (Section)
- [ ] Tela: Campos (FieldPlacement) com width_12, editable/computed

## Épico 3 — Import Excel (schema)
- [ ] Definir formato padrão da planilha (aba schema)
- [ ] Upload Excel (xlsx) e parser
- [ ] Mapeamento de tipos (excel -> maker_column.data_type)
- [ ] Preview + confirmação para criar tabelas/colunas
- [ ] Import incremental (merge com existentes)

## Épico 4 — Computed Fields
- [ ] Definir grammar segura (sem eval) e parser
- [ ] Validação de dependências + detecção de ciclos
- [ ] Implementar mode `ui` (gerar JS de recálculo)
- [ ] Implementar mode `api` (incluir no payload GET)
- [ ] Implementar mode `persisted` (recalcular em POST/PUT)

## Épico 5 — Grid ALV-like (v1)
- [ ] Definição de colunas do grid (visible/order/format)
- [ ] Filtros e sort (client-side)
- [ ] Agrupamento simples (1 coluna) client-side
- [ ] Agregações (sum/count) no footer
- [ ] Variantes: salvar/restaurar layout (colunas, ordem, agrupamento, sort)
- [ ] Export CSV/JSON respeitando variante atual

## Épico 6 — Gerador de Plugin-alvo (código)
- [ ] Templates de geração: install.json, menu_config.json
- [ ] Templates de geração: plugin.py + models.py + model_loader.py
- [ ] Templates de geração: api routes CRUD + export/import endpoints
- [ ] Templates de geração: controller/routes.py
- [ ] Templates de geração: templates HTML NiceAdmin (list + modal)
- [ ] Templates de geração: static JS padrão (CRUD com refresh, import/export)
- [ ] Rebuild: escrever no filesystem com proteção (guarded blocks)

## Épico 7 — Rebuild / Sync avançado (v2)
- [ ] Diff visual (arquivos mudados)
- [ ] Guarded blocks por arquivo (não sobrescrever custom)
- [ ] “Sync from filesystem” (ler plugin existente e tentar mapear)
- [ ] Hooks pós-geração (rodar comandos, ex: formatters)

## Épico 8 — Qualidade e UX (v2)
- [ ] Toast padrão (NiceAdmin) para sucesso/erro no Maker e plugins gerados
- [ ] Preview de tela (render parcial) antes de gerar
- [ ] Drag & drop para sections/fields (grid 12 col)
- [ ] Multi-grouping ALV + agregações por grupo
- [ ] Endpoint grid server-side para grandes volumes
```

---

Se você quiser, eu também posso te entregar um **“template de planilha Excel”** (schema) já com colunas e exemplos (para o import do Maker), no mesmo padrão do backlog.
