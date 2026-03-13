# 2. Backlog Geral e Roadmap

Abaixo estão definidos os itens de trabalho pendentes (Epic/Stories) focados na evolução contínua da BrewStation como plataforma de integração modular (Workstation).

## 📌 Epics em Andamento (WIP)

- **[Maker Engine] Aprimorar geração de Scaffoldings e MVC**
  - Consolidar rotas geradas pelo `maker_routes.py`.
  - Habilitar criação de GridViews (Listas Visuais) geradas via Web Interface.
- **[Device Manager] Estabilidade MQTT Backend**
  - Manter Threading do serviço rodando estavelmente dentro do Application Factory do Flask evitando recíclo do App Gunicorn.

## 🔜 Próximas Implementações

- **Automação Front-End de Componentes Vue.js/React (Standalone)**
  - O TemplateLoader atual carrega visões Jinja2. Como tornar a injeção do Manifest mais receptiva a SPAs empacotadas.
- **HookSystem (Event Dispatcher Público)**
  - Trocar o modelo em que o "Mash Control" depende do banco de dados do "Device Manager". Adicionar conceito de Hooks (um Singleton de disparo) no `PluginManager`. Ex: Quando "Mash" terminar uma etapa, dispara evento `BStation_MASH_STEP_COMPLETED` e os listeners reagem sem conhecer as tabelas subjacentes.

## ✅ Concluídos
- Auto prefixação de Modelos de SQLAlchemy Isolados.
- Integração básica e CLI funcional de Plugins (`List`, `Install`, `Activate`).
- Ocultamento de Rotas (`Blueprint injection`).
