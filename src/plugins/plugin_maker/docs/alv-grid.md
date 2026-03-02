# Grid estilo ALV (SAP-like)

Objetivo: oferecer listagens com recursos avançados:
- filtros, multi-sort
- agrupamento
- agregações (sum/count/avg/min/max)
- variantes (layout salvo)
- export respeitando layout

## MVP (realista)
- filtros e sort client-side
- agrupamento simples (1 coluna) client-side
- agregação básica (sum/count) no footer
- variantes armazenadas no Maker por usuário
- export CSV/JSON respeitando colunas visíveis e ordem

## V2 (avançado)
- multi-grouping
- agregação por grupo
- grid query server-side para grandes volumes
- freeze columns e reorder avançado

## Export
- export dados “flattened”
- opcional: incluir linhas de agregação no final