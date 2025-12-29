# Manual do Usuário — BrewStation

Este manual foi elaborado para orientar brassagens artesanais que utilizam o BrewStation para precificação, controle de estoque, envase e integrações com o BrewFather.

## 1. Acesso e Autenticação

- URL local padrão: `http://localhost:5000`
- Usuário inicial: `admin`
- Senha inicial: `admin123` (altere em `Perfil > Segurança` após o primeiro login).
- O fluxo público de cadastro coleta os dados em `/register/request` e depende da aprovação de um administrador.

## 2. Primeiros Passos

1. **Configurações básicas** — acesse `Configurações > Sistema` e defina chave secreta, diretórios de upload e limites de tamanho.
2. **Integração BrewFather** — informe `BREWFATHER_USER_ID` e `BREWFATHER_API_KEY` para liberar as rotas de sincronização.
3. **E-mail transacional** — configure host, porta, usuário e senha SMTP para habilitar notificações por e-mail.
4. **Parâmetros financeiros** — ajuste percentuais de margem, impostos e cartório no módulo de cálculos.

## 3. Painel Principal

O `Dashboard` resume:

- alertas recentes,
- sessões de brassagem em andamento,
- status do BrewFather e do e-mail,
- atalhos para módulos críticos (estoque, envase, cálculos e notificações).

## 4. Módulo de Configurações

- **Sistema**: parâmetros gerais, chaves secretas, diretórios e flags de depuração.
- **Integrações**: credenciais do BrewFather e cadência de sincronização.
- **E-mail**: servidor SMTP, porta, uso de TLS e remetente padrão.
- **Testes**: use `Testar Configurações` para validar banco, BrewFather e SMTP.

## 5. Ingredientes & Catálogo

### Cadastro manual
- `Ingredientes > Maltes/Lúpulos/Leveduras` permitem CRUD completo com status “ativo”.

### Importação em lote
- Utilize `Upload > Modelo` para baixar as planilhas base.
- Preencha os templates (`.xlsx`) e envie em `Upload > Importar`.
- O sistema valida colunas obrigatórias antes de persistir os registros.

## 6. Receitas e Cálculos

1. Crie ou importe receitas (`Receitas > Nova Receita` ou sincronização BrewFather).
2. Associe ingredientes e parâmetros de brassagem.
3. Em `Cálculos`, defina volume, embalagem, custos indiretos e margens.
4. Gere relatórios de precificação (margem esperada, valor por litro, sugestão de preço final).

## 7. Integração BrewFather

- **Sincronização manual**: `BrewFather > Sincronizar` para receitas, lotes, inventário ou tudo de uma vez.
- **Cadastro automático de insumos**: selecione uma receita e use `Cadastrar Insumos` para preencher o catálogo local com itens faltantes.
- **Relatórios**: filtre lotes por status, intervalo de datas e exporte para Excel com métricas de OG, FG, ABV, IBU e eficiência.

## 8. Estoque e Movimentações

- `Estoque > Movimentações`: registre entradas, saídas e ajustes com custo unitário, lote e validade.
- `Estoque > Atual`: visualize quantidades por ingrediente, status (crítico/baixo/ok) e valor total.
- `Relatórios`: obtenha resumos financeiros, alertas por estoque mínimo e custo médio por ingrediente.

## 9. Envase

- Cadastre embalagens (garrafas, latas, growlers) com volume, custo e SKU.
- Registre sessões de envase vinculadas a um lote do BrewFather, definindo quantidade produzida por tipo de embalagem.
- Acompanhe o custo de envase integrado ao módulo de custo de produção.

## 10. Uploads e Relatórios

- Uploads aceitam `.xlsx` e utilizam `pandas`/`openpyxl` para leitura.
- Exporte catálogos e relatórios (`Ingredientes`, `BrewFather`, `Estoque`) diretamente do front-end.

## 11. Notificações e Perfil

- Notificações podem ser criadas via API (`/api/notifications`) ou automaticamente pelo sistema.
- Filtros disponíveis: todas, não lidas, lidas e lixeira.
- O perfil do usuário contempla dados pessoais, redes sociais, preferências de notificação e alteração de senha.

### 11.1. Personalização de Tema

O BrewStation oferece suporte a tema escuro para melhorar a experiência visual:

- **Ativar/Desativar Tema Escuro**: Acesse `Perfil > Configurações` e ative o switch "Modo escuro"
- A preferência é salva automaticamente e aplicada em todas as páginas
- O tema é aplicado imediatamente sem necessidade de recarregar a página
- A preferência é mantida entre sessões

Para mais detalhes técnicos sobre manutenção e extensão do tema escuro, consulte a [Documentação de Tema Escuro](DARK_THEME.md).

## 12. Rotinas Sugeridas

| Frequência | Rotina | Responsável |
|------------|--------|-------------|
| Diário     | Registrar brassagens, sincronizar BrewFather, revisar alertas | Mestre cervejeiro |
| Semanal    | Atualizar estoque, conferir custos de produção | Operações |
| Mensal     | Revisar margens, exportar relatórios financeiros, ajustar preços | Financeiro |
| Ad hoc     | Importar novos ingredientes, atender solicitações de acesso | Administração |

## 13. Solução de Problemas

| Sintoma | Possível causa | Ação sugerida |
|---------|----------------|---------------|
| Erro ao logar | Credenciais incorretas ou usuário inativo | Validar em `users` via admin ou resetar senha |
| Sincronização BrewFather falha | API Key inválida ou rate limit | Atualizar credenciais e aguardar 60s antes de nova tentativa |
| Upload rejeitado | Colunas ausentes ou tipos numéricos inválidos | Regerar planilha usando o modelo oficial |
| E-mails não enviados | SMTP/TLS incorretos | Reexecutar `Testar Configurações` e revisar porta/credenciais |

---
Para dúvidas adicionais, registre uma issue no repositório ou contate o administrador listado no módulo de configurações.

