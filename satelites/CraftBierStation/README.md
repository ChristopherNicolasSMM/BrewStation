# 📄 Arquivo: `README.md` (para o servidor)


# BrewStation Device Server

Servidor Python para Raspberry Pi que gerencia sensores e atuadores para o sistema BrewStation.

## 📋 Requisitos

- Raspberry Pi (testado no modelo B+)
- Python 3.7+
- Bibliotecas Python (ver requirements.txt)
- Sensores compatíveis: DHT22, DS18B20, sensores digitais GPIO

## 🚀 Instalação Rápida

```bash
# Clone o repositório (se ainda não fez)
git clone https://github.com/ChristopherNicolasSMM/BrewStation.git
cd BrewStation/src/plugins/plugin_device_manager/server

# Crie ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure o arquivo de configuração
cp config/device_manager.conf.example config/device_manager.conf
nano config/device_manager.conf  # Ajuste conforme seu hardware

# Execute o servidor
python server.py


## 🔧 Configuração

### Mapeamento de Pinos GPIO

No arquivo `device_manager.conf`, seção `[gpio_mapping]`:

```ini
[gpio_mapping]
; Nome_Lógico = Número_GPIO (BCM)
SENSOR_TEMP_MOSTURA = 4      ; GPIO4 - Sensor da mostura
ATUADOR_AQUECEDOR = 23        ; GPIO23 - Controle do aquecedor
```

Use os números GPIO (BCM), não os números físicos dos pinos.

### Sensores

```ini
[sensors]
; nome = tipo, pino_logico_ou_id, intervalo
temp_mostura = dht22, SENSOR_TEMP_MOSTURA, 2
temp_mash = ds18b20, 28-000006d5a2e5, 3
```

### Atuadores

```ini
[actuators]
; nome = tipo, pino_logico, estado_inicial
aquecedor = gpio_output, ATUADOR_AQUECEDOR, off
```

### Interfaces

Configure MQTT e/ou HTTP conforme necessidade:

```ini
[mqtt]
enabled = true
mode = client
host = localhost
port = 1883

[http]
enabled = true
port = 5001
host = 0.0.0.0
```

## 📡 API REST

Com o HTTP habilitado, acesse:

- `GET /api/sensors` - Lista todos os sensores
- `GET /api/sensors/<nome>` - Leitura de um sensor
- `GET /api/actuators` - Lista atuadores
- `GET /api/actuators/<nome>` - Status do atuador
- `POST /api/actuators/<nome>/on` - Liga atuador
- `POST /api/actuators/<nome>/off` - Desliga atuador
- `POST /api/actuators/<nome>/toggle` - Inverte estado

Exemplo:
```bash
curl http://localhost:5001/api/sensors/temp_mostura
```

## 📡 MQTT

Tópicos padrão:
- `brewstation/devices/sensor/<nome>` - Dados de sensores
- `brewstation/devices/actuator/<nome>/status` - Status de atuadores
- `brewstation/devices/actuator/<nome>/set` - Comandos (publicar "on"/"off")

## 🔌 Integração com o BrewStation

Este servidor foi projetado para funcionar com o plugin `device_manager` do BrewStation. O plugin se comunicará com este servidor via REST API ou MQTT para obter dados dos sensores e controlar atuadores durante os processos de brassagem.

## 🐛 Solução de Problemas

### Sensores não aparecem
Verifique se o arquivo .conf está correto e se os pinos GPIO estão corretos.

### DS18B20 não encontrado
Habilite a interface 1-Wire no Raspberry Pi:
```bash
sudo raspi-config
# Interface Options → 1-Wire → Enable
```

### Erro de permissão GPIO
Execute com sudo ou adicione usuário ao grupo gpio:
```bash
sudo usermod -a -G gpio $USER
```

## 📝 Licença

Este projeto faz parte do BrewStation e está sob a mesma licença.
```

## 🚀 Como Usar

1. **Prepare o Raspberry Pi**:
   ```bash
   # Instale as dependências do sistema
   sudo apt update
   sudo apt install python3-pip git
   
   # Habilite interfaces necessárias
   sudo raspi-config
   # Interface Options → 1-Wire → Enable (para DS18B20)
   # Interface Options → SPI → Enable (para alguns sensores)
   ```

2. **Crie a estrutura de diretórios**:
   ```bash
   mkdir -p ~/brewstation_device_server
   cd ~/brewstation_device_server
   ```

3. **Copie todos os arquivos fornecidos** para a estrutura correta.

4. **Configure** o arquivo `config/device_manager.conf` com seus pinos reais.

5. **Execute**:
   ```bash
   python server.py
   ```

6. **Teste**:
   ```bash
   # Em outro terminal
   curl http://localhost:5001/api/sensors
   ```
