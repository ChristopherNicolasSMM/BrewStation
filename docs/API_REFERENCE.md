# Referência da API - BrewStation

Esta documentação descreve todas as rotas API disponíveis no BrewStation.

## Autenticação

A maioria das rotas requer autenticação. Use Flask-Login para gerenciar sessões.

**Headers necessários:**
```
Cookie: session=<session_id>
```

## Base URL

```
http://localhost:5000/api
```

## Endpoints

### Configurações

#### GET /api/configuracoes
Retorna todas as configurações do sistema.

**Resposta:**
```json
{
  "configuracoes": {
    "SECRET_KEY": "***",
    "BREWFATHER_USER_ID": "user123",
    ...
  },
  "campos_configurados": {
    "SECRET_KEY": true,
    ...
  }
}
```

#### POST /api/configuracoes
Salva configurações do sistema.

**Body:**
```json
{
  "BREWFATHER_USER_ID": "user123",
  "BREWFATHER_API_KEY": "key456",
  ...
}
```

#### POST /api/configuracoes/testar
Testa configurações (banco, BrewFather, e-mail).

**Resposta:**
```json
{
  "success": true,
  "database": "connected",
  "brewfather": "connected",
  "email": "connected"
}
```

### Ingredientes

#### GET /api/maltes
Lista todos os maltes ativos.

**Resposta:**
```json
[
  {
    "id": 1,
    "nome": "Pilsen",
    "fabricante": "Weyermann",
    "cor_ebc": 3.5,
    "preco_kg": 12.50,
    ...
  }
]
```

#### GET /api/maltes/{id}
Retorna um malte específico.

#### POST /api/maltes
Cria um novo malte.

**Body:**
```json
{
  "nome": "Pilsen",
  "fabricante": "Weyermann",
  "cor_ebc": 3.5,
  "poder_diastatico": 120,
  "rendimento": 80,
  "preco_kg": 12.50,
  "tipo": "base"
}
```

#### PUT /api/maltes/{id}
Atualiza um malte.

#### DELETE /api/maltes/{id}
Desativa um malte (soft delete).

#### GET /api/lupulos
Lista todos os lúpulos ativos.

#### GET /api/lupulos/{id}
Retorna um lúpulo específico.

#### POST /api/lupulos
Cria um novo lúpulo.

**Body:**
```json
{
  "nome": "Cascade",
  "fabricante": "US Hops",
  "alpha_acidos": 5.5,
  "beta_acidos": 4.8,
  "formato": "pellet",
  "origem": "EUA",
  "preco_kg": 45.00,
  "aroma": "Cítrico, floral"
}
```

#### GET /api/leveduras
Lista todas as leveduras ativas.

#### POST /api/leveduras
Cria uma nova levedura.

**Body:**
```json
{
  "nome": "Safale US-05",
  "fabricante": "Fermentis",
  "formato": "seca",
  "atenuacao": 78,
  "temp_fermentacao": 18,
  "preco_unidade": 8.50,
  "floculacao": "média"
}
```

### Receitas

#### GET /api/receitas
Lista todas as receitas.

#### GET /api/receitas/{id}
Retorna uma receita específica.

#### POST /api/receitas
Cria uma nova receita.

#### PUT /api/receitas/{id}
Atualiza uma receita.

#### DELETE /api/receitas/{id}
Remove uma receita.

### Estoque

#### GET /api/estoque
Lista estoque atual de ingredientes.

#### POST /api/estoque/movimentacao
Registra uma movimentação (entrada/saída/ajuste).

**Body:**
```json
{
  "ingrediente_id": 1,
  "tipo": "entrada",
  "quantidade": 50,
  "custo_unitario": 12.50,
  "lote": "LOTE001",
  "validade": "2025-12-31"
}
```

### BrewFather

#### POST /api/brewfather/sync/recipes
Sincroniza receitas do BrewFather.

#### POST /api/brewfather/sync/batches
Sincroniza lotes do BrewFather.

#### POST /api/brewfather/sync/inventory
Sincroniza inventário do BrewFather.

#### POST /api/brewfather/sync/all
Sincroniza tudo (receitas, lotes, inventário).

#### POST /api/brewfather/recipe/{id}/cadastrar-insumos
Cadastra automaticamente ingredientes faltantes de uma receita.

### Cálculos

#### POST /api/calculos
Calcula preço de uma receita.

**Body:**
```json
{
  "receita_id": 1,
  "volume_litros": 20,
  "margem_percentual": 30,
  "impostos_percentual": 15,
  "custo_envase": 2.50,
  "custo_sanitizacao": 0.50,
  "taxa_cartao_percentual": 3
}
```

**Resposta:**
```json
{
  "custo_ingredientes": 45.00,
  "custo_total": 48.00,
  "preco_sugerido": 62.40,
  "margem_real": 29.8
}
```

### Upload

#### GET /api/upload/modelo/{tipo}
Baixa planilha modelo para importação.

**Tipos:** `maltes`, `lupulos`, `leveduras`

#### POST /api/upload/importar
Importa dados de planilha Excel.

**Body:** FormData com arquivo `.xlsx`

### Perfil e Preferências do Usuário

#### GET /api/auth/profile
Retorna dados do perfil do usuário autenticado.

**Resposta:**
```json
{
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@example.com",
    "nome_completo": "Administrador",
    "modo_escuro": false,
    ...
  }
}
```

#### POST /api/atualizar_perfil
Atualiza dados do perfil do usuário.

**Body:**
```json
{
  "nome_completo": "Nome Completo",
  "empresa": "Empresa",
  "cargo": "Cargo",
  ...
}
```

#### POST /api/atualizar_configuracoes
Atualiza preferências de notificação e sistema.

**Body:**
```json
{
  "notificacao_alteracoes": true,
  "notificacao_novos_produtos": false,
  "notificacao_ofertas": true,
  "modo_escuro": true
}
```

#### POST /api/auth/update_theme
Atualiza a preferência de tema (claro/escuro) do usuário.

**Body:**
```json
{
  "modo_escuro": true
}
```

**Resposta:**
```json
{
  "message": "Tema atualizado com sucesso",
  "modo_escuro": true
}
```

**Códigos de Status:**
- `200 OK`: Tema atualizado com sucesso
- `400 Bad Request`: Dados inválidos
- `401 Unauthorized`: Não autenticado
- `500 Internal Server Error`: Erro ao atualizar tema

### Notificações

#### GET /api/notifications
Lista notificações do usuário.

**Query params:**
- `filter`: `all`, `unread`, `read`, `trash`

#### POST /api/notifications
Cria uma nova notificação.

#### PUT /api/notifications/{id}/read
Marca notificação como lida.

#### DELETE /api/notifications/{id}
Remove notificação.

### Dashboard

#### GET /api/dashboard/stats
Retorna estatísticas do dashboard.

**Resposta:**
```json
{
  "total_receitas": 15,
  "total_lotes": 8,
  "estoque_critico": 3,
  "notificacoes_nao_lidas": 5
}
```

## Códigos de Status HTTP

- `200 OK`: Requisição bem-sucedida
- `201 Created`: Recurso criado
- `400 Bad Request`: Dados inválidos
- `401 Unauthorized`: Não autenticado
- `403 Forbidden`: Sem permissão
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro do servidor

## Formato de Erro

```json
{
  "error": "Mensagem de erro",
  "details": "Detalhes adicionais (opcional)"
}
```

## Exemplos de Uso

### cURL

```bash
# Listar maltes
curl -X GET http://localhost:5000/api/maltes \
  -H "Cookie: session=<session_id>"

# Criar malte
curl -X POST http://localhost:5000/api/maltes \
  -H "Content-Type: application/json" \
  -H "Cookie: session=<session_id>" \
  -d '{
    "nome": "Pilsen",
    "fabricante": "Weyermann",
    "cor_ebc": 3.5,
    "preco_kg": 12.50
  }'
```

### JavaScript (Fetch)

```javascript
// Listar maltes
fetch('/api/maltes', {
  credentials: 'include'
})
  .then(response => response.json())
  .then(data => console.log(data));

// Criar malte
fetch('/api/maltes', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  credentials: 'include',
  body: JSON.stringify({
    nome: 'Pilsen',
    fabricante: 'Weyermann',
    cor_ebc: 3.5,
    preco_kg: 12.50
  })
})
  .then(response => response.json())
  .then(data => console.log(data));
```

### Python (Requests)

```python
import requests

session = requests.Session()

# Login
response = session.post('http://localhost:5000/auth/login', data={
    'username': 'admin',
    'password': '123'
})

# Listar maltes
response = session.get('http://localhost:5000/api/maltes')
maltes = response.json()

# Criar malte
response = session.post('http://localhost:5000/api/maltes', json={
    'nome': 'Pilsen',
    'fabricante': 'Weyermann',
    'cor_ebc': 3.5,
    'preco_kg': 12.50
})
```

## Rate Limiting

Atualmente não há rate limiting implementado. Em produção, considere adicionar.

## Versionamento

A API atual é v1. Futuras versões podem usar prefixo `/api/v2/`.

## Documentação Adicional

- [Manual do Usuário](MANUAL.md)
- [Arquitetura](ARCHITECTURE.md)
- [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)

