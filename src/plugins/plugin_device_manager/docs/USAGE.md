# Guia de Uso - Plugin Device Manager

## Introdução

Este guia explica como usar o Plugin Device Manager através da interface web e como configurar dispositivos, funções e atores.

## Fluxo Básico de Trabalho

### 1. Cadastrar um Dispositivo

1. Acesse **Dispositivos IoT > Adicionar Dispositivo**
2. Preencha as informações básicas:
   - **Nome**: Nome identificador do dispositivo
   - **Tipo**: Sensor, Atuador ou Gateway
   - **Protocolo**: MQTT, HTTP ou WebSocket
3. Se o protocolo for MQTT, configure:
   - **Broker**: Endereço e porta do broker (ex: `localhost:1883`)
   - **Client ID**: ID do cliente MQTT
   - **Usuário/Senha**: Credenciais se necessário
4. Adicione portas do dispositivo:
   - Clique em **+ Adicionar Porta**
   - Defina o nome da porta (ex: `GPIO1`, `ADC0`)
   - Selecione uma função ou crie uma nova
   - Opcionalmente, crie um ator para a porta
5. Clique em **Salvar**

### 2. Gerenciar Funções

#### Visualizar Funções

1. Acesse **Dispositivos IoT > Funções**
2. Use os filtros para encontrar funções:
   - **Categoria**: Sensor, Atuador ou Híbrido
   - **Tipo**: Pré-definidas ou Customizadas
   - **Busca**: Por nome ou descrição

#### Criar Função Customizada

1. Acesse **Dispositivos IoT > Funções**
2. Clique em **Criar Função**
3. Preencha os campos:
   - **Nome (ID)**: Nome único (ex: `meu_sensor`)
   - **Nome de Exibição**: Nome amigável
   - **Categoria**: Sensor, Atuador ou Híbrido
   - **Tipo de Dado**: Float, Inteiro, Boolean ou String
   - **Unidade**: Unidade de medida (ex: `°C`, `%`, `V`)
   - **Valor Mínimo/Máximo**: Faixa de valores (opcional)
   - **Ícone**: Classe do ícone Bootstrap Icons
4. Clique em **Salvar Função**

#### Editar/Deletar Função

- Funções pré-definidas não podem ser editadas ou deletadas
- Funções customizadas podem ser editadas clicando no ícone de lápis
- Funções customizadas podem ser deletadas clicando no ícone de lixeira
- Funções em uso por atores não podem ser deletadas

### 3. Gerenciar Atores

#### Visualizar Atores

1. Acesse **Dispositivos IoT > Atores**
2. Use os filtros:
   - **Dispositivo**: Filtrar por dispositivo
   - **Tipo**: Sensor, Atuador ou Trigger de Regra
   - **Plugin**: Filtrar por plugin que usa o ator
   - **Busca**: Por nome

#### Criar Ator

1. Acesse **Dispositivos IoT > Atores**
2. Clique em **Criar Ator**
3. Preencha os campos:
   - **Nome**: Nome identificador do ator
   - **Dispositivo**: Selecione o dispositivo
   - **Porta**: Nome da porta (ex: `GPIO1`)
   - **Função**: Selecione a função
   - **Tipo**: Sensor, Atuador ou Trigger de Regra
   - **Descrição**: Descrição opcional
   - **Plugin**: Plugin que usa este ator (opcional)
   - **ID da Entidade**: ID da entidade no plugin (opcional)
4. Clique em **Salvar Ator**

#### Testar Ator

1. Na lista de atores, clique no ícone de play (▶️) ao lado do ator
2. Para sensores: O valor atual será exibido
3. Para atuadores: Você pode definir um valor e executar a ação

#### Editar/Deletar Ator

- Clique no ícone de lápis para editar
- Clique no ícone de lixeira para deletar

### 4. Monitoramento MQTT

#### Visualizar Status do Broker

1. Acesse **Dispositivos IoT > Monitoramento MQTT**
2. O status do broker será exibido automaticamente

#### Testar Publicação

1. Acesse **Dispositivos IoT > Monitoramento MQTT**
2. Use a seção de testes para:
   - Publicar mensagens em tópicos
   - Inscrever-se em tópicos
   - Visualizar histórico de mensagens

## Casos de Uso Comuns

### Caso 1: Cadastrar Sensor de Temperatura

1. **Criar Dispositivo:**
   - Nome: "Sensor Temperatura Sala"
   - Tipo: Sensor
   - Protocolo: MQTT
   - Broker: `localhost:1883`

2. **Adicionar Porta:**
   - Nome: `GPIO1`
   - Função: Temperatura (pré-definida)
   - Criar Ator: Sensor de Temperatura Sala

3. **Resultado:**
   - Dispositivo cadastrado
   - Ator criado e pronto para uso
   - Outros plugins podem ler a temperatura via ator

### Caso 2: Cadastrar Relé para Controle

1. **Criar Dispositivo:**
   - Nome: "Controlador Relés"
   - Tipo: Atuador
   - Protocolo: MQTT

2. **Adicionar Porta:**
   - Nome: `RELAY1`
   - Função: Relé (pré-definida)
   - Criar Ator: Tipo "Atuador"

3. **Resultado:**
   - Ator criado para controlar o relé
   - Outros plugins podem ligar/desligar via `execute_action()`

### Caso 3: Criar Função Customizada

1. **Acessar Funções:**
   - Dispositivos IoT > Funções

2. **Criar Função:**
   - Nome: `ph_sensor`
   - Nome de Exibição: "Sensor de pH"
   - Categoria: Sensor
   - Tipo de Dado: Float
   - Unidade: `pH`
   - Min: 0.0, Max: 14.0

3. **Usar a Função:**
   - Agora você pode usar esta função ao criar atores

## Trabalhando com Portas

### Tipos de Portas

As portas representam interfaces físicas ou lógicas do dispositivo:

- **GPIO**: Entrada/saída digital
- **ADC**: Conversor analógico-digital
- **PWM**: Modulação por largura de pulso
- **Relé**: Controle de relé digital

### Configuração de Portas

Ao cadastrar um dispositivo, você pode:

1. Adicionar múltiplas portas
2. Associar cada porta a uma função
3. Criar um ator para cada porta (opcional)
4. Configurar propriedades específicas da porta

## Trabalhando com Atores

### Tipos de Atores

1. **Sensor**: Lê valores de sensores
   - Use `read_sensor()` para ler valores
   - Use `subscribe_sensor()` para monitorar mudanças

2. **Atuador**: Controla atuadores
   - Use `execute_action()` para executar ações
   - Valores podem ser bool, int, float ou string

3. **Trigger de Regra**: Dispara regras baseadas em condições
   - Similar a atuador, mas usado para lógica de regras

### Associação com Plugins

Atores podem ser associados a outros plugins:

1. Ao criar/editar um ator, defina:
   - **Plugin**: Nome do plugin (ex: `plugin_mash_control`)
   - **ID da Entidade**: ID da entidade no plugin (ex: `recipe_123`)

2. Isso permite que o plugin busque atores associados:
   ```python
   actors = DeviceAPI.list_actors_by_plugin('plugin_mash_control', 'recipe_123')
   ```

## Dicas e Boas Práticas

1. **Nomenclatura:**
   - Use nomes descritivos para dispositivos e atores
   - Siga um padrão consistente (ex: "Sensor Temperatura - GPIO1")

2. **Funções:**
   - Prefira usar funções pré-definidas quando possível
   - Crie funções customizadas apenas quando necessário
   - Documente funções customizadas com boas descrições

3. **Atores:**
   - Crie atores para todas as portas que serão usadas
   - Associe atores a plugins quando aplicável
   - Use descrições claras para facilitar identificação

4. **MQTT:**
   - Teste a conexão MQTT antes de cadastrar dispositivos
   - Use tópicos organizados (ex: `brewstation/devices/device_id/port`)
   - Monitore o histórico de mensagens para debugging

5. **Organização:**
   - Agrupe dispositivos relacionados
   - Use filtros para encontrar recursos rapidamente
   - Mantenha nomes consistentes

## Troubleshooting

### Dispositivo não conecta

1. Verifique a configuração do broker MQTT
2. Teste a conexão usando Monitoramento MQTT
3. Verifique se o broker está rodando
4. Verifique credenciais se houver autenticação

### Ator não executa ação

1. Verifique se o ator está ativo
2. Verifique se o tipo do ator é `actuator` ou `rule_trigger`
3. Verifique a conexão MQTT do dispositivo
4. Verifique os logs do sistema

### Sensor não retorna valor

1. Verifique se o ator está ativo
2. Verifique se o tipo do ator é `sensor`
3. Verifique se o dispositivo está online
4. Verifique se há mensagens MQTT chegando

### Função não pode ser deletada

1. Verifique se a função está sendo usada por algum ator
2. Funções pré-definidas não podem ser deletadas
3. Delete ou desassocie atores antes de deletar a função
