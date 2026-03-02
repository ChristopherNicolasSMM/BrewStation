# Visão Geral

## Objetivo
Criar um plugin Maker que possibilite gerar outros plugins do BrewStation de forma padronizada.

O Maker é um plugin normal (`plugin_maker`) que roda dentro do BrewStation e:
- Armazena um metamodelo de “projeto de plugin” (tabelas, colunas, telas)
- Permite importar schema via Excel
- Gera código em `src/plugins/<plugin_dir>/...`

## Termos
- **Maker**: plugin responsável por criar/gerar
- **Projeto**: definição interna no Maker que representa um plugin-alvo
- **Plugin-alvo**: plugin gerado no `src/plugins/`
- **Managed by Maker**: artefato controlado pelo Maker (pode ser regenerado)
- **Manual**: artefato existente que não foi criado pelo Maker (Maker não edita)

## Escopo MVP
- Projetos: criar/editar
- Tabelas/colunas/relações: criar/editar
- Telas CRUD: lista + modal create/edit + delete + export/import
- Telas: seções e campos (grid 12 col, sem drag&drop no MVP)
- Campos calculados (mode ui/api/persisted)
- Grid estilo ALV (v1): filtros, sort, grouping simples, agregação simples, variantes
- Rebuild: gerar arquivos e registrar manifest, com preview

## Escopo V2
- Drag&drop layout
- Many-to-many
- Grid ALV avançado server-side para grandes dados
- Migrations avançadas (alembic)
- Permissões por tela/ação