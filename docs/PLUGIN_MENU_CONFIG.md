# Configuração de Menu de Plugins

Este documento descreve como configurar o menu de navegação de um plugin no BrewStation.

## Visão Geral

O menu de navegação do plugin é configurado através do arquivo `menu_config.json`, que é separado do `install.json` para melhor organização. O menu é estruturado hierarquicamente, com o nome do plugin como item principal e os itens do `menu_config.json` como subitens.

## Estrutura do Menu

O menu segue uma estrutura hierárquica de três níveis:

```
📦 Nome do Plugin (do install.json: label > name > diretório)
  ├── 📄 Item Principal 1
  │   ├── Subitem 1.1
  │   ├── Subitem 1.2
  │   │   └── Sub-subitem 1.2.1
  │   └── Subitem 1.3
  ├── 📄 Item Principal 2
  └── 📄 Item Principal 3
```

## Arquivo menu_config.json

O arquivo `menu_config.json` deve estar na raiz do diretório do plugin e conter a seguinte estrutura:

```json
{
  "main_items": [
    {
      "id": "dashboard",
      "label": "Dashboard",
      "icon": "bi bi-grid",
      "url": "plugin_web.dashboard"
    },
    {
      "id": "ingredientes",
      "label": "Ingredientes",
      "icon": "bi bi-menu-button-wide",
      "children": [
        {
          "label": "Maltes",
          "url": "plugin_web.maltes",
          "icon": "bi bi-circle"
        },
        {
          "label": "Lúpulos",
          "url": "plugin_web.lupulos",
          "icon": "bi bi-circle"
        }
      ]
    },
    {
      "id": "relatorios",
      "label": "Relatórios",
      "icon": "bi bi-bar-chart",
      "children": [
        {
          "label": "Relatórios BrewFather",
          "url": "plugin_web.relatorios_brewfather",
          "icon": "bi bi-graph-up",
          "children": [
            {
              "label": "Relatório Detalhado",
              "url": "plugin_web.relatorio_detalhado",
              "icon": "bi bi-file-text"
            }
          ]
        }
      ]
    }
  ]
}
```

## Campos do menu_config.json

### Estrutura Principal

- **`main_items`** (obrigatório): Array de itens principais do menu

### Item do Menu

Cada item pode ter os seguintes campos:

- **`id`** (obrigatório): Identificador único do item (usado para IDs HTML)
- **`label`** (obrigatório): Texto exibido no menu
- **`icon`** (opcional): Classe do ícone Bootstrap Icons (padrão: `"bi bi-circle"`)
  - Exemplos: `"bi bi-house"`, `"bi bi-grid"`, `"bi bi-calculator"`
  - Veja [Bootstrap Icons](https://icons.getbootstrap.com/) para lista completa
- **`url`** (opcional): Endpoint do Flask para `url_for()`
  - Formato: `"blueprint_name.route_name"`
  - Exemplo: `"plugin_web.dashboard"`
  - Se não especificado, o item não terá link (útil para itens apenas com submenu)
- **`children`** (opcional): Array de subitens (suporta múltiplos níveis)

### Subitem

Subitens têm a mesma estrutura, mas sem o campo `id`:

- **`label`** (obrigatório): Texto exibido
- **`icon`** (opcional): Classe do ícone
- **`url`** (opcional): Endpoint do Flask
- **`children`** (opcional): Array de sub-subitens (terceiro nível)

## Referência no install.json

O `install.json` deve referenciar o arquivo de menu:

```json
{
  "name": "meu_plugin",
  "label": "Meu Plugin",
  "menu_config_path": "menu_config.json"
}
```

### Campo menu_config_path

- **Padrão**: `"menu_config.json"` (se não especificado)
- **Caminho**: Relativo à raiz do plugin
- **Exemplo**: Se o menu estiver em `config/menu.json`, use `"config/menu.json"`

## Nome do Plugin no Menu

O nome do plugin que aparece como item principal segue esta prioridade:

1. **`label`** (campo no `install.json`) - **Prioridade máxima**
2. **`name`** (campo no `install.json`) - Se `label` não existir
3. **Nome do diretório formatado** - Se nenhum dos dois existir
   - Exemplo: `plugin_integ_bFather` → `"Plugin Integ Bfather"`

### Exemplo

```json
{
  "name": "brewstation_core",
  "label": "Integração BrewFather"
}
```

No menu aparecerá: **"Integração BrewFather"**

## Endpoints e URLs

### Formato de URL

As URLs devem seguir o formato do Flask `url_for()`:

```
"blueprint_name.route_function_name"
```

### Exemplo de Blueprint

```python
# controller/routes.py
web_plugin_bp = Blueprint('plugin_meu_plugin_web', __name__)

@web_plugin_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
```

No `menu_config.json`:
```json
{
  "id": "dashboard",
  "label": "Dashboard",
  "url": "plugin_meu_plugin_web.dashboard"
}
```

### Tratamento de Erros

O sistema trata automaticamente endpoints inválidos:
- Se um endpoint não existir, o link apontará para `#` sem quebrar o template
- Use o helper `safe_url_for()` nos templates para garantir segurança

## Ícones Bootstrap Icons

Use classes do Bootstrap Icons. Alguns exemplos comuns:

- `"bi bi-grid"` - Dashboard/Grid
- `"bi bi-house"` - Home
- `"bi bi-calculator"` - Cálculos
- `"bi bi-bar-chart"` - Relatórios
- `"bi bi-box-seam"` - Estoque/Container
- `"bi bi-upload"` - Upload/Importar
- `"bi bi-cpu"` - Dispositivos/IoT
- `"bi bi-menu-button-wide"` - Menu/Lista
- `"bi bi-circle"` - Item genérico

Veja a [documentação completa do Bootstrap Icons](https://icons.getbootstrap.com/).

## Exemplos Completos

### Menu Simples

```json
{
  "main_items": [
    {
      "id": "dashboard",
      "label": "Dashboard",
      "icon": "bi bi-grid",
      "url": "plugin_web.dashboard"
    },
    {
      "id": "config",
      "label": "Configurações",
      "icon": "bi bi-gear",
      "url": "plugin_web.config"
    }
  ]
}
```

### Menu com Submenu

```json
{
  "main_items": [
    {
      "id": "ingredientes",
      "label": "Ingredientes",
      "icon": "bi bi-menu-button-wide",
      "children": [
        {
          "label": "Maltes",
          "url": "plugin_web.maltes",
          "icon": "bi bi-circle"
        },
        {
          "label": "Lúpulos",
          "url": "plugin_web.lupulos",
          "icon": "bi bi-circle"
        }
      ]
    }
  ]
}
```

### Menu com Múltiplos Níveis

```json
{
  "main_items": [
    {
      "id": "relatorios",
      "label": "Relatórios",
      "icon": "bi bi-bar-chart",
      "children": [
        {
          "label": "BrewFather",
          "icon": "bi bi-graph-up",
          "children": [
            {
              "label": "Receitas",
              "url": "plugin_web.relatorios_receitas",
              "icon": "bi bi-file-text"
            },
            {
              "label": "Lotes",
              "url": "plugin_web.relatorios_lotes",
              "icon": "bi bi-file-text"
            }
          ]
        }
      ]
    }
  ]
}
```

## Boas Práticas

### 1. Organização

- Mantenha o `menu_config.json` separado do `install.json`
- Use IDs descritivos e únicos
- Agrupe itens relacionados em submenus

### 2. Nomenclatura

- Use labels claros e descritivos
- Mantenha consistência nos ícones
- Evite menus muito profundos (máximo 3 níveis recomendado)

### 3. URLs

- Use endpoints válidos do Flask
- Teste todos os links após criar o menu
- O sistema trata endpoints inválidos automaticamente

### 4. Performance

- Evite menus muito grandes (máximo 20-30 itens principais)
- Use submenus para organizar muitos itens
- Considere agrupar funcionalidades relacionadas

## Troubleshooting

### Menu não aparece

**Verifique:**
- `menu_config.json` existe na raiz do plugin
- Campo `menu_config_path` no `install.json` está correto
- Plugin está ativo (`flask plugin list`)
- Estrutura JSON está válida

### Links não funcionam

**Verifique:**
- Endpoint existe no blueprint
- Formato da URL está correto (`blueprint.route`)
- Blueprint está registrado
- Plugin está ativo

### Nome do plugin incorreto

**Verifique:**
- Campo `label` no `install.json` (prioridade)
- Campo `name` no `install.json` (fallback)
- Nome do diretório do plugin

## Referências

- [Sistema de Plugins](PLUGIN_SYSTEM.md)
- [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)
- [Bootstrap Icons](https://icons.getbootstrap.com/)
- [Flask Blueprints](https://flask.palletsprojects.com/en/latest/blueprints/)

