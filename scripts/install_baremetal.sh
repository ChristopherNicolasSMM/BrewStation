#!/usr/bin/env bash
# BrewStation Install Script (bare-metal)
# Installs all system dependencies and configures the application for production.
# Usage: sudo ./scripts/install_baremetal.sh seu-dominio.com [email-para-certbot]

set -euo pipefail

APP_USER="brewstation"
APP_GROUP="brewstation"
APP_DIR="/opt/brewstation"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="brewstation"
DOMAIN="${1:-}"
EMAIL="${2:-}"

if [[ -z "$DOMAIN" ]]; then
  echo "Uso: sudo ./scripts/install_baremetal.sh seu-dominio.com [email-certbot]"
  exit 1
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "Execute como root: sudo ./scripts/install_baremetal.sh $DOMAIN [email-certbot]"
  exit 1
fi

if [[ ! -d "$APP_DIR" ]]; then
  echo "Diretório $APP_DIR não encontrado. Clone o BrewStation antes em $APP_DIR."
  exit 1
fi

# ---------------------------------------------------------------
# 1. System dependencies
# ---------------------------------------------------------------
export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y python3 python3-venv python3-pip nginx git ufw certbot python3-certbot-nginx openssh-server

# ---------------------------------------------------------------
# 2. Application user
# ---------------------------------------------------------------
if ! id "$APP_USER" >/dev/null 2>&1; then
  adduser --system --group --home "$APP_DIR" "$APP_USER"
fi
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

# ---------------------------------------------------------------
# 3. Python virtual environment
# ---------------------------------------------------------------
if [[ ! -d "$VENV_DIR" ]]; then
  sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
fi
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

# ---------------------------------------------------------------
# 4. Environment file
# ---------------------------------------------------------------
if [[ ! -f "$APP_DIR/src/.env" ]]; then
  if [[ -f "$APP_DIR/src/config.env.modelo" ]]; then
    sudo -u "$APP_USER" cp "$APP_DIR/src/config.env.modelo" "$APP_DIR/src/.env"
    echo "Arquivo src/.env criado a partir de src/config.env.modelo. Revise ANTES de usar."
  else
    echo "Aviso: src/config.env.modelo não encontrado. Crie manualmente $APP_DIR/src/.env"
  fi
fi

# ---------------------------------------------------------------
# 5. Scripts e systemd
# ---------------------------------------------------------------
install -m 755 "$APP_DIR/scripts/start_brewstation.sh" /usr/local/bin/start_brewstation.sh
install -m 755 "$APP_DIR/scripts/healthcheck.sh" /usr/local/bin/brewstation-healthcheck

# Instalar serviço systemd (da pasta old_project para referência histórica)
if [[ -f "$APP_DIR/old_project/systemd/brewstation.service" ]]; then
  cp "$APP_DIR/old_project/systemd/brewstation.service" "/etc/systemd/system/${SERVICE_NAME}.service"
  systemctl daemon-reload
  systemctl enable "$SERVICE_NAME"
else
  echo "Aviso: systemd service file não encontrado em old_project/systemd/brewstation.service"
fi

# ---------------------------------------------------------------
# 6. Nginx
# ---------------------------------------------------------------
if [[ -f "$APP_DIR/nginx/brewstation.conf" ]]; then
  cp "$APP_DIR/nginx/brewstation.conf" "/etc/nginx/sites-available/${SERVICE_NAME}"
  sed -i "s/__DOMAIN__/${DOMAIN}/g" "/etc/nginx/sites-available/${SERVICE_NAME}"
  if [[ ! -f "/etc/nginx/sites-enabled/${SERVICE_NAME}" ]]; then
    ln -s "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/"
  fi
  rm -f /etc/nginx/sites-enabled/default
fi

# ---------------------------------------------------------------
# 7. Firewall (UFW)
# ---------------------------------------------------------------
ufw allow OpenSSH
ufw allow "Nginx Full"
ufw --force enable

# ---------------------------------------------------------------
# 8. SSL (Certbot)
# ---------------------------------------------------------------
if [[ -n "$EMAIL" ]]; then
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL"
else
  echo "Nenhum email fornecido. Execute manualmente: certbot --nginx -d $DOMAIN"
fi

# ---------------------------------------------------------------
# 9. Start service
# ---------------------------------------------------------------
systemctl restart "$SERVICE_NAME"
systemctl status "$SERVICE_NAME" --no-pager

echo ""
echo "Instalação concluída! Acesse: https://${DOMAIN}"
