# Plano Técnico — Starter, Contagem e Viabilidade

Este documento descreve a implementação técnica do módulo Starter & Contagem.

---

# 1. Novos Campos

## Cepa

Adicionar:

- daily_viability_loss_pct
- viability_correction_factor
- initial_viability_pct
- viability_model

---

## Item do Banco

Adicionar:

- estimated_viability_pct
- estimated_viability_updated_at
- last_viability_reference_type
- last_viability_reference_date
- last_viability_reference_value

---

# 2. Nova Tabela (opcional)

yeast_bank_cell_counts

Campos:

- id
- bank_item_id
- starter_id
- method
- dilution
- cells_total
- cells_viable
- viability_pct
- notes
- created_at

---

# 3. Endpoint de Recalculo

POST /api/yeast_bank/viability/recalculate

Processo:

for item in bank_items:
    reference = find_reference(item)
    days = today - reference.date
    viability_base = reference.viability - (days * strain.daily_loss)
    viability_final = viability_base * strain.correction_factor
    update item

---

# 4. Referência de Viabilidade

Prioridade:

1. última contagem válida
2. último starter concluído
3. valor inicial da cepa

---

# 5. Status do Starter

- planned
- running
- completed
- cancelled
- contaminated
- discarded

---

# 6. Status do Item do Banco

- ok
- in_use
- suspect
- contaminated
- discarded
- exhausted
- retired

---

# 7. Regras de Contaminação

Quando contaminação for detectada:

Sistema sugere:

- marcar starter contaminado
- marcar item contaminado
- descartar amostra
- colocar cepa em observação

Usuário confirma ação.

---

# 8. Atualização Automática

Viabilidade pode ser recalculada:

- manualmente
- cron job
- endpoint externo

---

# 9. Estrutura de UI

Nova área:

Starter & Contagem

Seções:

- Starter
- Contagem
- Histórico
- Ações laboratoriais

---

# 10. Roadmap

Etapa 1:
- parâmetros de viabilidade
- endpoint de recalculo

Etapa 2:
- contagem vinculada
- histórico

Etapa 3:
- contaminação
- descarte

Etapa 4:
- propagação avançada
