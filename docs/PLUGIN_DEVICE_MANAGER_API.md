# Device Manager API - Referência Completa

## Visão Geral

Esta documentação descreve a API pública do Plugin Device Manager para uso por outros plugins do BrewStation.

## Importação

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService
```

## Métodos Disponíveis

### get_device_status(device_id: str) -> Optional[Dict[str, Any]]

Obtém o status atual de um dispositivo.

**Parâmetros:**
- `device_id` (str): ID único do dispositivo

**Retorna:**
- `Dict[str, Any]` ou `None`: Dicionário com status do dispositivo

**Exemplo:**
```python
status = DeviceAPIService.get_device_status('esp32-sensor-001')
# {
#   'device_id': 'esp32-sensor-001',
#   'name': 'Sensor de Temperatura',
#   'status': 'online',
#   'last_seen': '2024-01-01T12:00:00Z',
#   'telemetry': {'temperature': 68.5, 'humidity': 45.2},
#   'ports': {
#     'GPIO_32': {'value': 68.5, 'timestamp': '2024-01-01T12:00:00Z'}
#   },
#   'last_error': None
# }
```

### get_port_value(device_id: str, port: str) -> Optional[Any]

Obtém o valor atual de uma porta específica.

**Parâmetros:**
- `device_id` (str): ID do dispositivo
- `port` (str): Nome da porta (ex: 'GPIO_32')

**Retorna:**
- Valor da porta ou `None` se não encontrado

**Exemplo:**
```python
temperature = DeviceAPIService.get_port_value('esp32-sensor-001', 'GPIO_32')
# Retorna: 68.5
```

### get_all_ports(device_id: str) -> Optional[Dict[str, Any]]

Obtém todas as portas e seus valores de um dispositivo.

**Parâmetros:**
- `device_id` (str): ID do dispositivo

**Retorna:**
- `Dict[str, Any]` ou `None`: Dicionário com todas as portas

**Exemplo:**
```python
ports = DeviceAPIService.get_all_ports('esp32-sensor-001')
# {
#   'GPIO_32': {
#     'type': 'sensor',
#     'direction': 'input',
#     'function': 'temperature',
#     'current_value': 68.5,
#     'last_update': '2024-01-01T12:00:00Z',
#     'status': 'active'
#   },
#   'GPIO_25': {
#     'type': 'actuator',
#     'direction': 'output',
#     'function': 'relay',
#     'current_value': False,
#     'last_update': '2024-01-01T12:00:00Z',
#     'status': 'active'
#   }
# }
```

### get_port_config(device_id: str, port: str = None) -> Optional[Dict[str, Any]]

Obtém a configuração de uma ou todas as portas.

**Parâmetros:**
- `device_id` (str): ID do dispositivo
- `port` (str, opcional): Nome da porta específica. Se `None`, retorna todas

**Retorna:**
- `Dict[str, Any]` ou `None`: Configuração da(s) porta(s)

**Exemplo:**
```python
# Obter configuração de uma porta
config = DeviceAPIService.get_port_config('esp32-sensor-001', 'GPIO_32')
# {'type': 'sensor', 'direction': 'input', 'function': 'temperature', 'unit': 'celsius'}

# Obter configuração de todas as portas
all_configs = DeviceAPIService.get_port_config('esp32-sensor-001')
# {'GPIO_32': {...}, 'GPIO_25': {...}}
```

### set_port_value(device_id: str, port: str, value: Any) -> bool

Define o valor de uma porta específica.

**Parâmetros:**
- `device_id` (str): ID do dispositivo
- `port` (str): Nome da porta
- `value` (Any): Valor a definir

**Retorna:**
- `bool`: `True` se definido com sucesso

**Exemplo:**
```python
success = DeviceAPIService.set_port_value('esp32-sensor-001', 'GPIO_25', True)
# Envia comando MQTT para ativar a porta GPIO_25
```

### send_command(device_id: str, command: str, payload: Dict[str, Any] = None) -> bool

Envia um comando para um dispositivo.

**Parâmetros:**
- `device_id` (str): ID do dispositivo
- `command` (str): Nome do comando
- `payload` (Dict[str, Any], opcional): Dados do comando

**Retorna:**
- `bool`: `True` se comando enviado com sucesso

**Exemplo:**
```python
success = DeviceAPIService.send_command(
    'esp32-sensor-001',
    'set_temperature',
    {'target': 70.0, 'unit': 'celsius'}
)
```

### subscribe_telemetry(device_id: str, callback: Callable[[str, Dict], None]) -> bool

Inscreve-se em telemetria de um dispositivo.

**Parâmetros:**
- `device_id` (str): ID do dispositivo
- `callback` (Callable): Função callback(device_id, telemetry_data)

**Retorna:**
- `bool`: `True` se inscrito com sucesso

**Exemplo:**
```python
def handle_telemetry(device_id, data):
    print(f"Telemetria de {device_id}: {data}")
    if 'temperature' in data:
        # Processar temperatura
        pass

DeviceAPIService.subscribe_telemetry('esp32-sensor-001', handle_telemetry)
```

### list_devices_by_port_type(port_type: str = None) -> List[Dict[str, Any]]

Lista dispositivos filtrados por tipo de porta.

**Parâmetros:**
- `port_type` (str, opcional): Tipo de porta ('sensor' ou 'actuator'). Se `None`, retorna todos

**Retorna:**
- `List[Dict[str, Any]]`: Lista de dispositivos

**Exemplo:**
```python
# Obter todos os dispositivos com sensores
sensor_devices = DeviceAPIService.list_devices_by_port_type('sensor')

# Obter todos os dispositivos com atuadores
actuator_devices = DeviceAPIService.list_devices_by_port_type('actuator')

# Obter todos os dispositivos
all_devices = DeviceAPIService.list_devices_by_port_type()
```

## Exemplos de Uso Completo

### Exemplo 1: Monitorar Temperatura de Todos os Sensores

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService

# Obter todos os dispositivos com sensores de temperatura
sensor_devices = DeviceAPIService.list_devices_by_port_type('sensor')

for device in sensor_devices:
    device_id = device['device_id']
    ports = DeviceAPIService.get_all_ports(device_id)
    
    for port_name, port_data in ports.items():
        if port_data.get('function') == 'temperature':
            temp = port_data.get('current_value')
            if temp is not None:
                print(f"{device['name']} - {port_name}: {temp}°C")
```

### Exemplo 2: Controlar Múltiplos Atuadores

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService

# Obter todos os dispositivos com atuadores
actuator_devices = DeviceAPIService.list_devices_by_port_type('actuator')

for device in actuator_devices:
    device_id = device['device_id']
    ports_config = DeviceAPIService.get_port_config(device_id)
    
    for port_name, port_config in ports_config.items():
        if port_config.get('type') == 'actuator' and port_config.get('function') == 'relay':
            # Ativar relé
            DeviceAPIService.set_port_value(device_id, port_name, True)
            print(f"Relé {port_name} ativado em {device['name']}")
```

### Exemplo 3: Sistema de Alerta Baseado em Temperatura

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService

def check_temperature_alerts():
    """Verifica temperaturas e envia alertas se necessário."""
    sensor_devices = DeviceAPIService.list_devices_by_port_type('sensor')
    
    for device in sensor_devices:
        device_id = device['device_id']
        ports = DeviceAPIService.get_all_ports(device_id)
        
        for port_name, port_data in ports.items():
            if port_data.get('function') == 'temperature':
                temp = port_data.get('current_value')
                
                if temp is not None:
                    # Verificar limites
                    if temp > 80:
                        print(f"ALERTA: Temperatura alta em {device['name']}: {temp}°C")
                        # Enviar comando para desligar aquecedor
                        DeviceAPIService.send_command(device_id, 'emergency_shutdown')
                    elif temp < 10:
                        print(f"ALERTA: Temperatura baixa em {device['name']}: {temp}°C")

# Executar verificação periodicamente
import time
while True:
    check_temperature_alerts()
    time.sleep(60)  # Verificar a cada minuto
```

### Exemplo 4: Integração com Plugin de Receitas

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPIService

class RecipeController:
    def __init__(self):
        # Inscrever-se em telemetria de sensores de temperatura
        sensor_devices = DeviceAPIService.list_devices_by_port_type('sensor')
        
        for device in sensor_devices:
            device_id = device['device_id']
            DeviceAPIService.subscribe_telemetry(device_id, self.handle_temperature)
    
    def handle_temperature(self, device_id, telemetry_data):
        """Processa dados de temperatura para controle de receita."""
        if 'temperature' in telemetry_data:
            temp = telemetry_data['temperature']
            
            # Obter temperatura alvo da receita atual
            target_temp = self.get_current_recipe_target_temp()
            
            if temp < target_temp - 2:
                # Temperatura abaixo do alvo, ligar aquecedor
                self.activate_heater(device_id)
            elif temp > target_temp + 2:
                # Temperatura acima do alvo, desligar aquecedor
                self.deactivate_heater(device_id)
    
    def activate_heater(self, device_id):
        """Ativa aquecedor do dispositivo."""
        # Encontrar porta do aquecedor
        ports_config = DeviceAPIService.get_port_config(device_id)
        
        for port_name, port_config in ports_config.items():
            if port_config.get('function') == 'heater':
                DeviceAPIService.set_port_value(device_id, port_name, True)
                break
    
    def deactivate_heater(self, device_id):
        """Desativa aquecedor do dispositivo."""
        ports_config = DeviceAPIService.get_port_config(device_id)
        
        for port_name, port_config in ports_config.items():
            if port_config.get('function') == 'heater':
                DeviceAPIService.set_port_value(device_id, port_name, False)
                break
```

## Tratamento de Erros

Todos os métodos retornam `None` ou `False` em caso de erro. Sempre verifique o retorno:

```python
temperature = DeviceAPIService.get_port_value('device-id', 'GPIO_32')

if temperature is None:
    print("Erro ao obter temperatura")
    # Tratar erro
else:
    print(f"Temperatura: {temperature}°C")
```

## Notas Importantes

1. **Inicialização**: O `DeviceAPIService` é inicializado automaticamente quando o plugin é ativado
2. **Thread Safety**: Os métodos são thread-safe e podem ser chamados de qualquer thread
3. **Performance**: O histórico de mensagens é limitado a 1000 mensagens em memória
4. **MQTT**: Requer que o servidor MQTT esteja rodando para comandos e telemetria funcionarem

## Logs

Os erros são registrados automaticamente. Verifique `logs/brewstation.log` para detalhes.

