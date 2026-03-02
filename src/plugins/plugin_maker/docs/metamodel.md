# Metamodelo (Banco do Maker)

O metamodelo é o conjunto de tabelas do próprio plugin Maker. Elas descrevem os plugins-alvo que serão gerados.

## 1) Projeto
### maker_project
Campos principais:
- plugin_dir, plugin_name, label, version, description
- table_prefix (para evitar conflito de tabelas)
- status: draft | generated | synced | error
- generation_mode: full_overwrite | guarded_blocks

## 2) Modelo de dados
### maker_table
- name (lógico), label (humano)
- pk_strategy (int/uuid)
- timestamps, soft_delete

### maker_column
- name, label, data_type, length
- required, unique, indexed, default_value
- pk, fk (target_table/target_column, on_delete)
- ui_widget_hint (text/select/date/...)

### maker_relation
- relation_type: many_to_one (MVP)
- from_table, to_table, fk_column, backref_name

## 3) UI (telas)
### maker_screen
- screen_type: crud | dashboard | custom
- base_table_id (para CRUD)
- menu_label, menu_icon, menu_group
- route_path

### maker_tab_group / maker_tab
- habilita UI com abas

### maker_section
- title, icon, width_12 (1..12)
- layout_type: form_card | table_card | kpi_card | grid_card
- style_variant (NiceAdmin)

### maker_field_placement
- referencia column_id ou computed_field_id
- label_override, icon, help_text
- width_12, editable, visible_on (list/create/edit/details)

## 4) Computed fields
### maker_computed_field
- mode: ui | api | persisted
- expression, deps_json
- data_type, label

## 5) Grid ALV-like
### maker_grid_view
- config do grid: grouping, aggregations, export, reorder

### maker_grid_column
- coluna: visible, sortable, filterable, groupable, aggregatable

### maker_grid_variant
- “variant” por usuário/compartilhada