# Estrutura do install.json para Plugins BrewStation

O arquivo `install.json` é o arquivo de configuração principal de cada plugin. Ele define metadados, menu de navegação, dependências e modelos de banco de dados.

## Localização

O arquivo deve estar localizado em:
```
src/plugins/<nome_do_plugin>/install.json
```

## Estrutura Completa

```json
{
  "name": "nome_do_plugin",
  "version": "1.0.0",
  "description": "Descrição do plugin",
  "author": "Nome do Autor",
  "menu": {
    "main_items": [
      {
        "id": "item_id",
        "label": "Nome do Item",
        "icon": "bi bi-icon-class",
        "url": "blueprint.route",
        "children": [
          {
            "label": "Subitem",
            "icon": "bi bi-icon-class",
            "url": "blueprint.route"
          }
        ]
      }
    ]
  },
  "dependencies": ["plugin1", "plugin2"],
  "db_models": [
    "model.ingredientes",
    "model.estoque"
  ]
}
```

## Campos Obrigatórios

### `name` (string, obrigatório)
Nome único do plugin. Deve corresponder ao nome do diretório do plugin.

### `version` (string, obrigatório)
Versão do plugin no formato semântico (ex: "1.0.0").

### `description` (string, obrigatório)
Descrição do que o plugin faz.

### `author` (string, obrigatório)
Nome do autor ou equipe responsável pelo plugin.

## Menu de Navegação

O campo `menu.main_items` define os itens de menu que aparecerão na sidebar.

### Item de Menu Simples (sem submenu)

```json
{
  "id": "receitas",
  "label": "Receitas",
  "icon": "bi bi-journal-text",
  "url": "plugin_brewstation_core_web.receitas"
}
```

**Campos:**
- `id` (string, obrigatório): Identificador único do item
- `label` (string, obrigatório): Texto exibido no menu
- `icon` (string, obrigatório): Classe CSS do ícone (Bootstrap Icons)
- `url` (string, obrigatório): Nome do endpoint Flask (blueprint.route)

### Item de Menu com Submenu

```json
{
  "id": "ingredientes",
  "label": "Ingredientes",
  "icon": "bi bi-menu-button-wide",
  "children": [
    {
      "label": "Maltes",
      "icon": "bi bi-circle",
      "url": "plugin_brewstation_core_web.maltes"
    },
    {
      "label": "Lúpulos",
      "icon": "bi bi-circle",
      "url": "plugin_brewstation_core_web.lupulos"
    }
  ]
}
```

**Campos:**
- `id` (string, obrigatório): Identificador único do item
- `label` (string, obrigatório): Texto exibido no menu
- `icon` (string, obrigatório): Classe CSS do ícone
- `children` (array, opcional): Lista de subitens
  - `label` (string, obrigatório): Texto do subitem
  - `icon` (string, obrigatório): Classe CSS do ícone
  - `url` (string, obrigatório): Nome do endpoint Flask

**Nota:** Se um item tem `children`, o campo `url` no item pai é opcional (não será usado).

## Dependências

O campo `dependencies` (array, opcional) lista outros plugins que devem estar instalados antes deste plugin.

```json
{
  "dependencies": ["plugin_base", "plugin_auth"]
}
```

## Modelos de Banco de Dados

O campo `db_models` (array, opcional) lista os módulos de modelos que o plugin utiliza. Isso ajuda na documentação e migração.

```json
{
  "db_models": [
    "model.ingredientes",
    "model.estoque",
    "model.brewfather"
  ]
}
```

## Estrutura de Diretórios do Plugin

Cada plugin deve seguir esta estrutura:

```
src/plugins/<nome_do_plugin>/
├── install.json          # Configuração do plugin (obrigatório)
├── plugin.py             # Classe do plugin (obrigatório)
├── api/
│   └── routes/          # Rotas API (opcional)
│       ├── __init__.py  # Exporta blueprints
│       └── *.py         # Arquivos de rotas
├── controller/
│   └── routes.py        # Rotas web (opcional)
├── templates/           # Templates HTML (opcional)
│   └── *.html
├── static/              # Arquivos estáticos (opcional)
│   └── css/js/img/
├── model/               # Modelos do plugin (opcional)
│   └── *.py
└── utils/               # Utilitários (opcional)
    └── *.py
```

## Registro Automático

O sistema BrewStation registra automaticamente:

1. **Rotas API**: Todos os blueprints exportados em `api/routes/__init__.py` são registrados com prefixo `/api`
2. **Rotas Web**: O blueprint em `controller/routes.py` (deve exportar `web_plugin_bp`) é registrado com prefixo `/plugin/<nome_do_plugin>`
3. **Templates**: Templates em `templates/` são descobertos automaticamente pelo `PluginTemplateLoader`
4. **Static Files**: Arquivos em `static/` são servidos em `/plugin/<nome_do_plugin>/static/`
5. **Menu**: Itens de menu do `install.json` são adicionados automaticamente à sidebar

## Exemplo Completo

```json
{
  "name": "brewstation_core",
  "version": "1.0.0",
  "description": "Funcionalidades core do BrewStation",
  "author": "BrewStation Team",
  "menu": {
    "main_items": [
      {
        "id": "ingredientes",
        "label": "Ingredientes",
        "icon": "bi bi-menu-button-wide",
        "children": [
          {
            "label": "Maltes",
            "icon": "bi bi-circle",
            "url": "plugin_brewstation_core_web.maltes"
          },
          {
            "label": "Lúpulos",
            "icon": "bi bi-circle",
            "url": "plugin_brewstation_core_web.lupulos"
          }
        ]
      },
      {
        "id": "receitas",
        "label": "Receitas",
        "icon": "bi bi-journal-text",
        "url": "plugin_brewstation_core_web.receitas"
      }
    ]
  },
  "dependencies": [],
  "db_models": [
    "model.ingredientes",
    "model.estoque"
  ]
}
```

## Validação

O sistema valida automaticamente:
- Presença de `install.json` e `plugin.py`
- Estrutura básica do JSON
- Dependências instaladas antes da instalação
- Formato dos itens de menu

## Notas Importantes

1. O nome do plugin no `install.json` deve corresponder ao nome do diretório
2. URLs no menu devem usar o formato `blueprint.route` (nome do blueprint + nome da rota)
3. Ícones devem usar classes Bootstrap Icons (`bi bi-*`)
4. O sistema busca automaticamente por `web_plugin_bp` em `controller/routes.py`
5. Blueprints API devem ser exportados em `api/routes/__init__.py` via `all_blueprints` ou como atributos do módulo

