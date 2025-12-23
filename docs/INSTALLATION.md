# Guia de Instalação - BrewStation

Este guia fornece instruções detalhadas para instalar e configurar o BrewStation em diferentes ambientes.

## Requisitos do Sistema

### Software Necessário

- **Python**: 3.11 ou superior
- **pip**: Gerenciador de pacotes Python
- **Git**: Para clonar o repositório (opcional)
- **Banco de Dados**: SQLite (desenvolvimento) ou PostgreSQL (produção)

### Dependências Python

Todas as dependências estão listadas em `requirements.txt`:

- Flask 3.x
- SQLAlchemy 2.x
- Flask-Login
- Flask-Mail
- Flask-CORS
- python-dotenv
- pandas
- openpyxl

## Instalação em Desenvolvimento

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd BrewStation
```

### 2. Criar Ambiente Virtual

**Windows:**
```bash
python -m venv vEnvStation
.\vEnvStation\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv vEnvStation
source vEnvStation/bin/activate
```

### 3. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar Variáveis de Ambiente

Copie o arquivo de modelo e configure:

**Windows:**
```bash
copy src\config.env.modelo src\.env
```

**Linux/Mac:**
```bash
cp src/config.env.modelo src/.env
```

Edite o arquivo `src/.env` com suas configurações:

```env
# Segurança
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
FLASK_ENV=DEV

# Banco de Dados (SQLite para desenvolvimento)
DATABASE_URL=sqlite:///instance/brewstation.db

# Uploads
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# BrewFather (opcional)
BREWFATHER_USER_ID=
BREWFATHER_API_KEY=

# E-mail (opcional)
MAIL_SERVER=
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_USE_TLS=True
```

### 5. Inicializar o Banco de Dados

```bash
cd src
python main.py
```

Na primeira execução, o sistema criará:
- Banco de dados SQLite
- Tabelas necessárias
- Usuário administrador padrão (admin/123)

### 6. Acessar a Aplicação

Abra seu navegador em: `http://localhost:5000`

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `123`

⚠️ **IMPORTANTE**: Altere a senha no primeiro login!

## Instalação em Produção

### 1. Preparar Ambiente

```bash
# Criar diretório de produção
mkdir -p /opt/brewstation
cd /opt/brewstation

# Clonar repositório
git clone <url> .

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Configurar PostgreSQL

Instale e configure PostgreSQL:

```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# Criar banco de dados
sudo -u postgres psql
CREATE DATABASE brewstation;
CREATE USER brewstation_user WITH PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE brewstation TO brewstation_user;
\q
```

### 3. Configurar Variáveis de Ambiente

Crie `src/.env` com configurações de produção:

```env
SECRET_KEY=<chave-secreta-forte>
DEBUG=False
FLASK_ENV=PRD

# PostgreSQL
DATABASE_URL=postgresql://brewstation_user:senha_segura@localhost/brewstation

# Ou Neon (PostgreSQL gerenciado)
NEON_HOST=ep-xxx.us-east-2.aws.neon.tech
NEON_DATABASE=brewstation
NEON_USER=brewstation_user
NEON_PASSWORD=senha_segura

# Outras configurações...
```

### 4. Configurar Servidor Web (Nginx + Gunicorn)

**Instalar Gunicorn:**
```bash
pip install gunicorn
```

**Criar arquivo de configuração Gunicorn (`gunicorn_config.py`):**
```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
```

**Configurar Nginx (`/etc/nginx/sites-available/brewstation`):**
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
    }
}
```

**Habilitar site:**
```bash
sudo ln -s /etc/nginx/sites-available/brewstation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 5. Criar Serviço Systemd

Crie `/etc/systemd/system/brewstation.service`:

```ini
[Unit]
Description=BrewStation Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/brewstation/src
Environment="PATH=/opt/brewstation/venv/bin"
ExecStart=/opt/brewstation/venv/bin/gunicorn \
    --config /opt/brewstation/gunicorn_config.py \
    main:app

[Install]
WantedBy=multi-user.target
```

**Iniciar serviço:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable brewstation
sudo systemctl start brewstation
sudo systemctl status brewstation
```

## Verificação da Instalação

### Testar Conexão com Banco

```bash
cd src
flask test-db
```

### Listar Plugins Instalados

```bash
flask plugin list
```

### Verificar Logs

```bash
tail -f logs/application.log
tail -f logs/errors.log
```

## Troubleshooting

### Erro: "ModuleNotFoundError"

**Solução:** Verifique se o ambiente virtual está ativado e as dependências instaladas:
```bash
pip install -r requirements.txt
```

### Erro: "Database connection failed"

**Solução:** Verifique as credenciais no `.env` e se o banco de dados está rodando:
```bash
# PostgreSQL
sudo systemctl status postgresql

# SQLite
ls -la src/instance/brewstation.db
```

### Erro: "Port already in use"

**Solução:** Altere a porta ou pare o processo:
```bash
# Verificar processo na porta 5000
lsof -i :5000

# Matar processo
kill -9 <PID>
```

### Erro: "Permission denied"

**Solução:** Ajuste permissões:
```bash
chmod -R 755 src/
chown -R www-data:www-data src/static/uploads/
```

## Próximos Passos

Após a instalação:

1. ✅ Configure as integrações (BrewFather, E-mail)
2. ✅ Importe seus ingredientes
3. ✅ Configure usuários e permissões
4. ✅ Leia o [Manual do Usuário](MANUAL.md)
5. ✅ Explore a [Documentação de Plugins](PLUGIN_SYSTEM.md)

## Suporte

Para problemas de instalação:
- Verifique os logs em `logs/`
- Consulte a [Documentação de Configuração](CONFIGURATION.md)
- Abra uma issue no repositório

