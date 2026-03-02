# Fluxos de UI

O Maker segue o fluxo:
**Plugin → Tabelas → Tipos/Colunas → Telas → Sessões → Campos → Rebuild**

## 1) Home
- Lista plugins existentes (filesystem) + status (plugins.json)
- Lista projetos do Maker

Ações:
- Novo Projeto
- Rebuild (com preview)
- Logs

## 2) Projeto
Tela de configuração do projeto:
- plugin_dir, plugin_name, label, prefix, version

## 3) Tabelas
- Criar tabela
- Importar Excel (gera tabelas/colunas)
- Ver colunas e relações

## 4) Colunas
- Tipo, required, default, size, unique/index
- FK: selecionar tabela destino e on_delete

## 5) Telas
Criar telas:
- CRUD (tabela base)
- Dashboard (KPIs)
- Custom (v2)

Config:
- menu_label, menu_icon, menu_group

## 6) Abas e Seções
- Criar TabGroup/Tab (opcional)
- Criar Sections com icon/title/layout_type/width_12

## 7) Campos (Field placements)
- Selecionar coluna (ou computed field)
- Definir width_12 e comportamento: editable/computed/visible_on
- Widget override e format

## 8) Grid ALV
Configurar:
- colunas visíveis e ordem
- filtros e sort
- agrupamento (MVP: 1 coluna)
- agregações (sum/count)
- variantes (salvar layout)

## 9) Rebuild
- Preview (diff)
- Resolver conflitos (drift)
- Gerar e aplicar