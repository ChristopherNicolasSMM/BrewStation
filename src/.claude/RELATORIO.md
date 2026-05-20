# Relatório de Progresso — Dashboard de Brassagem (CraftBeerPi 4 Style)

> Atualizado em: 2026-05-20
> Branch: main
> Objetivo: Implementar drag-and-drop de dispositivos + dashboard visual estilo CraftBeerPi 4

---

## Resumo Geral

**Progresso: ~90% concluído**

| Fase | Descrição | Status |
|------|-----------|--------|
| 1 | Arrastar dispositivo da lista para o canvas | ✅ Completo |
| 2 | Grid de fundo estilo CraftBeerPi | ✅ Completo |
| 3 | Indicadores visuais de estado nos elementos SVG | ✅ Completo |
| 4 | Animações CSS para atuadores | ✅ Completo |
| 5 | Click-to-toggle em modo visual | ✅ Completo |
| 6 | Configuração visual do elemento (modal melhorado) | ✅ Completo |
| 7 | Ajustes no backend | ✅ Completo |
| 8 | Melhorias de UX no toolbar | ✅ Completo |

---

## ✅ O Que Foi Implementado

### 1. Drag de Dispositivo para Canvas (dashboard.js)
- `MashDashboard.DEVICE_SVG_MAP` — mapeia tipo do ator/função para tipo de componente SVG
- `MashDashboard.DEVICE_COLOR_MAP` — cores padrão por tipo de dispositivo
- `getSvgTypeForDevice(device)` — resolve tipo SVG com fallback por nome
- `getColorForDevice(device)` — cor padrão com fallback
- `addDeviceToDashboard(deviceData, x, y)` — cria elemento já vinculado ao device
- `setupCanvasDropHandler()` — destaca canvas durante drag
- `_showToast()` — feedback visual (toast notifications)
- `_escapeJson()` — sanitiza JSON para dataset HTML
- `renderDevicesList()` — agora renderiza dispositivos com `draggable="true"`
- Drop handler modificado: tenta `application/json` (device) primeiro, depois `component-type` (biblioteca)

### 2. Grid de Fundo (styles.css + dashboard.js)
- CSS grid pattern 20px via `background-image` com linear-gradient
- Toggle via Ctrl+G ou botão `#grid-toggle-btn`
- Classe `.grid-enabled` no SVG
- Estado persiste em `this.gridEnabled`

### 3. Indicadores Visuais (svg-components.js + dashboard.js)
- **Status dot**: círculo no canto superior direito (verde=online, cinza=offline, vermelho=erro)
- **Label do dispositivo**: texto abaixo do SVG (`class="device-label"`)
- **Temperatura/valor**: texto centralizado (`data-temp-display="true"`, `class="temp-label"`)
- **Tooltip**: title com nome/status/valor
- **Classes active/inactive**: aplicadas dinamicamente pela telemetria
- **Fallback**: fallback SVG (`createFallback`) também inclui status dot + label + temp

### 4. Animações CSS (styles.css)
- `@keyframes spin` — bomba girando (`.pump.active .impeller`, 2s linear infinite)
- `@keyframes pulse-glow` — heater pulsando (`.heater.active`, 1.5s ease-in-out infinite)
- `@keyframes valve-open` — válvula abrindo (`.valve.active`, 0.5s ease)
- Transições: `.element-status-dot` (fill 0.3s), `.element-fill` (brightness/filter 0.3s)
- Classe `.active` → brightness 1.15
- Classe `.inactive` → brightness 0.7, saturate 0.5

### 5. Click-to-Toggle (dashboard.js)
- Em modo visual (não edição): clique em atuadores chama `toggleActuator()`
- Em modo edição: clique não aciona toggle (só seleção/drag)

### 6. Configuração Visual do Elemento (dashboard.html + dashboard.js)
- Modal `#elementConfigModal` reformulado para layout de duas colunas
- Color picker (`#element-config-color`) com preview em tempo real
- Label customizado (`#element-config-label`)
- Toggles show-temp / show-status
- Preview dinâmico (`#element-config-preview`) atualizado via `_updateConfigPreview()`
- `_updateSvgElementVisuals()` atualiza cor, label e indicadores no SVG após salvar

### 7. Ajustes no Backend
- `dashboard_builder.py` já preserva properties dict (incluindo campos visuais extras)
- Endpoint de telemetria já retorna `actor_type`, `status`, `value`

### 8. Melhorias no Toolbar (dashboard.html + dashboard.js)
- Botão grid toggle `#grid-toggle-btn`
- Indicador de zoom `#zoom-indicator` (percentual, auto-hide 3s)
- `updateZoomIndicator()` chamado em zoomIn, zoomOut, resetZoom

---

## 📋 O Que Falta / Pode Ser Melhorado

### 🔴 Pendentes (Não implementados)

| Item | Descrição | Arquivos | Esforço |
|------|-----------|----------|---------|
| **Auto-arrange** | Botão "Auto Arrange" que organiza elementos em grid | dashboard.js | Médio |
| **Snap-to-grid no drop** | Quando grid está ativo, elementos devem alinhar ao grid de 20px ao serem dropados | dashboard.js | Pequeno |
| **Indicador visual de "drop zone"** | Mostrar linha fantasma/overlay no local do drop | dashboard.js | Pequeno |

### 🟡 Melhorias (Implementados parcialmente)

| Item | Descrição | Motivo |
|------|-----------|--------|
| **Animações por tipo SVG** | As animações CSS dependem da estrutura interna de cada SVG. Funciona para pumps/heaters/valves padrão, mas SVGs customizados podem não ter os seletores `.impeller`, `[id*="heater"]` etc. | Variabilidade dos SVGs baixados |
| **Config de rotação** | Modal de config não tem campo para rotação do elemento | Não solicitado, mas comum em dashboards CBPI4 |
| **Persistência completa no DB** | `saveElementConfig()` salva no layout object em memória e chama `saveLayout()`, mas se o layout não tem ID (nunca foi salvo), só atualiza visual sem persistir vinculação de device | Requer salvar layout primeiro |
| **Testes do frontend** | Não há testes automatizados para o JS (`*.test.js`) | Projeto não tem setup de testes frontend |

### 🔵 Ideias para Futuro (Não escopo original)

| Item | Descrição |
|------|-----------|
| **WebSocket para telemetria** | Substituir polling de 2s por WebSocket para dados em tempo real |
| **Temas de cor** | Presets de cor para o dashboard (escuro, claro, CBPI4 classic) |
| **Exportar layout como imagem** | Botão para exportar o SVG como PNG |
| **Zoom com scroll do mouse (sem Ctrl)** | Zoom mais natural, igual Google Maps |
| **Múltiplas seleções** | Shift+click para selecionar vários elementos e mover em grupo |

---

## Arquivos Modificados

| Arquivo | Linhas (aprox) | Principais Mudanças |
|---------|----------------|---------------------|
| `static/js/dashboard.js` | ~1788 | Drag de dispositivos, grid toggle, zoom indicator, config visual, telemetria aprimorada, toast |
| `static/js/svg-components.js` | ~260 | Status dot, label, temp display, active/inactive, `_applyProperties()`, fallback aprimorado |
| `static/styles.css` | ~420 | Grid pattern, animações (spin/pulse/valve), transições, tooltips |
| `templates/mash_control/dashboard.html` | ~290 | Modal config 2 colunas, grid-btn, zoom-indicator |

---

## Como Continuar

Para retomar o trabalho, ler estes arquivos primeiro:

```bash
# Core JS
src/plugins/plugin_mash_control/static/js/dashboard.js
src/plugins/plugin_mash_control/static/js/svg-components.js

# CSS
src/plugins/plugin_mash_control/static/styles.css

# Template
src/plugins/plugin_mash_control/templates/mash_control/dashboard.html

# Plano original
.claude/PLANO.md

# Este relatório
.claude/RELATORIO.md
```

**Próxima tarefa recomendada:** Implementar snap-to-grid no drop de dispositivos + auto-arrange.
