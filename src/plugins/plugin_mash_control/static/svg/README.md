# Componentes SVG do Dashboard de Brassagem

Esta pasta contém os arquivos SVG dos componentes visuais do dashboard e seus arquivos de configuração JSON.

## Como Funciona

O sistema descobre automaticamente todos os arquivos `.svg` nesta pasta e carrega suas configurações correspondentes dos arquivos `.json` com o mesmo nome.

## Estrutura de Arquivos

Para cada componente SVG, você precisa de dois arquivos:

1. **`nome_componente.svg`** - O arquivo SVG do componente
2. **`nome_componente.json`** - Arquivo de configuração JSON

### Exemplo: `sensor.svg` e `sensor.json`

## Formato do Arquivo JSON de Configuração

```json
{
  "name": "sensor",
  "label": "Sensor",
  "description": "Sensor de temperatura ou outro tipo",
  "default_width": 30,
  "default_height": 30,
  "category": "sensors",
  "icon": "bi bi-thermometer",
  "properties": {
    "show_value": true,
    "fill_color": "#F44336"
  }
}
```

### Campos do JSON

- **`name`** (string, obrigatório): Nome interno do componente (deve corresponder ao nome do arquivo SVG sem extensão)
- **`label`** (string, obrigatório): Nome exibido na biblioteca de componentes
- **`description`** (string, opcional): Descrição do componente
- **`default_width`** (number, obrigatório): Largura padrão em pixels
- **`default_height`** (number, obrigatório): Altura padrão em pixels
- **`category`** (string, opcional): Categoria do componente (ex: "sensors", "equipment", "valves")
- **`icon`** (string, opcional): Classe de ícone Bootstrap Icons (padrão: "bi bi-square")
- **`properties`** (object, opcional): Propriedades padrão do componente
  - **`show_value`** (boolean): Mostrar indicador de valor
  - **`show_temp`** (boolean): Mostrar indicador de temperatura
  - **`show_level`** (boolean): Mostrar indicador de nível
  - **`show_status`** (boolean): Mostrar indicador de status
  - **`fill_color`** (string): Cor de preenchimento padrão (formato hex)

## Como Adicionar um Novo Componente

1. **Crie o arquivo SVG** (`meu_componente.svg`):
   - Use um viewBox apropriado
   - Mantenha o SVG simples para melhor performance
   - Use classes CSS para elementos dinâmicos (ex: `.temperature-indicator`)

2. **Crie o arquivo JSON** (`meu_componente.json`):
   ```json
   {
     "name": "meu_componente",
     "label": "Meu Componente",
     "description": "Descrição do componente",
     "default_width": 50,
     "default_height": 50,
     "category": "equipment",
     "icon": "bi bi-circle",
     "properties": {
       "fill_color": "#4CAF50"
     }
   }
   ```

3. **Recarregue a página** do dashboard - o componente aparecerá automaticamente na biblioteca de componentes!

## Classes CSS Especiais nos SVGs

Você pode usar estas classes CSS nos seus SVGs para elementos dinâmicos:

- **`.temperature-indicator`** - Texto que será atualizado com valores de temperatura
- **`.level-indicator`** - Elemento visual que será atualizado com nível
- **`.status-indicator`** - Elemento visual que será atualizado com status
- **`.sensor-value`** - Texto que será atualizado com valores do sensor

## Exemplo de SVG com Indicador Dinâmico

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 30 30" width="30" height="30">
  <!-- Corpo do componente -->
  <circle cx="15" cy="15" r="13" fill="#F44336" stroke="#333" stroke-width="1"/>
  
  <!-- Indicador de valor (será atualizado dinamicamente) -->
  <text x="15" y="28" text-anchor="middle" font-size="8" fill="#fff" 
        font-weight="bold" class="sensor-value">--</text>
</svg>
```

## Funcionalidades do Dashboard

### Modo de Edição

1. Clique em **"Editar Layout"** para entrar no modo de edição
2. Arraste componentes da biblioteca lateral para o dashboard
3. Arraste elementos no dashboard para reposicioná-los
4. Clique em um elemento para selecioná-lo
5. Pressione **Delete** para remover um elemento selecionado
6. Clique em **"Salvar Layout"** para salvar as alterações

### Salvamento Automático

- O layout é salvo automaticamente quando você sai do modo de edição
- As posições são salvas quando você move elementos
- O layout é recarregado automaticamente ao abrir o dashboard

## Notas Importantes

- Os SVGs devem ser válidos e bem formados
- Use cores que contrastem bem com o fundo branco
- Mantenha os SVGs simples para melhor performance
- Teste os SVGs em diferentes tamanhos
- O sistema usa `preserveAspectRatio="xMidYMid meet"` para manter proporções
