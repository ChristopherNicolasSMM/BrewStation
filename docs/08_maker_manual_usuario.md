# Manual do Usuário: Plugin Maker

Bem-vindo ao **Manual Oficial do Plugin Maker**, a fábrica de extensões (Scaffolding Engine) da **BrewStation**.

O Plugin Maker é uma extensão nativa que roda dentro da plataforma para construir **outros plugins**. Em vez de codificar rotas repetidamente e conectar bancos SQL do zero, o Maker lê Metadados (Projetos, Tabelas, Colunas) e ejeta de imediato modelos robustos seguindo estritamente a arquitetura de **Estação de Trabalho Inteligente** (v2.0).

---

## 1. O Conceito de Metamodelo

O Maker trabalha catalogando o seu projeto futuro no próprio banco de dados SQLite/PostgreSQL antes mesmo das linhas de código nascerem:

1. **`MakerProject`**: As configurações globais do plugin (Nome, Meta, Prefixo das Tabelas e Autor).
2. **`MakerTable` / `MakerColumn`**: O mapeamento das tabelas de negócio e colunas (como `varchar`, `int`, `uuid`) que o módulo gerenciará.
3. **`MakerScreen` (Views)**: O planejamento de como o Frontend (Jinja2/NiceAdmin) exibirá os modais e relatórios.

---

## 2. Palavras Reservadas (Parser Safety)

A nova engine de proteção contra corrupção bloqueia que nomes perigosos sejam escolhidos pelos arquitetos. 
Ao batizar Projetos, Tabelas ou Colunas **nunca** empregue palavras estritas da sintaxe SQL ou Python, como:
- `select`, `insert`, `update`, `delete`, `table`, `column`
- `def`, `class`, `import`, `return`, `from`

A API devolverá Status 400 (Bad Request) apontando imediatamente uma infração de segurança caso o Parser Safety intervenha.

---

## 3. Segurança de Reconstrução: *Guarded Blocks*

Ao executar a reconstrução do módulo (`POST /projects/<id>/rebuild/apply`), o Maker injeta silenciosamente um diretório físico recheado de controladores automáticos (Rotas HTML, JSON de Menus, Arquivo-Mestre em `plugin.py`).

**E como proteger as edições personalizadas do desenvolvedor?**
O engine de Regeração **nunca** destrói seus arquivos na brutalidade. Seus algoritmos mapeiam as fronteiras conhecidas como **Guarded Blocks** (Blocos Guardiões).

No meio do seu código fonte gerado (como o diretório de `api/routes/generated_routes.py`), você observará as seguintes diretivas comentadas:

```python
# [MAKER_ROUTES_API_START]
... (Rotas Geradas Automaticamente pelo Sistema) ...
# [MAKER_ROUTES_API_END]

# Insira rotas de API customizadas abaixo desta linha
@meu_plugin_api.get("/minhas_rotas_manuais")
def teste():
    pass
```

Se precisar clicar em "Gerar Código (Rebuild)" no Web Interface ou na API do Maker após ter editado o arquivo para inserir uma regra de frete ou imposto manual, todo código fora ou além da fronteira (`_END`) será **imaculadamente preservado**.

---

## 4. Gerenciamento e Endpoints Básicos (MVP)

Acesse o Maker sob a rota-base da aplicação (Autenticado como Admin):

- `GET /api/maker/info`: Verifica o Status Vital do Maker.
- `GET /api/maker/projects`: Lista de metadados planejados.
- `POST /api/maker/projects/<id>/rebuild/apply`: Engatilha a fábrica de pastas para ejetar localmente seu módulo sob a pasta física de extensões (`src/plugins/ plugin_seu_sistema`).
