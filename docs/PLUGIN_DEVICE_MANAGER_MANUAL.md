# Manual do Usuário - Plugin Device Manager

## Índice

1. [Introdução](#introdução)
2. [Primeiros Passos](#primeiros-passos)
3. [Gerenciando Dispositivos](#gerenciando-dispositivos)
4. [Configurando o Broker MQTT](#configurando-o-broker-mqtt)
5. [Monitoramento MQTT](#monitoramento-mqtt)
6. [Configuração de Portas](#configuração-de-portas)
7. [Troubleshooting](#troubleshooting)

## Introdução

O Plugin Device Manager permite gerenciar dispositivos IoT conectados ao BrewStation através do protocolo MQTT. Com ele você pode:

- Cadastrar e gerenciar sensores, atuadores e gateways
- Configurar portas GPIO e suas funções
- Monitorar mensagens MQTT em tempo real
- Testar comunicação com dispositivos
- Controlar dispositivos remotamente

## Primeiros Passos

### 1. Instalar o Plugin

O plugin já vem instalado com o BrewStation. Se necessário, instale manualmente:

```bash
python run.py plugin -i device_manager
```

### 2. Ativar o Plugin

Ative o plugin via interface web ou CLI:

```bash
python run.py plugin -a device_manager
```

### 3. Acessar a Interface

Acesse o menu **"Dispositivos IoT"** na sidebar. Você verá as seguintes opções:

- **Todos Dispositivos**: Lista e gerencia dispositivos cadastrados
- **Adicionar Dispositivo**: Cadastra novos dispositivos
- **Brokers MQTT**: Configura o servidor MQTT
- **Logs e Status**: Visualiza logs do sistema
- **Monitoramento MQTT**: Monitora mensagens em tempo real

## Gerenciando Dispositivos

### Cadastrar um Novo Dispositivo

1. Clique em **"Adicionar Dispositivo"**
2. Preencha os campos:
   - **Nome**: Nome descritivo do dispositivo
   - **Tipo**: Sensor, Atuador ou Gateway
   - **Protocolo**: MQTT, HTTP ou WebSocket
3. Se o protocolo for **MQTT**, configure:
   - **Broker**: Endereço do broker (ex: `localhost:1883`)
   - **Client ID**: ID único do cliente MQTT
   - **Usuário/Senha**: Se o broker exigir autenticação
4. Configure as **Portas IoT**:
   - Clique em **"Adicionar Porta"**
   - Preencha:
     - **Nome da Porta**: Ex: `GPIO_32`
     - **Tipo**: Sensor ou Atuador
     - **Direção**: Entrada ou Saída
     - **Função**: Descrição (ex: `temperature`, `relay`)
5. Clique em **"Salvar"**

### Editar um Dispositivo

1. Na lista de dispositivos, clique em **"Editar"** no dispositivo desejado
2. Modifique os campos necessários
3. Clique em **"Salvar"**

### Remover um Dispositivo

1. Na lista de dispositivos, clique em **"Remover"**
2. Confirme a remoção

**⚠️ Atenção**: A remoção é permanente e não pode ser desfeita.

### Visualizar Detalhes

1. Clique em **"Ver"** no dispositivo desejado
2. Visualize:
   - Configuração completa
   - Estado atual das portas
   - Última atualização
   - Telemetria recebida

## Configurando o Broker MQTT

### Configuração Básica

1. Acesse **"Brokers MQTT"**
2. Configure:
   - **Habilitar Broker**: Ativa/desativa o servidor
   - **Host**: Endereço IP (use `0.0.0.0` para aceitar conexões de qualquer IP)
   - **Porta**: Porta padrão é `1883`
3. Clique em **"Salvar Configuração"**

### Autenticação

1. Marque **"Habilitar Autenticação"**
2. Preencha **Usuário** e **Senha**
3. Salve a configuração

**⚠️ Importante**: Após alterar a configuração, o servidor será reiniciado automaticamente.

### Iniciar/Parar o Servidor

- Use o botão **"Iniciar Servidor"** para iniciar manualmente
- Use o botão **"Parar Servidor"** para parar manualmente
- O status é exibido no topo da página

## Monitoramento MQTT

### Inscrever-se em um Tópico

1. Acesse **"Monitoramento MQTT"**
2. No campo **"Tópico MQTT"**, digite o tópico desejado
   - Exemplo: `brewstation/devices/+/telemetry`
   - Use `+` para wildcard de nível único
   - Use `#` para wildcard multinível
3. Selecione o **QoS** (0, 1 ou 2)
4. Clique em **"Inscrever"**

### Publicar Mensagem de Teste

1. No formulário **"Publicar Mensagem de Teste"**:
   - Digite o **Tópico**
   - Digite o **Payload** (JSON ou texto)
   - Selecione **QoS**
   - Marque **Retain** se necessário
2. Clique em **"Publicar"**

### Visualizar Mensagens

- Mensagens aparecem automaticamente na área de mensagens
- Mensagens recebidas aparecem em **verde**
- Mensagens enviadas aparecem em **amarelo**
- Mensagens do sistema aparecem em **azul**

### Controles

- **Rolagem Automática**: Ativa/desativa scroll automático
- **Limpar Mensagens**: Remove todas as mensagens do histórico
- **Pausar/Retomar**: Pausa ou retoma o monitoramento

### Estatísticas

No topo da página você vê:
- **Status do Broker**: Online/Offline
- **Mensagens Recebidas**: Contador de mensagens recebidas
- **Mensagens Enviadas**: Contador de mensagens enviadas
- **Tópicos Inscritos**: Número de tópicos ativos

## Configuração de Portas

### Tipos de Porta

#### Sensor (Entrada)
- Lê valores do ambiente ou dispositivo
- Exemplos: temperatura, umidade, pressão
- Direção: **Input**

#### Atuador (Saída)
- Controla ações do dispositivo
- Exemplos: relé, válvula, motor
- Direção: **Output**

### Configuração de Portas

Cada porta pode ter:

- **Nome**: Identificador único (ex: `GPIO_32`)
- **Tipo**: Sensor ou Atuador
- **Direção**: Entrada ou Saída
- **Função**: Descrição da função (ex: `temperature`, `relay`)

### Exemplo de Configuração

**Sensor de Temperatura:**
```
Nome: GPIO_32
Tipo: Sensor
Direção: Entrada
Função: temperature
```

**Relé de Controle:**
```
Nome: GPIO_25
Tipo: Atuador
Direção: Saída
Função: relay
```

## Troubleshooting

### Dispositivo não conecta ao Broker

**Sintomas**: Dispositivo aparece como "offline"

**Soluções**:
1. Verifique se o broker MQTT está rodando (status na página de configuração)
2. Verifique se o endereço do broker está correto
3. Verifique se a porta está correta (padrão: 1883)
4. Verifique se há firewall bloqueando a conexão
5. Verifique as credenciais de autenticação (se configuradas)

### Mensagens não aparecem no monitoramento

**Sintomas**: Nenhuma mensagem aparece na área de monitoramento

**Soluções**:
1. Verifique se está inscrito no tópico correto
2. Verifique se o dispositivo está realmente publicando mensagens
3. Verifique se o broker está rodando
4. Use o formulário de publicação para testar se o broker está funcionando

### Erro ao publicar mensagem

**Sintomas**: Erro ao tentar publicar mensagem de teste

**Soluções**:
1. Verifique se o broker está rodando
2. Verifique se o tópico está correto
3. Verifique se há permissões para publicar no tópico
4. Verifique os logs em `logs/brewstation.log`

### Porta não atualiza valor

**Sintomas**: Valor da porta não muda mesmo com dispositivo enviando dados

**Soluções**:
1. Verifique se o dispositivo está enviando dados no formato correto
2. Verifique se o tópico MQTT está configurado corretamente
3. Verifique se o nome da porta no dispositivo corresponde ao cadastrado
4. Verifique os logs para erros de parsing

### Servidor MQTT não inicia

**Sintomas**: Status mostra "Offline" e não consegue iniciar

**Soluções**:
1. Verifique se a porta 1883 está disponível
2. Verifique se há outro servidor MQTT rodando na mesma porta
3. Verifique os logs em `logs/brewstation.log`
4. Tente usar outra porta (ex: 1884)

## Dicas e Boas Práticas

### Nomenclatura de Tópicos

Use uma estrutura hierárquica consistente:

```
brewstation/devices/{device_id}/{tipo}
```

Exemplos:
- `brewstation/devices/temp001/telemetry`
- `brewstation/devices/temp001/command`
- `brewstation/devices/temp001/status`

### QoS (Quality of Service)

- **QoS 0**: "No máximo uma vez" - Mais rápido, pode perder mensagens
- **QoS 1**: "Pelo menos uma vez" - Garante entrega, pode duplicar
- **QoS 2**: "Exatamente uma vez" - Garante entrega única, mais lento

**Recomendação**: Use QoS 1 para a maioria dos casos.

### Retain

Marque **Retain** quando:
- A mensagem contém estado atual que novos subscribers devem receber
- Exemplo: Estado atual de um sensor

Não marque **Retain** quando:
- A mensagem é um evento único
- Exemplo: Comando para executar uma ação

### Segurança

1. **Sempre** configure autenticação em produção
2. Use TLS/SSL para comunicação segura
3. Restrinja padrões de tópicos permitidos
4. Use senhas fortes
5. Monitore logs regularmente

## Exemplos Práticos

### Exemplo 1: Monitorar Temperatura

1. Cadastre um dispositivo sensor de temperatura
2. Configure porta `GPIO_32` como sensor de entrada, função `temperature`
3. Configure tópico de telemetria: `brewstation/devices/temp001/telemetry`
4. No monitoramento, inscreva-se em: `brewstation/devices/+/telemetry`
5. Visualize as mensagens de temperatura em tempo real

### Exemplo 2: Controlar Relé

1. Cadastre um dispositivo com relé
2. Configure porta `GPIO_25` como atuador de saída, função `relay`
3. Configure tópico de comando: `brewstation/devices/relay001/command`
4. No monitoramento, publique mensagem:
   - Tópico: `brewstation/devices/relay001/command`
   - Payload: `{"command": "set_port", "port": "GPIO_25", "value": true}`

### Exemplo 3: Monitorar Múltiplos Dispositivos

1. Use wildcards para inscrever-se em múltiplos dispositivos:
   - Tópico: `brewstation/devices/+/telemetry`
2. Filtre mensagens por dispositivo no payload JSON
3. Use diferentes funções de porta para identificar tipos de dados

## Suporte

Para mais informações:
- Documentação técnica: [Plugin Device Manager](PLUGIN_DEVICE_MANAGER.md)
- API para desenvolvedores: [Device Manager API](PLUGIN_DEVICE_MANAGER_API.md)
- Logs do sistema: `logs/brewstation.log`

