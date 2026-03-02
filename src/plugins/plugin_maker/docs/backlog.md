# Backlog — Plugin Maker (Plugin Forge)

## Épico 0 — Fundamentos e segurança
- [ ] Criar plugin plugin_maker com estrutura padrão
- [ ] Controle de acesso (somente admin) para operações de filesystem
- [ ] Registro de logs (generation runs)
- [ ] Dry-run preview (diff) antes de aplicar

## Épico 1 — Metamodelo
- [ ] Criar modelos do Maker (project/table/column/relation)
- [ ] Criar modelos UI (screen/tab/section/field placement)
- [ ] Criar computed fields
- [ ] Criar ALV grid (view/columns/variants/aggregations)

## Épico 2 — UI Maker
- [ ] Home (plugins existentes + projetos)
- [ ] Wizard de Projeto
- [ ] CRUD tabelas/colunas/relações
- [ ] CRUD telas/abas/seções/campos
- [ ] Config grid ALV + variantes

## Épico 3 — Import Excel
- [ ] Upload + parser xlsx
- [ ] Preview + confirmação
- [ ] Merge incremental

## Épico 4 — Code Generation
- [ ] Templates de geração (install/menu/plugin/model/loader/api/web/templates/js)
- [ ] Guarded blocks + manifest
- [ ] Rebuild apply com diff

## Épico 5 — Computed Fields
- [ ] Parser seguro de expressão
- [ ] deps + ciclo
- [ ] ui/api/persisted

## Épico 6 — ALV v1
- [ ] grouping 1 coluna
- [ ] aggregations sum/count
- [ ] variants por usuário
- [ ] export respeitando layout

## Épico 7 — V2
- [ ] drag&drop
- [ ] many-to-many
- [ ] grid server-side
- [ ] migrations avançadas