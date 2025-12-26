# Arquivos SVG do Plugin Mash Control

Esta pasta contém os arquivos SVG dos componentes visuais do dashboard.

## Arquivos Esperados

Os seguintes arquivos SVG devem ser colocados nesta pasta:

- `kettle.svg` - Panela/Caldeira
- `mash_tun.svg` - Tunel de Mostura
- `pump.svg` - Bomba
- `valve.svg` - Válvula
- `sensor.svg` - Sensor
- `heater.svg` - Aquecedor
- `chiller.svg` - Resfriador

## Especificações

### ViewBox e Tamanhos Recomendados

- **kettle**: viewBox="0 0 100 120" (width: 100, height: 120)
- **mash_tun**: viewBox="0 0 120 150" (width: 120, height: 150)
- **pump**: viewBox="0 0 60 60" (width: 60, height: 60)
- **valve**: viewBox="0 0 40 40" (width: 40, height: 40)
- **sensor**: viewBox="0 0 30 30" (width: 30, height: 30)
- **heater**: viewBox="0 0 50 50" (width: 50, height: 50)
- **chiller**: viewBox="0 0 50 50" (width: 50, height: 50)

### Classes CSS Importantes

Os SVGs podem usar as seguintes classes CSS para elementos dinâmicos:

- `.temperature-indicator` - Indicador de temperatura (texto)
- `.level-indicator` - Indicador de nível (linha)
- `.status-indicator` - Indicador de status (círculo)

### Propriedades Customizáveis

O sistema pode aplicar as seguintes propriedades aos SVGs:

- `fill_color` - Cor de preenchimento principal
- `show_temp` - Mostrar indicador de temperatura (kettle, mash_tun)
- `show_level` - Mostrar indicador de nível (kettle, mash_tun)
- `show_status` - Mostrar indicador de status (pump, valve, heater)

## Como Funciona

1. O sistema carrega os SVGs desta pasta via JavaScript
2. Os SVGs são posicionados dinamicamente no dashboard
3. Propriedades personalizadas são aplicadas aos elementos SVG
4. Indicadores dinâmicos (temperatura, status) são adicionados quando necessário
5. Se um SVG não for encontrado, um fallback simples é usado

## Exemplo de Estrutura SVG

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 120" width="100" height="120">
  <!-- Elementos do componente -->
  <text class="temperature-indicator">--°C</text>
</svg>
```

## Notas

- Os SVGs devem ser válidos e bem formados
- Use cores que contrastem bem com o fundo
- Mantenha os SVGs simples para melhor performance
- Teste os SVGs em diferentes tamanhos

