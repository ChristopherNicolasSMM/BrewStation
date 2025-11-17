# BrewStation 🍺

Plataforma web para controle de brassagens artesanais, classificação de ingredientes, precificação, estoque e relatórios – construída com Flask, SQLAlchemy e integração nativa com o BrewFather.

## Visão Geral

- **Público-alvo**: cervejarias artesanais, laboratórios de testes e homebrewers avançados.
- **Pilares**: catálogo de insumos, cálculo de custos, sincronização BrewFather, rastreabilidade de envase, notificações e painéis operacionais.
- **Stack**: Python 3.11+, Flask 3, SQLAlchemy 2, SQLite/PostgreSQL (Neon), Flask-Login, Flask-Mail, Pandas/OpenPyXL para importação/exportação.

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

## Arquitetura & Tecnologias

| Camada | Diretório | Descrição |
|--------|-----------|-----------|
| Backend/API | `src/api`, `src/controller` | Blueprints REST e rotas server-side render |
| Modelos | `src/model` | ORM SQLAlchemy para usuários, ingredientes, estoque, BrewFather, etc. |
| Persistência | `src/db` | Configurações SQLite (dev) e PostgreSQL/Neon (prod) |
| Front-end | `src/templates`, `src/static` | Templates Jinja2 + assets (Bootstrap, ApexCharts, ECharts) |
| Utilidades | `src/utils` | Calculadoras e scripts auxiliares |

Fluxo padrão: navegador → rotas Flask → modelos SQLAlchemy → banco (SQLite/Neon) + integrações externas (BrewFather/SMTP).

## Instalação Rápida

```bash
git clone <url>
cd BrewStation
python -m venv vEnvStation
.\vEnvStation\Scripts\activate   # Windows
pip install -r requirements.txt
copy src\config.env.modelo src\.env   # Windows
cd src
python main.py
```

Acesse `http://localhost:5000` com `admin / admin123` (troque a senha no primeiro login via `Perfil > Segurança`).

## Variáveis de Ambiente Essenciais

| Chave | Descrição |
|-------|-----------|
| `SECRET_KEY` | Chave Flask para sessões |
| `FLASK_ENV` | `DEV` (SQLite local) ou `PRD` (PostgreSQL/Neon) |
| `DATABASE_URL` ou `NEON_*` | Parâmetros de banco em produção |
| `BREWFATHER_USER_ID` / `BREWFATHER_API_KEY` | Credenciais API BrewFather |
| `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USERNAME`, `MAIL_PASSWORD`, `MAIL_USE_TLS` | SMTP |
| `UPLOAD_FOLDER`, `MAX_CONTENT_LENGTH` | Controle de uploads |

## Estrutura de Pastas

```
src/
├── api/              # Rotas REST (config, ingredientes, receitas, estoque, BrewFather, etc.)
├── controller/       # Rotas web (dashboard, autenticação, perfil)
├── db/               # Configuração SQLite/Neon
├── model/            # Modelos SQLAlchemy
├── static/           # CSS, JS, vendors, uploads
├── templates/        # Layouts e páginas Jinja2
└── main.py           # Application factory + bootstrap
```

## Integração com o BrewFather

1. Configure `BREWFATHER_USER_ID` e `BREWFATHER_API_KEY` em `Configurações`.
2. Use as rotas `/api/brewfather/sync/*` para sincronizar receitas, lotes, inventário ou tudo de uma vez.
3. Cadastre automaticamente os ingredientes faltantes por receita (`/brewfather/recipe/<id>/cadastrar-insumos`).
4. Gere relatórios filtrados por lote, status ou intervalo de datas e exporte para Excel com métricas de OG, FG, ABV, IBU e eficiência.

## Observabilidade e Logs

- Estrutura sugerida: `logs/application.log`, `logs/errors.log`, `logs/devices.log`, `logs/brew_sessions.log`.
- A aplicação imprime no console os principais eventos (registro de blueprints, criação de admin, testes de conexão).
- Use `test_connection()` para validar rapidamente a camada de dados após implantações.

## Roadmap Breve

- ✅ Catálogo completo de ingredientes e cálculo de preço.
- ✅ Integração BrewFather com cadastro automático de insumos.
- ✅ Relatórios exportáveis (BrewFather, ingredientes, estoque).
- 🔜 Fluxo de aprovação/rejeição das solicitações de acesso.
- 🔜 Alertas automáticos (e-mail/Push) para estoque crítico e falhas de sincronização.

## Manual do Usuário

O passo a passo detalhado de uso (onboarding, rotinas diárias, integrações e troubleshooting) está no **[Manual do BrewStation](docs/MANUAL.md)**.

---
**BrewStation** — do grão ao copo, com operação rastreável e precificação sob controle. 🍻⚙️

