# Importação Excel (Schema)

O Maker aceita importação de schema para criar tabelas/colunas.

## Formato recomendado (aba "schema")
Colunas:
- table_name
- column_name
- label
- data_type
- length
- required
- unique
- index
- default
- pk
- fk_table
- fk_column
- on_delete
- notes

## Fluxo
1) Upload
2) Parse e validação
3) Preview (tabelas/colunas detectadas)
4) Confirmar criação/merge

## Mapeamento de tipos
- VARCHAR/text → string/text
- INT → int
- DECIMAL → decimal (precision/scale)
- DATE → date
- DATETIME → datetime