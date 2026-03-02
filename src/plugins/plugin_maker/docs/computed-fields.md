# Campos Calculados

Campos calculados podem existir em 3 modos:

## Modes
1) ui: calculado no JS (melhor UX, não persistido)
2) api: calculado no backend no GET list/details
3) persisted: calculado no backend no POST/PUT e gravado em coluna

## Expressões seguras (sem eval)
A expressão pode usar:
- row.<field>
- cfg.<key>
- operadores: + - * / ( )
- funções: min, max, round, abs

Exemplos:
- round(row.price * row.qty, 2)
- row.prepared_date + cfg.expiry_work_days

## Dependências
Cada computed field registra deps_json:
- [ "price", "qty" ]

O Maker valida:
- tipos compatíveis
- ausência de ciclos (grafo acíclico)

## Eficiência
- ui: recalcular apenas quando dependências mudarem
- api: calcular em lote no backend
- persisted: recalcular apenas se dependências mudaram