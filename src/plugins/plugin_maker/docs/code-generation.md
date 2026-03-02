# Geração de Código (Plugins-alvo)

O Maker gera um plugin-alvo em `src/plugins/<plugin_dir>/...`.

## Estrutura gerada
- install.json
- menu_config.json
- plugin.py
- model/*.py
- utils/model_loader.py
- api/routes/*.py
- controller/routes.py
- templates/<slug>/*.html
- static/js/*.js

## Padrões
### Prefixo API
Rotas no blueprint devem ser relativas:
- GET /items
- POST /items
- PUT /items/<id>
- DELETE /items/<id>

O core aplica `/api/<plugin_name>` automaticamente.

### Static
JS do plugin:
- arquivo: src/plugins/<plugin_dir>/static/js/<screen>.js
- script tag: /plugin/<plugin_name>/static/js/<screen>.js

### CRUD padrão
Gerar:
- Lista com toolbar (novo/export/import)
- Modal bootstrap (create/edit)
- JS separado com:
  - load list
  - create/edit/delete
  - refresh após ações
  - export endpoints (csv/json)
  - import json (POST item a item no MVP)

### Export endpoints (padrão)
- GET /<entity>/export/csv
- GET /<entity>/export/json

### Delete seguro
Se houver dependência (ex.: FK):
- retornar 409 e JSON com mensagem
- sugerir "retired" ou deletar dependência antes