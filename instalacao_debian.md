![Logo do BrewStation](src/static/img/nova_logo.png)

# BrewStation 🍺

Plataforma web modular para controle de brassagens artesanais, classificação de ingredientes, precificação, estoque e relatórios – construída com Flask, SQLAlchemy e integração nativa com o BrewFather.

> Este documento combina a documentação de projeto e o pack de servidor. Leia as seções na ordem que precisar.

## Visão geral

- **Público-alvo**: cervejarias artesanais, laboratórios de testes e homebrewers avançados.
- **Pilares**: catálogo de insumos, cálculo de custos, sincronização BrewFather, rastreabilidade de envase, notificações e painéis operacionais.
- **Stack**: Python 3.11+, Flask 3, SQLAlchemy 2, SQLite/PostgreSQL (Neon), Flask-Login, Flask-Mail, Pandas/OpenPyXL.
- **Arquitetura**: sistema modular com plugins extensíveis.

## Funcionalidades Principais

### Catálogo e precificação
- CRUD completo de maltes, lúpulos e leveduras, com importação via planilhas-modelo (`/upload/modelo/<tipo>`).
- Criação de receitas locais ou a partir de sincronizações BrewFather.
- Motor de cálculo configurável (margens, impostos, custo de envase, sanitização, taxa de cartão).
- Relatórios consolidados com preço sugerido, custo por litro e margens previstas.

### Estoque, envase e custos
- Movimentações (entrada/saída/ajuste) com custo médio e alerta por estoque mínimo.
- Módulo de envase vinculado a lotes do BrewFather, incluindo embalagens, SKUs e quantidades produzidas.
- Cálculo de custo de produção e sugestão de preço final.

### Operação e monitoramento
- Dashboard com indicadores de produção, notificações e status das integrações.
- Sistema de notificações com filtros (todas/lidas/não lidas/lixeira).
- Perfil de usuário completo (dados pessoais, redes sociais, preferências de alertas, troca de senha).

### Integrações
- **BrewFather**: sincronização de receitas, lotes e inventário.
- **E-mail (SMTP)**: envio de notificações e workflow de solicitações de acesso.
- **Uploads/Relatórios**: importação/exportação em Excel.

### Sistema de Plugins
- Arquitetura modular extensível, gerador de plugins, instalação/ativação dinâmica e menu configurável.

## Instalação Rápida (desenvolvimento)
```bash
git clone <url>
cd BrewStation
python -m venv vEnvStation
.\vEnvStation\Scripts\activate   # Windows
source vEnvStation/bin/activate  # Linux/Mac
pip install -r requirements.txt
copy src\config.env.modelo src\.env   # Windows
cp src/config.env.modelo src/.env     # Linux/Mac
cd src
python main.py
```
Acesse `http://localhost:5000` com `admin / 123`.

## BrewStation Server Pack v2 (Debian)
Arquivos novos para subir o BrewStation em **Debian** com:
- HTTPS público
- SSH administrativo
- Nginx como proxy reverso
- inicialização via `python run.py start`

### Pré‑requisitos
- Debian 12 recomendado
- domínio apontando para o IP do servidor
- repositório clonado em `/opt/brewstation`
- portas 80, 443 e 22 liberadas

### Instalação sugerida
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

### Instalação automática
```bash
cd /opt/brewstation
sudo bash install.sh seu-dominio.com seu-email@exemplo.com
```
O script instala dependências, cria usuário e venv, configura serviço systemd e Nginx, obtém certificado Let's Encrypt.

### Operação e manutenção
- Verificar status: `sudo systemctl status brewstation`
- Logs: `sudo journalctl -u brewstation -f`
- Atualizar: `sudo bash update.sh`
- Backup rápido: `sudo bash backup.sh`

### Notas adicionais
Consulte o restante deste arquivo para detalhes de variáveis de ambiente, estrutura de pastas, e plugins.

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
