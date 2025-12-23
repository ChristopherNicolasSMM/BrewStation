# BrewStation 🍺

Plataforma web modular para controle de brassagens artesanais, classificação de ingredientes, precificação, estoque e relatórios – construída com Flask, SQLAlchemy e integração nativa com o BrewFather.

## Visão Geral

- **Público-alvo**: cervejarias artesanais, laboratórios de testes e homebrewers avançados.
- **Pilares**: catálogo de insumos, cálculo de custos, sincronização BrewFather, rastreabilidade de envase, notificações e painéis operacionais.
- **Stack**: Python 3.11+, Flask 3, SQLAlchemy 2, SQLite/PostgreSQL (Neon), Flask-Login, Flask-Mail, Pandas/OpenPyXL para importação/exportação.
- **Arquitetura**: Sistema modular com plugins extensíveis para adicionar funcionalidades dinamicamente.

## Funcionalidades Principais

### Catálogo e precificação
- CRUD completo de maltes, lúpulos e leveduras, com importação via planilhas-modelo (`/upload/modelo/<tipo>`).
- Criação de receitas locais ou a partir de sincronizações BrewFather.
- Motor de cálculo configurável (margens, impostos, custo de envase, sanitização, taxa de cartão).
- Relatórios consolidados com preço sugerido, custo por litro e margens previstas.

### Estoque, envase e custos
- Movimentações (entrada/saída/ajuste) com custo médio e alerta por estoque mínimo.
- Módulo de envase vinculado a lotes do BrewFather, incluindo embalagens, SKUs e quantidades produzidas.
- Cálculo de custo de produção (ingredientes + embalagens + operacionais) e sugestão de preço final.

### Operação e monitoramento
- Dashboard com indicadores de produção, notificações e status das integrações.
- Sistema de notificações com filtros (todas/lidas/não lidas/lixeira) e ações rápidas.
- Perfil de usuário completo (dados pessoais, redes sociais, preferências de alertas, troca de senha).

### Integrações
- **BrewFather**: sincronização de receitas, lotes e inventário, com cadastro automático dos insumos faltantes.
- **E-mail (SMTP)**: envio de notificações administrativas e workflow de solicitações de acesso.
- **Uploads/Relatórios**: importação e exportação em Excel com ajustes automáticos de layout.

### Sistema de Plugins
- Arquitetura modular extensível
- Instalação e ativação dinâmica de plugins
- Menu de navegação hierárquico configurável por plugin
- Configuração de menu separada em `menu_config.json`
- Templates e rotas isolados por plugin
- Suporte a múltiplos níveis de submenu

## Instalação Rápida

```bash
git clone <url>
cd BrewStation
python -m venv vEnvStation
.\vEnvStation\Scripts\activate   # Windows
source vEnvStation/bin/activate  # Linux/Mac
pip install -r requirements.txt
copy src\config.env.modelo src\.env   # Windows
cp src/config.env.modelo src/.env     # Linux/Mac
cd src
python main.py
```

Acesse `http://localhost:5000` com `admin / 123` (troque a senha no primeiro login via `Perfil > Segurança`).

Para instalação detalhada, veja o [Guia de Instalação](docs/INSTALLATION.md).

## Documentação Completa

### 📚 Guias Principais

- **[Guia de Instalação](docs/INSTALLATION.md)** - Instalação passo a passo em desenvolvimento e produção
- **[Manual do Usuário](docs/MANUAL.md)** - Guia completo de uso do sistema
- **[Guia de Configuração](docs/CONFIGURATION.md)** - Todas as configurações disponíveis
- **[Guia de Deploy](docs/DEPLOYMENT.md)** - Deploy em produção com Nginx e Gunicorn

### 🏗️ Arquitetura e Desenvolvimento

- **[Arquitetura do Sistema](docs/ARCHITECTURE.md)** - Estrutura técnica, componentes e fluxos
- **[Referência da API](docs/API_REFERENCE.md)** - Documentação completa das rotas API
- **[Sistema de Plugins](docs/PLUGIN_SYSTEM.md)** - Visão geral do sistema de plugins
- **[Desenvolvimento de Plugins](docs/PLUGIN_DEVELOPMENT.md)** - Guia completo para criar plugins
- **[Estrutura do install.json](docs/PLUGIN_INSTALL_JSON.md)** - Referência do arquivo de configuração de plugins

## Variáveis de Ambiente Essenciais

| Chave | Descrição |
|-------|-----------|
| `SECRET_KEY` | Chave Flask para sessões |
| `FLASK_ENV` | `DEV` (SQLite local) ou `PRD` (PostgreSQL/Neon) |
| `DATABASE_URL` ou `NEON_*` | Parâmetros de banco em produção |
| `BREWFATHER_USER_ID` / `BREWFATHER_API_KEY` | Credenciais API BrewFather |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS` | SMTP |
| `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH` | Controle de uploads |

Veja [Guia de Configuração](docs/CONFIGURATION.md) para detalhes completos.

## Estrutura de Pastas

```
BrewStation/
├── src/
│   ├── api/              # Rotas REST API
│   ├── controller/       # Rotas web (server-side render)
│   ├── core/             # Sistema de plugins
│   ├── db/               # Configuração SQLite/PostgreSQL
│   ├── model/            # Modelos SQLAlchemy
│   ├── plugins/          # Plugins do sistema
│   ├── services/         # Serviços de negócio
│   ├── templates/        # Templates HTML core
│   ├── static/           # CSS, JS, vendors, uploads
│   ├── utils/            # Utilitários
│   └── main.py           # Application factory
├── docs/                 # Documentação completa
└── requirements.txt       # Dependências Python
```

## Integração com o BrewFather

1. Configure `BREWFATHER_USER_ID` e `BREWFATHER_API_KEY` em `Configurações`.
2. Use as rotas `/api/brewfather/sync/*` para sincronizar receitas, lotes, inventário ou tudo de uma vez.
3. Cadastre automaticamente os ingredientes faltantes por receita (`/api/brewfather/recipe/<id>/cadastrar-insumos`).
4. Gere relatórios filtrados por lote, status ou intervalo de datas e exporte para Excel com métricas de OG, FG, ABV, IBU e eficiência.

Veja [Manual do Usuário](docs/MANUAL.md) para detalhes.

## Sistema de Plugins

O BrewStation possui um sistema modular de plugins que permite:

- ✅ Adicionar funcionalidades sem modificar o core
- ✅ Instalar/desinstalar plugins dinamicamente
- ✅ Configurar menu de navegação via JSON
- ✅ Isolar rotas, templates e modelos por plugin

### Comandos CLI de Plugins

```bash
# Listar plugins
flask plugin list

# Instalar plugin
flask plugin install <nome>

# Ativar plugin
flask plugin activate <nome>

# Informações do plugin
flask plugin info <nome>
```

Veja [Sistema de Plugins](docs/PLUGIN_SYSTEM.md) e [Desenvolvimento de Plugins](docs/PLUGIN_DEVELOPMENT.md) para mais informações.

## Observabilidade e Logs

- Estrutura sugerida: `logs/application.log`, `logs/errors.log`, `logs/devices.log`, `logs/brew_sessions.log`.
- A aplicação imprime no console os principais eventos (registro de blueprints, criação de admin, testes de conexão).
- Use `flask test-db` para validar rapidamente a camada de dados após implantações.

## Roadmap

- ✅ Catálogo completo de ingredientes e cálculo de preço.
- ✅ Integração BrewFather com cadastro automático de insumos.
- ✅ Relatórios exportáveis (BrewFather, ingredientes, estoque).
- ✅ Sistema de plugins modular.
- 🔜 Fluxo de aprovação/rejeição das solicitações de acesso.
- 🔜 Alertas automáticos (e-mail/Push) para estoque crítico e falhas de sincronização.
- 🔜 Interface de gerenciamento de plugins via web.

## Contribuindo

Contribuições são bem-vindas! Veja a documentação de desenvolvimento:
- [Arquitetura](docs/ARCHITECTURE.md)
- [Desenvolvimento de Plugins](docs/PLUGIN_DEVELOPMENT.md)
- [Referência da API](docs/API_REFERENCE.md)

## Suporte

- 📖 Consulte a [documentação completa](docs/)
- 🐛 Reporte bugs abrindo uma issue
- 💬 Dúvidas sobre uso: [Manual do Usuário](docs/MANUAL.md)
- 🔧 Dúvidas técnicas: [Arquitetura](docs/ARCHITECTURE.md)

---

**BrewStation** — do grão ao copo, com operação rastreável e precificação sob controle. 🍻⚙️
