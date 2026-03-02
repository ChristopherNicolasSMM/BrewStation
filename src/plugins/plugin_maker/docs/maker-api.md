# API do Plugin Maker (interna)

A API do Maker existe para o próprio UI.

## Projetos
- GET /api/maker/projects
- POST /api/maker/projects
- PUT /api/maker/projects/<id>
- DELETE /api/maker/projects/<id>

## Modelo de dados
- GET/POST/PUT/DELETE /api/maker/projects/<id>/tables
- GET/POST/PUT/DELETE /api/maker/tables/<id>/columns
- POST /api/maker/relations

## UI
- screens/sections/fields/tabs CRUD

## Rebuild
- POST /api/maker/projects/<id>/rebuild/preview
- POST /api/maker/projects/<id>/rebuild/apply
- GET  /api/maker/projects/<id>/generation_runs

## Drift
- GET /api/maker/projects/<id>/scan
- POST /api/maker/projects/<id>/resolve (detach/copy/takeover)