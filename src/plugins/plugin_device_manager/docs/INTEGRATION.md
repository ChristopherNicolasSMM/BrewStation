# Guia de Integração - Plugin Device Manager

## Visão Geral

Este guia explica como outros plugins do BrewStation podem integrar-se com o Plugin Device Manager para controlar dispositivos IoT e ler sensores.

## API Pública

O Device Manager expõe uma API pública através da classe `DeviceAPI` localizada em `plugins.plugin_device_manager.utils.device_api`.

## Importação

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPI
```

## Métodos Disponíveis

### Obter Ator

```python
actor = DeviceAPI.get_actor(actor_id)
```

Retorna informações completas do ator, incluindo dispositivo, função e configuração.

**Parâmetros:**
- `actor_id` (str): ID do ator

**Retorno:**
```python
{
    'id': 'uuid',
    'device_id': 'device_uuid',
    'port_name': 'GPIO1',
    'function_id': 1,
    'actor_type': 'sensor',
    'name': 'Sensor de Temperatura',
    'description': '...',
    'config': {},
    'plugin_name': None,
    'plugin_entity_id': None,
    'is_active': True
}
```

### Executar Ação

```python
success = DeviceAPI.execute_action(actor_id, value)
```

Executa uma ação em um ator (liga/desliga, define valor).

**Parâmetros:**
- `actor_id` (str): ID do ator (deve ser do tipo `actuator` ou `rule_trigger`)
- `value` (Any): Valor a enviar (bool, int, float, string)

**Retorno:**
- `bool`: True se executado com sucesso

**Exemplo:**
```python
# Ligar relé
DeviceAPI.execute_action('actor_uuid', True)

# Definir valor PWM (0-100)
DeviceAPI.execute_action('pwm_actor_uuid', 75)

# Enviar string
DeviceAPI.execute_action('display_actor_uuid', 'Hello')
```

### Ler Sensor

```python
value = DeviceAPI.read_sensor(actor_id)
```

Lê o valor atual de um sensor.

**Parâmetros:**
- `actor_id` (str): ID do ator (deve ser do tipo `sensor`)

**Retorno:**
- Valor do sensor (int, float, bool, string ou None)

**Exemplo:**
```python
temperature = DeviceAPI.read_sensor('temp_sensor_uuid')
if temperature is not None:
    print(f"Temperatura: {temperature}°C")
```

### Inscrever em Sensor

```python
success = DeviceAPI.subscribe_sensor(actor_id, callback)
```

Inscreve-se em mudanças de valor de um sensor.

**Parâmetros:**
- `actor_id` (str): ID do ator (deve ser do tipo `sensor`)
- `callback` (callable): Função `callback(actor_id, value)` chamada quando o valor muda

**Retorno:**
- `bool`: True se inscrito com sucesso

**Exemplo:**
```python
def on_temperature_change(actor_id, value):
    print(f"Temperatura mudou: {value}°C")
    # Atualizar UI, salvar em banco, etc.

DeviceAPI.subscribe_sensor('temp_sensor_uuid', on_temperature_change)
```

### Listar Atores por Tipo

```python
actors = DeviceAPI.list_actors_by_type(actor_type, plugin_name=None)
```

Lista atores filtrados por tipo.

**Parâmetros:**
- `actor_type` (str): Tipo do ator (`sensor`, `actuator`, `rule_trigger`)
- `plugin_name` (str, opcional): Filtrar por plugin

**Retorno:**
- `List[Dict]`: Lista de atores

**Exemplo:**
```python
# Listar todos os sensores
sensors = DeviceAPI.list_actors_by_type('sensor')

# Listar atuadores do meu plugin
actuators = DeviceAPI.list_actors_by_type('actuator', 'plugin_mash_control')
```

### Listar Atores por Plugin

```python
actors = DeviceAPI.list_actors_by_plugin(plugin_name, plugin_entity_id=None)
```

Lista atores associados a um plugin.

**Parâmetros:**
- `plugin_name` (str): Nome do plugin
- `plugin_entity_id` (str, opcional): ID da entidade no plugin

**Retorno:**
- `List[Dict]`: Lista de atores

**Exemplo:**
```python
# Listar todos os atores do meu plugin
my_actors = DeviceAPI.list_actors_by_plugin('plugin_mash_control')

# Listar atores de uma receita específica
recipe_actors = DeviceAPI.list_actors_by_plugin('plugin_mash_control', 'recipe_123')
```

### Associar Ator a Plugin

```python
success = DeviceAPI.link_actor_to_plugin(actor_id, plugin_name, plugin_entity_id)
```

Associa um ator a uma entidade do plugin.

**Parâmetros:**
- `actor_id` (str): ID do ator
- `plugin_name` (str): Nome do plugin
- `plugin_entity_id` (str): ID da entidade no plugin

**Retorno:**
- `bool`: True se associado com sucesso

## Exemplo Completo: Controle de Temperatura

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPI

class MashControlProcess:
    def __init__(self, recipe_id):
        self.recipe_id = recipe_id
        self.temp_sensor_actor = None
        self.heater_actor = None
        self.target_temp = 65.0
        
    def setup(self):
        # Buscar atores associados a esta receita
        actors = DeviceAPI.list_actors_by_plugin('plugin_mash_control', self.recipe_id)
        
        # Encontrar sensor de temperatura e aquecedor
        for actor in actors:
            if actor['actor_type'] == 'sensor':
                # Verificar função (assumindo função de temperatura tem id 1)
                if actor['function_id'] == 1:  # Temperatura
                    self.temp_sensor_actor = actor
            elif actor['actor_type'] == 'actuator':
                # Assumindo que há um aquecedor
                self.heater_actor = actor
        
        # Inscrever em mudanças de temperatura
        if self.temp_sensor_actor:
            DeviceAPI.subscribe_sensor(
                self.temp_sensor_actor['id'],
                self.on_temperature_change
            )
    
    def on_temperature_change(self, actor_id, value):
        """Callback chamado quando temperatura muda"""
        if value is None:
            return
        
        if value < self.target_temp:
            # Ligar aquecedor
            if self.heater_actor:
                DeviceAPI.execute_action(self.heater_actor['id'], True)
        else:
            # Desligar aquecedor
            if self.heater_actor:
                DeviceAPI.execute_action(self.heater_actor['id'], False)
    
    def get_current_temperature(self):
        """Lê temperatura atual"""
        if self.temp_sensor_actor:
            return DeviceAPI.read_sensor(self.temp_sensor_actor['id'])
        return None
    
    def set_heater(self, on):
        """Controla aquecedor"""
        if self.heater_actor:
            return DeviceAPI.execute_action(self.heater_actor['id'], on)
        return False
```

## Exemplo: Seleção de Atores na Interface

```python
# No seu plugin, forneça interface para selecionar atores
def get_available_actors(actor_type):
    """Lista atores disponíveis para seleção"""
    actors = DeviceAPI.list_actors_by_type(actor_type)
    
    # Formatar para select/dropdown
    options = []
    for actor in actors:
        options.append({
            'value': actor['id'],
            'label': f"{actor['name']} ({actor['device_id']})"
        })
    
    return options

# Na UI (JavaScript)
# Usar API REST diretamente:
fetch('/api/device_manager/actors?actor_type=sensor')
  .then(r => r.json())
  .then(data => {
    // Preencher dropdown com data.actors
  });
```

## Fluxo de Integração Recomendado

### 1. Durante Configuração

1. O usuário configura seu plugin (ex: receita de brassagem)
2. O plugin oferece interface para selecionar atores
3. Usuário seleciona atores (sensor de temperatura, aquecedor, etc.)
4. Plugin associa atores usando `link_actor_to_plugin()`

### 2. Durante Execução

1. Plugin busca atores associados usando `list_actors_by_plugin()`
2. Plugin lê valores de sensores usando `read_sensor()`
3. Plugin executa ações usando `execute_action()`
4. Plugin pode inscrever-se em mudanças usando `subscribe_sensor()`

### 3. Durante Monitoramento

1. Plugin lê valores periodicamente
2. Plugin atualiza interface/base de dados
3. Plugin reage a mudanças via callbacks

## Tratamento de Erros

```python
from plugins.plugin_device_manager.utils.device_api import DeviceAPI

try:
    value = DeviceAPI.read_sensor(actor_id)
    if value is None:
        # Sensor não retornou valor (offline, erro, etc.)
        handle_sensor_error()
    else:
        process_sensor_value(value)
except Exception as e:
    # Erro ao acessar API
    logger.error(f"Erro ao ler sensor: {e}")
    handle_api_error()
```

## Boas Práticas

1. **Validação:**
   - Sempre verifique se atores existem antes de usar
   - Valide tipos de atores (sensor vs actuator)
   - Trate valores None de sensores

2. **Associação:**
   - Associe atores a entidades do plugin para facilitar busca
   - Use IDs únicos e consistentes para entidades

3. **Callbacks:**
   - Callbacks devem ser thread-safe
   - Evite operações bloqueantes em callbacks
   - Trate erros em callbacks

4. **Performance:**
   - Use subscrições para monitoramento contínuo
   - Use leituras diretas para valores pontuais
   - Cache atores quando apropriado

5. **Logging:**
   - Registre uso de atores para debugging
   - Log erros e valores importantes
   - Mantenha rastreabilidade

## Dependências

O plugin Device Manager deve estar instalado e ativo. Verifique:

```python
from flask import current_app

plugin_manager = current_app.plugin_manager
device_manager = plugin_manager.get_plugin('device_manager')

if not device_manager or not device_manager.is_active:
    raise RuntimeError("Device Manager plugin não está ativo")
```

## Limitações e Considerações

1. **Thread Safety:**
   - A API é thread-safe, mas callbacks podem ser chamados de threads diferentes
   - Use locks quando necessário para operações críticas

2. **Disponibilidade:**
   - Sensores podem estar offline
   - Sempre trate valores None
   - Implemente timeouts para operações críticas

3. **Performance:**
   - Múltiplas subscrições podem impactar performance
   - Use polling quando subscrições não são necessárias
   - Considere agregar múltiplas leituras

4. **MQTT:**
   - Ações via MQTT dependem da conexão
   - Mensagens podem ser perdidas (QoS 0)
   - Use QoS 1 ou 2 para mensagens críticas

## Exemplo de Integração Completa

Veja o plugin `plugin_mash_control` para um exemplo completo de integração com o Device Manager.
