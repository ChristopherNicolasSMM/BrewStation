/**
 * JavaScript para o editor de receitas.
 */

class RecipeEditor {
    constructor() {
        this.recipeId = null;
        this.steps = [];
        this.equipmentMapping = {};
    }
    
    init() {
        // Inicialização será feita pelo template HTML
    }
    
    addStep(stepData = {}) {
        this.steps.push({
            type: stepData.type || 'mash',
            name: stepData.name || '',
            target_temp: stepData.target_temp || 0,
            duration: stepData.duration || 0,
            devices: stepData.devices || {},
            actions: stepData.actions || []
        });
        
        this.renderSteps();
    }
    
    removeStep(index) {
        this.steps.splice(index, 1);
        this.renderSteps();
    }
    
    renderSteps() {
        // Renderização será feita pelo template HTML
    }
    
    validateRecipe() {
        if (!this.recipeData || !this.recipeData.name) {
            return {valid: false, error: 'Nome da receita é obrigatório'};
        }
        
        if (!this.steps || this.steps.length === 0) {
            return {valid: false, error: 'Pelo menos uma etapa é necessária'};
        }
        
        for (const step of this.steps) {
            if (!step.name) {
                return {valid: false, error: 'Todas as etapas devem ter um nome'};
            }
            if (step.target_temp < 0 || step.target_temp > 100) {
                return {valid: false, error: 'Temperatura deve estar entre 0 e 100°C'};
            }
            if (step.duration < 0) {
                return {valid: false, error: 'Duração deve ser positiva'};
            }
        }
        
        return {valid: true};
    }
    
    calculateTimeline() {
        let currentTime = 0;
        const timeline = [];
        
        for (const step of this.steps) {
            timeline.push({
                step_name: step.name,
                start_time: currentTime,
                end_time: currentTime + step.duration,
                duration: step.duration,
                target_temp: step.target_temp,
                type: step.type
            });
            currentTime += step.duration;
        }
        
        return timeline;
    }
    
    async saveRecipe() {
        const validation = this.validateRecipe();
        if (!validation.valid) {
            alert(validation.error);
            return false;
        }
        
        const recipeData = {
            name: this.recipeData.name,
            description: this.recipeData.description || '',
            recipe_data: {
                steps: this.steps
            },
            equipment_mapping: this.equipmentMapping
        };
        
        try {
            const url = this.recipeId 
                ? `/api/mash_control/recipes/${this.recipeId}`
                : '/api/mash_control/recipes';
            const method = this.recipeId ? 'PUT' : 'POST';
            
            const response = await fetch(url, {
                method: method,
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(recipeData)
            });
            
            const data = await response.json();
            
            if (data.id || data.message) {
                alert('Receita salva com sucesso!');
                return true;
            } else {
                alert('Erro ao salvar receita: ' + (data.error || 'Erro desconhecido'));
                return false;
            }
        } catch (error) {
            console.error('Erro ao salvar receita:', error);
            alert('Erro ao salvar receita');
            return false;
        }
    }
    
    async loadRecipe(recipeId) {
        try {
            const response = await fetch(`/api/mash_control/recipes/${recipeId}`);
            const data = await response.json();
            
            if (data) {
                this.recipeId = recipeId;
                this.recipeData = {
                    name: data.name,
                    description: data.description
                };
                this.steps = data.recipe_data?.steps || [];
                this.equipmentMapping = data.equipment_mapping || {};
                
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Erro ao carregar receita:', error);
            return false;
        }
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') {
    window.RecipeEditor = RecipeEditor;
}

