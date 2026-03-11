# BrewStation Server Pack v2

Arquivos novos para subir o BrewStation em **Debian** com:

- acesso web público por **HTTPS**
- administração por **SSH**
- **Nginx** como proxy reverso
- inicialização usando **`python run.py start`**
- sem necessidade de instalar nada no cliente que acessa

## Importante

Este pacote foi ajustado para a estrutura atual do repositório BrewStation, que possui `run.py` na raiz. A entrada do serviço foi configurada para:

```bash
/opt/brewstation/venv/bin/python /opt/brewstation/run.py start
```

## Observação técnica importante

Esse modo usa o servidor embutido do Flask disparado pelo `run.py start`. Ele funciona e atende ao que você pediu, mas para produção de maior carga o mais indicado continua sendo **Gunicorn ou uWSGI** atrás do Nginx. Aqui o pack foi propositalmente alinhado ao seu pedido de usar `run.py start` como entrada.

## Estrutura do pacote

- `install.sh`
- `update.sh`
- `backup.sh`
- `env.example`
- `nginx/brewstation.conf`
- `systemd/brewstation.service`
- `scripts/start_brewstation.sh`
- `scripts/healthcheck.sh`
- `logrotate/brewstation`
- `README.md`

## Pré-requisitos

- Debian 12 recomendado
- domínio apontando para o IP do servidor
- repositório do BrewStation clonado em `/opt/brewstation`
- portas **80**, **443** e **22** liberadas

## Instalação sugerida

### 1. Clone o projeto

```bash
git clone https://github.com/ChristopherNicolasSMM/BrewStation.git /opt/brewstation
```

### 2. Copie estes arquivos novos para dentro do projeto

Copie mantendo a estrutura de pastas:

- `nginx/`
- `systemd/`
- `scripts/`
- `logrotate/`
- arquivos `.sh` e `env.example` na raiz

### 3. Ajuste o `.env`

Se ainda não existir:

```bash
cp /opt/brewstation/src/config.env.modelo /opt/brewstation/src/.env
```

Depois revise o arquivo. Para produção atrás do Nginx, a base recomendada é:

```env
FLASK_ENV=PRD
DEBUG=False
HOST=127.0.0.1
PORT=5000
HTTPS=False
```

## Instalação automática

Execute:

```bash
cd /opt/brewstation
sudo bash install.sh seu-dominio.com seu-email@exemplo.com
```

Esse script:

- instala dependências do sistema
- cria o usuário `brewstation` se necessário
- cria o `venv`
- instala dependências Python
- instala o serviço `systemd`
- publica a configuração do Nginx
- solicita e instala o certificado Let's Encrypt

## Operação

### Subir e verificar

```bash
sudo systemctl status brewstation
sudo journalctl -u brewstation -f
sudo nginx -t
```

### Atualizar o sistema

```bash
cd /opt/brewstation
sudo bash update.sh
```

### Gerar backup rápido

```bash
cd /opt/brewstation
sudo bash backup.sh
```

## SSH seguro

Recomendações no servidor:

```bash
sudo nano /etc/ssh/sshd_config
```

Ajustes recomendados:

```text
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
```

Depois:

```bash
sudo systemctl restart ssh
```

## Healthcheck simples

Arquivo incluído:

```bash
/usr/local/bin/brewstation-healthcheck
```

Teste manual:

```bash
brewstation-healthcheck
```

## Nginx

O proxy reverso encaminha para:

```text
http://127.0.0.1:5000
```

e publica externamente em:

```text
https://seu-dominio.com
```

## Logs

- aplicação: `/opt/brewstation/logs/brewstation_stdout.log`
- erros: `/opt/brewstation/logs/brewstation_stderr.log`

## Pontos para revisar no BrewStation

Como o `run.py start` usa variáveis de ambiente, confira no `src/.env` principalmente:

- `HOST`
- `PORT`
- `DEBUG`
- `HTTPS`
- `FLASK_ENV`
- conexão de banco
- SMTP
- integrações BrewFather

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
