# Plugin Device Manager - Documentação

## Visão Geral

O Plugin Device Manager é um sistema completo de gerenciamento de dispositivos IoT para o BrewStation. Ele fornece funcionalidades para cadastro, configuração e controle de dispositivos, além de um sistema de funções e atores que permite integração com outros plugins do sistema.

## Funcionalidades Principais

### 1. Gerenciamento de Dispositivos
- Cadastro e configuração de dispositivos IoT (sensores, atuadores, gateways)
- Suporte para múltiplos protocolos (MQTT, HTTP, WebSocket)
- Configuração de portas (GPIO, ADC, PWM, etc.)
- Monitoramento de estado e telemetria em tempo real

### 2. Sistema de Funções
- Funções pré-definidas (temperatura, umidade, pressão, relé, PWM, ADC, GPIO)
- Criação de funções customizadas
- Categorização (sensor, actuator, hybrid)
- Definição de unidades, tipos de dados e faixas de valores

### 3. Sistema de Atores
- Associação de portas de dispositivos a funções
- Tipos de atores: sensor, actuator, rule_trigger
- Integração com outros plugins
- Execução de ações e leitura de sensores

### 4. Broker MQTT
- Servidor MQTT embutido (suporte a hbmqtt)
- Testes de publicação e subscrição
- Histórico de mensagens
- Monitoramento de tópicos

### 5. API Pública
- Interface simplificada para outros plugins
- Métodos para executar ações, ler sensores e listar atores
- Suporte a subscrição em mudanças de sensores

## Estrutura do Plugin

```
plugin_device_manager/
├── model/
│   ├── device_metadata.py      # Modelo de metadados dos dispositivos
│   ├── device_function.py      # Modelo de funções
│   └── device_actor.py         # Modelo de atores
├── utils/
│   ├── device_registry.py      # Gerenciamento de dispositivos
│   ├── actor_manager.py        # Gerenciamento de atores
│   ├── mqtt_service.py         # Serviço MQTT
│   ├── device_api.py           # API pública para outros plugins
│   └── model_loader.py         # Loader de modelos prefixados
├── api/routes/
│   ├── device_routes.py        # Rotas de dispositivos
│   ├── function_routes.py      # Rotas de funções
│   ├── actor_routes.py         # Rotas de atores
│   └── mqtt_test_routes.py     # Rotas de teste MQTT
├── controller/
│   └── routes.py               # Rotas web
├── templates/
│   ├── device_manager.html     # Lista de dispositivos
│   ├── device_form.html        # Formulário de dispositivos
│   ├── function_manager.html   # Gerenciador de funções
│   ├── actor_manager.html      # Gerenciador de atores
│   └── mqtt_monitor.html       # Monitor MQTT
└── docs/
    ├── README.md               # Este arquivo
    ├── API.md                  # Documentação da API
    ├── USAGE.md                # Guia de uso
    └── INTEGRATION.md          # Guia de integração com outros plugins
```

## Documentação Detalhada

- [API Reference](API.md) - Documentação completa da API REST
- [Guia de Uso](USAGE.md) - Como usar o plugin (interfaces e fluxos)
- [Guia de Integração](INTEGRATION.md) - Como integrar com outros plugins

## Instalação

O plugin é instalado automaticamente quando o BrewStation é iniciado. Para garantir que está ativo:

1. Verifique se o plugin está listado em `src/plugins/plugins.json`
2. Certifique-se de que está marcado como ativo
3. As tabelas do banco de dados serão criadas automaticamente com prefixo `dvmanage_`

## Dependências

- `paho-mqtt`: Cliente MQTT (opcional, mas recomendado)
- `hbmqtt`: Broker MQTT embutido (opcional, para broker interno)

## Prefixos de Tabelas

Todas as tabelas do plugin são prefixadas automaticamente com `dvmanage_`:

- `dvmanage_device_metadata`
- `dvmanage_device_function`
- `dvmanage_device_actor`

## Funções Pré-definidas

O plugin cria automaticamente as seguintes funções na instalação:

1. **Temperatura** (°C) - Sensor de temperatura
2. **Umidade** (%) - Sensor de umidade relativa
3. **Pressão** (bar) - Sensor de pressão
4. **Relé** (bool) - Relé digital (liga/desliga)
5. **PWM** (%) - Modulação por largura de pulso
6. **ADC** (int) - Conversor analógico-digital
7. **GPIO Digital** (bool) - Entrada/saída digital GPIO

## Conceitos Principais

### Device (Dispositivo)
Um dispositivo físico ou virtual que se conecta ao sistema (sensores, atuadores, gateways).

### Function (Função)
Define o tipo de operação que uma porta pode realizar (temperatura, umidade, relé, etc.).

### Actor (Ator)
Associa uma porta específica de um dispositivo a uma função, permitindo que outros plugins usem essa associação.

### Port (Porta)
Uma interface física ou lógica do dispositivo (GPIO1, ADC0, etc.).

## Suporte

Para questões e suporte, consulte a documentação principal do BrewStation ou abra uma issue no repositório do projeto.
