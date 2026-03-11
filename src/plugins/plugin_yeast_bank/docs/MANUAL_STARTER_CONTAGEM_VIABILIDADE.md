# YeastBank — Starter, Contagem de Levedura e Viabilidade

Este documento descreve o fluxo operacional do módulo **Starter & Contagem de Levedura** do YeastBank.

Este módulo conecta:

- Cepas
- Itens do banco (slants / placas / salina)
- Armazenamento
- Starters
- Contagem de células
- Viabilidade estimada
- Controle de contaminação

---

# 1. Estrutura Conceitual

## 1.1 Cepa
Representa a identidade genética da levedura.

Exemplos:
- US-05
- W34/70
- Conan
- Brett Brux

A cepa **não muda**.

Ela possui parâmetros biológicos como:
- taxa de mortalidade estimada
- fator de correção de viabilidade
- notas laboratoriais

---

## 1.2 Item do Banco
Representa uma **amostra física real**.

Exemplos:
- Slant mestre A
- Slant de trabalho
- Placa isolada
- Salina

Cada item possui:
- cepa associada
- data de preparo
- validade
- armazenamento
- status
- histórico
- viabilidade estimada

---

## 1.3 Armazenamento
Define onde a amostra está guardada.

Exemplo:

GEL-01 — Geladeira Casa 1  
FRZ-01 — Freezer Banco Principal

Campos:
- unidade de refrigeração
- slot / posição
- observação complementar

---

# 2. Starter

O **starter** é o processo de ativação ou propagação da levedura.

Fluxo:

Item do banco → Starter → Resultado

Campos principais:
- item do banco
- brewday
- início do starter
- volume alvo
- status
- notas

Status possíveis:

- Planejado
- Em andamento
- Concluído
- Cancelado
- Contaminado
- Descartado

---

# 3. Contagem de Levedura

A contagem permite medir:

- células/mL
- viabilidade
- total de células

Pode ser feita em:
- item do banco
- starter
- propagação

Dados registrados:
- método de contagem
- diluição
- contagem de células
- células vivas
- células mortas
- viabilidade %

---

# 4. Viabilidade Estimada

O sistema calcula automaticamente uma **viabilidade estimada** baseada em:

- último starter válido
- última contagem
- parâmetros da cepa
- tempo decorrido

Fórmula conceitual:

viabilidade_base = referencia - (dias * perda_diaria)  
viabilidade_final = viabilidade_base * fator_correcao_cepa

Exemplo:

referência: 96%  
perda diária: 0,30%  
dias: 30  

96 - (30 × 0,30) = 87%  

fator correção: 0,95  

87 × 0,95 = 82,65%

---

# 5. Recalcular Viabilidade

Endpoint:

POST /api/yeast_bank/viability/recalculate

Processo:
1. encontra referência
2. calcula dias
3. aplica perda diária
4. aplica fator de correção
5. atualiza item

---

# 6. Contaminação

Durante contagem ou starter pode ser detectada contaminação.

O sistema permite:
- marcar starter como contaminado
- marcar item do banco como contaminado
- descartar amostra
- colocar cepa em observação

Status possíveis do item:

- OK
- Em uso
- Suspeito
- Contaminado
- Descartado
- Esgotado

---

# 7. Histórico

Cada item possui histórico:

- starter iniciado
- starter concluído
- contagem registrada
- viabilidade recalculada
- contaminação detectada
- descarte

---

# 8. Fluxo operacional

Cepa → Item do banco → Armazenamento → Starter → Contagem → Atualização de viabilidade → Decisão operacional
