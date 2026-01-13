


# Backlog para o cursor

## 1
(Plan)

Analise o sistema BrewStation e como os plugin e ele se integram.


### 2
(Plan)
Agora elabore o planejamento para que o plugin plugin_device_manager tenha um Broker MQTT funcional onde possa ser enviado requisições de teste, cadastro de devices e etc. 
Tem de ter area ao cadastrar novo device para cadastrar função deste device, e caso a função não esteja cadastrada, deve permitir inserir nova. 
Crie um sistema de atores para os devices onde é possivel associar portas dos devices a atores de ação, sensores e regras de operação dentro dos demais plugins. 
Os devices serão utilizados posteriormente para controle de sensores e ações de liga e desliga dentro dos outros plugins. 
Deixe isso preparado. 

### 3
FAZER COMMIT ANTES

Faça agora um upgrade no sistema de plugin onde permite selecionar um plugin como dependencia e ao fazer a instalação deve ser verificado se o plugin e versão caso preenchida do plugin de dependencia esta no sistema, caso não esteja deve ser informado e abortado o processo e na mensagem deve fornecer a lista dos plugins de dependencia e se estão instalados ou não e caso istalado se estão ativos ou inativos, para seguir istalaçao todos os plugins de dependencia devem estar ativos. 


###

dentro da pasta C:\Users\christopher.mauricio\Desktop\Christopher Pessoal\Programação e Tecnologia\Python\BrewStation\src\plugins\plugin_device_manager\iot_mt_esp32 deve ser gerado um progeto em C++ para usar com platformio onde será  o codigo para ser enviado a quaser esp32 que deseje se conectar com o plugin de mtqq:

Para isso sera carregado um servidor wifi chamado "ND_BrewStation" abreviação de New Device Brew Station, onde após se socentar por wifi ou outro celular / dispositivo seja possível setar uma rede para este device se conectar, ip dinamico ou fixo e salvar estas configurações onde caso não encontre a rede ele inicia com a rede de configuração. Isso deve ser feito e salvo no device para permitir a conexão e que ele seja usado no projeto e plugin


---



### 4
... Penso e montar algo para ser possível atribuir calculos para os valores coletados das portas e depois em montar algo para ser possivel uma "programação por fluxograma" para facilitar usabilidade de não devs. 



---




# Backlog — BrewStation

## Visão geral
Backlog do sistema BrewStation: lista priorizada de features, histórias de usuário, bugs e tarefas técnicas para evolução do produto.
As receitas serão montadas sempre via BrewFather porém utilizando a API de integração conseguimos obter os dados da receita.
Com isso será feito a utilização destes dados para cadastrar insumos, obter perfil de equipamento, montar estoque.
---

## Roadmap / Milestones
- Milestone 1 — MVP: Controle básico de receitas e perfil de brassagem
- Milestone 2 — Automação: Integração com sensores criando ou utilizando hardware existente e monitoramento e controle de brassagem e fermentação com ispindel
- Milestone 3 — Analytics & Sharing: Gráficos, exportação e comunidade

---

## Prioridades
- P0 — Essencial para MVP
- P1 — Importante para experiência
- P2 — Nice-to-have

---

## Features (P0)
- [ ] Cadastro e autenticação de usuário
    - Critérios de aceitação:
        - Registro com email e senha
        - Login/logout funcional
        - Recuperação de senha por email
- [ ] CRUD de receitas de brassagem
    - Critérios de aceitação:
        - Criar, editar, apagar e ver receita
        - Campos: nome, descrição, ingredientes, etapas, tempo/temperatura
- [ ] Execução de batch (modo manual)
    - Critérios de aceitação:
        - Iniciar/pausar/parar execução
        - Mostrar etapa atual e temporizador

---

## Features (P1)
- [ ] Perfis de equipamentos (tanque, capacidade, elementos)
- [ ] Histórico de batches com notas e resultados
- [ ] Exportar/Importar receita (JSON/CSV)
- [ ] Permissões básicas (usuário vs admin)

---

## Features (P2)
- [ ] Integração com sensores (temperatura, fluxo)
- [ ] Controlador automático de temperatura (PID)
- [ ] Compartilhamento público de receitas
- [ ] Gráficos de performance e rendimento

---

## Histórias de usuário (exemplos)
- Como usuário, quero salvar uma receita para repeti-la futuramente. (P0)
- Como mestre de brassagem, quero um perfil de equipamento para ajustar tempos/temperaturas automaticamente. (P1)
- Como usuário avançado, quero que o sistema regule a temperatura automaticamente conforme etapas. (P2)

---

## Bugs / Correções
- [ ] Corrigir validação de campos no formulário de receita (P0)
- [ ] Resolver perda de sessão em navegadores específicos (P1)

---

## Tarefas técnicas / Infraestrutura
- [ ] Estruturar DB inicial e migrations (P0)
- [ ] Pipeline CI/CD básico e testes unitários (P0)
- [ ] Contêinerização (Docker) e docs de deploy (P1)
- [ ] Documentação de API (OpenAPI) (P1)

---

## Definição de Pronto (DoD)
- Código revisado e aprovado
- Testes unitários cobrindo funcionalidades críticas
- Documentação de uso mínima
- Deployado no ambiente de staging

---

## Notas
- Estimar tarefas em pontos de história na planning session.
- Priorizar features que reduzem esforço manual primeiro (MVP focado em workflow de brassagem).
