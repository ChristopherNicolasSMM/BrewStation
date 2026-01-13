# Arquitetura do Sistema

## Visão Geral

O firmware ND_BrewStation foi projetado com uma arquitetura modular que separa claramente as responsabilidades entre diferentes componentes. Esta separação facilita a manutenção, teste e extensão do código.

## Componentes Principais

### 1. ConfigManager

**Responsabilidade**: Gerenciamento de configurações persistentes

- Armazena configurações WiFi (SSID, senha, IP, etc.)
- Armazena configurações MQTT (host, porta, credenciais, etc.)
- Usa Preferences do ESP32 para persistência
- Fornece métodos para carregar, salvar e resetar configurações

### 2. WiFiManager

**Responsabilidade**: Gerenciamento de conexão WiFi

- Modo Access Point (AP) para configuração inicial
- Modo Station para conexão à rede WiFi
- Lógica de fallback automático
- Monitoramento de status de conexão

### 3. WebConfigServer

**Responsabilidade**: Servidor web para configuração

- Servidor HTTP na porta 80
- Rotas para configuração, status e reset
- Serve arquivos estáticos do SPIFFS
- Interface web responsiva

### 4. MQTTClientManager

**Responsabilidade**: Comunicação MQTT (opcional)

- Conexão com broker MQTT
- Publicação de mensagens
- Subscrição em tópicos
- Reconexão automática

### 5. StatusLED

**Responsabilidade**: Feedback visual

- Indica estado do dispositivo através do LED built-in
- Diferentes padrões para diferentes estados

## Fluxo de Dados

```
┌─────────────┐
│   Boot      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ ConfigManager   │◄────────┐
│  (load config)  │         │
└────────┬────────┘         │
         │                  │
         ▼                  │
┌─────────────────┐         │
│ WiFiManager     │         │
│  (connect/AP)   │         │
└────────┬────────┘         │
         │                  │
         ▼                  │
┌─────────────────┐         │
│ WebConfigServer │         │
│  (always on)    │         │
└────────┬────────┘         │
         │                  │
         ▼                  │
┌─────────────────┐         │
│ MQTTClient      │         │
│  (if enabled)   │         │
└─────────────────┘         │
         │                  │
         │                  │
         └──────────────────┘
         (save config)
```

## Armazenamento

### Preferences (NVRAM)

O ESP32 usa Preferences para armazenar configurações na memória não-volátil:

- **Namespace**: `brewstation`
- **Chaves WiFi**: `wifi_ssid`, `wifi_pass`, `wifi_static`, `wifi_ip`, etc.
- **Chaves MQTT**: `mqtt_en`, `mqtt_host`, `mqtt_port`, `mqtt_user`, etc.

### SPIFFS (Filesystem)

Usado para armazenar arquivos estáticos:

- Interface web (`index.html`)
- Outros recursos estáticos (se necessário)

## Estados do Sistema

1. **Inicialização**
   - Carrega configurações
   - Verifica se há configuração WiFi
   - Inicia modo AP ou tenta conectar

2. **Modo AP**
   - Access Point ativo
   - Servidor web acessível
   - Aguardando configuração

3. **Modo Station**
   - Conectado à rede WiFi
   - Servidor web ativo
   - MQTT conectado (se configurado)

4. **Fallback**
   - Perde conexão WiFi
   - Retorna ao modo AP automaticamente

## Comunicação

### HTTP

- **Porta**: 80
- **Protocolo**: HTTP/1.1
- **Rotas**:
  - `GET /`: Interface de configuração
  - `POST /config`: Salvar configurações
  - `GET /status`: Status JSON
  - `GET /reset`: Resetar configurações

### MQTT

- **Protocolo**: MQTT 3.1.1
- **QoS**: 1 (para mensagens importantes)
- **Keep-alive**: 60 segundos
- **Will Topic**: Status offline quando desconecta

## Threading e Concorrência

O ESP32 Arduino framework usa um modelo de execução single-threaded:

- Loop principal processa tudo sequencialmente
- WiFi, WebServer e MQTT são processados no loop
- Delays são minimizados para responsividade
- Operações bloqueantes são evitadas quando possível

## Segurança

### WiFi AP

- Atualmente sem senha (para facilitar configuração)
- Pode ser adicionada senha padrão se necessário

### MQTT

- Suporta autenticação (usuário/senha)
- Conexão não criptografada por padrão (MQTT sobre TCP)
- TLS pode ser adicionado no futuro

### Web Server

- Sem autenticação (assumindo que AP é temporário)
- Pode ser adicionada autenticação básica se necessário

## Extensibilidade

A arquitetura foi projetada para facilitar extensões:

- Novos tipos de configuração podem ser adicionados ao ConfigManager
- Novos protocolos podem ser adicionados como novos managers
- Interface web pode ser estendida com novas rotas
- Novos sensores/atuadores podem usar a estrutura MQTT existente
