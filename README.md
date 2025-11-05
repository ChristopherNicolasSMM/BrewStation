# BrewStation - Estação CraftBeer 🍻

Sistema completo para brassagem caseira e controle de processos cervejeiros artesanais, desenvolvido com Flask e arquitetura modular.

## 🚀 Visão Geral

O **BrewStation** é uma plataforma integrada para cervejeiros caseiros que une **precificação de receitas** com **controle de dispositivos IoT** para brassagem, fermentação e monitoramento em tempo real.

## ✨ Funcionalidades Principais

### 🧮 Sistema de Precificação
- **Gestão de Ingredientes**: Maltes, lúpulos, leveduras e adjuntos
- **Criação de Receitas**: Formulação e cálculo automático de custos
- **Cálculo de Preços**: Margens, impostos e custos operacionais
- **Análise de Rentabilidade**: Relatórios detalhados de custo-benefício

### 🔌 Controle de Dispositivos IoT
- **iSpindel**: Monitoramento de gravidade e temperatura em tempo real
- **Controladores de Temperatura**: PID para aquecimento/resfriamento
- **Sensores Multi-protocolo**: MQTT, HTTP, Bluetooth, Serial
- **Dashboard em Tempo Real**: Gráficos e alertas de processo

### 📊 Monitoramento e Controle
- **Sessões de Brassagem**: Controle completo do processo
- **Fermentação**: Acompanhamento de temperatura e gravidade
- **Alertas e Notificações**: Sistema de notificações em tempo real
- **Histórico de Dados**: Armazenamento temporal para análise

## 🏗️ Arquitetura e Camadas

### 📁 Estrutura do Projeto
```
BrewStation/
├── src/
│   ├── api/                 # 🚀 Rotas da API REST
│   ├── controllers/         # 🎮 Controladores (MVC)
│   ├── models/              # 🗄️ Modelos de dados (SQLAlchemy)
│   ├── db/                  # 🗃️ Configuração do banco
│   ├── templates/           # 🎨 Templates HTML (Jinja2)
│   ├── static/              # 🎭 Arquivos estáticos
│   ├── utils/               # 🔧 Utilitários e helpers
│   └── main.py              # ⚡ Entry point da aplicação
├── instance/                # 💾 Banco de dados SQLite
├── logs/                    # 📝 Logs da aplicação
└── requirements.txt         # 📦 Dependências
```

### 🔄 Fluxo de Dados
```
Frontend (HTML/Jinja2) 
    → Controllers (Flask Routes) 
    → Models (SQLAlchemy ORM) 
    → Database (SQLite)
    → Dispositivos IoT (MQTT/HTTP)
```

### 🛡️ Camadas de Responsabilidade

1. **Camada de Apresentação** (`templates/`, `static/`)
   - Templates Jinja2 para renderização HTML
   - CSS, JavaScript e assets estáticos
   - Interface responsiva para usuários

2. **Camada de Controle** (`controllers/`)
   - Rotas Flask e lógica de aplicação
   - Validação de dados de entrada
   - Coordenação entre models e views
   - Autenticação e autorização

3. **Camada de Modelo** (`models/`)
   - Definição de entidades do banco
   - Relacionamentos e business logic
   - Operações CRUD via SQLAlchemy ORM

4. **Camada de Dados** (`db/`)
   - Configuração do banco de dados
   - Migrations e inicialização
   - Conexão e pooling

5. **Camada de API** (`api/`)
   - Endpoints REST para integração
   - Comunicação com dispositivos IoT
   - Webhooks e integrações externas

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.8+
- pip e virtualenv
- Git

### 🔧 Configuração Inicial

1. **Clone o repositório**
```bash
git clone <url-do-repositorio>
cd BrewStation
```

2. **Configure o ambiente virtual**
```bash
# Criar ambiente virtual
python -m venv vEnvStation

# Ativar (Windows)
vEnvStation\Scripts\activate

# Ativar (Linux/Mac)
source vEnvStation/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
# Copie o arquivo modelo
cp src/utils/env/config.env.modelo .env

# Edite o .env com suas configurações
# SECRET_KEY=sua-chave-secreta-aqui
# DEBUG=True
# DATABASE_URL=sqlite:///instance/brewstation.db
```

5. **Execute a aplicação**
```bash
cd src
python main.py
```

6. **Acesse o sistema**
- URL: http://localhost:5000
- Usuário: `admin`
- Senha: `admin123`

## 🗄️ Modelos de Dados Principais

### 🧪 Ingredientes
```python
class Malte, class Lupulo, class Levedura
# Propriedades: nome, fabricante, especificações técnicas, preços
```

### 📋 Receitas e Processos
```python
class Receita, class IngredienteReceita, class CalculoPreco
# Formulação completa e cálculos de custo
```

### 🔌 Dispositivos IoT
```python
class Dispositivo, class HistoricoDispositivo
# Configuração, comunicação e dados em tempo real
```

### ⚙️ Configurações do Sistema
```python
class Configuracao
# Configurações dinâmicas do sistema
```

## 🔌 Integração com Dispositivos

### Protocolos Suportados
- **MQTT**: Para dispositivos IoT (iSpindel, ESP32, etc.)
- **HTTP/REST**: APIs de controladores
- **Bluetooth**: Dispositivos próximos
- **Serial**: Controladores diretos

### Dispositivos Compatíveis
- **iSpindel**: Hidrômetro digital
- **ESP32/Arduino**: Controladores customizados
- **Tilt Hydrometer**: Hidrômetro Bluetooth
- **BrewPi**: Controlador de fermentação

## 🛠️ Desenvolvimento

### 📝 Como Contribuir

1. **Clone e Crie uma Branch**
```bash
git clone <url>
git checkout -b feature/nova-funcionalidade
```

2. **Desenvolva e Teste**
```bash
# Execute os testes
python -m pytest tests/

# Verifique a qualidade do código
flake8 src/
```

3. **Commit e Push**
```bash
git add .
git commit -m "feat: adiciona nova funcionalidade"
git push origin feature/nova-funcionalidade
```

4. **Abra um Pull Request**
- Descreva as mudanças
- Inclua screenshots se aplicável
- Referencie issues relacionadas

### 🐛 Reportando Bugs

1. **Verifique Issues Existentes**
2. **Crie uma Nova Issue** com:
   - Descrição detalhada do bug
   - Passos para reproduzir
   - Comportamento esperado vs atual
   - Screenshots e logs

### 🚀 Adicionando Novas Funcionalidades

1. **Planeje a Estrutura**
   - Modelo de dados em `models/`
   - Controlador em `controllers/`
   - Template em `templates/`
   - Rotas API em `api/routes.py`

2. **Siga o Padrão MVC**
```python
# Model
class NovaFuncionalidade(db.Model):

# Controller  
@main_bp.route('/nova-funcionalidade')

# View
templates/nova_funcionalidade.html
```

3. **Teste Completamente**
   - Testes unitários
   - Testes de integração
   - Testes manuais

## 🔧 Configuração de Produção

### Variáveis de Ambiente Críticas
```env
SECRET_KEY=chave-super-secreta-aqui
DEBUG=False
DATABASE_URL=sqlite:///instance/brewstation.db
MQTT_BROKER_URL=localhost
MQTT_BROKER_PORT=1883
```

### Deployment com WSGI
```python
# wsgi.py
from main import create_app
app = create_app()
```

## 📊 Monitoramento e Logs

### Estrutura de Logs
```
logs/
├── application.log    # Logs gerais da aplicação
├── errors.log         # Erros e exceções
├── devices.log        # Comunicação com dispositivos
└── brew_sessions.log  # Sessões de brassagem
```

### Métricas Monitoradas
- Temperaturas em tempo real
- Gravidade específica
- Status de dispositivos
- Performance da aplicação

## 🤝 Comunidade e Suporte

### 📞 Canais de Suporte
- **Issues no GitHub**: Para bugs e feature requests
- **Documentação**: Guias detalhados de uso
- **Fórum da Comunidade**: [Link para fórum]

### 🎯 Roadmap
- [ ] App mobile para monitoramento
- [ ] Integração com BrewFather
- [ ] Controle automático de temperatura
- [ ] Receitas compartilháveis
- [ ] Marketplace de ingredientes

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 👨‍💻 Autor

**Christopher Mauricio**
- Desenvolvedor Full Stack & Cervejeiro Caseiro
- Python/Flask | IoT | DevOps
- [GitHub](https://github.com/christophermauricio) | [Portfólio](https://seusite.com)

---

**BrewStation** - Transformando paixão por cerveja artesanal em tecnologia! 🍺⚡

*"Do grão ao copo, controlando cada etapa com precisão e paixão."*