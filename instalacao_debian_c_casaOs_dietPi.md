# Instalação no Linux (DietPi + CasaOS + Docker)

Este arquivo contém instruções específicas para implantar o BrewStation em um servidor utilizando a combinação otimizada de **DietPi** (Debian ultra-leve) e **CasaOS** (gerenciamento visual via Docker). 

---

## Arquitetura de Produção

Para máxima eficiência de hardware e facilidade de manutenção, o ambiente é estruturado em três camadas:
1. **Base (OS):** DietPi (Debian 12 otimizado para console).
2. **Painel (Dashboard):** CasaOS (Interface web para monitoramento e gerenciamento de arquivos/containers).
3. **Aplicação:** BrewStation rodando como container Docker isolado.

---

## Pré‑requisitos

- Servidor com **DietPi** (Debian 12) instalado e atualizado.
- **CasaOS** instalado e acessível via navegador.
- Domínio ou subdomínio apontando para o IP do servidor (para acesso externo).
- Portas `80`, `443` (se usar proxy reverso) e `22` (SSH) liberadas no roteador/firewall.

---

## Preparação do Ambiente

### 1. Otimização do Sistema (DietPi Terminal)
Acesse seu servidor via SSH e garanta que o Docker e o Git estejam instalados através das ferramentas nativas do DietPi:
```bash
# Abre o gerenciador de software do DietPi
sudo dietpi-software

```

*Selecione e instale o **Docker** (ID: 162) e o **Git** (ID: 83) caso ainda não estejam ativos.*

### 2. Instalação do CasaOS

Se ainda não tiver o painel web instalado, execute o script oficial por cima do DietPi:

```bash
curl -fsSL [https://get.casaos.io](https://get.casaos.io) | sudo bash

```

---

## Instalação do BrewStation (Via App Customizada no CasaOS)

Como o projeto será modificado para rodar via Docker, você pode adicioná-lo diretamente no painel visual do CasaOS.

### 1. Clonar o Projeto

No terminal do servidor, clone o repositório na pasta de aplicativos do sistema:

```bash
git clone [https://github.com/ChristopherNicolasSMM/BrewStation.git](https://github.com/ChristopherNicolasSMM/BrewStation.git) /opt/brewstation

```

### 2. Ajustar as Variáveis de Ambiente

Crie o arquivo `.env` de produção a partir do modelo:

```bash
cp /opt/brewstation/src/config.env.modelo /opt/brewstation/src/.env

```

Configurações recomendadas para rodar dentro do container Docker:

```text
FLASK_ENV=PRD
DEBUG=False
HOST=0.0.0.0
PORT=5000

```

### 3. Implantação no CasaOS

1. Acesse o painel do CasaOS pelo navegador (`http://seu-ip-local`).
2. Na seção **App Store**, clique em **Custom Install** (no canto superior direito).
3. Preencha os campos de configuração do container:
* **Docker Image:** `christophernicolassmm/brewstation:latest` *(ou o nome da sua imagem buildada localmente)*
* **App Name:** `BrewStation`
* **Port (Container):** `5000` -> **Port (Host):** `5000`
* **Volumes:** Mapeie `/opt/brewstation/src/.env` para o caminho interno de configuração do container, se necessário.


4. Clique em **Install**.

---

## Operação e Manutenção

Toda a manutenção diária passa a ser visual e simplificada:

* **Verificar Status/Logs:** Clique nos três pontinhos no bloco do BrewStation dentro do painel do CasaOS e selecione **Logs** ou **Terminal**.
* **Atualizar a Aplicação:** ```bash
cd /opt/brewstation
git pull
# Se estiver usando Docker Compose ou Build local:


docker compose down && docker compose up -d --build
```

```


* **Manutenção do Sistema Base:** Acesse via SSH e utilize o utilitário do DietPi:
```bash
sudo dietpi-launcher

```



---

## Resultado Esperado

### Cliente Final / Produção

Acessa a interface do BrewStation através do navegador:

```text
[http://seu-dominio.com:5000](http://seu-dominio.com:5000)

```

*(Nota: Para remover a porta `:5000` do endereço e usar HTTPS `https://seu-dominio.com`, você pode instalar o app **Nginx Proxy Manager** com um clique pela App Store do CasaOS e apontar o domínio para o container do BrewStation).*

### Administração Geral

* **Painel Visual (Apps e Arquivos):** `http://seu-ip-local` (Interface CasaOS).
* **Gerenciamento do Servidor (Infraestrutura):** Acesso via SSH para ferramentas do DietPi.

```bash
ssh usuario@seu-ip-local

```
