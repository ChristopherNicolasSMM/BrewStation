# Guia de Desenvolvimento

## Ambiente de Desenvolvimento

### Pré-requisitos

- **PlatformIO**: IDE ou CLI instalado
- **Python 3.7+**: Necessário para PlatformIO
- **ESP32 DevKit**: Hardware para testes
- **Cabo USB**: Para upload e monitoramento serial
- **Editor de código**: VSCode recomendado (com extensão PlatformIO)

### Instalação

1. Instalar PlatformIO:
   ```bash
   pip install platformio
   ```

2. Ou usar PlatformIO IDE (VSCode):
   - Instalar extensão "PlatformIO IDE"
   - Abrir projeto

### Estrutura do Projeto

```
iot_mt_esp32/
├── platformio.ini          # Configuração do projeto
├── src/                    # Código fonte
│   ├── main.cpp
│   ├── config_manager.h/cpp
│   ├── wifi_config.h/cpp
│   ├── web_server.h/cpp
│   ├── mqtt_client.h/cpp
│   └── utils.h/cpp
├── data/                   # Arquivos do filesystem
│   └── index.html
├── doc/                    # Documentação
└── .pio/                   # Build files (gerado)
```

## Comandos de Desenvolvimento

### Compilação

```bash
# Compilar
pio run

# Compilar com verbose
pio run -v

# Compilar apenas um ambiente
pio run -e esp32dev
```

### Upload

```bash
# Upload do firmware
pio run -t upload

# Upload de filesystem (SPIFFS)
pio run -t uploadfs

# Upload e monitor serial
pio run -t upload && pio device monitor
```

### Monitoramento

```bash
# Monitor serial
pio device monitor

# Monitor com filtros
pio device monitor --filter esp32_exception_decoder

# Listar dispositivos
pio device list
```

### Limpeza

```bash
# Limpar build
pio run -t clean

# Limpar tudo (incluindo bibliotecas)
pio run -t cleanall
```

### Testes

```bash
# Executar testes (se houver)
pio test

# Testes com verbose
pio test -v
```

## Desenvolvimento de Código

### Convenções de Código

#### Nomenclatura

- **Classes**: PascalCase (`ConfigManager`, `WiFiManager`)
- **Métodos**: camelCase (`loadWiFiConfig`, `connectToWiFi`)
- **Variáveis**: camelCase (`apMode`, `lastConnectionAttempt`)
- **Constantes**: UPPER_SNAKE_CASE (`AP_SSID`, `CONNECTION_TIMEOUT`)
- **Namespaces**: lowercase (`brewstation`)

#### Estrutura de Arquivos

- Header files (`.h`): Declarações de classes, estruturas, constantes
- Source files (`.cpp`): Implementações
- Um arquivo por classe (quando possível)

#### Comentários

```cpp
// Comentário de linha única

/**
 * Comentário de bloco
 * Para documentação de funções
 */
```

### Adicionando Novas Funcionalidades

#### 1. Adicionar Nova Configuração

**Exemplo: Adicionar configuração de NTP**

1. Atualizar `config_manager.h`:
```cpp
struct NTPConfig {
    bool enabled;
    char server[64];
    int timezone;
};
```

2. Adicionar métodos em `ConfigManager`:
```cpp
bool loadNTPConfig(NTPConfig& config);
bool saveNTPConfig(const NTPConfig& config);
bool hasNTPConfig();
void resetNTP();
```

3. Implementar em `config_manager.cpp`

4. Atualizar interface web (`data/index.html`)

5. Atualizar `web_server.cpp` para processar novos campos

#### 2. Adicionar Nova Rota Web

1. Adicionar método handler em `web_server.h`:
```cpp
void handleNewRoute();
```

2. Registrar rota em `web_server.cpp`:
```cpp
server.on("/newroute", HTTP_GET, [this]() { this->handleNewRoute(); });
```

3. Implementar handler

#### 3. Adicionar Novo Tópico MQTT

1. Adicionar método em `mqtt_client.h`:
```cpp
bool publishCustom(const String& topic, const String& payload);
```

2. Implementar em `mqtt_client.cpp`

3. Usar nos pontos apropriados do código

### Debugging

#### Serial Debug

```cpp
Serial.println("[Modulo] Mensagem de debug");
Serial.printf("[Modulo] Valor: %d\n", valor);
```

#### Logging Estruturado

```cpp
#define DEBUG_CONFIG 1

#if DEBUG_CONFIG
  Serial.println("[ConfigManager] Debug message");
#endif
```

#### Breakpoints e Debugging

- Usar GDB com PlatformIO
- Configurar debugger no `platformio.ini`:
```ini
debug_tool = esp-prog
debug_init_break = tbreak setup
```

### Testes

#### Testes Unitários (Futuro)

Criar estrutura de testes:
```
test/
├── test_config_manager.cpp
├── test_wifi_manager.cpp
└── ...
```

#### Testes de Integração

1. Testar fluxo completo de configuração
2. Testar reconexão WiFi
3. Testar reconexão MQTT
4. Testar fallback

### Otimização

#### Memória

- Usar `String` apenas quando necessário (preferir `char[]` em estruturas)
- Limitar tamanho de buffers
- Evitar alocação dinâmica
- Usar `PROGMEM` para strings constantes grandes

#### Performance

- Minimizar delays no loop principal
- Processar operações assíncronas quando possível
- Usar callbacks em vez de polling quando apropriado
- Evitar operações bloqueantes

#### Exemplo de Otimização

```cpp
// Ruim: Alocação dinâmica
String message = "Hello " + name;

// Bom: Buffer pré-alocado
char message[64];
snprintf(message, sizeof(message), "Hello %s", name);
```

## Extensão do Sistema

### Adicionar Novo Sensor

1. Criar função de leitura
2. Integrar com MQTT:
```cpp
String value = readSensor();
mqttClient.publishSensor("sensor1", value);
```

3. Publicar periodicamente no loop

### Adicionar Novo Atuador

1. Criar função de controle
2. Configurar callback MQTT:
```cpp
mqttClient.setActuatorCallback([](const String& port, const String& value) {
    if (port == "relay1") {
        digitalWrite(RELAY_PIN, value.toInt());
    }
});
```

3. Subscrever no tópico:
```cpp
mqttClient.subscribeToActuator("relay1");
```

### Adicionar Novo Protocolo

1. Criar novo manager (ex: `BluetoothManager.h/cpp`)
2. Seguir padrão dos outros managers
3. Integrar no `main.cpp`
4. Adicionar configuração ao `ConfigManager`

## Versionamento

### Versionamento Semântico

- **MAJOR**: Mudanças incompatíveis
- **MINOR**: Novas funcionalidades compatíveis
- **PATCH**: Correções de bugs

### Changelog

Manter `CHANGELOG.md` com:

```
## [1.1.0] - 2024-01-15
### Added
- Suporte para NTP

### Changed
- Melhorado timeout de conexão WiFi

### Fixed
- Bug na reconexão MQTT
```

## Contribuindo

### Workflow

1. Criar branch para nova funcionalidade
2. Desenvolver e testar
3. Commit com mensagens descritivas
4. Pull Request com descrição clara

### Padrões de Commit

```
feat: Adiciona suporte para NTP
fix: Corrige timeout de conexão WiFi
docs: Atualiza documentação de classes
refactor: Reorganiza código do WiFiManager
test: Adiciona testes para ConfigManager
```

### Code Review

- Verificar se segue convenções
- Verificar se há testes
- Verificar se documentação está atualizada
- Verificar se não há memory leaks
- Verificar se código está otimizado

## Troubleshooting de Desenvolvimento

### Erros de Compilação Comuns

#### Biblioteca não encontrada

```bash
# Instalar biblioteca manualmente
pio lib install <library_name>
```

#### Erro de memória

- Reduzir tamanho de buffers
- Otimizar uso de String
- Verificar uso de PROGMEM

#### Erro de upload

- Verificar porta USB
- Verificar drivers
- Tentar manter botão BOOT pressionado durante upload

### Problemas Comuns

#### SPIFFS não monta

- Verificar se filesystem foi formatado
- Tentar `SPIFFS.format()` uma vez

#### WiFi não conecta

- Verificar logs serial
- Verificar SSID e senha
- Verificar se rede está no alcance
- Tentar IP estático

#### MQTT não conecta

- Verificar se broker está acessível
- Verificar credenciais
- Verificar firewall
- Verificar logs serial

## Recursos Úteis

### Documentação Oficial

- [ESP32 Arduino Core](https://github.com/espressif/arduino-esp32)
- [PlatformIO Docs](https://docs.platformio.org/)
- [PubSubClient](https://github.com/knolleary/pubsubclient)
- [ArduinoJson](https://arduinojson.org/)

### Ferramentas

- **ESP32 Flash Tool**: Para formatação de SPIFFS
- **MQTT Client**: Para testar broker (MQTT.fx, MQTT Explorer)
- **Serial Monitor**: Monitor serial integrado do PlatformIO

### Comunidade

- Fóruns ESP32
- Stack Overflow
- GitHub Issues
