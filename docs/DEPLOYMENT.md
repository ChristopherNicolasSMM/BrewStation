# Guia de Deploy - BrewStation

Este guia fornece instruções para fazer deploy do BrewStation em produção.

## Pré-requisitos

- Servidor Linux (Ubuntu 20.04+ recomendado)
- Python 3.11+
- PostgreSQL (ou Neon)
- Nginx
- Gunicorn
- Certificado SSL (Let's Encrypt)

## Preparação do Servidor

### 1. Atualizar Sistema

```bash
sudo apt update
sudo apt upgrade -y
```

### 2. Instalar Dependências

```bash
sudo apt install -y python3 python3-pip python3-venv postgresql nginx git
```

### 3. Criar Usuário

```bash
sudo adduser --system --group brewstation
sudo mkdir -p /opt/brewstation
sudo chown brewstation:brewstation /opt/brewstation
```

## Deploy da Aplicação

### 1. Clonar Repositório

```bash
cd /opt/brewstation
sudo -u brewstation git clone <url-do-repositorio> .
```

### 2. Criar Ambiente Virtual

```bash
sudo -u brewstation python3 -m venv venv
sudo -u brewstation venv/bin/pip install --upgrade pip
sudo -u brewstation venv/bin/pip install -r requirements.txt
sudo -u brewstation venv/bin/pip install gunicorn
```

### 3. Configurar Variáveis de Ambiente

```bash
sudo -u brewstation cp src/config.env.modelo src/.env
sudo -u brewstation nano src/.env
```

Configure todas as variáveis necessárias (veja [CONFIGURATION.md](CONFIGURATION.md)).

### 4. Configurar Banco de Dados

```bash
sudo -u postgres psql
```

```sql
CREATE DATABASE brewstation;
CREATE USER brewstation_user WITH PASSWORD 'senha_segura';
GRANT ALL PRIVILEGES ON DATABASE brewstation TO brewstation_user;
\q
```

### 5. Inicializar Banco

```bash
cd /opt/brewstation/src
sudo -u brewstation ../venv/bin/python main.py
```

Isso criará as tabelas e o usuário admin inicial.

## Configurar Gunicorn

### 1. Criar Arquivo de Configuração

```bash
sudo -u brewstation nano /opt/brewstation/gunicorn_config.py
```

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
accesslog = "/opt/brewstation/logs/gunicorn_access.log"
errorlog = "/opt/brewstation/logs/gunicorn_error.log"
loglevel = "info"
```

### 2. Criar Diretório de Logs

```bash
sudo -u brewstation mkdir -p /opt/brewstation/logs
```

## Configurar Systemd

### 1. Criar Serviço

```bash
sudo nano /etc/systemd/system/brewstation.service
```

```ini
[Unit]
Description=BrewStation Gunicorn daemon
After=network.target postgresql.service

[Service]
User=brewstation
Group=brewstation
WorkingDirectory=/opt/brewstation/src
Environment="PATH=/opt/brewstation/venv/bin"
EnvironmentFile=/opt/brewstation/src/.env
ExecStart=/opt/brewstation/venv/bin/gunicorn \
    --config /opt/brewstation/gunicorn_config.py \
    main:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Habilitar e Iniciar

```bash
sudo systemctl daemon-reload
sudo systemctl enable brewstation
sudo systemctl start brewstation
sudo systemctl status brewstation
```

## Configurar Nginx

### 1. Criar Configuração

```bash
sudo nano /etc/nginx/sites-available/brewstation
```

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    # Redirecionar para HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com;

    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;

    # Configurações SSL
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Tamanho máximo de upload
    client_max_body_size 16M;

    # Proxy para Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # Arquivos estáticos
    location /static {
        alias /opt/brewstation/src/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Uploads
    location /static/uploads {
        alias /opt/brewstation/src/static/uploads;
        expires 7d;
    }
}
```

### 2. Habilitar Site

```bash
sudo ln -s /etc/nginx/sites-available/brewstation /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Configurar SSL com Let's Encrypt

### 1. Instalar Certbot

```bash
sudo apt install certbot python3-certbot-nginx
```

### 2. Obter Certificado

```bash
sudo certbot --nginx -d seu-dominio.com
```

Certbot configurará automaticamente o Nginx.

### 3. Renovação Automática

Certbot cria um timer systemd para renovação automática. Verifique:

```bash
sudo systemctl status certbot.timer
```

## Firewall

### Configurar UFW

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## Monitoramento

### 1. Logs da Aplicação

```bash
# Logs do Gunicorn
sudo journalctl -u brewstation -f

# Logs do Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Logs da aplicação
sudo tail -f /opt/brewstation/logs/application.log
```

### 2. Status dos Serviços

```bash
sudo systemctl status brewstation
sudo systemctl status nginx
sudo systemctl status postgresql
```

## Atualizações

### Script de Atualização

Crie `/opt/brewstation/update.sh`:

```bash
#!/bin/bash
set -e

cd /opt/brewstation
sudo -u brewstation git pull
sudo -u brewstation venv/bin/pip install -r requirements.txt
sudo systemctl restart brewstation
echo "Atualização concluída!"
```

```bash
sudo chmod +x /opt/brewstation/update.sh
```

### Executar Atualização

```bash
sudo /opt/brewstation/update.sh
```

## Backup

### 1. Script de Backup

Crie `/opt/brewstation/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/brewstation"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup do banco
sudo -u postgres pg_dump brewstation > $BACKUP_DIR/db_$DATE.sql

# Backup de uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/brewstation/src/static/uploads

# Manter apenas últimos 7 dias
find $BACKUP_DIR -type f -mtime +7 -delete
```

### 2. Agendar Backup

```bash
sudo crontab -e
```

Adicione:
```
0 2 * * * /opt/brewstation/backup.sh
```

## Troubleshooting

### Aplicação não inicia

```bash
# Verificar logs
sudo journalctl -u brewstation -n 50

# Verificar permissões
ls -la /opt/brewstation/src/.env

# Testar manualmente
cd /opt/brewstation/src
sudo -u brewstation ../venv/bin/python main.py
```

### Erro 502 Bad Gateway

- Verificar se Gunicorn está rodando: `sudo systemctl status brewstation`
- Verificar porta 8000: `sudo netstat -tlnp | grep 8000`
- Verificar logs do Nginx: `sudo tail -f /var/log/nginx/error.log`

### Erro de conexão com banco

- Verificar PostgreSQL: `sudo systemctl status postgresql`
- Testar conexão: `psql -U brewstation_user -d brewstation`
- Verificar `.env`: Credenciais corretas

## Segurança

### 1. Atualizar Regularmente

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Firewall

Configure UFW adequadamente (veja seção Firewall).

### 3. Permissões

```bash
# Arquivo .env
sudo chmod 600 /opt/brewstation/src/.env

# Diretórios
sudo chmod 755 /opt/brewstation/src
sudo chmod -R 755 /opt/brewstation/src/static
```

### 4. Fail2Ban (Opcional)

Proteção contra brute force:

```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## Próximos Passos

- [Configuração](CONFIGURATION.md)
- [Manual do Usuário](MANUAL.md)
- [Monitoramento e Logs](ARCHITECTURE.md#observabilidade-e-logs)

