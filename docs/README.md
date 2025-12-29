# Documentação do BrewStation

Bem-vindo à documentação completa do BrewStation! Este diretório contém todos os guias, manuais e referências técnicas do sistema.

## 📚 Guias Principais

### Para Usuários

- **[Manual do Usuário](MANUAL.md)** - Guia completo de uso do sistema
- **[Guia de Instalação](INSTALLATION.md)** - Instalação passo a passo
- **[Guia de Configuração](CONFIGURATION.md)** - Todas as configurações disponíveis
- **[Guia de Deploy](DEPLOYMENT.md)** - Deploy em produção
- **[Tema Escuro](DARK_THEME.md)** - Documentação de manutenção do tema escuro

### Para Desenvolvedores

- **[Arquitetura do Sistema](ARCHITECTURE.md)** - Estrutura técnica, componentes e fluxos
- **[Referência da API](API_REFERENCE.md)** - Documentação completa das rotas API
- **[Sistema de Plugins](PLUGIN_SYSTEM.md)** - Visão geral do sistema de plugins
- **[Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)** - Guia completo para criar plugins

## 🔌 Documentação de Plugins

### Device Manager

- **[Documentação Completa](PLUGIN_DEVICE_MANAGER.md)** - Visão geral, instalação, uso e exemplos
- **[Manual do Usuário](PLUGIN_DEVICE_MANAGER_MANUAL.md)** - Guia passo a passo para usuários finais
- **[Referência da API](PLUGIN_DEVICE_MANAGER_API.md)** - API pública para outros plugins

### Mash Control

- **[Documentação Completa](PLUGIN_MASH_CONTROL.md)** - Visão geral, instalação, uso e exemplos
- **[Manual do Usuário](PLUGIN_MASH_CONTROL_MANUAL.md)** - Guia passo a passo para usuários finais
- **[Referência da API](PLUGIN_MASH_CONTROL_API.md)** - API REST completa do plugin

### Sistema de Plugins

- **[Sistema de Plugins](PLUGIN_SYSTEM.md)** - Visão geral e conceitos
- **[Estrutura do install.json](PLUGIN_INSTALL_JSON.md)** - Referência do arquivo de configuração
- **[Configuração de Menu](PLUGIN_MENU_CONFIG.md)** - Como configurar menus de navegação
- **[Sistema de Rotas](PLUGIN_ROUTES_SYSTEM.md)** - Como criar rotas API e web
- **[Sistema de Banco de Dados](PLUGIN_DATABASE.md)** - Gerenciamento de modelos e tabelas
- **[Model Loader](PLUGIN_MODEL_LOADER.md)** - Como usar modelos prefixados corretamente
- **[Comandos CLI](PLUGIN_CLI.md)** - Comandos disponíveis para gerenciar plugins

## 📖 Índice por Tópico

### Instalação e Configuração

- [Guia de Instalação](INSTALLATION.md)
- [Guia de Configuração](CONFIGURATION.md)
- [Guia de Deploy](DEPLOYMENT.md)

### Uso do Sistema

- [Manual do Usuário](MANUAL.md)
- [Manual do Device Manager](PLUGIN_DEVICE_MANAGER_MANUAL.md)
- [Manual do Mash Control](PLUGIN_MASH_CONTROL_MANUAL.md)
- [Tema Escuro](DARK_THEME.md)

### Desenvolvimento

- [Arquitetura do Sistema](ARCHITECTURE.md)
- [Referência da API](API_REFERENCE.md)
- [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)

### Plugins

- [Sistema de Plugins](PLUGIN_SYSTEM.md)
- [Device Manager](PLUGIN_DEVICE_MANAGER.md)
- [Device Manager API](PLUGIN_DEVICE_MANAGER_API.md)
- [Mash Control](PLUGIN_MASH_CONTROL.md)
- [Mash Control API](PLUGIN_MASH_CONTROL_API.md)
- [Estrutura do install.json](PLUGIN_INSTALL_JSON.md)
- [Configuração de Menu](PLUGIN_MENU_CONFIG.md)
- [Sistema de Rotas](PLUGIN_ROUTES_SYSTEM.md)
- [Sistema de Banco de Dados](PLUGIN_DATABASE.md)
- [Model Loader](PLUGIN_MODEL_LOADER.md)
- [Comandos CLI](PLUGIN_CLI.md)

## 🚀 Início Rápido

### Para Usuários

1. Leia o [Manual do Usuário](MANUAL.md)
2. Configure o sistema seguindo o [Guia de Configuração](CONFIGURATION.md)
3. Para dispositivos IoT, consulte o [Manual do Device Manager](PLUGIN_DEVICE_MANAGER_MANUAL.md)

### Para Desenvolvedores

1. Leia a [Arquitetura do Sistema](ARCHITECTURE.md)
2. Consulte o [Guia de Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)
3. Use a [Referência da API](API_REFERENCE.md) para integrações

## 📝 Convenções

- **Código**: Exemplos de código são mostrados em blocos de código
- **Comandos**: Comandos CLI são prefixados com `$` ou `python run.py`
- **Rotas**: Rotas API são mostradas como `GET /api/endpoint`
- **Arquivos**: Caminhos de arquivos são mostrados como `src/path/to/file.py`

## 🔍 Busca Rápida

### Como fazer...

- **Instalar um plugin**: [Sistema de Plugins](PLUGIN_SYSTEM.md)
- **Criar um novo plugin**: [Desenvolvimento de Plugins](PLUGIN_DEVELOPMENT.md)
- **Configurar menu**: [Configuração de Menu](PLUGIN_MENU_CONFIG.md)
- **Usar modelos no plugin**: [Model Loader](PLUGIN_MODEL_LOADER.md)
- **Cadastrar dispositivo IoT**: [Manual do Device Manager](PLUGIN_DEVICE_MANAGER_MANUAL.md)
- **Usar API de dispositivos**: [Device Manager API](PLUGIN_DEVICE_MANAGER_API.md)
- **Automatizar brassagem**: [Manual do Mash Control](PLUGIN_MASH_CONTROL_MANUAL.md)
- **Usar API de controle de brassagem**: [Mash Control API](PLUGIN_MASH_CONTROL_API.md)
- **Configurar MQTT**: [Manual do Device Manager](PLUGIN_DEVICE_MANAGER_MANUAL.md#configurando-o-broker-mqtt)
- **Monitorar mensagens MQTT**: [Manual do Device Manager](PLUGIN_DEVICE_MANAGER_MANUAL.md#monitoramento-mqtt)
- **Personalizar tema escuro**: [Tema Escuro](DARK_THEME.md)

## 📞 Suporte

- **Documentação**: Consulte os guias acima
- **Logs**: Verifique `logs/brewstation.log` para erros
- **Issues**: Abra uma issue no repositório para bugs ou sugestões

---

**Última atualização**: Documentação atualizada para incluir sistema de tema escuro e Plugin Device Manager completo.
