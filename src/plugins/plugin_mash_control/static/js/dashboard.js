/**
 * JavaScript para o dashboard de brassagem com drag-and-drop.
 */

class MashDashboard {
    constructor() {
        this.svg = null;
        this.svgContainer = null;
        this.svgWrapper = null;
        this.layout = null;
        this.devices = [];
        this.activeSession = null;
        this.updateInterval = null;
        this.components = [];
        this.isEditMode = false;
        this.selectedElement = null;
        this.draggedElement = null;
        this.dragOffset = { x: 0, y: 0 };
        this.zoomLevel = 1;
        this.gridEnabled = false;
        this.panX = 0;
        this.panY = 0;
        this.baseWidth = null;  // Será calculado dinamicamente
        this.baseHeight = null; // Será calculado dinamicamente
    }
    
    init() {
        this.svg = document.getElementById('dashboard-svg');
        this.svgContainer = document.getElementById('dashboard-svg-container');
        this.svgWrapper = document.getElementById('svg-wrapper');
        if (!this.svg || !this.svgContainer || !this.svgWrapper) return;
        
        // Carregar componentes primeiro, depois layout (para evitar condição de corrida)
        this.loadComponents().then(() => {
            // Após componentes carregados, carregar layout
            this.loadLayout();
        });
        
        this.loadDevices();
        this.loadActiveSession();
        this.setupEventListeners();
        this.setupZoomControls();
        this.setupCollapseIcons();
        this.setupCanvasDropHandler();
        
        
        // Calcular tamanho base e inicializar zoom após um pequeno delay
        setTimeout(() => {
            this.calculateBaseSize();
            this.applyZoom();
        }, 100);
        
        // Atualizar a cada 2 segundos
        this.updateInterval = setInterval(() => {
            if (!this.isEditMode) {
                this.updateDashboard();
            }
        }, 2000);
        
    }
    
    setupCollapseIcons() {
        // Atualizar ícones de collapse quando os elementos são expandidos/colapsados
        document.querySelectorAll('[data-bs-toggle="collapse"]').forEach(trigger => {
            trigger.addEventListener('shown.bs.collapse', (e) => {
                const icon = trigger.querySelector('.collapse-icon');
                if (icon) {
                    icon.classList.remove('bi-chevron-down');
                    icon.classList.add('bi-chevron-up');
                }
            });
            
            trigger.addEventListener('hidden.bs.collapse', (e) => {
                const icon = trigger.querySelector('.collapse-icon');
                if (icon) {
                    icon.classList.remove('bi-chevron-up');
                    icon.classList.add('bi-chevron-down');
                }
            });
        });
    }
    
    setupZoomControls() {
        const zoomInBtn = document.getElementById('zoom-in-btn');
        const zoomOutBtn = document.getElementById('zoom-out-btn');
        const zoomResetBtn = document.getElementById('zoom-reset-btn');
        const gridToggleBtn = document.getElementById('grid-toggle-btn');

        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.zoomIn());
        }

        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.zoomOut());
        }

        if (zoomResetBtn) {
            zoomResetBtn.addEventListener('click', () => this.resetZoom());
        }

        if (gridToggleBtn) {
            gridToggleBtn.addEventListener('click', () => this.toggleGrid());
        }

        // Zoom com scroll do mouse (Ctrl+Scroll ou Cmd+Scroll)
        if (this.svgWrapper) {
            this.svgWrapper.addEventListener('wheel', (e) => {
                if (e.ctrlKey || e.metaKey) {
                    e.preventDefault();
                    const delta = e.deltaY > 0 ? 0.9 : 1.1;
                    this.zoomLevel *= delta;
                    this.zoomLevel = Math.max(0.25, Math.min(3, this.zoomLevel));
                    this.applyZoom();
                }
            });
        }

        // Atalho de teclado: Ctrl+G para grid
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'g') {
                e.preventDefault();
                this.toggleGrid();
            }
        });
    }
    
    calculateBaseSize() {
        if (!this.svgWrapper) return;
        
        // Usar o tamanho do wrapper como base (sem scrollbars)
        this.baseWidth = this.svgWrapper.clientWidth;
        this.baseHeight = this.svgWrapper.clientHeight;
        
        // Definir tamanho inicial do SVG igual ao wrapper
        if (this.svg) {
            this.svg.setAttribute('width', this.baseWidth);
            this.svg.setAttribute('height', this.baseHeight);
            this.svg.style.width = this.baseWidth + 'px';
            this.svg.style.height = this.baseHeight + 'px';
        }
    }
    
    toggleGrid() {
        this.gridEnabled = !this.gridEnabled;
        const svg = document.getElementById('dashboard-svg');
        if (svg) {
            svg.classList.toggle('grid-enabled', this.gridEnabled);
        }
        // Feedback no botão
        const btn = document.getElementById('grid-toggle-btn');
        if (btn) {
            btn.classList.toggle('btn-primary', this.gridEnabled);
            btn.classList.toggle('btn-light', !this.gridEnabled);
            btn.title = this.gridEnabled ? 'Ocultar Grid (Ctrl+G)' : 'Mostrar Grid (Ctrl+G)';
        }
    }

    updateZoomIndicator() {
        const indicator = document.getElementById('zoom-indicator');
        if (indicator) {
            const pct = Math.round(this.zoomLevel * 100);
            indicator.textContent = `${pct}%`;
            indicator.style.display = 'block';
            // Auto-hide após 3s
            clearTimeout(this._zoomIndicatorTimer);
            this._zoomIndicatorTimer = setTimeout(() => {
                indicator.style.display = 'none';
            }, 3000);
        }
    }

    zoomIn() {
        this.zoomLevel = Math.min(3, this.zoomLevel * 1.2);
        this.applyZoom();
        this.updateZoomIndicator();
    }

    zoomOut() {
        this.zoomLevel = Math.max(0.25, this.zoomLevel / 1.2);
        this.applyZoom();
        this.updateZoomIndicator();
    }

    resetZoom() {
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
        this.updateZoomIndicator();

        // Recalcular tamanho base se necessário
        if (!this.baseWidth || !this.baseHeight) {
            this.calculateBaseSize();
        }
        
        this.applyZoom();
        
        // Resetar scroll para o topo esquerdo
        if (this.svgWrapper) {
            setTimeout(() => {
                this.svgWrapper.scrollLeft = 0;
                this.svgWrapper.scrollTop = 0;
            }, 50);
        }
    }
    
    applyZoom() {
        if (!this.svg || !this.baseWidth || !this.baseHeight) {
            // Se ainda não calculou o tamanho base, calcular agora
            if (!this.baseWidth || !this.baseHeight) {
                this.calculateBaseSize();
            }
            if (!this.baseWidth || !this.baseHeight) return;
        }
        
        // Aplicar zoom mantendo a posição atual do scroll
        const currentScrollLeft = this.svgWrapper.scrollLeft;
        const currentScrollTop = this.svgWrapper.scrollTop;
        
        // Calcular novo tamanho baseado no zoom
        const newWidth = this.baseWidth * this.zoomLevel;
        const newHeight = this.baseHeight * this.zoomLevel;
        
        this.svg.setAttribute('width', newWidth);
        this.svg.setAttribute('height', newHeight);
        this.svg.style.width = newWidth + 'px';
        this.svg.style.height = newHeight + 'px';
        
        // Ajustar scroll para manter posição relativa
        const scrollRatioX = currentScrollLeft / (this.svgWrapper.scrollWidth - this.svgWrapper.clientWidth || 1);
        const scrollRatioY = currentScrollTop / (this.svgWrapper.scrollHeight - this.svgWrapper.clientHeight || 1);
        
        setTimeout(() => {
            const newScrollLeft = scrollRatioX * (this.svgWrapper.scrollWidth - this.svgWrapper.clientWidth);
            const newScrollTop = scrollRatioY * (this.svgWrapper.scrollHeight - this.svgWrapper.clientHeight);
            this.svgWrapper.scrollLeft = newScrollLeft;
            this.svgWrapper.scrollTop = newScrollTop;
        }, 10);
    }
    
    async loadComponents() {
        try {
            const response = await fetch('/api/mash_control/dashboard/components');
            const components = await response.json();
            
            this.components = components;
            this.renderComponentsLibrary();
        } catch (error) {
            console.error('Erro ao carregar componentes:', error);
        }
    }
    
    async loadLayout() {
        try {
            const response = await fetch('/api/mash_control/dashboard/layout');
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data && !data.error) {
                // Normalizar dados do layout
                this.layout = {
                    id: data.id || null,
                    name: data.name || 'Novo Layout',
                    elements: data.elements || data.layout_data || [],
                    is_default: data.is_default !== false
                };
                
                console.log('Layout carregado:', this.layout);
                this.updateDashboardName();
                this.renderLayout();
            } else {
                // Criar layout vazio
                this.layout = {
                    id: null,
                    name: 'Novo Layout',
                    elements: [],
                    is_default: true
                };
                console.log('Nenhum layout encontrado, criando novo');
            }
        } catch (error) {
            console.error('Erro ao carregar layout:', error);
            // Criar layout vazio em caso de erro
            this.layout = {
                id: null,
                name: 'Novo Layout',
                elements: [],
                is_default: true
            };
        }
    }
    
    async loadDevices() {
        try {
            const response = await fetch('/api/mash_control/dashboard/devices');
            const devices = await response.json();
            
            this.devices = devices;
            this.renderDevicesList();
        } catch (error) {
            console.error('Erro ao carregar dispositivos:', error);
        }
    }
    
    async loadActiveSession() {
        try {
            const response = await fetch('/api/mash_control/sessions?status=running');
            const sessions = await response.json();
            
            if (sessions && sessions.length > 0) {
                this.activeSession = sessions[0];
            } else {
                this.activeSession = null;
            }
            
            this.renderActiveSession();
        } catch (error) {
            console.error('Erro ao carregar sessão ativa:', error);
            this.activeSession = null;
            this.renderActiveSession();
        }
    }
    
    renderComponentsLibrary() {
        const container = document.getElementById('components-library');
        if (!container) return;
        
        if (this.components.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhum componente disponível</p>';
            return;
        }
        
        // Ordenar componentes alfabeticamente por label
        const sortedComponents = [...this.components].sort((a, b) => {
            const labelA = (a.label || a.name || '').toLowerCase();
            const labelB = (b.label || b.name || '').toLowerCase();
            return labelA.localeCompare(labelB, 'pt-BR');
        });
        
        const svgBasePath = '/plugin/mash_control/static/mash_control/svg/';
        
        container.innerHTML = sortedComponents.map(component => {
            const svgPath = `${svgBasePath}${component.type}.svg`;
            console.log(`Gerando item para componente ${component.type} com SVG ${svgPath}`);
            const iconFallback = component.icon || 'bi bi-square';
            return `
            <div class="component-item border rounded" 
                 draggable="true" 
                 data-component-type="${component.type}"
                 style="cursor: grab; user-select: none;">
                <div class="d-flex align-items-center">
                    <div class="component-icon-wrapper me-2" style="width: 32px; height: 32px; flex-shrink: 0; display: flex; align-items: center; justify-content: center;">
                        <img src="${svgPath}" 
                             alt="${component.label}" 
                             class="component-icon" 
                             style="max-width: 100%; max-height: 100%; object-fit: contain;"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='inline-block';">
                        <i class="${iconFallback}" style="display: none; font-size: 20px; color: #6c757d;"></i>
                    </div>
                    <div class="flex-grow-1" style="min-width: 0;">
                        <strong class="d-block text-truncate">${component.label}</strong>
                        <small class="text-muted text-truncate d-block">${component.description || component.name}</small>
                    </div>
                </div>
            </div>
        `;
        }).join('');
        
        // Adicionar event listeners para drag
        container.querySelectorAll('.component-item').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                e.dataTransfer.effectAllowed = 'copy';
                e.dataTransfer.setData('component-type', item.dataset.componentType);
                item.style.opacity = '0.5';
            });
            
            item.addEventListener('dragend', (e) => {
                item.style.opacity = '1';
            });
        });
    }
    
    async renderLayout() {
        if (!this.layout) {
            console.log('Layout não disponível para renderização');
            return;
        }
        
        // Verificar se SVG está pronto
        if (!this.svg) {
            console.log('SVG não está pronto, aguardando...');
            setTimeout(() => {
                this.renderLayout();
            }, 100);
            return;
        }
        
        // Verificar se componentes estão carregados
        if (!this.components || this.components.length === 0) {
            console.log('Aguardando componentes serem carregados antes de renderizar layout...');
            // Aguardar um pouco e tentar novamente
            setTimeout(() => {
                this.renderLayout();
            }, 200);
            return;
        }
        
        // Limpar SVG
        this.svg.innerHTML = '';
        
        const elements = this.layout.elements || this.layout.layout_data || [];
        
        if (elements.length === 0) {
            console.log('Nenhum elemento para renderizar no layout');
            return;
        }
        
        console.log(`Renderizando ${elements.length} elementos do layout`);
        
        // Carregar elementos SVG de forma assíncrona
        for (const element of elements) {
            await this.addElementToSVG(element);
        }
        
        // Adicionar event listeners para drag dos elementos existentes
        this.setupElementDragListeners();
    }
    
    async addElementToSVG(element) {
        if (!this.svg || !window.SVGComponents) return;
        
        const component = this.components.find(c => c.type === element.type);
        if (!component) {
            console.warn(`Componente ${element.type} não encontrado`);
            return;
        }
        
        const width = element.width || component.default_size.width;
        const height = element.height || component.default_size.height;
        const x = element.x || 0;
        const y = element.y || 0;
        
        try {
            const svgElement = await SVGComponents.loadSVG(
                element.type,
                x,
                y,
                width,
                height,
                element.properties || component.properties || {}
            );
            
            if (svgElement) {
                svgElement.setAttribute('data-element-id', element.id);
                svgElement.setAttribute('data-device-id', element.device_id || '');
                svgElement.setAttribute('data-component-type', element.type);
                svgElement.classList.add('dashboard-svg-element');
                
                // Adicionar indicador de seleção
                if (this.isEditMode) {
                    svgElement.style.cursor = 'move';
                }
                
                this.svg.appendChild(svgElement);
            }
        } catch (error) {
            console.error(`Erro ao adicionar elemento ${element.type} ao SVG:`, error);
        }
    }
    
    setupElementDragListeners() {
        const elements = this.svg.querySelectorAll('.dashboard-svg-element');
        
        elements.forEach(element => {
            // Remover listeners antigos
            const newElement = element.cloneNode(true);
            element.parentNode.replaceChild(newElement, element);
            
            if (this.isEditMode) {
                newElement.addEventListener('mousedown', (e) => {
                    if (e.button === 0) { // Botão esquerdo
                        this.startElementDrag(newElement, e);
                    }
                });
                
                newElement.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.selectElement(newElement);
                });
            }
        });
    }
    
    startElementDrag(element, e) {
        this.draggedElement = element;
        const rect = this.svg.getBoundingClientRect();
        
        // Obter transform atual
        const transform = element.getAttribute('transform') || '';
        const translateMatch = transform.match(/translate\(([^,]+),\s*([^)]+)\)/);
        let currentX = translateMatch ? parseFloat(translateMatch[1]) : 0;
        let currentY = translateMatch ? parseFloat(translateMatch[2]) : 0;
        
        // Considerar zoom e scroll ao calcular offset
        const scrollLeft = this.svgWrapper ? this.svgWrapper.scrollLeft : 0;
        const scrollTop = this.svgWrapper ? this.svgWrapper.scrollTop : 0;
        const mouseX = (e.clientX - rect.left + scrollLeft) / this.zoomLevel;
        const mouseY = (e.clientY - rect.top + scrollTop) / this.zoomLevel;
        
        this.dragOffset = {
            x: mouseX - currentX,
            y: mouseY - currentY
        };
        
        element.style.cursor = 'grabbing';
        
        document.addEventListener('mousemove', this.handleElementDrag.bind(this));
        document.addEventListener('mouseup', this.stopElementDrag.bind(this));
    }
    
    handleElementDrag(e) {
        if (!this.draggedElement) return;
        
        const rect = this.svg.getBoundingClientRect();
        const scrollLeft = this.svgWrapper ? this.svgWrapper.scrollLeft : 0;
        const scrollTop = this.svgWrapper ? this.svgWrapper.scrollTop : 0;
        
        // Considerar zoom e scroll ao calcular posição
        const mouseX = (e.clientX - rect.left + scrollLeft) / this.zoomLevel;
        const mouseY = (e.clientY - rect.top + scrollTop) / this.zoomLevel;
        const x = mouseX - this.dragOffset.x;
        const y = mouseY - this.dragOffset.y;
        
        // Limitar dentro do SVG (usando tamanho atual do SVG)
        const svgWidth = parseFloat(this.svg.getAttribute('width')) || this.baseWidth || this.svg.clientWidth;
        const svgHeight = parseFloat(this.svg.getAttribute('height')) || this.baseHeight || this.svg.clientHeight;
        const maxX = Math.max(0, svgWidth - 50);
        const maxY = Math.max(0, svgHeight - 50);
        const constrainedX = Math.max(0, Math.min(x, maxX));
        const constrainedY = Math.max(0, Math.min(y, maxY));
        
        this.draggedElement.setAttribute('transform', `translate(${constrainedX}, ${constrainedY})`);
    }
    
    stopElementDrag(e) {
        if (!this.draggedElement) return;
        
        this.draggedElement.style.cursor = 'move';
        
        // Salvar posição
        const transform = this.draggedElement.getAttribute('transform') || '';
        const translateMatch = transform.match(/translate\(([^,]+),\s*([^)]+)\)/);
        if (translateMatch) {
            const x = parseFloat(translateMatch[1]);
            const y = parseFloat(translateMatch[2]);
            const elementId = this.draggedElement.getAttribute('data-element-id');
            
            this.updateElementPosition(elementId, x, y);
        }
        
        this.draggedElement = null;
        document.removeEventListener('mousemove', this.handleElementDrag.bind(this));
        document.removeEventListener('mouseup', this.stopElementDrag.bind(this));
    }
    
    selectElement(element) {
        // Remover seleção anterior
        this.svg.querySelectorAll('.dashboard-svg-element').forEach(el => {
            el.classList.remove('selected');
        });
        
        // Selecionar novo elemento
        element.classList.add('selected');
        this.selectedElement = element;
    }
    
    async updateElementPosition(elementId, x, y) {
        if (!this.layout) return;
        
        const elements = this.layout.elements || this.layout.layout_data || [];
        const element = elements.find(el => el.id === elementId);
        
        if (element) {
            element.x = x;
            element.y = y;
            
            // Salvar layout
            await this.saveLayout();
        }
    }
    
    renderDevicesList() {
        const container = document.getElementById('devices-list');
        if (!container) return;

        if (this.devices.length === 0) {
            container.innerHTML = '<p class="text-muted mb-0">Nenhum dispositivo disponível</p>';
            return;
        }

        // Ordenar dispositivos alfabeticamente
        const sortedDevices = [...this.devices].sort((a, b) => {
            const nameA = (a.name || '').toLowerCase();
            const nameB = (b.name || '').toLowerCase();
            return nameA.localeCompare(nameB, 'pt-BR');
        });

        container.innerHTML = sortedDevices.map(device => {
            const svgType = MashDashboard.getSvgTypeForDevice(device);
            return `
            <div class="device-item border rounded"
                 draggable="true"
                 data-device-id="${device.id || device.device_id || ''}"
                 data-svg-type="${svgType}"
                 data-device-json='${this._escapeJson(JSON.stringify(device))}'>
                <div class="d-flex align-items-center">
                    <div class="device-status-indicator me-2 ${device.is_active ? 'online' : 'offline'}"></div>
                    <div class="flex-grow-1" style="min-width: 0;">
                        <strong class="d-block text-truncate">${device.name}</strong>
                        <small class="text-muted device-status-${device.is_active ? 'online' : 'offline'}">
                            ${device.is_active ? 'Online' : 'Offline'}
                        </small>
                    </div>
                    <span class="badge bg-secondary ms-1" style="font-size: 0.65rem; cursor: grab;">↕</span>
                </div>
            </div>`;
        }).join('');

        // Adicionar dragstart handler em cada item
        container.querySelectorAll('.device-item[draggable]').forEach(item => {
            item.addEventListener('dragstart', (e) => {
                const deviceJson = item.dataset.deviceJson;
                e.dataTransfer.setData('application/json', deviceJson);
                e.dataTransfer.setData('device-id', item.dataset.deviceId);
                e.dataTransfer.setData('svg-type', item.dataset.svgType);
                e.dataTransfer.effectAllowed = 'copy';
                item.style.opacity = '0.5';
            });
            item.addEventListener('dragend', (e) => {
                item.style.opacity = '1';
            });
        });
    }

    _escapeJson(str) {
        return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                  .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    static getSvgTypeForDevice(device) {
        // Extrair tipo do device: actor_type, function, device_type
        const typeKey = (device.actor_type || device.function || device.device_type || device.type || '').toLowerCase();
        const nameKey = (device.name || '').toLowerCase();

        // Procurar no mapa estático
        if (MashDashboard.DEVICE_SVG_MAP[typeKey]) {
            return MashDashboard.DEVICE_SVG_MAP[typeKey];
        }

        // Procurar no nome
        for (const [key, svgType] of Object.entries(MashDashboard.DEVICE_SVG_MAP)) {
            if (nameKey.includes(key)) {
                return svgType;
            }
        }

        // Fallback: tentar encontrar um SVG que corresponda ao nome
        if (nameKey.includes('bomb') || nameKey.includes('pump')) return 'P_gradi_1';
        if (nameKey.includes('temperatura') || nameKey.includes('temp') || nameKey.includes('sensor')) return 'sensor';
        if (nameKey.includes('resist') || nameKey.includes('aquecedor') || nameKey.includes('heater')) return 'heater';
        if (nameKey.includes('valv') || nameKey.includes('valve')) return 'valve';

        return 'sensor'; // Fallback genérico
    }

    static getColorForDevice(device) {
        const typeKey = (device.actor_type || device.function || device.device_type || device.type || '').toLowerCase();
        return MashDashboard.DEVICE_COLOR_MAP[typeKey] || '#4CAF50';
    }
    
    renderActiveSession() {
        const infoContainer = document.getElementById('active-session-info');
        const controlsContainer = document.getElementById('session-controls');
        
        if (!this.activeSession) {
            if (infoContainer) {
                infoContainer.innerHTML = '<p class="text-muted mb-0">Nenhuma sessão ativa</p>';
            }
            if (controlsContainer) {
                controlsContainer.style.display = 'none';
            }
            return;
        }
        
        if (infoContainer) {
            infoContainer.innerHTML = `
                <div class="session-item border rounded">
                    <div class="d-flex align-items-start">
                        <div class="flex-grow-1" style="min-width: 0;">
                            <strong class="d-block text-truncate">${this.activeSession.name}</strong>
                            <small class="text-muted d-block">Etapa: ${this.activeSession.current_step || 'N/A'}</small>
                            ${this.activeSession.status ? `<span class="badge bg-${this.activeSession.status === 'running' ? 'success' : 'warning'} mt-1">${this.activeSession.status}</span>` : ''}
                        </div>
                    </div>
                </div>
            `;
        }
        
        if (controlsContainer) {
            controlsContainer.style.display = 'block';
            
            // Configurar botões
            const pauseBtn = document.getElementById('pause-session-btn');
            const stopBtn = document.getElementById('stop-session-btn');
            
            if (pauseBtn) {
                pauseBtn.onclick = () => this.pauseSession();
            }
            if (stopBtn) {
                stopBtn.onclick = () => this.stopSession();
            }
        }
    }
    
    setupEventListeners() {
        // Botão de editar layout
        const editBtn = document.getElementById('edit-layout-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                this.toggleEditMode();
            });
        }
        
        // Botão de resetar visualização
        const resetBtn = document.getElementById('reset-view-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.loadLayout();
            });
        }
        
        // Botão de gerenciar dashboards
        const manageBtn = document.getElementById('manage-dashboards-btn');
        if (manageBtn) {
            manageBtn.addEventListener('click', () => {
                this.loadDashboardsList();
            });
        }
        
        // Event listener para modal de dashboards
        const dashboardsModal = document.getElementById('dashboardsModal');
        if (dashboardsModal) {
            dashboardsModal.addEventListener('show.bs.modal', () => {
                this.loadDashboardsList();
            });
        }
        
        // Drag and drop de componentes e dispositivos na área SVG
        this.svgWrapper.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
        });

        this.svgWrapper.addEventListener('drop', async (e) => {
            e.preventDefault();

            if (!this.isEditMode) {
                alert('Ative o modo de edição para adicionar componentes.');
                return;
            }

            // Calcular posição do drop (considerando zoom e scroll)
            const rect = this.svg.getBoundingClientRect();
            const scrollLeft = this.svgWrapper.scrollLeft;
            const scrollTop = this.svgWrapper.scrollTop;
            const x = Math.max(0, (e.clientX - rect.left + scrollLeft) / this.zoomLevel - 50);
            const y = Math.max(0, (e.clientY - rect.top + scrollTop) / this.zoomLevel - 50);

            // Tentar drop de dispositivo primeiro (application/json)
            const deviceJson = e.dataTransfer.getData('application/json');
            if (deviceJson) {
                try {
                    const deviceData = JSON.parse(deviceJson);
                    await this.addDeviceToDashboard(deviceData, x, y);
                    return;
                } catch (err) {
                    console.warn('Erro ao processar drop de dispositivo:', err);
                }
            }

            // Fallback: drop de componente da biblioteca
            const componentType = e.dataTransfer.getData('component-type');
            if (componentType) {
                await this.addComponentToDashboard(componentType, x, y);
            }
        });
        
        // Double-click para abrir configuração do elemento (em qualquer modo)
        this.svg.addEventListener('dblclick', (e) => {
            const svgElement = e.target.closest('.dashboard-svg-element');
            if (svgElement) {
                this.openElementConfig(svgElement);
            }
        });

        // Click fora para deselecionar OU toggle em atuador
        this.svg.addEventListener('click', async (e) => {
            // Se clicou em um elemento com device_id e é atuador, tentar toggle
            const actuatorElement = e.target.closest('[data-device-id]');
            if (actuatorElement && actuatorElement.getAttribute('data-device-id')) {
                const deviceId = actuatorElement.getAttribute('data-device-id');
                const componentType = actuatorElement.getAttribute('data-component-type') || '';
                // Verificar se é um tipo que representa atuador (heater, pump, valve, etc)
                const isActuator = /heater|pump|valve|actuator|toggle/i.test(componentType);
                if (isActuator && !this.isEditMode) {
                    e.stopPropagation();
                    await this.toggleActuator(deviceId, actuatorElement);
                    return;
                }
            }

            // Comportamento original: desselecionar se clicou no fundo
            if (e.target === this.svg) {
                this.svg.querySelectorAll('.dashboard-svg-element').forEach(el => {
                    el.classList.remove('selected');
                });
                this.selectedElement = null;
            }
        });
        
        // Tecla Delete para remover elemento selecionado
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Delete' && this.isEditMode && this.selectedElement) {
                this.removeSelectedElement();
            }
        });
    }
    
    async addComponentToDashboard(componentType, x, y) {
        const component = this.components.find(c => c.type === componentType);
        if (!component) return;
        
        const elementId = 'element_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        
        const element = {
            id: elementId,
            type: componentType,
            x: Math.max(0, x),
            y: Math.max(0, y),
            width: component.default_size.width,
            height: component.default_size.height,
            properties: { ...component.properties }
        };
        
        // Adicionar ao layout
        if (!this.layout.elements) {
            this.layout.elements = [];
        }
        this.layout.elements.push(element);
        
        // Renderizar no SVG
        await this.addElementToSVG(element);
        this.setupElementDragListeners();
        
        // Salvar layout
        await this.saveLayout();
    }

    async addDeviceToDashboard(deviceData, x, y) {
        // Determinar tipo SVG baseado no dispositivo
        const svgType = MashDashboard.getSvgTypeForDevice(deviceData);
        const deviceId = deviceData.id || deviceData.device_id;

        // Encontrar componente correspondente na biblioteca
        const component = this.components.find(c => c.type === svgType);

        const elementId = 'element_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);

        const element = {
            id: elementId,
            type: svgType,
            x: Math.max(0, x),
            y: Math.max(0, y),
            width: component ? component.default_size.width : 50,
            height: component ? component.default_size.height : 50,
            device_id: deviceId,
            properties: {
                fill_color: MashDashboard.getColorForDevice(deviceData),
                show_temp: /temp|sensor/i.test(svgType),
                show_status: true,
                label: deviceData.name || svgType
            }
        };

        // Adicionar ao layout
        if (!this.layout.elements) {
            this.layout.elements = [];
        }
        this.layout.elements.push(element);

        // Renderizar no SVG
        await this.addElementToSVG(element);
        this.setupElementDragListeners();

        // Salvar layout
        await this.saveLayout();

        // Feedback visual
        this._showToast(`Dispositivo "${deviceData.name}" adicionado ao dashboard`, 'success');
    }

    setupCanvasDropHandler() {
        if (!this.svgWrapper) return;

        // Destacar canvas quando dispositivo está sendo arrastado
        const highlightEnter = () => {
            if (!this.isEditMode) return;
            this.svgWrapper.style.borderColor = '#007bff';
            this.svgWrapper.style.backgroundColor = '#f0f7ff';
        };
        const highlightLeave = () => {
            this.svgWrapper.style.borderColor = '';
            this.svgWrapper.style.backgroundColor = '';
        };

        document.addEventListener('dragenter', (e) => {
            if (e.dataTransfer.types.includes('application/json') ||
                e.dataTransfer.types.includes('component-type')) {
                highlightEnter();
            }
        });

        document.addEventListener('dragleave', (e) => {
            if (!this.svgWrapper.contains(e.relatedTarget)) {
                highlightLeave();
            }
        });

        document.addEventListener('dragend', () => {
            highlightLeave();
        });

        this.svgWrapper.addEventListener('drop', () => {
            highlightLeave();
        });
    }

    _showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>`;
        document.body.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast, { delay: 3000 });
        bsToast.show();
        toast.addEventListener('hidden.bs.toast', () => toast.remove());
    }

    async removeSelectedElement() {
        if (!this.selectedElement) return;
        
        const elementId = this.selectedElement.getAttribute('data-element-id');
        
        // Remover do layout
        if (this.layout.elements) {
            this.layout.elements = this.layout.elements.filter(el => el.id !== elementId);
        }
        
        // Remover do SVG
        this.selectedElement.remove();
        this.selectedElement = null;
        
        // Salvar layout
        await this.saveLayout();
    }
    
    toggleEditMode() {
        this.isEditMode = !this.isEditMode;
        
        const editBtn = document.getElementById('edit-layout-btn');
        const editIndicator = document.getElementById('edit-mode-indicator');
        
        if (editBtn) {
            if (this.isEditMode) {
                editBtn.classList.add('btn-primary');
                editBtn.classList.remove('btn-outline-primary');
                editBtn.innerHTML = '<i class="bi bi-check"></i> Salvar Layout';
                if (editIndicator) editIndicator.style.display = 'block';
            } else {
                editBtn.classList.remove('btn-primary');
                editBtn.classList.add('btn-outline-primary');
                editBtn.innerHTML = '<i class="bi bi-pencil"></i> Editar Layout';
                if (editIndicator) editIndicator.style.display = 'none';
                
                // Mostrar modal para salvar com nome
                this.showSaveModal();
            }
        }
        
        // Atualizar elementos SVG
        this.svg.querySelectorAll('.dashboard-svg-element').forEach(element => {
            if (this.isEditMode) {
                element.style.cursor = 'move';
            } else {
                element.style.cursor = 'default';
                element.classList.remove('selected');
            }
        });
        
        this.setupElementDragListeners();
    }
    
    showSaveModal() {
        const modal = new bootstrap.Modal(document.getElementById('saveDashboardModal'));
        const nameInput = document.getElementById('dashboard-name-input');
        const setAsDefault = document.getElementById('set-as-default');
        
        // Preencher nome atual se existir
        if (this.layout && this.layout.name) {
            nameInput.value = this.layout.name;
        } else {
            nameInput.value = '';
        }
        
        // Marcar como padrão se for o layout atual
        if (this.layout && this.layout.is_default) {
            setAsDefault.checked = true;
        }
        
        // Limpar listener anterior e adicionar novo
        const confirmBtn = document.getElementById('confirm-save-btn');
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        newConfirmBtn.addEventListener('click', async () => {
            const name = nameInput.value.trim();
            if (!name) {
                alert('Por favor, informe um nome para o dashboard');
                return;
            }
            
            const isDefault = setAsDefault.checked;
            
            // Atualizar nome do layout
            this.layout.name = name;
            this.layout.is_default = isDefault;
            
            // Salvar layout
            await this.saveLayout();
            
            // Fechar modal
            modal.hide();
            
            // Atualizar interface
            this.updateDashboardName();
        });
        
        modal.show();
    }
    
    updateDashboardName() {
        const nameElement = document.getElementById('dashboard-name');
        const badgeElement = document.getElementById('dashboard-badge');
        
        if (nameElement && this.layout) {
            nameElement.textContent = this.layout.name || 'Brewhouse';
        }
        
        if (badgeElement && this.layout && this.layout.is_default) {
            badgeElement.style.display = 'inline';
        } else if (badgeElement) {
            badgeElement.style.display = 'none';
        }
    }
    
    async loadDashboardsList() {
        try {
            const response = await fetch('/api/mash_control/dashboard/layouts');
            const layouts = await response.json();
            
            const container = document.getElementById('dashboards-list');
            if (!container) return;
            
            if (layouts.length === 0) {
                container.innerHTML = '<div class="col-12"><p class="text-muted text-center">Nenhum dashboard salvo</p></div>';
                return;
            }
            
            container.innerHTML = layouts.map(layout => `
                <div class="col-md-6">
                    <div class="card h-100 ${layout.is_default ? 'border-warning' : ''}">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title mb-0">
                                    ${layout.name}
                                    ${layout.is_default ? '<span class="badge bg-warning text-dark ms-2"><i class="bi bi-star-fill"></i> Padrão</span>' : ''}
                                </h6>
                            </div>
                            <p class="text-muted small mb-2">
                                ${layout.element_count || 0} componente(s)
                            </p>
                            <div class="btn-group w-100" role="group">
                                <button class="btn btn-sm btn-primary" onclick="window.mashDashboard.loadDashboard('${layout.id}')">
                                    <i class="bi bi-box-arrow-in-right"></i> Carregar
                                </button>
                                ${!layout.is_default ? `
                                    <button class="btn btn-sm btn-outline-warning" onclick="window.mashDashboard.setAsDefault('${layout.id}')">
                                        <i class="bi bi-star"></i> Padrão
                                    </button>
                                ` : ''}
                                <button class="btn btn-sm btn-outline-danger" onclick="window.mashDashboard.deleteDashboard('${layout.id}')">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Erro ao carregar lista de dashboards:', error);
            const container = document.getElementById('dashboards-list');
            if (container) {
                container.innerHTML = '<div class="col-12"><p class="text-danger text-center">Erro ao carregar dashboards</p></div>';
            }
        }
    }
    
    async loadDashboard(layoutId) {
        try {
            const response = await fetch(`/api/mash_control/dashboard/layout?layout_id=${layoutId}`);
            const data = await response.json();
            
            if (data && !data.error) {
                this.layout = {
                    id: data.id || null,
                    name: data.name || 'Novo Layout',
                    elements: data.elements || data.layout_data || [],
                    is_default: data.is_default !== false
                };
                
                this.renderLayout();
                this.updateDashboardName();
                
                // Fechar modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('dashboardsModal'));
                if (modal) modal.hide();
            }
        } catch (error) {
            console.error('Erro ao carregar dashboard:', error);
            alert('Erro ao carregar dashboard: ' + error.message);
        }
    }
    
    async setAsDefault(layoutId) {
        try {
            const response = await fetch(`/api/mash_control/dashboard/layout/${layoutId}/set-default`, {
                method: 'POST'
            });
            
            const data = await response.json();
            if (data.message) {
                // Recarregar lista de dashboards
                await this.loadDashboardsList();
                // Recarregar dashboard atual se for o selecionado
                if (this.layout && this.layout.id === layoutId) {
                    this.layout.is_default = true;
                    this.updateDashboardName();
                }
            } else {
                alert('Erro ao definir dashboard como padrão');
            }
        } catch (error) {
            console.error('Erro ao definir dashboard padrão:', error);
            alert('Erro ao definir dashboard padrão: ' + error.message);
        }
    }
    
    async deleteDashboard(layoutId) {
        if (!confirm('Tem certeza que deseja deletar este dashboard?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/mash_control/dashboard/layout/${layoutId}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            if (data.message) {
                // Se deletou o dashboard atual, carregar o padrão
                if (this.layout && this.layout.id === layoutId) {
                    await this.loadLayout();
                }
                // Recarregar lista
                await this.loadDashboardsList();
            } else {
                alert('Erro ao deletar dashboard');
            }
        } catch (error) {
            console.error('Erro ao deletar dashboard:', error);
            alert('Erro ao deletar dashboard: ' + error.message);
        }
    }
    
    async saveLayout() {
        if (!this.layout) {
            console.warn('Tentativa de salvar layout sem layout inicializado');
            return;
        }
        
        try {
            // Coletar posições atuais dos elementos do SVG
            const elements = [];
            this.svg.querySelectorAll('.dashboard-svg-element').forEach(svgElement => {
                const elementId = svgElement.getAttribute('data-element-id');
                const componentType = svgElement.getAttribute('data-component-type');
                const deviceId = svgElement.getAttribute('data-device-id') || null;
                
                // Encontrar elemento existente ou criar novo
                let element = this.layout.elements?.find(el => el.id === elementId);
                
                if (!element) {
                    // Criar novo elemento baseado no SVG
                    element = {
                        id: elementId,
                        type: componentType,
                        x: 0,
                        y: 0,
                        width: 50,
                        height: 50,
                        properties: {}
                    };
                }
                
                // Atualizar posição do transform
                const transform = svgElement.getAttribute('transform') || '';
                const translateMatch = transform.match(/translate\(([^,]+),\s*([^)]+)\)/);
                if (translateMatch) {
                    element.x = parseFloat(translateMatch[1]);
                    element.y = parseFloat(translateMatch[2]);
                }
                
                // Manter outros atributos
                element.device_id = deviceId;
                element.type = componentType;
                
                elements.push(element);
            });
            
            // Atualizar layout com elementos coletados
            this.layout.elements = elements;
            
            console.log('Salvando layout:', {
                id: this.layout.id,
                name: this.layout.name,
                elements_count: elements.length,
                elements: elements
            });
            
            // Sempre salvar como padrão se não houver ID (primeiro salvamento)
            const isDefault = this.layout.id ? this.layout.is_default !== false : true;
            
            const payload = {
                id: this.layout.id || null,
                name: this.layout.name || 'Novo Layout',
                elements: elements,
                is_default: isDefault
            };
            
            console.log('Enviando para salvar:', payload);
            
            const response = await fetch('/api/mash_control/dashboard/layout', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(`Erro ao salvar: ${response.status} - ${errorData.error || response.statusText}`);
            }
            
            const data = await response.json();
            console.log('Resposta do servidor:', data);
            
            if (data.id) {
                this.layout.id = data.id;
                console.log('Layout salvo com sucesso, ID:', data.id);
                
                // Atualizar nome do dashboard na interface
                this.updateDashboardName();
                
                // Mostrar feedback visual
                const editBtn = document.getElementById('edit-layout-btn');
                if (editBtn) {
                    const originalText = editBtn.innerHTML;
                    editBtn.innerHTML = '<i class="bi bi-check-circle"></i> Salvo!';
                    editBtn.classList.add('btn-success');
                    editBtn.classList.remove('btn-primary', 'btn-outline-primary');
                    
                    setTimeout(() => {
                        editBtn.innerHTML = '<i class="bi bi-pencil"></i> Editar Layout';
                        editBtn.classList.remove('btn-success');
                        editBtn.classList.add('btn-outline-primary');
                    }, 2000);
                }
            } else {
                console.error('Resposta do servidor não contém ID:', data);
                throw new Error('Resposta do servidor não contém ID do layout salvo');
            }
        } catch (error) {
            console.error('Erro ao salvar layout:', error);
            alert('Erro ao salvar layout: ' + error.message);
        }
    }
    
    async updateDashboard() {
        // Usar endpoint de telemetria em lote
        await this.fetchTelemetry();

        // Atualizar sessão ativa
        this.loadActiveSession();
    }
    
    async updateElementValue(element) {
        try {
            const response = await fetch(`/api/mash_control/dashboard/devices?device_id=${element.device_id}`);
            const device = await response.json();
            
            if (device && device.ports) {
                // Atualizar indicadores no SVG
                const svgElement = this.svg.querySelector(`[data-element-id="${element.id}"]`);
                if (svgElement) {
                    const tempIndicator = svgElement.querySelector('.temperature-indicator');
                    if (tempIndicator) {
                        // Encontrar porta de temperatura
                        for (const [portName, portConfig] of Object.entries(device.ports)) {
                            if (portConfig.type === 'sensor' && 'temp' in portName.toLowerCase()) {
                                const value = portConfig.current_value || '--';
                                tempIndicator.textContent = `${value}°C`;
                                break;
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error(`Erro ao atualizar elemento ${element.id}:`, error);
        }
    }
    
    // ========== Config Modal (device linking) ==========

    openElementConfig(svgElement) {
        this.configElement = svgElement;
        this.configElementId = svgElement.getAttribute('data-element-id');
        const componentType = svgElement.getAttribute('data-component-type');
        const currentDeviceId = svgElement.getAttribute('data-device-id') || '';

        // Mostrar tipo do elemento
        const typeEl = document.getElementById('element-config-type');
        if (typeEl) {
            const component = this.components.find(c => c.type === componentType);
            typeEl.textContent = component ? (component.label || component.name || componentType) : componentType;
        }

        // Popular dropdown de dispositivos
        const select = document.getElementById('element-config-device-select');
        if (select) {
            select.innerHTML = '<option value="">Nenhum dispositivo</option>';
            this.devices.forEach(device => {
                const opt = document.createElement('option');
                opt.value = device.id || device.device_id || '';
                opt.textContent = device.name || device.id;
                if (opt.value === currentDeviceId) {
                    opt.selected = true;
                }
                select.appendChild(opt);
            });

            // Remover listener antigo e adicionar novo
            const newSelect = select.cloneNode(true);
            select.parentNode.replaceChild(newSelect, select);
            newSelect.addEventListener('change', (e) => this.onConfigDeviceChange(e.target.value));
        }

        // Mostrar info do dispositivo atual
        const deviceInfoEl = document.getElementById('element-config-device-info');
        const deviceStatusEl = document.getElementById('element-config-device-status');
        if (currentDeviceId) {
            if (deviceInfoEl) deviceInfoEl.style.display = 'block';
            if (deviceStatusEl) {
                const device = this.devices.find(d => (d.id || d.device_id) === currentDeviceId);
                deviceStatusEl.innerHTML = device
                    ? `<span class="text-${device.is_active ? 'success' : 'muted'}">${device.name || currentDeviceId} — ${device.is_active ? 'Online' : 'Offline'}</span>`
                    : `<span class="text-muted">Dispositivo não encontrado</span>`;
            }
        } else {
            if (deviceInfoEl) deviceInfoEl.style.display = 'none';
        }

        // ─── Campos visuais ─────────────────────────────────────

        // Buscar elemento no layout para pegar properties atuais
        let elementProps = {};
        if (this.layout && this.layout.elements) {
            const el = this.layout.elements.find(e => e.id === this.configElementId);
            if (el && el.properties) elementProps = el.properties;
        }

        // Label
        const labelInput = document.getElementById('element-config-label');
        if (labelInput) {
            labelInput.value = elementProps.label || '';
        }

        // Cor
        const colorInput = document.getElementById('element-config-color');
        const colorValue = document.getElementById('element-config-color-value');
        const fillColor = elementProps.fill_color || '#4CAF50';
        if (colorInput) {
            colorInput.value = fillColor;
            colorInput.addEventListener('input', (e) => {
                if (colorValue) colorValue.textContent = e.target.value;
                this._updateConfigPreview(e.target.value);
            });
        }
        if (colorValue) colorValue.textContent = fillColor;

        // Show temp
        const showTempInput = document.getElementById('element-config-show-temp');
        if (showTempInput) {
            showTempInput.checked = elementProps.show_temp !== false;
        }

        // Show status
        const showStatusInput = document.getElementById('element-config-show-status');
        if (showStatusInput) {
            showStatusInput.checked = elementProps.show_status !== false;
        }

        // Preview
        this._updateConfigPreview(fillColor);

        // Configurar botão salvar
        const saveBtn = document.getElementById('element-config-save-btn');
        if (saveBtn) {
            const newBtn = saveBtn.cloneNode(true);
            saveBtn.parentNode.replaceChild(newBtn, saveBtn);
            newBtn.addEventListener('click', () => this.saveElementConfig());
        }

        // Abrir modal
        const modalEl = document.getElementById('elementConfigModal');
        if (modalEl) {
            const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
            modal.show();
        }
    }

    _updateConfigPreview(color) {
        const preview = document.getElementById('element-config-preview');
        if (!preview) return;
        preview.innerHTML = `
            <svg width="60" height="50" viewBox="0 0 60 50">
                <rect x="5" y="5" width="50" height="40" rx="4" fill="${color}" stroke="#333" stroke-width="1.5"/>
                <text x="30" y="30" text-anchor="middle" font-size="10" fill="#fff" font-weight="bold">--°C</text>
            </svg>`;
    }

    onConfigDeviceChange(deviceId) {
        const deviceInfoEl = document.getElementById('element-config-device-info');
        const deviceStatusEl = document.getElementById('element-config-device-status');

        if (!deviceId) {
            if (deviceInfoEl) deviceInfoEl.style.display = 'none';
            return;
        }

        if (deviceInfoEl) deviceInfoEl.style.display = 'block';
        if (deviceStatusEl) {
            const device = this.devices.find(d => (d.id || d.device_id) === deviceId);
            deviceStatusEl.innerHTML = device
                ? `<span class="text-${device.is_active ? 'success' : 'muted'}">${device.name || deviceId} — ${device.is_active ? 'Online' : 'Offline'}</span>`
                : `<span class="text-muted">Carregando...</span>`;
        }
    }

    async saveElementConfig() {
        const elementId = this.configElementId;
        const layoutId = this.layout ? this.layout.id : null;
        const select = document.getElementById('element-config-device-select');
        const deviceId = select ? select.value : '';

        // Coletar campos visuais
        const label = document.getElementById('element-config-label')?.value || '';
        const fillColor = document.getElementById('element-config-color')?.value || '#4CAF50';
        const showTemp = document.getElementById('element-config-show-temp')?.checked ?? true;
        const showStatus = document.getElementById('element-config-show-status')?.checked ?? true;

        // Atualizar no layout object (mesmo antes de salvar no backend)
        if (this.layout && this.layout.elements) {
            const el = this.layout.elements.find(e => e.id === elementId);
            if (el) {
                el.device_id = deviceId || null;
                el.properties = el.properties || {};
                el.properties.label = label;
                el.properties.fill_color = fillColor;
                el.properties.show_temp = showTemp;
                el.properties.show_status = showStatus;
            }
        }

        if (!layoutId || !elementId) {
            // Layout ainda não foi salvo — salvar primeiro
            // Atualizar dataset no SVG element
            this._updateSvgElementVisuals(elementId, deviceId, { label, fill_color: fillColor, show_temp: showTemp, show_status: showStatus });

            const modalEl = document.getElementById('elementConfigModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }
            return;
        }

        try {
            // Salvar vinculação de dispositivo
            if (deviceId) {
                await fetch(`/api/mash_control/dashboard/layout/${layoutId}/element/${elementId}/link-device`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ device_id: deviceId })
                });
            }

            // Salvar configuração visual — re-salvar layout completo
            await this.saveLayout();

            // Atualizar dataset no SVG element
            this._updateSvgElementVisuals(elementId, deviceId, { label, fill_color: fillColor, show_temp: showTemp, show_status: showStatus });

            // Fechar modal
            const modalEl = document.getElementById('elementConfigModal');
            if (modalEl) {
                const modal = bootstrap.Modal.getInstance(modalEl);
                if (modal) modal.hide();
            }
        } catch (error) {
            console.error('Erro ao salvar configuração:', error);
            alert('Erro ao salvar configuração: ' + error.message);
        }
    }

    _updateSvgElementVisuals(elementId, deviceId, props) {
        if (this.configElement) {
            this.configElement.setAttribute('data-device-id', deviceId);

            // Atualizar label
            let labelEl = this.configElement.querySelector('.device-label');
            if (props.label && labelEl) {
                labelEl.textContent = props.label;
            }

            // Atualizar cor de preenchimento
            if (props.fill_color) {
                const fillEls = this.configElement.querySelectorAll('[fill]');
                const skipColors = ['none', 'transparent', '#fff', '#ffffff', 'white', '#333', '#555', '#6c757d'];
                fillEls.forEach(el => {
                    const curFill = el.getAttribute('fill')?.toLowerCase();
                    if (curFill && !skipColors.includes(curFill) && !curFill.startsWith('url(')) {
                        el.setAttribute('fill', props.fill_color);
                    }
                });
            }

            // Mostrar/esconder temperatura
            const tempEl = this.configElement.querySelector('[data-temp-display="true"]');
            if (tempEl) {
                tempEl.style.display = props.show_temp ? 'block' : 'none';
            }

            // Mostrar/esconder status dot
            const statusDot = this.configElement.querySelector('.element-status-dot');
            if (statusDot) {
                statusDot.style.display = props.show_status !== false ? 'block' : 'none';
            }
        }
    }

    // ========== Telemetry ==========

    async fetchTelemetry() {
        if (!this.layout || !this.layout.id) return;

        try {
            const response = await fetch(`/api/mash_control/dashboard/layout/${this.layout.id}/telemetry`);

            if (!response.ok) {
                // Telemetry endpoint pode falhar se device_manager não disponível — silencioso
                return;
            }

            const data = await response.json();
            if (!data || !data.elements) return;

            // Atualizar cada elemento no SVG baseado na telemetria
            for (const tele of data.elements) {
                if (!tele.element_id) continue;

                const svgEl = this.svg.querySelector(`[data-element-id="${tele.element_id}"]`);
                if (!svgEl) continue;

                // Atualizar device_id se veio do backend
                if (tele.device_id) {
                    svgEl.setAttribute('data-device-id', tele.device_id);
                }

                // Estado ativo/inativo para atuadores
                if (tele.status === 'active' || tele.status === 'on' || tele.status === 'online') {
                    svgEl.classList.add('active');
                    svgEl.classList.remove('inactive');
                } else if (tele.status === 'inactive' || tele.status === 'off' || tele.status === 'offline') {
                    svgEl.classList.add('inactive');
                    svgEl.classList.remove('active');
                }

                // Status dot (bolinha no canto superior direito)
                const statusDot = svgEl.querySelector('.element-status-dot');
                if (statusDot) {
                    const isOnline = tele.status === 'online' || tele.status === 'active' || tele.status === 'on';
                    const isError = tele.status === 'error' || tele.status === 'fault';
                    statusDot.setAttribute('fill', isError ? '#dc3545' : (isOnline ? '#28a745' : '#6c757d'));
                }

                // Temperatura/valor
                const tempIndicator = svgEl.querySelector('[data-temp-display="true"]');
                if (tempIndicator) {
                    if (tele.value !== null && tele.value !== undefined) {
                        const displayValue = typeof tele.value === 'number' ? tele.value.toFixed(1) : tele.value;
                        tempIndicator.textContent = `${displayValue}°C`;
                    } else {
                        tempIndicator.textContent = '--°C';
                    }
                }

                // Atualizar ou criar tooltip com info completa
                const deviceName = tele.name || tele.device_id || '';
                const deviceStatus = tele.status || 'unknown';
                svgEl.setAttribute('title', `${deviceName} | Status: ${deviceStatus}${tele.value !== undefined && tele.value !== null ? ` | ${tele.value}°C` : ''}`);
            }
        } catch (error) {
            // Silencioso — telemetry é best-effort
        }
    }

    async pauseSession() {
        if (!this.activeSession) return;
        
        try {
            const response = await fetch(`/api/mash_control/sessions/${this.activeSession.id}/pause`, {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.message) {
                this.loadActiveSession();
            }
        } catch (error) {
            console.error('Erro ao pausar sessão:', error);
        }
    }
    
    async stopSession() {
        if (!this.activeSession) return;
        
        if (confirm('Tem certeza que deseja parar esta sessão?')) {
            try {
                const response = await fetch(`/api/mash_control/sessions/${this.activeSession.id}/stop`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.message) {
                    window.location.reload();
                }
            } catch (error) {
                console.error('Erro ao parar sessão:', error);
            }
        }
    }

    /**
     * Toggle de atuador: envia comando para ligar/desligar via device_manager API.
     * @param {string} deviceId - ID do ator (device/actor_id)
     * @param {Element} svgElement - Elemento SVG clicado
     */
    async toggleActuator(deviceId, svgElement) {
        try {
            // Descobrir estado atual via telemetria ou atributo visual
            const statusIndicator = svgElement.querySelector('.status-indicator');
            const isCurrentlyOn = svgElement.classList.contains('active')
                || (statusIndicator && statusIndicator.classList.contains('text-success'));

            const command = isCurrentlyOn ? 'OFF' : 'ON';

            const response = await fetch(`/api/device_manager/actors/${deviceId}/command`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ command, value: command === 'ON' ? 1 : 0 })
            });

            if (!response.ok) {
                console.error('Falha ao enviar comando para atuador');
                return;
            }

            // Feedback visual imediato
            svgElement.classList.toggle('active', !isCurrentlyOn);
            if (statusIndicator) {
                statusIndicator.className = `status-indicator ${!isCurrentlyOn ? 'text-success' : 'text-muted'}`;
            }

            console.log(`Atuador ${deviceId}: ${command}`);
        } catch (error) {
            console.error('Erro ao controlar atuador:', error);
        }
    }

    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// ─── Mapas estáticos de dispositivo → SVG ───────────────────────────

MashDashboard.DEVICE_SVG_MAP = {
    'temperature': 'sensor',
    'temperatura': 'sensor',
    'temp': 'sensor',
    'relay': 'heater',
    'pwm': 'heater',
    'pump': 'P_gradi_1',
    'valve': 'valve',
    'valvula': 'valve',
    'gpio_digital': 'actuator',
    'actuator': 'actuator',
    'sensor': 'sensor',
    'heater': 'heater',
    'chiller': 'chiller',
    'kettle': 'kettle',
    'mash_tun': 'mash_tun'
};

MashDashboard.DEVICE_COLOR_MAP = {
    'temperature': '#F44336',
    'temperatura': '#F44336',
    'relay': '#FF5722',
    'pwm': '#FF5722',
    'pump': '#FF9800',
    'valve': '#9E9E9E',
    'valvula': '#9E9E9E',
    'gpio_digital': '#4CAF50',
    'sensor': '#F44336',
    'heater': '#FF5722',
    'chiller': '#00BCD4'
};

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    const dashboard = new MashDashboard();
    dashboard.init();
    
    // Expor globalmente para debug
    window.mashDashboard = dashboard;
});
