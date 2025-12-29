# Guia de Configuração - BrewStation

Este guia detalha todas as configurações disponíveis no BrewStation e como utilizá-las.

## Variáveis de Ambiente

O BrewStation utiliza variáveis de ambiente para configuração. Crie um arquivo `.env` em `src/` baseado em `config.env.modelo`.

### Segurança

```env
# Chave secreta para sessões Flask (OBRIGATÓRIO)
SECRET_KEY=sua-chave-secreta-forte-aqui

# Modo debug (True/False)
DEBUG=False

# Ambiente (DEV/PRD)
FLASK_ENV=PRD
```

**SECRET_KEY**: Gere uma chave forte:
```python
import secrets
print(secrets.token_hex(32))
```

### Banco de Dados

#### SQLite (Desenvolvimento)

```env
DATABASE_URL=sqlite:///instance/brewstation.db
```

#### PostgreSQL (Produção)

```env
DATABASE_URL=postgresql://usuario:senha@localhost:5432/brewstation
```

#### Neon (PostgreSQL Gerenciado)

```env
NEON_HOST=ep-xxx.us-east-2.aws.neon.tech
NEON_DATABASE=brewstation
NEON_USER=usuario
NEON_PASSWORD=senha
```

### Uploads

```env
# Diretório de uploads
UPLOAD_FOLDER=uploads

# Tamanho máximo de upload (bytes)
MAX_CONTENT_LENGTH=16777216  # 16MB
```

### Integração BrewFather

```env
# User ID do BrewFather
BREWFATHER_USER_ID=seu_user_id

# API Key do BrewFather
BREWFATHER_API_KEY=sua_api_key
```

**Como obter credenciais:**
1. Acesse https://web.brewfather.app/
2. Vá em Settings > API
3. Copie User ID e API Key

### E-mail (SMTP)

```env
# Servidor SMTP
MAIL_SERVER=smtp.gmail.com

# Porta SMTP
MAIL_PORT=587

# Usuário SMTP
MAIL_USERNAME=seu-email@gmail.com

# Senha SMTP
MAIL_PASSWORD=sua-senha

# Usar TLS
MAIL_USE_TLS=True

# Remetente padrão
MAIL_DEFAULT_SENDER=noreply@brewstation.com
```

**Configurações comuns:**

**Gmail:**
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

**Outlook:**
```env
MAIL_SERVER=smtp-mail.outlook.com
MAIL_PORT=587
MAIL_USE_TLS=True
```

**SendGrid:**
```env
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USERNAME=apikey
MAIL_PASSWORD=<sua-api-key>
MAIL_USE_TLS=True
```

## Configurações via Interface

Acesse `Configurações` no menu para configurar via interface web.

### Sistema

- **SECRET_KEY**: Chave secreta Flask
- **DEBUG**: Modo debug
- **UPLOAD_FOLDER**: Diretório de uploads
- **MAX_CONTENT_LENGTH**: Tamanho máximo de upload

### Integrações

- **BREWFATHER_USER_ID**: User ID do BrewFather
- **BREWFATHER_API_KEY**: API Key do BrewFather
- **BREWFATHER_ENABLED**: Habilitar/desabilitar integração

### E-mail

- **MAIL_SERVER**: Servidor SMTP
- **MAIL_PORT**: Porta SMTP
- **MAIL_USERNAME**: Usuário SMTP
- **MAIL_PASSWORD**: Senha SMTP
- **MAIL_USE_TLS**: Usar TLS

### Preferências do Usuário

As preferências do usuário são configuradas em `Perfil > Configurações`:

- **Notificações por Email**:
  - Alterações na conta
  - Novos produtos e serviços
  - Ofertas e promoções
  - Alertas de segurança (sempre ativo)

- **Preferências do Sistema**:
  - **Modo Escuro**: Alterna entre tema claro e escuro
    - A preferência é salva no banco de dados (`users.modo_escuro`)
    - Aplicada automaticamente em todas as páginas
    - Mantida entre sessões
    - Para mais detalhes técnicos, consulte [Documentação de Tema Escuro](DARK_THEME.md)

### Testar Configurações

Use o botão "Testar Configurações" para validar:
- Conexão com banco de dados
- Integração BrewFather
- Configuração de e-mail

## Configurações de Plugins

Cada plugin pode ter suas próprias configurações. Veja a documentação específica de cada plugin.

## Configurações de Logs

Os logs são configurados em `src/logs/setup_logging.py`.

**Estrutura de logs:**
```
logs/
├── application.log    # Logs gerais
├── errors.log         # Erros
├── devices.log        # Dispositivos IoT
└── brew_sessions.log  # Sessões de brassagem
```

**Níveis de log:**
- DEBUG: Informações detalhadas
- INFO: Informações gerais
- WARNING: Avisos
- ERROR: Erros
- CRITICAL: Erros críticos

## Configurações de Produção

### Gunicorn

Crie `gunicorn_config.py`:

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

### Nginx

Configuração básica:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/brewstation/src/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
```

### SSL/HTTPS

Use Let's Encrypt:

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d seu-dominio.com
```

## Variáveis de Ambiente por Ambiente

### Desenvolvimento

```env
FLASK_ENV=DEV
DEBUG=True
DATABASE_URL=sqlite:///instance/brewstation.db
```

### Produção

```env
FLASK_ENV=PRD
DEBUG=False
DATABASE_URL=postgresql://...
SECRET_KEY=<chave-forte>
```

## Segurança

### Boas Práticas

1. **Nunca commite o arquivo `.env`**
   - Adicione ao `.gitignore`
   - Use `config.env.modelo` como template

2. **Use chaves fortes**
   - Gere `SECRET_KEY` com `secrets.token_hex(32)`
   - Use senhas complexas para banco e SMTP

3. **Limite acesso ao `.env`**
   ```bash
   chmod 600 src/.env
   ```

4. **Use variáveis de ambiente do sistema**
   - Em produção, configure via sistema operacional
   - Evite hardcode de credenciais

5. **Rotacione credenciais regularmente**
   - Especialmente API keys e senhas

## Troubleshooting

### Configurações não aplicadas

**Verifique:**
- Arquivo `.env` existe em `src/`
- Variáveis estão corretas (sem espaços extras)
- Aplicação foi reiniciada após mudanças

### Erro de conexão com banco

**Verifique:**
- Credenciais corretas
- Banco de dados existe
- Serviço PostgreSQL rodando (se aplicável)
- Firewall permite conexão

### E-mails não enviados

**Verifique:**
- Credenciais SMTP corretas
- Porta não bloqueada por firewall
- TLS/SSL configurado corretamente
- Teste via "Testar Configurações"

### Integração BrewFather falha

**Verifique:**
- User ID e API Key corretos
- API Key não expirada
- Rate limit não excedido
- Teste via "Testar Configurações"

## Próximos Passos

- [Guia de Instalação](INSTALLATION.md)
- [Manual do Usuário](MANUAL.md)
- [Guia de Deploy](DEPLOYMENT.md)

