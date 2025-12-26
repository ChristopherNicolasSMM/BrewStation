/**
 * JavaScript para o dashboard de brassagem.
 */

class MashDashboard {
    constructor() {
        this.svg = null;
        this.layout = null;
        this.devices = [];
        this.activeSession = null;
        this.updateInterval = null;
    }
    
    init() {
        this.svg = document.getElementById('dashboard-svg');
        if (!this.svg) return;
        
        this.loadLayout();
        this.loadDevices();
        this.loadActiveSession();
        this.setupEventListeners();
        
        // Atualizar a cada 2 segundos
        this.updateInterval = setInterval(() => {
            this.updateDashboard();
        }, 2000);
    }
    
    async loadLayout() {
        try {
            const response = await fetch('/api/mash_control/dashboard/layout');
            const data = await response.json();
            
            if (data && data.layout_data) {
                this.layout = data;
                this.renderLayout();
            }
        } catch (error) {
            console.error('Erro ao carregar layout:', error);
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
                this.renderActiveSession();
            } else {
                document.getElementById('active-session-info').innerHTML = 
                    '<p class="text-muted">Nenhuma sessão ativa</p>';
                document.getElementById('session-controls').style.display = 'none';
            }
        } catch (error) {
            console.error('Erro ao carregar sessão ativa:', error);
        }
    }
    
    async renderLayout() {
        if (!this.layout || !this.layout.layout_data) return;
        
        const elements = Array.isArray(this.layout.layout_data) 
            ? this.layout.layout_data 
            : JSON.parse(this.layout.layout_data || '[]');
        
        // Carregar elementos SVG de forma assíncrona
        for (const element of elements) {
            await this.addElementToSVG(element);
        }
    }
    
    async addElementToSVG(element) {
        if (!this.svg || !window.SVGComponents) return;
        
        let svgElement = null;
        
        try {
            switch (element.type) {
                case 'kettle':
                    svgElement = await SVGComponents.createKettle(
                        element.x || 0,
                        element.y || 0,
                        element.properties?.width || 100,
                        element.properties?.height || 120,
                        element.properties || {}
                    );
                    break;
                case 'mash_tun':
                    svgElement = await SVGComponents.createMashTun(
                        element.x || 0,
                        element.y || 0,
                        element.properties?.width || 120,
                        element.properties?.height || 150,
                        element.properties || {}
                    );
                    break;
                case 'pump':
                    svgElement = await SVGComponents.createPump(
                        element.x || 0,
                        element.y || 0,
                        element.properties?.width || 60,
                        element.properties?.height || 60,
                        element.properties || {}
                    );
                    break;
                case 'valve':
                    svgElement = await SVGComponents.createValve(
                        element.x || 0,
                        element.y || 0,
                        element.properties?.width || 40,
                        element.properties?.height || 40,
                        element.properties || {}
                    );
                    break;
                case 'sensor':
                    svgElement = await SVGComponents.createSensor(
                        element.x || 0,
                        element.y || 0,
                        element.properties?.width || 30,
                        element.properties?.height || 30,
                        element.properties || {}
                    );
                    break;
                case 'heater':
                    svgElement = await SVGComponents.createHeater(
                        element.x || 0,
                        element.y || 0,
                        element.properties?.width || 50,
                        element.properties?.height || 50,
                        element.properties || {}
                    );
                    break;
                case 'chiller':
                    svgElement = await SVGComponents.createChiller(
                        element.x || 0,
                        element.y || 0,
                        element.properties?.width || 50,
                        element.properties?.height || 50,
                        element.properties || {}
                    );
                    break;
            }
            
            if (svgElement) {
                svgElement.setAttribute('data-element-id', element.id);
                svgElement.setAttribute('data-device-id', element.device_id || '');
                this.svg.appendChild(svgElement);
            }
        } catch (error) {
            console.error(`Erro ao adicionar elemento ${element.type} ao SVG:`, error);
        }
    }
    
    renderDevicesList() {
        const container = document.getElementById('devices-list');
        if (!container) return;
        
        if (this.devices.length === 0) {
            container.innerHTML = '<p class="text-muted">Nenhum dispositivo disponível</p>';
            return;
        }
        
        container.innerHTML = this.devices.map(device => `
            <div class="mb-2">
                <small>
                    <strong>${device.name}</strong><br>
                    <span class="device-status-${device.is_active ? 'online' : 'offline'}">
                        ${device.is_active ? 'Online' : 'Offline'}
                    </span>
                </small>
            </div>
        `).join('');
    }
    
    renderActiveSession() {
        if (!this.activeSession) return;
        
        const infoContainer = document.getElementById('active-session-info');
        const controlsContainer = document.getElementById('session-controls');
        
        infoContainer.innerHTML = `
            <p><strong>${this.activeSession.name}</strong></p>
            <p class="text-muted">Etapa: ${this.activeSession.current_step}</p>
        `;
        
        controlsContainer.style.display = 'block';
        
        // Configurar botões
        document.getElementById('pause-session-btn').onclick = () => this.pauseSession();
        document.getElementById('stop-session-btn').onclick = () => this.stopSession();
    }
    
    setupEventListeners() {
        // Botão de editar layout
        const editBtn = document.getElementById('edit-layout-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                alert('Funcionalidade de edição de layout será implementada em breve.');
            });
        }
        
        // Botão de resetar visualização
        const resetBtn = document.getElementById('reset-view-btn');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.loadLayout();
            });
        }
    }
    
    async updateDashboard() {
        // Atualizar valores dos dispositivos no SVG
        if (this.layout && this.layout.layout_data) {
            const elements = Array.isArray(this.layout.layout_data) 
                ? this.layout.layout_data 
                : JSON.parse(this.layout.layout_data || '[]');
            
            for (const element of elements) {
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

