/**
 * Componentes SVG reutilizáveis para o dashboard.
 * 
 * Carrega SVGs da pasta static/mash_control/svg/
 * 
 * Nomes de arquivos esperados:
 * - kettle.svg
 * - mash_tun.svg
 * - pump.svg
 * - valve.svg
 * - sensor.svg
 * - heater.svg
 * - chiller.svg
 */

class SVGComponents {
    /**
     * Base URL para os arquivos SVG
     */
    static get svgBasePath() {
        return '/plugin/mash_control/static/mash_control/svg/';
    }
    
    /**
     * Carrega um SVG de arquivo e cria um elemento posicionado.
     */
    static async loadSVG(type, x, y, width, height, properties = {}) {
        const svgPath = `${this.svgBasePath}${type}.svg`;
        
        try {
            // Carregar conteúdo do SVG
            const response = await fetch(svgPath);
            if (!response.ok) {
                console.warn(`SVG não encontrado: ${svgPath}, usando fallback`);
                return this.createFallback(type, x, y, width, height, properties);
            }
            
            const svgText = await response.text();
            const parser = new DOMParser();
            const svgDoc = parser.parseFromString(svgText, 'image/svg+xml');
            const svgElement = svgDoc.documentElement;
            
            // Verificar se houve erro no parsing
            const parserError = svgDoc.querySelector('parsererror');
            if (parserError) {
                console.error(`Erro ao parsear SVG ${type}:`, parserError.textContent);
                return this.createFallback(type, x, y, width, height, properties);
            }
            
            // Criar grupo para posicionamento
            const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
            group.setAttribute('class', `svg-component ${type}`);
            group.setAttribute('transform', `translate(${x}, ${y})`);
            
            // Ajustar tamanho se necessário
            if (width && height) {
                svgElement.setAttribute('width', width);
                svgElement.setAttribute('height', height);
            }
            
            // Aplicar propriedades personalizadas
            if (properties.fill_color) {
                const elements = svgElement.querySelectorAll('[fill]');
                elements.forEach(el => {
                    const fillValue = el.getAttribute('fill');
                    if (fillValue && fillValue !== 'none' && fillValue !== 'transparent') {
                        el.setAttribute('fill', properties.fill_color);
                    }
                });
            }
            
            // Clonar e adicionar ao grupo
            const clonedSvg = svgElement.cloneNode(true);
            group.appendChild(clonedSvg);
            
            // Adicionar indicadores dinâmicos se necessário
            if (properties.show_temp && (type === 'kettle' || type === 'mash_tun')) {
                const tempText = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                tempText.setAttribute('x', (width || 100) / 2);
                tempText.setAttribute('y', (height || 120) / 2);
                tempText.setAttribute('text-anchor', 'middle');
                tempText.setAttribute('font-size', '14');
                tempText.setAttribute('fill', '#fff');
                tempText.setAttribute('class', 'temperature-indicator');
                tempText.textContent = '--°C';
                group.appendChild(tempText);
            }
            
            return group;
        } catch (error) {
            console.error(`Erro ao carregar SVG ${type}:`, error);
            return this.createFallback(type, x, y, width, height, properties);
        }
    }
    
    /**
     * Cria um elemento SVG de panela (kettle).
     */
    static createKettle(x, y, width = 100, height = 120, properties = {}) {
        return this.loadSVG('kettle', x, y, width, height, properties);
    }
    
    /**
     * Cria um elemento SVG de tunel de mostura (mash_tun).
     */
    static createMashTun(x, y, width = 120, height = 150, properties = {}) {
        return this.loadSVG('mash_tun', x, y, width, height, properties);
    }
    
    /**
     * Cria um elemento SVG de bomba (pump).
     */
    static createPump(x, y, width = 60, height = 60, properties = {}) {
        return this.loadSVG('pump', x, y, width, height, properties);
    }
    
    /**
     * Cria um elemento SVG de válvula (valve).
     */
    static createValve(x, y, width = 40, height = 40, properties = {}) {
        return this.loadSVG('valve', x, y, width, height, properties);
    }
    
    /**
     * Cria um elemento SVG de sensor (sensor).
     */
    static createSensor(x, y, width = 30, height = 30, properties = {}) {
        return this.loadSVG('sensor', x, y, width, height, properties);
    }
    
    /**
     * Cria um elemento SVG de aquecedor (heater).
     */
    static createHeater(x, y, width = 50, height = 50, properties = {}) {
        return this.loadSVG('heater', x, y, width, height, properties);
    }
    
    /**
     * Cria um elemento SVG de resfriador (chiller).
     */
    static createChiller(x, y, width = 50, height = 50, properties = {}) {
        return this.loadSVG('chiller', x, y, width, height, properties);
    }
    
    /**
     * Cria um fallback simples caso o SVG não esteja disponível.
     */
    static createFallback(type, x, y, width = 100, height = 100, properties = {}) {
        const fillColor = properties.fill_color || '#9E9E9E';
        
        const group = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        group.setAttribute('class', `svg-component ${type} fallback`);
        group.setAttribute('transform', `translate(${x}, ${y})`);
        
        // Retângulo simples como fallback
        const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
        rect.setAttribute('x', 0);
        rect.setAttribute('y', 0);
        rect.setAttribute('width', width);
        rect.setAttribute('height', height);
        rect.setAttribute('fill', fillColor);
        rect.setAttribute('stroke', '#333');
        rect.setAttribute('stroke-width', '2');
        rect.setAttribute('rx', '5');
        
        // Texto indicando o tipo
        const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
        text.setAttribute('x', width / 2);
        text.setAttribute('y', height / 2);
        text.setAttribute('text-anchor', 'middle');
        text.setAttribute('font-size', '12');
        text.setAttribute('fill', '#fff');
        text.setAttribute('font-weight', 'bold');
        text.textContent = type;
        
        group.appendChild(rect);
        group.appendChild(text);
        
        return group;
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.SVGComponents = SVGComponents;
}
