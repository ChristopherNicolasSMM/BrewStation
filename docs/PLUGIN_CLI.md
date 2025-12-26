# Comandos CLI para Plugins

Este documento descreve todos os comandos disponíveis para gerenciar plugins no BrewStation.

## Comandos via run.py

O `run.py` fornece comandos simplificados para gerenciar plugins diretamente da raiz do projeto.

### Criar Plugin

Cria um plugin template completo com toda a estrutura necessária.

#### Modo Interativo

```bash
python run.py plugin -c
```

O sistema fará perguntas interativas:
- **Nome do plugin** (diretório, ex: `meu_plugin`)
- **Nome exibido no menu** (ex: `Meu Plugin`)
- **Descrição** (opcional)
- **Autor** (opcional)
- **Versão** (padrão: `1.0.0`)

#### Modo Direto

```bash
python run.py plugin -c meu_plugin "Meu Plugin"
```

Cria o plugin diretamente com os parâmetros fornecidos:
- Primeiro argumento: nome do plugin (diretório)
- Segundo argumento: nome exibido no menu

**O que é criado:**
- ✅ Estrutura completa de diretórios (`api/`, `controller/`, `templates/`, `model/`, `utils/`, `logs/`)
- ✅ `install.json` configurado
- ✅ `menu_config.json` básico
- ✅ `plugin.py` com implementação mínima
- ✅ Rota API de exemplo (`/api/meu_plugin/info`)
- ✅ Rota web de exemplo (`/meu_plugin`)
- ✅ Template HTML funcional com teste de API

**Exemplo de uso:**
```bash
# Criar plugin interativo
python run.py plugin -c

# Criar plugin direto
python run.py plugin -c receitas_avancadas "Receitas Avançadas"
```

### Instalar Plugin

Instala um plugin da pasta `plugins/` no sistema.

```bash
python run.py plugin -i <nome_do_plugin>
```

**O que faz:**
- Carrega o plugin da pasta `plugins/<nome_do_plugin>/`
- Registra no banco de dados
- Cria tabelas de modelos (se houver)
- Marca como instalado

**Exemplo:**
```bash
python run.py plugin -i meu_plugin
```

### Ativar Plugin

Ativa um plugin instalado, tornando-o disponível no sistema.

```bash
python run.py plugin -a <nome_do_plugin>
```

**O que faz:**
- Registra rotas do plugin
- Adiciona templates ao template loader
- Adiciona itens ao menu
- Marca como ativo

**Exemplo:**
```bash
python run.py plugin -a meu_plugin
```

**Nota:** O plugin deve estar instalado antes de ser ativado.

### Desativar Plugin

Desativa um plugin ativo, removendo-o temporariamente do sistema.

```bash
python run.py plugin -d <nome_do_plugin>
```

**O que faz:**
- Remove rotas do plugin
- Remove templates do template loader
- Remove itens do menu
- Marca como inativo

**Exemplo:**
```bash
python run.py plugin -d meu_plugin
```

**Nota:** O plugin permanece instalado, apenas desativado.

### Ajuda

Mostra ajuda completa sobre os comandos de plugin.

```bash
python run.py plugin -h
```

Ou:

```bash
python run.py plugin --help
```

## Comandos via Flask CLI

Os comandos Flask CLI também estão disponíveis quando executados de dentro de `src/`:

### Listar Plugins

```bash
cd src
flask plugin list
```

Lista todos os plugins descobertos, mostrando:
- Nome
- Versão
- Status (instalado/ativo)
- Descrição

### Descobrir Plugins

```bash
cd src
flask plugin discover
```

Escaneia a pasta `plugins/` procurando por novos plugins.

### Instalar Plugin

```bash
cd src
flask plugin install <nome_do_plugin>
```

### Desinstalar Plugin

```bash
cd src
flask plugin uninstall <nome_do_plugin>
```

**Atenção:** Desinstalar remove o plugin do banco de dados, mas não remove os arquivos.

### Ativar Plugin

```bash
cd src
flask plugin activate <nome_do_plugin>
```

### Desativar Plugin

```bash
cd src
flask plugin deactivate <nome_do_plugin>
```

### Informações do Plugin

```bash
cd src
flask plugin info <nome_do_plugin>
```

Mostra informações detalhadas sobre um plugin:
- Nome e versão
- Descrição e autor
- Dependências
- Status (instalado/ativo)
- Modelos de banco de dados

## Fluxo de Trabalho Recomendado

### 1. Criar Novo Plugin

```bash
# Criar plugin template
python run.py plugin -c meu_plugin "Meu Plugin"

# Ou modo interativo
python run.py plugin -c
```

### 2. Desenvolver Plugin

Edite os arquivos criados:
- `plugin.py` - Lógica do plugin
- `api/routes/` - Rotas API
- `controller/routes.py` - Rotas web
- `templates/` - Templates HTML
- `model/` - Modelos SQLAlchemy

### 3. Instalar e Ativar

```bash
# Instalar
python run.py plugin -i meu_plugin

# Ativar
python run.py plugin -a meu_plugin
```

### 4. Testar

- Acesse a rota web: `http://localhost:5000/meu_plugin`
- Teste a API: `http://localhost:5000/api/meu_plugin/info`
- Verifique o menu na sidebar

### 5. Desativar (se necessário)

```bash
python run.py plugin -d meu_plugin
```

## Exemplos Completos

### Exemplo 1: Criar e Usar Plugin Simples

```bash
# 1. Criar plugin
python run.py plugin -c calculadora "Calculadora"

# 2. Instalar
python run.py plugin -i calculadora

# 3. Ativar
python run.py plugin -a calculadora

# 4. Acessar
# http://localhost:5000/calculadora
```

### Exemplo 2: Plugin com Múltiplas Rotas

Após criar o plugin template:

1. Edite `controller/routes.py` para adicionar mais rotas
2. Edite `menu_config.json` para adicionar itens ao menu
3. Crie templates adicionais em `templates/`
4. Instale e ative:

```bash
python run.py plugin -i meu_plugin
python run.py plugin -a meu_plugin
```

### Exemplo 3: Plugin com Modelos de Banco

1. Crie modelos em `model/meu_modelo.py`
2. Registre em `plugin.py` no método `register_models()`
3. Adicione ao `install.json` em `db_models`
4. Instale (cria tabelas automaticamente):

```bash
python run.py plugin -i meu_plugin
```

## Troubleshooting

### Plugin não aparece após criar

**Verifique:**
- Plugin foi criado em `src/plugins/<nome>/`
- `install.json` e `plugin.py` existem
- Estrutura JSON válida

**Solução:**
```bash
cd src
flask plugin discover
```

### Erro ao instalar

**Verifique:**
- Banco de dados está acessível
- Dependências do plugin estão instaladas
- Modelos estão corretos

**Solução:**
```bash
# Verificar logs
tail -f logs/application.log

# Verificar status
flask plugin info <nome>
```

### Rotas não funcionam após ativar

**Verifique:**
- Plugin está ativo (`flask plugin list`)
- Blueprints estão exportados corretamente
- URLs no menu estão corretas

**Solução:**
```bash
# Reativar plugin
python run.py plugin -d <nome>
python run.py plugin -a <nome>
```

### Menu não aparece

**Verifique:**
- `menu_config.json` existe e está válido
- Plugin está ativo
- Campo `label` ou `name` no `install.json`

**Solução:**
```bash
# Verificar configuração
cat src/plugins/<nome>/menu_config.json

# Reativar
python run.py plugin -d <nome>
python run.py plugin -a <nome>
```

## Comandos de Diagnóstico e Migração de Tabelas

### Diagnóstico de Tabelas

O comando `flask diagnose-brewfather-tables` verifica quais tabelas relacionadas ao BrewFather existem no banco e identifica necessidade de migração:

```bash
cd src
python -m flask diagnose-brewfather-tables
```

**Quando usar:**
- Após criar novos modelos em plugins
- Quando receber erros de "tabela não encontrada"
- Para verificar se tabelas têm prefixos corretos
- Antes de migrar dados entre tabelas

**Saída esperada:**
```
============================================================
DIAGNÓSTICO DE TABELAS BREWFATHER
============================================================

Tabelas encontradas relacionadas ao BrewFather:
  - brewfather_recipes: 10 registros
  - plugin_integ_bFather_brewfather_recipes: 0 registros

Verificando migração necessária:
  ⚠️  brewfather_recipes existe (10 registros) mas plugin_integ_bFather_brewfather_recipes não existe
     → Migração necessária!

============================================================

⚠️  MIGRAÇÃO NECESSÁRIA DETECTADA
Execute: flask migrate-brewfather-tables
```

### Recriar Tabelas de Plugins

O comando `flask recreate-plugin-tables` recria todas as tabelas de plugins com os prefixos corretos:

```bash
cd src
python -m flask recreate-plugin-tables
```

**Quando usar:**
- Após mudanças em modelos de plugins
- Quando prefixos de tabelas foram alterados
- Para garantir que todas as tabelas têm os prefixos corretos
- Antes de migrar dados (para criar tabelas destino)

**O que faz:**
- Remove tabelas antigas dos modelos de plugins
- Recria todas as tabelas (core e plugins) com os prefixos corretos
- Preserva dados em tabelas core

**⚠️ ATENÇÃO**: Este comando remove tabelas de plugins. Certifique-se de fazer backup se necessário.

### Migrar Dados entre Tabelas

O comando `flask migrate-brewfather-tables` migra dados de tabelas sem prefixo para tabelas com prefixo:

```bash
cd src
python -m flask migrate-brewfather-tables
```

**Quando usar:**
- Após executar `flask diagnose-brewfather-tables` e identificar necessidade de migração
- Quando dados foram inseridos em tabelas sem prefixo antes do sistema de prefixos
- Quando o `table_prefix` de um plugin foi alterado

**Processo recomendado:**
```bash
# 1. Diagnosticar situação atual
flask diagnose-brewfather-tables

# 2. Recriar tabelas com prefixos (se necessário)
flask recreate-plugin-tables

# 3. Migrar dados
flask migrate-brewfather-tables

# 4. Verificar resultados
flask diagnose-brewfather-tables
```

**O que faz:**
- Identifica tabelas que precisam migração (sem prefixo → com prefixo)
- Copia dados preservando estrutura
- Pede confirmação se tabela destino já tem dados
- Mostra progresso e estatísticas

**Exemplo de saída:**
```
============================================================
MIGRAÇÃO DE TABELAS BREWFATHER
============================================================

Migrando brewfather_recipes -> plugin_integ_bFather_brewfather_recipes...
  ✅ Migrados 10 de 10 registros de brewfather_recipes para plugin_integ_bFather_brewfather_recipes

============================================================
✅ Migração concluída! Total de registros migrados: 10
============================================================

⚠️  IMPORTANTE: Após verificar que os dados foram migrados corretamente,
   você pode remover as tabelas antigas manualmente se desejar.
```

**⚠️ IMPORTANTE**: 
- Execute `flask recreate-plugin-tables` primeiro para criar as tabelas destino
- Verifique os dados após migração antes de remover tabelas antigas
- Faça backup do banco antes de migrações importantes

## Referências

- [Sistema de Plugins](PLUGIN_SYSTEM.md)
- [Sistema de Banco de Dados](PLUGIN_DATABASE.md)
- [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)
- [Configuração de Menu](PLUGIN_MENU_CONFIG.md)
- [Estrutura do install.json](PLUGIN_INSTALL_JSON.md)

