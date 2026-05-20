**Especificação para Implementação de Sessões de Brassagem Visuais e Dashboards Personalizáveis no BrewStation**  
*Documento para Agentes de IA – Versão 1.0*

**Objetivo Geral**  
Evoluir o sistema BrewStation para oferecer uma experiência de brassagem fluida, inspirada no CraftBeerPi4, com dashboards visuais personalizáveis por usuário, integrando profundamente os plugins `plugin_device_manager` e `plugin_mash_control`. A solução deve permitir que cada usuário crie plantas (equipamentos) associando sensores e atuadores, execute sessões de mostura baseadas nessas plantas e monte dashboards arrastando widgets.

**Instruções para o Agente**  
- Você é um desenvolvedor encarregado de implementar as tarefas descritas abaixo na base de código do BrewStation (disponível nos caminhos fornecidos).  
- Trabalhe em branches separadas para cada tarefa (ex: `feat/plant-model`) e faça commits frequentes com mensagens claras.  
- Todo novo código deve incluir docstrings (Python) ou comentários (JavaScript/HTML) explicando propósito, parâmetros e retornos.  
- Após cada tarefa, atualize ou crie a documentação na pasta `docs/` do repositório principal, em arquivos Markdown (ex: `docs/plants.md`, `docs/dashboards.md`). Mantenha um índice em `docs/README.md`.  
- Siga boas práticas: trate erros, valide entradas, use modularidade e, sempre que possível, inclua testes unitários.  
- Comunique-se com o usuário ao final de cada tarefa, informando o que foi feito e onde está a documentação.

---

## Fase 1 – Conceito de Planta (Equipamento) e Sua Integração com Device Manager

**Objetivo:** Criar uma entidade `Plant` que agrupa atores lógicos (sensor, heater, pump) a partir dos dispositivos cadastrados no `plugin_device_manager`. Isso elimina a necessidade de selecionar atores manualmente a cada sessão.

### Tarefa 1.1 – Modelo de Dados da Planta
- Criar modelo `Plant` no arquivo `src/plugins/plugin_mash_control/models.py`.  
  - Campos: `id` (int, PK), `name` (str), `description` (str), `user_id` (int, FK), `configuration` (JSON) – o JSON armazenará mapeamento como `{"sensor_temp": <actor_id>, "heater": <actor_id>, "pump": <actor_id>}`.  
  - Métodos de validação: verificar se os `actor_id` referenciados existem no `plugin_device_manager`.  
- Atualizar o esquema do banco de dados (migration) se aplicável (ex: SQLAlchemy `Base.metadata.create_all`).  
- Adicionar no `__init__.py` do plugin a importação do novo modelo.  
- Documentar: adicionar `docs/plants.md` com descrição do modelo, campos e exemplo de JSON de configuração.

### Tarefa 1.2 – API CRUD de Plantas
- No arquivo `src/plugins/plugin_mash_control/api.py` (ou onde já existam rotas `/mash_control/plants`), implementar endpoints completos:  
  - `GET /api/plants` – listar plantas do usuário logado.  
  - `POST /api/plants` – criar nova planta, recebendo `name`, `description` e `configuration` (JSON com mapeamento de atores).  
  - `GET /api/plants/<id>` – detalhes da planta.  
  - `PUT /api/plants/<id>` – atualizar.  
  - `DELETE /api/plants/<id>` – remover.  
- Validar que os `actor_id` existem usando a `DeviceAPI` do `plugin_device_manager`.  
- Retornar mensagens de erro claras (ex: "Ator não encontrado").  
- Documentar: descrever endpoints, parâmetros e respostas em `docs/plants.md`.

### Tarefa 1.3 – Interface do Usuário para Gerenciar Plantas
- Criar templates HTML e JavaScript dentro do `plugin_mash_control` para:
  - Listar plantas existentes.
  - Formulário de criação/edição com campos: nome, descrição.
  - Seção dinâmica para adicionar funções (sensor_temp, heater, pump) usando dropdowns que carregam atores disponíveis via `DeviceAPI.list_actors()` (endpoint a ser garantido, senão criar um auxiliar no plugin).
- A interface deve ser acessível pela rota `/mash_control/plants`.  
- Documentar: instruções de uso no `docs/plants.md` e capturas de tela (se possível).

### Tarefa 1.4 – Testes Unitários para Planta
- Criar arquivo `tests/test_plants.py` (ou na estrutura do plugin).  
- Testar criação, validação de ator inexistente, listagem, atualização e remoção.  
- Usar fixtures para simular usuário e atores mockados.  
- Documentar: como rodar os testes em `docs/plants.md`.

---

## Fase 2 – Integração da Sessão de Mostura com Plantas

**Objetivo:** Fazer com que a `MashSession` utilize uma planta para resolver automaticamente quais atores usar durante a execução dos passos.

### Tarefa 2.1 – Atualizar Modelo de Sessão
- No modelo `MashSession` (models.py do plugin_mash_control), adicionar campo `plant_id` (FK para `Plant`, opcional inicialmente para manter compatibilidade).  
- Se a sessão usar uma planta, os campos soltos de sensor/heater existentes podem ser preenchidos automaticamente ao iniciar a sessão (lógica na Tarefa 2.3).  
- Garantir que migrações sejam aplicadas.  
- Documentar: atualizar `docs/sessions.md` explicando a relação.

### Tarefa 2.2 – Ajustar Criação de Sessão
- Na API de criação de `MashSession` (`POST /api/mash_control/sessions`), aceitar `plant_id` em vez de (ou além de) parâmetros diretos.  
- Se `plant_id` for informado, carregar a planta e popular os campos de atores da sessão a partir da configuração.  
- Atualizar a interface de criação de sessão para selecionar uma planta existente (dropdown).  
- Documentar: novos parâmetros e comportamento.

### Tarefa 2.3 – Modificar Executor de Passo (MashExecutor)
- No arquivo responsável pelo controle da temperatura (ex: `src/plugins/plugin_mash_control/mash_executor.py`), adaptar o método `execute_step` para usar a `DeviceAPI` com os atores definidos na sessão.  
  - Obter `sensor = DeviceAPI.get_actor(session.sensor_temp_id)` e `heater = DeviceAPI.get_actor(session.heater_id)`.  
  - Substituir qualquer referência genérica a dispositivo por essas chamadas.  
- Manter controle PID (já existente) usando a leitura do sensor e acionamento do heater.  
- Adicionar tratamento de erro robusto (ex: ator desconectado, falha de leitura), emitindo alertas para o front-end (via futuro WebSocket, mas por ora via logs e status da sessão).  
- Documentar: fluxo de controle no código com comentários e em `docs/mash_execution.md`.

### Tarefa 2.4 – Expor Lista de Atores para UI de Plantas
- Garantir que o `plugin_device_manager` disponibilize endpoint `GET /api/device/actors` ou similar, retornando todos os atores cadastrados com tipo e função.  
- Se não existir, implementar no próprio plugin (já que há `DeviceAPI`).  
- Documentar: atualizar documentação do device manager.

### Tarefa 2.5 – Testes de Integração
- Criar teste em `tests/test_mash_integration.py`:  
  - Cria uma planta com atores mock.  
  - Cria uma sessão vinculada.  
  - Simula execução de passo verificando se leituras e ações são direcionadas aos atores corretos.  
- Documentar: explicação dos cenários em `docs/testing.md`.

---

## Fase 3 – Sistema de Dashboards Personalizáveis

**Objetivo:** Permitir que cada usuário monte visualmente seu painel de controle arrastando widgets (display de sensor, botão de atuador, controle de passo) e salvando o layout.

### Tarefa 3.1 – Design do Sistema de Widgets
- Definir uma estrutura JSON para descrever widgets e layouts. Exemplo de `layout`:
  ```json
  {
    "grid": { "columns": 4, "rows": 3 },
    "widgets": [
      {
        "id": "w1",
        "type": "sensor_display",
        "config": { "actor_id": 12, "label": "Temperatura" },
        "position": { "col": 1, "row": 1, "width": 2, "height": 1 }
      },
      ...
    ]
  }
  ```
- Mapear tipos de widget iniciais:
  - `sensor_display`: exibe valor do sensor em tempo real.
  - `actuator_button`: botão liga/desliga para atuador.
  - `step_control`: mostra passo atual, botões iniciar/pausar/avançar.
  - `timer`: temporizador regressivo do passo.
  - `chart`: gráfico de temperatura (posterior).
- Documentar: criar `docs/dashboard_widgets.md` com especificação de cada tipo, opções de configuração e exemplos.

### Tarefa 3.2 – Modelo `UserDashboard`
- Criar novo plugin `plugin_dashboard` (ou manter dentro de mash_control, mas recomendo novo para separar responsabilidades).  
- Modelo SQLAlchemy: `UserDashboard` com campos `id`, `user_id` (FK), `name`, `layout_json` (TEXT ou JSON), `created_at`, `updated_at`.  
- Método para validar estrutura do JSON (widgets com tipos conhecidos, posições dentro do grid).  
- Criar rota base `/dashboard`.  
- Documentar: `docs/dashboards.md` com modelo e esquema do JSON.

### Tarefa 3.3 – API de Dashboards
- Endpoints:
  - `GET /api/dashboards` – lista dashboards do usuário.
  - `POST /api/dashboards` – criar novo (recebe `name` e `layout_json`).
  - `GET /api/dashboards/<id>` – obtém layout completo.
  - `PUT /api/dashboards/<id>` – atualiza layout.
  - `DELETE /api/dashboards/<id>` – remove.
- Validação do JSON usando schema (pode ser uma função de validação simples).  
- Documentar: adicionar seção de API em `docs/dashboards.md`.

### Tarefa 3.4 – Editor de Dashboard (Front-end)
- Criar template `dashboard/editor.html` com:
  - Grid CSS vazio (representando o layout salvo).
  - Paleta lateral de widgets disponíveis (ícones e nomes).
  - Funcionalidade de arrastar e soltar (drag & drop) usando biblioteca leve como `interact.js` ou vanilla JS.
  - Ao soltar, abrir modal de configuração do widget (ex: para sensor, selecionar ator via dropdown carregado dinamicamente da API de atores).
  - Botão "Salvar" que envia o JSON do layout atualizado para a API.
- JavaScript modular; comentar funções principais.  
- Documentar: como usar o editor, dependências, em `docs/dashboards.md`.

### Tarefa 3.5 – Visualizador de Dashboard (Modo de Uso)
- Criar template `dashboard/view.html` que renderiza o grid conforme o `layout_json`.
- Cada widget é um componente HTML que chama APIs para obter estado inicial:
  - `sensor_display`: faz `GET /api/device/actors/<id>/sensor/current` e exibe valor.
  - `actuator_button`: obtém estado atual e permite toggle via `POST /api/device/actors/<id>/action`.
  - `step_control`: interage com endpoints de sessão (`/api/mash_control/session/<id>/start`, `/pause`, `/next_step`).
- Inicialmente, atualizações manuais (sem WebSocket) – o usuário pode recarregar ou ter um botão "atualizar".  
- Documentar: como o usuário final usa o dashboard.

### Tarefa 3.6 – Conexão dos Widgets com DeviceAPI
- No lado servidor, preparar endpoints auxiliares que os widgets vão consumir:
  - `GET /api/dashboard/widgets/sensor/<actor_id>` – retorna última leitura.
  - `POST /api/dashboard/widgets/actuator/<actor_id>/toggle` – alterna estado.
  - `GET /api/mash_control/sessions/current/step` – informações do passo atual.
- Implementar lógica que busca dados do `plugin_device_manager` e `plugin_mash_control`.  
- Documentar: adicionar na documentação da API do dashboard.

### Tarefa 3.7 – Testes do Dashboard
- Testar endpoints de CRUD de dashboard.  
- Testar validação de JSON (rejeitar layouts inválidos).  
- Testar mock de chamadas de widget.  
- Documentar: instruções de teste em `docs/dashboards.md`.

---

## Fase 4 – Atualizações em Tempo Real com WebSockets

**Objetivo:** Substituir as atualizações manuais por um fluxo contínuo de dados, fazendo com que displays de sensor e botões reajam instantaneamente às mudanças do hardware.

### Tarefa 4.1 – Integrar Flask-SocketIO no BrewStation
- Na inicialização do sistema (app.py ou core), configurar Flask-SocketIO.  
- Garantir que o servidor suporte a conexão de WebSockets.  
- Criar um módulo `socketio` central que outros plugins possam importar para emitir eventos.  
- Documentar: `docs/websockets.md` com instruções de configuração, requisitos (eventlet/gevent).

### Tarefa 4.2 – Emitir Eventos de Sensores
- No `plugin_device_manager`, onde quer que uma nova leitura de sensor seja processada (ex: após uma assinatura de sensor), emitir um evento SocketIO:  
  `socketio.emit('sensor_update', {'actor_id': actor.id, 'value': reading, 'timestamp': ...}, room=user_room)`  
- Criar salas (rooms) por usuário ou por sessão para isolar os dados.  
- Documentar: eventos disponíveis e formato dos dados.

### Tarefa 4.3 – Assinar Eventos no Dashboard Viewer
- No front-end do visualizador (view.html), incluir script Socket.IO e conectar ao servidor.  
- Para cada widget do tipo `sensor_display`, inscrever-se no evento `sensor_update` e atualizar o DOM apenas se o `actor_id` corresponder.  
- Para `actuator_button`, ouvir eventos de mudança de estado do ator (se implementado) ou atualizar via callback após a ação.  
- Para `step_control`, ouvir eventos como `step_changed`, `timer_tick` (definidos no mash_control).  
- Documentar: em `docs/dashboards.md` como funciona a parte cliente dos WebSockets.

### Tarefa 4.4 – Emitir Eventos da Sessão de Mostura
- No `MashExecutor`, emitir eventos SocketIO sempre que:
  - Um novo passo é iniciado.
  - O temporizador do passo avança (a cada segundo? a cada 10s? – escolher uma periodicidade para não sobrecarregar).
  - Um erro ocorre (ex: falha no aquecimento).
- Usar a sala da sessão atual.  
- Documentar: lista de eventos da sessão.

### Tarefa 4.5 – Testes dos WebSockets
- Testar conexão e recepção de eventos com cliente de teste (ex: pytest com flask-socketio test client).  
- Documentar: cenários e como rodar.

---

## Fase 5 – Refinamento e Consolidação da Documentação

**Objetivo:** Garantir que toda a documentação esteja coesa, atualizada e que o sistema ofereça uma experiência de usuário polida.

### Tarefa 5.1 – Melhorias de Experiência
- Adicionar histórico de sessões e relatórios simples (temperatura ao longo do tempo, saltos de passo).  
- Possibilidade de salvar o layout do dashboard como padrão.  
- Notificações visuais para alertas (ex: temperatura fora da faixa).  
- Documentar essas melhorias no `docs/changelog.md`.

### Tarefa 5.2 – Revisão de Documentação Geral
- Verificar se todos os novos arquivos em `docs/` estão linkados em um índice `docs/README.md`.  
- Atualizar o `README.md` principal do repositório com a nova arquitetura, fluxo de uso e links para a documentação detalhada.  
- Adicionar diagrama de blocos (pode ser em texto ASCII) mostrando a interação entre plugins, plantas e dashboards.  
- Garantir que cada módulo/script tenha comentários de cabeçalho e documentação inline suficiente.

### Tarefa 5.3 – Testes de Aceitação
- Escrever um cenário de ponta a ponta (manual ou script de teste) que:
  1. Cadastra um sensor e um atuador no device manager.
  2. Cria uma planta com esses atores.
  3. Cria um dashboard com um display de sensor e um botão de atuador.
  4. Inicia uma sessão de mostura e verifica se os widgets reagem.
- Documentar o roteiro em `docs/e2e_test.md`.

