# YeastBank — Manual de Armazenamento

## O que foi adicionado

Nova área **Armazenamento** para cadastrar e monitorar:
- freezers
- geladeiras
- frigobares
- câmaras frias
- incubadoras
- outros dispositivos de refrigeração

## Funcionalidades

### 1. Cadastro de equipamentos
Menu: **YeastBank > Armazenamento**

Campos principais:
- nome
- tipo
- status
- ativo/inativo
- temperatura alvo
- faixa mínima e máxima
- endereço físico
- endereço virtual
- marca / modelo / serial
- descrição

### 2. Leituras de temperatura
Na própria tela de armazenamento é possível lançar:
- temperatura em °C
- data/hora
- umidade (opcional)
- origem da leitura
- observações

Cada leitura atualiza automaticamente:
- temperatura atual do equipamento
- data/hora da última leitura

### 3. Associação com itens do banco
Na tela **Banco (Slants / Placas / Salina)**, cada item agora pode ter:
- equipamento de armazenamento
- posição / slot
- localização complementar

### 4. Dashboard
O dashboard do YeastBank agora possui uma seção **Armazenamento** com:
- cards dos equipamentos
- status
- temperatura atual
- faixa alvo
- últimas temperaturas

## API disponível

### Listar equipamentos
`GET /api/yeast_bank/storage/devices`

### Criar equipamento
`POST /api/yeast_bank/storage/devices`

### Editar equipamento
`PUT /api/yeast_bank/storage/devices/<id>`

### Inativar equipamento
`DELETE /api/yeast_bank/storage/devices/<id>`

### Listar leituras de um equipamento
`GET /api/yeast_bank/storage/devices/<id>/readings?limit=30`

### Registrar leitura
`POST /api/yeast_bank/storage/readings`

Payload exemplo:

```json
{
  "device_id": 1,
  "temperature_c": -18.5,
  "recorded_at": "2026-03-09T14:30:00",
  "humidity_percent": 52.1,
  "source_type": "api",
  "source_ref": "sensor-freezer-01",
  "notes": "Leitura automática"
}
```

## Observações técnicas
- O plugin mantém compatibilidade com o campo legado `location` do item.
- Novas colunas adicionadas ao item do banco:
  - `storage_device_id`
  - `storage_slot`
- Novas tabelas:
  - `yeast_storage_device`
  - `yeast_storage_reading`

## Próximos passos sugeridos
- autenticação própria para sensores/API externa
- alertas por temperatura fora da faixa
- exportação CSV/JSON de leituras
- gráficos avançados por período
