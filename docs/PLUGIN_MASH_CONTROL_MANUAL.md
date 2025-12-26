# Manual do Usuário - Plugin Mash Control

## Introdução

O **Mash Control** é um sistema completo de automação de processos de brassagem que permite controlar e monitorar seu brewhouse através de uma interface visual interativa. Com ele, você pode criar receitas, executá-las automaticamente e acompanhar todo o processo em tempo real.

## Primeiros Passos

### Pré-requisitos

Antes de usar o Mash Control, certifique-se de que:

1. O plugin **Device Manager** está instalado e ativo
2. Você tem dispositivos IoT cadastrados no Device Manager
3. Os dispositivos estão conectados e funcionando

### Acessando o Plugin

Após a instalação, o Mash Control aparece no menu lateral como **"Controle de Brassagem"** com os seguintes itens:

- **Dashboard** - Visão geral do brewhouse
- **Receitas** - Lista de receitas disponíveis
- **Nova Receita** - Criar nova receita
- **Sessões Ativas** - Monitorar sessões em execução
- **Histórico** - Ver histórico de sessões concluídas
- **Configurações** - Configurações do plugin

## Dashboard

O Dashboard é a tela principal do Mash Control, onde você visualiza seu brewhouse de forma interativa.

### Visualização

- **Área SVG**: Representação visual do seu equipamento
- **Painel Lateral**: Informações sobre sessão ativa, dispositivos e componentes disponíveis

### Funcionalidades

- **Visualizar Status**: Veja o status de todos os dispositivos em tempo real
- **Monitorar Temperaturas**: Acompanhe temperaturas atualizadas automaticamente
- **Controlar Sessão**: Pause, retome ou pare sessões ativas diretamente do dashboard

## Receitas

### Lista de Receitas

Na página de **Receitas**, você pode:

- Ver todas as receitas disponíveis
- Filtrar por origem (criadas ou importadas do BrewFather)
- Buscar receitas por nome
- Executar, editar ou remover receitas

### Criar Nova Receita

1. Clique em **"Nova Receita"** no menu ou no botão **"Nova Receita"** na lista
2. Preencha as informações básicas:
   - **Nome da Receita**: Nome descritivo
   - **Descrição**: Descrição opcional
3. Adicione etapas da receita:
   - Clique em **"Adicionar Etapa"**
   - Selecione o **Tipo** (Mostura, Fervura, Whirlpool, Resfriamento)
   - Defina **Nome**, **Temperatura Alvo** e **Duração**
   - Repita para cada etapa
4. Configure o mapeamento de equipamento (associe dispositivos às funções)
5. Clique em **"Salvar Receita"**

### Importar do BrewFather

1. Na página de **Receitas**, clique em **"Importar do BrewFather"**
2. Selecione a receita desejada da lista
3. Clique em **"Importar"**
4. A receita será convertida automaticamente para o formato Mash Control
5. Você pode editar a receita importada antes de executá-la

### Editar Receita

1. Na lista de receitas, clique em **"Editar"** na receita desejada
2. Faça as alterações necessárias
3. Clique em **"Salvar Receita"**

### Executar Receita

1. Na lista de receitas, clique em **"Executar"** na receita desejada
2. Configure o mapeamento de equipamento (se ainda não estiver configurado)
3. Confirme o início da sessão
4. A sessão será iniciada e você será redirecionado para o controle de sessão

## Sessões

### Controle de Sessão

A página de **Controle de Sessão** permite monitorar e controlar uma sessão em execução.

#### Informações da Sessão

- **Nome**: Nome da sessão
- **Status**: Status atual (pending/running/paused/completed/error)
- **Etapa Atual**: Etapa sendo executada no momento
- **Tempo de Início**: Quando a sessão foi iniciada

#### Progresso

Visualize o progresso da receita:
- Etapas concluídas
- Etapa atual em execução
- Etapas pendentes

#### Controles

- **Pausar**: Pausa temporariamente a execução
- **Retomar**: Retoma uma sessão pausada
- **Parar**: Finaliza a sessão completamente

#### Logs em Tempo Real

Acompanhe todos os eventos da sessão:
- Início e fim de etapas
- Alterações de temperatura
- Comandos enviados aos dispositivos
- Alarmes e erros

#### Controle Manual

Você pode controlar dispositivos manualmente durante a sessão:
- Ligar/desligar aquecedores
- Controlar bombas e válvulas
- Ler valores de sensores

### Histórico de Sessões

Na página de **Histórico**, você pode:

- Ver todas as sessões concluídas
- Filtrar por status (concluídas, erro, pausadas)
- Filtrar por data
- Ver detalhes de cada sessão
- Analisar gráficos de temperatura ao longo do tempo

## Configurações

A página de **Configurações** permite ajustar:

- Preferências do dashboard
- Configurações de alarmes
- Limites de segurança
- Outras configurações do plugin

## Dicas e Boas Práticas

### Antes de Iniciar uma Sessão

1. **Verifique os Dispositivos**: Certifique-se de que todos os dispositivos necessários estão online
2. **Configure o Mapeamento**: Associe corretamente os dispositivos às funções da receita
3. **Valide a Receita**: Use a validação automática para verificar se tudo está correto
4. **Teste Manualmente**: Teste os dispositivos manualmente antes de iniciar a automação

### Durante a Execução

1. **Monitore Regularmente**: Acompanhe os logs e valores em tempo real
2. **Esteja Preparado**: Tenha um plano para intervir manualmente se necessário
3. **Documente Problemas**: Anote qualquer problema ou comportamento inesperado

### Após a Execução

1. **Revise o Histórico**: Analise os dados da sessão para melhorias futuras
2. **Ajuste Receitas**: Use os dados coletados para refinar suas receitas
3. **Mantenha Dispositivos**: Certifique-se de que os dispositivos estão em bom estado

## Troubleshooting

### Sessão não inicia

- Verifique se todos os dispositivos necessários estão disponíveis
- Verifique se o mapeamento de equipamento está correto
- Consulte os logs para mensagens de erro específicas

### Temperatura não atinge o alvo

- Verifique se o aquecedor está funcionando corretamente
- Verifique se o sensor de temperatura está calibrado
- Ajuste a tolerância na receita se necessário

### Dispositivo não responde

- Verifique a conexão do dispositivo
- Verifique se o Device Manager está funcionando
- Consulte os logs do Device Manager

### Receita importada não funciona

- Verifique se todos os dispositivos necessários estão cadastrados
- Configure o mapeamento de equipamento manualmente
- Ajuste as etapas conforme necessário

## Suporte

Para mais informações técnicas, consulte:

- [Documentação Técnica](PLUGIN_MASH_CONTROL.md)
- [Referência da API](PLUGIN_MASH_CONTROL_API.md)
- [Device Manager Manual](PLUGIN_DEVICE_MANAGER_MANUAL.md)

