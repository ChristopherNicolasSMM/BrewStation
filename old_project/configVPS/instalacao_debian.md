# Instalação no Linux (Debian)

Este arquivo contém instruções específicas para instalar o BrewStation em um servidor Debian. Para visão geral e demais documentação, consulte o [README principal](README.md).



## Pré‑requisitos
- Debian 12 recomendado
- domínio apontando para o IP do servidor
- repositório clonado em `/opt/brewstation`
- portas 80, 443 e 22 liberadas

## Instalação sugerida
1. Clone o projeto:
   ```bash
git clone https://github.com/ChristopherNicolasSMM/BrewStation.git /opt/brewstation
``` 
2. Copie os arquivos do pack mantendo a estrutura (`nginx/`, `systemd/`, `scripts/`, `logrotate/`, `.sh` e `env.example`).
3. Ajuste o `.env`:
    ```bash
cp /opt/brewstation/src/config.env.modelo /opt/brewstation/src/.env
``` 
   Recomendações para produção atrás de Nginx:
    ```text
FLASK_ENV=PRD
DEBUG=False
HOST=127.0.0.1
PORT=5000
HTTPS=False
```  

## Instalação automática
```bash
cd /opt/brewstation
sudo bash install.sh seu-dominio.com seu-email@exemplo.com
```
O script instala dependências, cria usuário e venv, configura serviço systemd e Nginx, obtém certificado Let's Encrypt.

## Operação e manutenção
- Verificar status: `sudo systemctl status brewstation`
- Logs: `sudo journalctl -u brewstation -f`
- Atualizar: `sudo bash update.sh`
- Backup rápido: `sudo bash backup.sh`



---

*Este documento complementa o README.md com instruções práticas de instalação no Debian.*



## Resultado esperado

### Cliente final

Acessa apenas com navegador:

```text
https://seu-dominio.com
```

### Administração

Acesso por SSH:

```bash
ssh usuario@seu-dominio.com
```
