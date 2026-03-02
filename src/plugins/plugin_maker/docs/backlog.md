# Backlog — Plugin Maker (Plugin Forge)

> Atualizado em: 2026-03-02

## Status atual (MVP entregue)
- CRUD de **Projetos** (listar/criar/editar/deletar)
- CRUD de **Tabelas** e **Colunas**
- UI: tela **/maker** (lista projetos + plugins existentes)
- UI: tela **/maker/projects/<id>** (editor de tabelas/colunas + ações)
- Generator v1 (skeleton do plugin + manifest .maker + rotas web/api básicas)

---

## Épico 0 — Fundamentos e segurança
- [x] Criar plugin **plugin_maker** com estrutura padrão
- [ ] Controle de acesso (somente admin) para operações de filesystem (rebuild/apply)
- [x] Registro de logs (generation runs)
- [x] Dry-run preview (diff) antes de aplicar

## Épico 1 — Metamodelo
- [x] Modelos do Maker (project/table/column/relation + geração run)
- [ ] Relações (FKs/one-to-many/many-to-many) — UI + validação + geração
- [ ] Tipos avançados (enum/json/decimal/datetime) e constraints

## Épico 2 — UI/UX (Maker)
- [x] Importar plugin existente do filesystem para o Maker (cria MakerProject)

- [x] Tela inicial com projetos + plugins existentes
- [x] Tela de projeto com tabelas/colunas
- [ ] Melhorias UX: seleção visual, inline-edit opcional, mensagens vazias padronizadas
- [ ] Confirmações e estados de loading (spinners) em todas as ações
- [ ] Filtros/pesquisa de tabelas e colunas
- [ ] Paginação em projetos (quando crescer)

## Épico 3 — Generator
- [x] Generator v1: cria pastas/arquivos do plugin (install/menu/plugin.py/controller/api/templates/static) + .maker/manifest.json
- [ ] Generator v2: gerar **models SQLAlchemy** a partir de MakerTable/MakerColumn
- [ ] Generator v3: gerar CRUD API + CRUD Web (templates + js) por tabela
- [ ] Guarded blocks (preservar edições manuais em arquivos gerados)
- [ ] Estratégia de migração (Alembic) / versionamento do schema
- [ ] Testes de geração (unit) + snapshots

## Épico 4 — Documentação
- [x] Atualizar endpoints do Maker API
- [x] Atualizar backlog
- [ ] Documentar fluxo completo: criar projeto → tabelas/colunas → gerar plugin → instalar/ativar
- [ ] Documentar padrões de naming (plugin_dir/plugin_name/table_prefix)
- [ ] Documentar “ownership” e manifest (.maker)

