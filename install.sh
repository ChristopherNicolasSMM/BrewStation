#!/usr/bin/env bash
set -euo pipefail

APP_USER="brewstation"
APP_GROUP="brewstation"
APP_DIR="/opt/brewstation"
VENV_DIR="$APP_DIR/venv"
SERVICE_NAME="brewstation"
DOMAIN="${1:-}"
EMAIL="${2:-}"

if [[ -z "$DOMAIN" ]]; then
  echo "Uso: sudo ./install.sh seu-dominio.com [email-certbot]"
  exit 1
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "Execute como root: sudo ./install.sh $DOMAIN [email-certbot]"
  exit 1
fi

if [[ ! -d "$APP_DIR" ]]; then
  echo "Diretório $APP_DIR não encontrado. Clone o BrewStation antes em $APP_DIR."
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt update
apt install -y python3 python3-venv python3-pip nginx git ufw certbot python3-certbot-nginx openssh-server

if ! id "$APP_USER" >/dev/null 2>&1; then
  adduser --system --group --home "$APP_DIR" "$APP_USER"
fi

chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
  sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
fi

sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install -r "$APP_DIR/requirements.txt"

if [[ ! -f "$APP_DIR/src/.env" ]]; then
  if [[ -f "$APP_DIR/src/config.env.modelo" ]]; then
    sudo -u "$APP_USER" cp "$APP_DIR/src/config.env.modelo" "$APP_DIR/src/.env"
    echo "Arquivo src/.env criado a partir de src/config.env.modelo. Revise-o antes de subir para produção."
  else
    echo "Aviso: src/config.env.modelo não encontrado; crie manualmente $APP_DIR/src/.env"
  fi
fi

install -m 755 "$APP_DIR/scripts/start_brewstation.sh" /usr/local/bin/start_brewstation.sh
install -m 755 "$APP_DIR/scripts/healthcheck.sh" /usr/local/bin/brewstation-healthcheck
install -m 644 "$APP_DIR/systemd/brewstation.service" "/etc/systemd/system/${SERVICE_NAME}.service"
cp "$APP_DIR/nginx/brewstation.conf" "/etc/nginx/sites-available/${SERVICE_NAME}"
sed -i "s/__DOMAIN__/${DOMAIN}/g" "/etc/nginx/sites-available/${SERVICE_NAME}"

ln -sf "/etc/nginx/sites-available/${SERVICE_NAME}" "/etc/nginx/sites-enabled/${SERVICE_NAME}"
rm -f /etc/nginx/sites-enabled/default

mkdir -p "$APP_DIR/logs" "$APP_DIR/backups"
chown -R "$APP_USER:$APP_GROUP" "$APP_DIR/logs" "$APP_DIR/backups"

nginx -t
systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl enable nginx
systemctl restart nginx

ufw allow OpenSSH || true
ufw allow 'Nginx Full' || true

if [[ -n "$EMAIL" ]]; then
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m "$EMAIL" --redirect
else
  certbot --nginx -d "$DOMAIN" --register-unsafely-without-email --non-interactive --agree-tos --redirect
fi

systemctl restart nginx

cat <<MSG

Instalação concluída.

Valide:
  systemctl status ${SERVICE_NAME}
  journalctl -u ${SERVICE_NAME} -f
  nginx -t

Acesso web:
  https://${DOMAIN}

Acesso SSH:
  ssh <usuario>@<ip-ou-dominio>

Revise também:
  ${APP_DIR}/src/.env
MSG
