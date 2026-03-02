# Maker API (MVP)

Base: `/api/maker`

Todas as rotas exigem autenticação (login).

## Health
- `GET /info` → `{ ok, name, message }`

## Plugins existentes (filesystem)
- `GET /plugins` → `{ ok, items: [{dir,name,label,version}] }`

## Projetos
- `GET /projects` → `{ ok, items: [...], total }`
- `GET /projects/<project_id>` → `{ ok, item }`
- `POST /projects` → `{ ok, item }`
  - body: `plugin_dir`, `plugin_name`, `label`, `version?`, `table_prefix?`, `description?`, `author?`, `generation_mode?`
- `PUT /projects/<project_id>` → `{ ok, item }`
  - body (MVP): `label?`, `version?`, `table_prefix?`, `description?`, `author?`, `generation_mode?`, `status?`
- `DELETE /projects/<project_id>` → `{ ok }`

## Tabelas
- `GET /projects/<project_id>/tables` → `{ ok, items }`
- `POST /projects/<project_id>/tables` → `{ ok, item }`
  - body: `name`, `label`, `description?`
- `PUT /tables/<table_id>` → `{ ok, item }`
  - body: `name?`, `label?`, `description?`, `pk_strategy?`, `timestamps?`, `soft_delete?`
- `DELETE /tables/<table_id>` → `{ ok }` (MVP: também apaga colunas da tabela)

## Colunas
- `GET /tables/<table_id>/columns` → `{ ok, items }`
- `POST /tables/<table_id>/columns` → `{ ok, item }`
  - body: `name`, `label`, `data_type`, `length?`, `required?`, `unique?`, `indexed?`
- `PUT /columns/<column_id>` → `{ ok, item }`
- `DELETE /columns/<column_id>` → `{ ok }`

## Generator (rebuild)
- `POST /projects/<project_id>/rebuild/preview` → `{ ok, diff }`
- `POST /projects/<project_id>/rebuild/apply` → `{ ok, generated, plugin_dir }`

> Nota: no MVP o generator cria um skeleton mínimo (rotas web/api, template e js). Próximas versões vão gerar models e CRUDs por tabela.



## Importar plugin existente

**POST** `/api/maker/projects/import`

Payload:
```json
{ "plugin_dir": "plugin_yeast_bank" }
```

Resposta:
```json
{ "ok": true, "item": {"id": 1, "plugin_dir": "plugin_yeast_bank", "...": "..."}, "existing": false }
```
