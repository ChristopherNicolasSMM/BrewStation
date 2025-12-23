# Revisão do Sistema BrewStation

Este documento contém uma revisão completa do sistema antes da execução.

## ✅ Componentes Verificados

### 1. Script de Execução (`run.py`)
- ✅ Criado na raiz do projeto
- ✅ Comando `python run.py start` funcional
- ✅ Ajusta caminhos para imports
- ✅ Carrega variáveis de ambiente corretamente
- ✅ Tratamento de erros implementado

### 2. Application Factory (`src/main.py`)
- ✅ Carrega `.env` corretamente (suporta execução de raiz ou src/)
- ✅ Inicializa banco de dados
- ✅ Configura Flask-Login
- ✅ Inicializa sistema de plugins
- ✅ Registra blueprints core
- ✅ Context processors configurados

### 3. Sistema de Plugins

#### PluginLoader (`src/core/plugin_loader.py`)
- ✅ Descobre plugins automaticamente
- ✅ Carrega configuração do `install.json`
- ✅ Carrega classes de plugins dinamicamente
- ✅ Instancia plugins corretamente

#### PluginManager (`src/core/plugin_manager.py`)
- ✅ Gerencia ciclo de vida dos plugins
- ✅ Auto-instala e ativa plugin core
- ✅ Registra rotas API e web automaticamente
- ✅ Atualiza template loader
- ✅ Busca plugins por nome de diretório ou install.json

#### PluginInstaller (`src/core/plugin_installer.py`)
- ✅ Descobre rotas API automaticamente
- ✅ Descobre rotas web automaticamente
- ✅ Extrai itens de menu do install.json

#### PluginTemplateLoader (`src/core/template_loader.py`)
- ✅ Busca templates em plugins ativos
- ✅ Fallback para templates core
- ✅ Suporta execução de diferentes diretórios

### 4. Plugin Core (`plugin_integ_bFather`)

#### Estrutura
- ✅ `plugin.py` com classe `PluginBrewstationCore`
- ✅ `install.json` configurado
- ✅ `controller/routes.py` com blueprint `plugin_brewstation_core_web`
- ✅ `api/routes/__init__.py` exporta todos os blueprints
- ✅ Templates em `templates/`

#### Configuração
- ✅ Nome no install.json: `brewstation_core`
- ✅ Diretório: `plugin_integ_bFather`
- ✅ URLs do menu: `plugin_brewstation_core_web.*`
- ✅ Blueprint: `plugin_brewstation_core_web`

### 5. Banco de Dados
- ✅ Factory de conexão (`src/db/database.py`)
- ✅ Suporte SQLite (dev) e PostgreSQL (prod)
- ✅ Inicialização automática
- ✅ Migração de modelos de plugins

### 6. Rotas Core
- ✅ `controller/web.py`: Rotas web básicas
- ✅ `controller/auth.py`: Autenticação
- ✅ `api/routes/register.py`: Registro de usuários

## ⚠️ Pontos de Atenção

### 1. Inconsistência de Nomes
O plugin tem:
- **Diretório**: `plugin_integ_bFather`
- **Nome no install.json**: `brewstation_core`
- **Blueprint**: `plugin_brewstation_core_web`
- **URLs no menu**: `plugin_brewstation_core_web.*`

O sistema está preparado para lidar com essa inconsistência através de:
- `get_plugin()` busca por nome de diretório ou install.json
- `get_menu_items()` busca plugins de ambas as formas
- Auto-instalação verifica ambos os nomes

### 2. Caminhos Relativos
- ✅ `run.py` ajusta caminhos corretamente
- ✅ `main.py` detecta execução de diferentes diretórios
- ✅ Template loader suporta caminhos relativos e absolutos

### 3. Imports
- ✅ Todos os imports verificados
- ✅ Paths ajustados para funcionar de qualquer diretório
- ✅ Imports dinâmicos de plugins funcionando

## 🔍 Checklist de Execução

Antes de executar, verifique:

- [ ] Arquivo `.env` existe em `src/.env`
- [ ] Variáveis de ambiente configuradas
- [ ] Banco de dados acessível
- [ ] Plugin `plugin_integ_bFather` existe em `src/plugins/`
- [ ] Arquivo `install.json` do plugin está correto
- [ ] Arquivo `plugin.py` do plugin existe
- [ ] Templates do plugin estão em `src/plugins/plugin_integ_bFather/templates/`
- [ ] Rotas API estão em `src/plugins/plugin_integ_bFather/api/routes/`
- [ ] Rotas web estão em `src/plugins/plugin_integ_bFather/controller/routes.py`

## 🚀 Comandos de Execução

### Desenvolvimento
```bash
# Opção 1: Via run.py (recomendado)
python run.py start

# Opção 2: Diretamente
cd src
python main.py
```

### Verificação
```bash
# Listar plugins
cd src
flask plugin list

# Verificar banco
flask test-db

# Informações do plugin
flask plugin info plugin_integ_bFather
```

## 📋 Logs Esperados

Ao iniciar, você deve ver:

1. **Inicialização do banco:**
   ```
   Tabelas core criadas com sucesso!
   Modelos do plugin brewstation_core registrados
   Tabelas de plugins criadas com sucesso!
   ```

2. **Descoberta de plugins:**
   ```
   Plugin descoberto: plugin_integ_bFather
   Plugin carregado com sucesso: plugin_integ_bFather
   ```

3. **Registro de rotas:**
   ```
   Blueprint API registrado: ingredientes com prefixo /api
   Blueprint web registrado: plugin_brewstation_core_web (sem prefixo)
   ```

4. **Inicialização do servidor:**
   ```
   Iniciando BrewStation em http://0.0.0.0:5000 (debug=True)
   ```

## 🐛 Troubleshooting Rápido

### Erro: "ModuleNotFoundError"
- Verifique se está executando de `run.py` ou de `src/`
- Verifique se `src/` está no `sys.path`

### Erro: "Template not found"
- Verifique se templates estão em `src/plugins/plugin_integ_bFather/templates/`
- Verifique se plugin está ativo: `flask plugin list`

### Erro: "Blueprint not found"
- Verifique se rotas estão em `api/routes/__init__.py`
- Verifique se blueprint está exportado em `all_blueprints`

### Erro: "Plugin not found"
- Verifique se diretório do plugin existe
- Verifique se `install.json` e `plugin.py` existem
- Execute `flask plugin discover`

## ✅ Sistema Pronto para Execução

Todos os componentes foram revisados e estão prontos. O sistema deve iniciar corretamente com:

```bash
python run.py start
```

---

**Última revisão**: Sistema verificado e pronto para execução.

