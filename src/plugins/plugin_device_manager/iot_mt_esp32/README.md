# ND_BrewStation - Firmware ESP32

Firmware para ESP32 DevKit que implementa um sistema de configuração WiFi via Access Point e integração opcional com broker MQTT do plugin_device_manager do BrewStation.

## Visão Geral

Este projeto fornece um firmware completo para dispositivos ESP32 que permite configuração inicial através de uma interface web acessível via Access Point WiFi. Após a configuração, o dispositivo pode se conectar à rede WiFi configurada e, opcionalmente, integrar-se com o broker MQTT do sistema BrewStation.

## Características Principais

- **Modo AP para configuração inicial**: Cria rede WiFi "ND_BrewStation" para configuração via navegador
- **Configuração WiFi persistente**: Salva SSID, senha e configurações de IP (DHCP/estático)
- **Configuração MQTT opcional**: Permite configurar conexão com broker MQTT
- **Fallback automático**: Se perder conexão WiFi, retorna ao modo AP
- **Interface web responsiva**: Página de configuração moderna e intuitiva
- **Reset de fábrica**: Mantenha botão BOOT pressionado por 10 segundos durante boot
- **Armazenamento persistente**: Usa Preferences do ESP32 para salvar configurações
- **LED de status**: Indica o estado atual do dispositivo

## Estrutura do Projeto

```
iot_mt_esp32/
├── platformio.ini              # Configuração PlatformIO
├── README.md                   # Este arquivo
├── doc/                        # Documentação detalhada
│   ├── ARCHITECTURE.md         # Arquitetura do sistema
│   ├── CLASSES.md              # Documentação das classes
│   ├── FLOW.md                 # Fluxo de funcionamento
│   └── DEVELOPMENT.md          # Guia de desenvolvimento
├── src/
│   ├── main.cpp                # Ponto de entrada
│   ├── config_manager.h/cpp    # Gerenciamento de configurações
│   ├── wifi_config.h/cpp       # Gerenciamento WiFi
│   ├── web_server.h/cpp        # Servidor web
│   ├── mqtt_client.h/cpp       # Cliente MQTT
│   └── utils.h/cpp             # Utilitários
└── data/
    └── index.html              # Interface web
```

## Requisitos

- PlatformIO IDE ou PlatformIO CLI
- ESP32 DevKit
- Conexão USB para upload do firmware
- Python 3.7+ (para PlatformIO)

## Instalação Rápida

1. Clone ou baixe este repositório
2. Abra o projeto no PlatformIO
3. Conecte o ESP32 via USB
4. Compile e faça upload do firmware:
   ```bash
   pio run -t upload
   ```
5. Abra o monitor serial (115200 baud) para ver logs:
   ```bash
   pio device monitor
   ```

## Primeira Configuração

1. Após o upload, o ESP32 criará uma rede WiFi chamada **"ND_BrewStation"**
2. Conecte-se a esta rede (sem senha)
3. Abra um navegador e acesse: `http://192.168.4.1`
4. Preencha o formulário de configuração
5. Clique em "Salvar Configuração"
6. O dispositivo será reiniciado e tentará conectar à rede configurada

## Documentação

Para informações detalhadas, consulte a documentação na pasta `doc/`:

- **[Arquitetura](doc/ARCHITECTURE.md)**: Arquitetura geral do sistema
- **[Classes](doc/CLASSES.md)**: Documentação completa das classes
- **[Fluxo de Funcionamento](doc/FLOW.md)**: Fluxo detalhado de operação
- **[Desenvolvimento](doc/DEVELOPMENT.md)**: Guia de desenvolvimento e extensão

## Uso Básico

### Configuração WiFi

- **Modo DHCP** (padrão): Apenas informe SSID e senha
- **Modo IP Estático**: Marque "Usar IP Estático" e preencha os campos

### Configuração MQTT (Opcional)

- Marque "Habilitar MQTT"
- Preencha host, porta, usuário/senha (se necessário)
- Device ID será auto-gerado se não informado
- Tópico base padrão: `brewstation/devices`

### Reset de Fábrica

Mantenha o botão BOOT pressionado por 10 segundos durante o boot do ESP32.

## LED de Status

- **Piscando rápido**: Modo AP ativo (aguardando configuração)
- **Piscando lento**: Tentando conectar WiFi
- **Fixo ligado**: WiFi conectado
- **Desligado**: Erro ou desconectado

## Integração com Plugin Device Manager

O dispositivo, após configurado, se conecta ao broker MQTT e:

- Publica status em `brewstation/devices/{device_id}/status`
- Publica leituras de sensores em `brewstation/devices/{device_id}/sensor/{porta}`
- Recebe comandos em `brewstation/devices/{device_id}/actuator/{porta}/set`
- Publica estado de atuadores em `brewstation/devices/{device_id}/actuator/{porta}/state`

## Compilação e Desenvolvimento

### Comandos Úteis

```bash
# Compilar
pio run

# Upload
pio run -t upload

# Monitor serial
pio device monitor

# Limpar build
pio run -t clean

# Upload filesystem (SPIFFS)
pio run -t uploadfs
```

### Bibliotecas Utilizadas

- `PubSubClient`: Cliente MQTT
- `ArduinoJson`: Parsing JSON
- `WiFi` (built-in): Gerenciamento WiFi
- `WebServer` (built-in): Servidor HTTP
- `Preferences` (built-in): Armazenamento persistente
- `SPIFFS`: Sistema de arquivos

## Troubleshooting

### Rede "ND_BrewStation" não aparece

- Verifique se o firmware foi carregado corretamente
- Verifique o monitor serial para erros
- Tente fazer reset de fábrica

### Não consegue conectar à rede WiFi

- Verifique SSID e senha
- Verifique se a rede está no alcance (2.4GHz)
- Tente usar IP estático se DHCP falhar

### MQTT não conecta

- Verifique se o broker está acessível
- Verifique host, porta, usuário e senha
- Verifique firewall/roteador
- Verifique logs no monitor serial

### Página web não carrega

- Verifique se está conectado à rede "ND_BrewStation"
- Tente acessar `http://192.168.4.1` diretamente
- Limpe cache do navegador
- Tente outro navegador/dispositivo

## Licença

MIT License - Veja LICENSE para detalhes

## Autor

BrewStation Project

## Links

- [Documentação Completa](doc/)
- [Plugin Device Manager](../docs/README.md)
- [BrewStation Main](../..)
