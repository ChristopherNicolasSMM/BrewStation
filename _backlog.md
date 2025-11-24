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
