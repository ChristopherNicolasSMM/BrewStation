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
        
        if (zoomInBtn) {
            zoomInBtn.addEventListener('click', () => this.zoomIn());
        }
        
        if (zoomOutBtn) {
            zoomOutBtn.addEventListener('click', () => this.zoomOut());
        }
        
        if (zoomResetBtn) {
            zoomResetBtn.addEventListener('click', () => this.resetZoom());
        }
        
        // Zoom com scroll do mouse
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
    
    zoomIn() {
        this.zoomLevel = Math.min(3, this.zoomLevel * 1.2);
        this.applyZoom();
    }
    
    zoomOut() {
        this.zoomLevel = Math.max(0.25, this.zoomLevel / 1.2);
        this.applyZoom();
    }
    
    resetZoom() {
        this.zoomLevel = 1;
        this.panX = 0;
        this.panY = 0;
        
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
        
        container.innerHTML = sortedDevices.map(device => `
            <div class="device-item border rounded">
                <div class="d-flex align-items-center">
                    <div class="device-status-indicator me-2 ${device.is_active ? 'online' : 'offline'}"></div>
                    <div class="flex-grow-1" style="min-width: 0;">
                        <strong class="d-block text-truncate">${device.name}</strong>
                        <small class="text-muted device-status-${device.is_active ? 'online' : 'offline'}">
                            ${device.is_active ? 'Online' : 'Offline'}
                        </small>
                    </div>
                </div>
            </div>
        `).join('');
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
        
        // Drag and drop de componentes na área SVG
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
            
            const componentType = e.dataTransfer.getData('component-type');
            if (!componentType) return;
            
            const rect = this.svg.getBoundingClientRect();
            // Considerar zoom e scroll ao calcular posição
            const scrollLeft = this.svgWrapper.scrollLeft;
            const scrollTop = this.svgWrapper.scrollTop;
            const x = (e.clientX - rect.left + scrollLeft) / this.zoomLevel - 50;
            const y = (e.clientY - rect.top + scrollTop) / this.zoomLevel - 50;
            
            await this.addComponentToDashboard(componentType, Math.max(0, x), Math.max(0, y));
        });
        
        // Click fora para deselecionar
        this.svg.addEventListener('click', (e) => {
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
        // Atualizar valores dos dispositivos no SVG
        if (this.layout && this.layout.elements) {
            for (const element of this.layout.elements) {
                if (element.device_id) {
                    await this.updateElementValue(element);
                }
            }
        }
        
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
    
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
    }
}

// Inicializar quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', function() {
    const dashboard = new MashDashboard();
    dashboard.init();
    
    // Expor globalmente para debug
    window.mashDashboard = dashboard;
});
