# Estrutura do install.json para Plugins BrewStation

O arquivo `install.json` é o arquivo de configuração principal de cada plugin. Ele define metadados, referência ao menu de navegação, dependências e modelos de banco de dados.

**Nota**: A partir da versão atual, o menu de navegação é configurado em um arquivo separado (`menu_config.json`). Veja [Configuração de Menu](PLUGIN_MENU_CONFIG.md) para detalhes.

## Localização

O arquivo deve estar localizado em:
```
src/plugins/<nome_do_plugin>/install.json
```

## Estrutura Completa

```json
{
  "name": "nome_do_plugin",
  "label": "Nome Exibido no Menu",
  "version": "1.0.0",
  "description": "Descrição do plugin",
  "author": "Nome do Autor",
  "menu_config_path": "menu_config.json",
  "dependencies": ["plugin1", "plugin2"],
  "db_models": [
    "model.ingredientes",
    "model.estoque"
  ]
}
```

## Campos Obrigatórios

### `name` (string, obrigatório)
Nome único do plugin usado para identificação interna. Pode ser diferente do nome do diretório.

### `version` (string, obrigatório)
Versão do plugin no formato semântico (ex: "1.0.0").

### `description` (string, obrigatório)
Descrição do que o plugin faz.

### `author` (string, obrigatório)
Nome do autor ou equipe responsável pelo plugin.

## Campos Opcionais

### `label` (string, opcional)
Nome exibido no menu de navegação. **Prioridade sobre `name`**.

**Prioridade do nome no menu:**
1. `label` (se existir) - **Prioridade máxima**
2. `name` (se `label` não existir)
3. Nome do diretório formatado (se nenhum dos dois existir)

**Exemplo:**
```json
{
  "name": "brewstation_core",
  "label": "Integração BrewFather"
}
```
No menu aparecerá: **"Integração BrewFather"**

### `menu_config_path` (string, opcional)
Caminho relativo para o arquivo de configuração do menu. Padrão: `"menu_config.json"`.

**Exemplo:**
```json
{
  "menu_config_path": "menu_config.json"
}
```

Se não especificado, o sistema procura por `menu_config.json` na raiz do plugin.

## Menu de Navegação

O menu de navegação é configurado em um arquivo separado (`menu_config.json`), referenciado pelo campo `menu_config_path` no `install.json`.

**Estrutura do Menu:**
```
📦 Nome do Plugin (do campo "label" ou "name")
  ├── 📄 Item 1 (do menu_config.json)
  ├── 📄 Item 2
  └── 📄 Item 3
```

O nome do plugin aparece como item principal, e os itens do `menu_config.json` aparecem como subitens.

**Veja [Configuração de Menu](PLUGIN_MENU_CONFIG.md) para detalhes completos sobre a estrutura do `menu_config.json`.**

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

## Prefixo de Tabelas

O campo `table_prefix` (string, opcional) define o prefixo que será aplicado aos nomes das tabelas dos modelos do plugin.

### Comportamento

- **Se `table_prefix` for `null` ou não especificado**: Usa o nome do diretório do plugin como prefixo padrão
  - Exemplo: Plugin em `plugins/plugin_meu_plugin/` → prefixo `plugin_meu_plugin_`
  - Tabela `produtos` → `plugin_meu_plugin_produtos`

- **Se `table_prefix` for especificado**: Usa o valor fornecido como prefixo
  - Exemplo: `"table_prefix": "estoque_"` → prefixo `estoque_`
  - Tabela `produtos` → `estoque_produtos`

- **Se `table_prefix` for string vazia `""`**: Tabelas são criadas sem prefixo (não recomendado, pode causar conflitos)

### Exemplos

#### Exemplo 1: Prefixo Padrão (Recomendado)
```json
{
  "name": "meu_plugin",
  "table_prefix": null
}
```
**Resultado**: Tabelas serão criadas como `plugin_meu_plugin_nome_tabela`

#### Exemplo 2: Prefixo Customizado
```json
{
  "name": "meu_plugin",
  "table_prefix": "custom_"
}
```
**Resultado**: Tabelas serão criadas como `custom_nome_tabela`

#### Exemplo 3: Sem Prefixo (Não Recomendado)
```json
{
  "name": "meu_plugin",
  "table_prefix": ""
}
```
**Resultado**: Tabelas serão criadas sem prefixo (pode causar conflitos com outros plugins ou core)

### Boas Práticas

1. **Use prefixos sempre**: Evite conflitos de nomes usando prefixos apropriados
2. **Prefira prefixo padrão**: Deixe `table_prefix: null` para usar o nome do diretório automaticamente
3. **Use nomes descritivos**: Se usar prefixo customizado, escolha um nome que reflita o propósito do plugin
4. **Documente mudanças**: Se mudar o prefixo, documente o processo de migração necessário

### Migração após Mudança de Prefixo

Se você mudar o `table_prefix` de um plugin existente:

1. Execute `flask diagnose-brewfather-tables` para identificar tabelas afetadas
2. Execute `flask recreate-plugin-tables` para criar novas tabelas com prefixo correto
3. Execute `flask migrate-brewfather-tables` para migrar dados (se necessário)
4. Verifique que tudo funciona antes de remover tabelas antigas

Veja [Sistema de Banco de Dados](PLUGIN_DATABASE.md) para mais detalhes sobre migração.

## Estrutura de Diretórios do Plugin

Cada plugin deve seguir esta estrutura:

```
src/plugins/<nome_do_plugin>/
├── install.json          # Configuração do plugin (obrigatório)
├── menu_config.json      # Configuração do menu (opcional, recomendado)
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
2. **Rotas Web**: O blueprint em `controller/routes.py` (deve exportar `web_plugin_bp`) é registrado sem prefixo (acessível diretamente)
3. **Templates**: Templates em `templates/` são descobertos automaticamente pelo `PluginTemplateLoader`
4. **Static Files**: Arquivos em `static/` são servidos em `/plugin/<nome_do_plugin>/static/`
5. **Menu**: Itens de menu do `menu_config.json` são adicionados automaticamente à sidebar, com o nome do plugin (do campo `label` ou `name`) como item principal

## Exemplo Completo

**install.json:**
```json
{
  "name": "brewstation_core",
  "label": "Integração BrewFather",
  "version": "1.0.0",
  "description": "Funcionalidades core do BrewStation",
  "author": "BrewStation Team",
  "menu_config_path": "menu_config.json",
  "dependencies": [],
  "db_models": [
    "model.ingredientes",
    "model.estoque"
  ]
}
```

**menu_config.json:**
```json
{
  "main_items": [
    {
      "id": "dashboard",
      "label": "Dashboard",
      "icon": "bi bi-grid",
      "url": "plugin_brewstation_core_web.dashboard"
    },
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
}
```

**Resultado no menu:**
```
📦 Integração BrewFather
  ├── 📄 Dashboard
  ├── 📄 Ingredientes
  │   ├── Maltes
  │   └── Lúpulos
  └── 📄 Receitas
```

## Validação

O sistema valida automaticamente:
- Presença de `install.json` e `plugin.py`
- Estrutura básica do JSON
- Dependências instaladas antes da instalação
- Formato dos itens de menu

## Notas Importantes

1. O campo `name` no `install.json` é usado para identificação interna e pode ser diferente do nome do diretório
2. O campo `label` tem prioridade sobre `name` para exibição no menu
3. O menu é configurado em `menu_config.json` separado (recomendado) ou inline no `install.json` (legado)
4. URLs no menu devem usar o formato `blueprint.route` (nome do blueprint + nome da rota)
5. Ícones devem usar classes Bootstrap Icons (`bi bi-*`)
6. O sistema busca automaticamente por `web_plugin_bp` em `controller/routes.py`
7. Blueprints API devem ser exportados em `api/routes/__init__.py` via `all_blueprints` ou como atributos do módulo
8. O nome do plugin aparece como item principal no menu, e os itens do `menu_config.json` aparecem como subitens

## Referências

- [Configuração de Menu](PLUGIN_MENU_CONFIG.md) - Guia completo sobre `menu_config.json`
- [Sistema de Plugins](PLUGIN_SYSTEM.md) - Visão geral do sistema
- [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md) - Guia de desenvolvimento

