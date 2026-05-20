# Plano: Drag-and-Drop de Dispositivos + Dashboard Estilo CraftBeerPi 4

> Status: ✅ **Implementado** (2026-05-20)

## Etapas

### 1. Arrastar dispositivo da lista para o canvas ✅
- `getSvgTypeForDevice()`, `getColorForDevice()` — mapas estáticos DEVICE_SVG_MAP e DEVICE_COLOR_MAP
- `renderDevicesList()` — draggable com `application/json` dataTransfer
- `setupCanvasDropHandler()` — destaca canvas durante drag
- `addDeviceToDashboard()` — cria elemento com device_id pré-vinculado
- Drop handler existente expandido para aceitar device drops com fallback

### 2. Grid de fundo estilo CraftBeerPi ✅
- CSS pattern 20px no SVG (`.grid-enabled`)
- Toggle Ctrl+G + botão `#grid-toggle-btn`
- `toggleGrid()` em dashboard.js

### 3. Indicadores visuais de estado nos elementos SVG ✅
- Status dot (green/grey/red) via `element-status-dot`
- Label do dispositivo abaixo do SVG (`device-label`)
- Temperatura centralizada (`temp-label` / `data-temp-display`)
- Active/inactive classes dinâmicas via telemetria
- Tooltip completo (nome, status, valor)

### 4. Animações CSS para atuadores ✅
- Bomba: `@keyframes spin` (`.pump.active .impeller`)
- Heater: `@keyframes pulse-glow` (`.heater.active`)
- Válvula: `@keyframes valve-open` (`.valve.active`)
- Transições suaves de cor/brilho

### 5. Click-to-toggle em modo visual ✅
- Atuadores clicáveis em modo visual chamam `toggleActuator()`
- Em modo edição o clique não aciona toggle

### 6. Configuração visual do elemento ✅
- Modal `#elementConfigModal` com 2 colunas: vinculo dispositivo + aparência
- Color picker com preview ao vivo (`_updateConfigPreview`)
- Label customizado, toggles show-temp/show-status
- `_updateSvgElementVisuals()` atualiza SVG sem recarregar

### 7. Ajustes no backend ✅
- `dashboard_builder.py` preserva properties dict
- Telemetria retorna `actor_type`, `status`, `value`

### 8. Melhorias de UX no toolbar ✅
- Grid toggle button + zoom indicator + auto-hide

## O Que NÃO Foi Feito (fora do escopo original)
- Auto-arrange (botão para organizar elementos em grid)
- Snap-to-grid no drop
- Testes frontend JS
- WebSocket para telemetria

## Arquivos modificados
- `static/js/dashboard.js`
- `static/js/svg-components.js`
- `static/styles.css`
- `templates/mash_control/dashboard.html`
