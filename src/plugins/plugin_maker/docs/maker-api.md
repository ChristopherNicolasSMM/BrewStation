# API do Plugin Maker (interna)

A API do Maker existe para o próprio UI do Maker.

> Observação: o BrewStation prefixa as tabelas de plugins no banco via core.  
> Por isso, o Maker sempre deve obter modelos via `get_prefixed_model()` (registry).

## Projetos
- GET    /api/maker/projects
- GET    /api/maker/projects/<id>
- POST   /api/maker/projects
- PUT    /api/maker/projects/<id>
- DELETE /api/maker/projects/<id>

## Tabelas
- GET    /api/maker/projects/<project_id>/tables
- POST   /api/maker/projects/<project_id>/tables
- PUT    /api/maker/tables/<table_id>
- DELETE /api/maker/tables/<table_id>

## Colunas
- GET    /api/maker/tables/<table_id>/columns
- POST   /api/maker/tables/<table_id>/columns
- PUT    /api/maker/columns/<column_id>
- DELETE /api/maker/columns/<column_id>

## Rebuild (primeiro MVP)
- POST /api/maker/projects/<id>/rebuild/preview
- POST /api/maker/projects/<id>/rebuild/apply

## Auxiliares
- GET /api/maker/plugins  (lista plugins existentes via filesystem)
