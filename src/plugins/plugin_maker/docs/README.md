# Plugin Maker (Plugin Forge) — Documentação Técnica

Este documento descreve a especificação do **Plugin Maker** (também chamado de *Plugin Forge*), um plugin do BrewStation que permite **criar e gerenciar plugins gerados** a partir de um metamodelo (tabelas/colunas/relações/telas), com interface baseada no template NiceAdmin.

O Plugin Maker:
- Lista plugins existentes do BrewStation
- Permite criar um **Projeto de Plugin** (um “plugin-alvo” gerado)
- Permite definir **tabelas, colunas, relações**
- Permite criar **telas** (CRUD/Dashboard) com **seções, campos, abas**
- Gera código: **Models + API + Templates + Static JS** no padrão do BrewStation
- Possui governança para não quebrar customizações: **ownership, manifest, guarded blocks e drift detection**

## Sumário
- [Visão Geral](./overview.md)
- [Metamodelo](./metamodel.md)
- [Fluxos de UI](./ui-flows.md)
- [Geração de Código](./code-generation.md)
- [Governança: Ownership & Drift](./governance.md)
- [Campos Calculados](./computed-fields.md)
- [Grid estilo ALV (Agrupamento/Agregação/Variantes)](./alv-grid.md)
- [Importação Excel](./excel-import.md)
- [API do Plugin Maker](./maker-api.md)
- [Backlog](./backlog.md)

## Regras essenciais (para leitura rápida)
1. Rotas de API geradas **não incluem** o nome do plugin; o prefixo `/api/<plugin_name>` é aplicado pelo core.
2. Arquivos JS/CSS gerados ficam em `static/` do plugin e são carregados via:
   `/plugin/<plugin_name>/static/js/<file>.js`
3. O Maker só edita artefatos com **managed_by_maker = true** e controlados via manifest/guarded blocks.