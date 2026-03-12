/**
 * Gerenciamento de Receitas de Cerveja
 * 
 * Interface para criar, editar, listar e deletar receitas no Mash Control.
 * Uma receita contém ingredientes, etapas de infusão e parâmetros de brassagem.
 */

class GerenciadorReceitas {
    constructor() {
        this.apiUrl = '/api/mash_control/recipes';
        this.receitaSelecionada = null;
        this.plants = [];
        this.modalDetalhes = null;
        this.modalDelecao = null;
        this.inicializar();
    }

    inicializar() {
        try {
            // Inicializar modais
            const modalDetalhesEl = document.getElementById('modalDetalhesReceita');
            const modalDelecaoEl = document.getElementById('modalConfirmarDelecaoReceita');
            
            this.modalDetalhes = new bootstrap.Modal(modalDetalhesEl);
            this.modalDelecao = new bootstrap.Modal(modalDelecaoEl);
            
            // Registrar event listeners
            this.registrarEventos();
            
            // Carregar plants e receitas
            this.carregarPlants();
            this.carregarReceitas();
        } catch (error) {
            console.error('Erro ao inicializar GerenciadorReceitas:', error);
        }
    }

    registrarEventos() {
        try {
            const btnNovaReceita = document.getElementById('btnNovaReceita');
            const linkNovaReceitaVazio = document.getElementById('linkNovaReceitaVazio');
            const formReceita = document.getElementById('formReceita');
            const btnLimparFormulario = document.getElementById('btnLimparFormularioReceita');
            const btnAdicionarMashStep = document.getElementById('btnAdicionarMashStep');
            const btnEditarNaModal = document.getElementById('btnEditarNaModalReceita');
            const btnConfirmarDelecao = document.getElementById('btnConfirmarDelecaoReceita');
            const inputsParamCalculoABV = [
                document.getElementById('inputOGReceita'),
                document.getElementById('inputFGReceita')
            ];
            
            // Botão nova receita
            if (btnNovaReceita) {
                btnNovaReceita.addEventListener('click', () => {
                    this.abrirNovaReceita();
                });
            }
            
            if (linkNovaReceitaVazio) {
                linkNovaReceitaVazio.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.abrirNovaReceita();
                });
            }

            // Formulário
            if (formReceita) {
                formReceita.addEventListener('submit', (e) => {
                    this.handleSubmitFormulario(e);
                });
            }
            
            if (btnLimparFormulario) {
                btnLimparFormulario.addEventListener('click', () => {
                    this.limparFormulario();
                });
            }
            
            if (btnAdicionarMashStep) {
                btnAdicionarMashStep.addEventListener('click', () => {
                    this.adicionarMashStep();
                });
            }

            // Modal de edição
            if (btnEditarNaModal) {
                btnEditarNaModal.addEventListener('click', () => {
                    if (this.receitaSelecionada) {
                        this.carregarReceitaNoFormulario(this.receitaSelecionada);
                        this.modalDetalhes.hide();
                        document.getElementById('tab-editor').click();
                    }
                });
            }

            // Modal de deleção
            if (btnConfirmarDelecao) {
                btnConfirmarDelecao.addEventListener('click', () => {
                    this.confirmarDelecao();
                });
            }
            
            // Monitorar mudanças em OG e FG para calcular ABV
            inputsParamCalculoABV.forEach(input => {
                if (input) {
                    input.addEventListener('change', () => {
                        this.atualizarResumoReceita();
                    });
                }
            });
        } catch (error) {
            console.error('Erro ao registrar eventos de receitas:', error);
        }
    }

    async carregarPlants() {
        try {
            const response = await fetch('/api/mash_control/plants');
            
            if (response.ok) {
                this.plants = await response.json();
                this.atualizarSelectPlants();
            }
        } catch (error) {
            console.error('Erro ao carregar plants:', error);
        }
    }

    atualizarSelectPlants() {
        const select = document.getElementById('selectPlantaReceita');
        if (!select) return;
        
        const opcaoSelecionada = select.value;
        select.innerHTML = '<option value="">Nenhuma plant selecionada</option>';
        
        this.plants.forEach(plant => {
            const option = document.createElement('option');
            option.value = plant.id;
            option.textContent = plant.name;
            select.appendChild(option);
        });
        
        select.value = opcaoSelecionada;
    }

    async carregarReceitas() {
        try {
            const response = await fetch(this.apiUrl);
            
            if (!response.ok) {
                console.error('Erro ao carregar receitas:', response.status);
                return;
            }

            const receitas = await response.json();
            
            const divCarregando = document.getElementById('divCarregandoReceitas');
            const divVazio = document.getElementById('divReceitasVazio');
            
            if (divCarregando) divCarregando.style.display = 'none';

            if (receitas.length === 0) {
                if (divVazio) divVazio.style.display = 'block';
            } else {
                if (divVazio) divVazio.style.display = 'none';
                this.renderizarReceitas(receitas);
            }
        } catch (error) {
            console.error('Erro ao carregar receitas:', error);
            const div = document.getElementById('divCarregandoReceitas');
            if (div) {
                div.innerHTML = '<div class="alert alert-danger">Erro ao carregar receitas. Tente novamente.</div>';
            }
        }
    }

    renderizarReceitas(receitas) {
        const div = document.getElementById('divReceitas');
        
        if (!div) {
            console.error('Elemento divReceitas não encontrado!');
            return;
        }
        
        div.innerHTML = '';
        
        receitas.forEach((receita, index) => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            
            const abv = receita.abv || 0;
            const og = (receita.original_gravity / 1000.0 + 1.0).toFixed(3);
            const fg = (receita.final_gravity / 1000.0 + 1.0).toFixed(3);
            
            card.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-0">${this.escapeHtml(receita.name)}</h5>
                        <small class="text-muted">${receita.style || 'Sem estilo definido'}</small>
                    </div>
                    <div>
                        <span class="badge badge-gravity me-2">OG: ${og}</span>
                        <span class="badge badge-abv me-2">ABV: ${abv.toFixed(1)}%</span>
                        <span class="badge badge-ibu">IBU: ${receita.ibu}</span>
                    </div>
                </div>
                <div class="card-body">
                    <p class="mb-2">${receita.description || '<em class="text-muted">Sem descrição</em>'}</p>
                    <small class="text-muted">
                        Volume: ${receita.volume}L | 
                        Fervura: ${receita.boil_time}min | 
                        Criada em: ${new Date(receita.created_at).toLocaleDateString('pt-BR')}
                    </small>
                </div>
                <div class="card-footer">
                    <button class="btn btn-sm btn-info" onclick="gerenciadorReceitas.exibirDetalhes('${receita.id}')">
                        <i class="fas fa-eye"></i> Detalhes
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="gerenciadorReceitas.carregarReceitaNoFormulario('${receita.id}')">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-sm btn-success" onclick="gerenciadorReceitas.clonarReceita('${receita.id}', '${this.escapeHtml(receita.name)}')">
                        <i class="fas fa-copy"></i> Clonar
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="gerenciadorReceitas.abrirDelecao('${receita.id}', '${this.escapeHtml(receita.name)}')">
                        <i class="fas fa-trash"></i> Deletar
                    </button>
                </div>
            `;
            div.appendChild(card);
        });
    }

    abrirNovaReceita() {
        this.receitaSelecionada = null;
        this.limparFormulario();
        const tabEditor = document.getElementById('tab-editor');
        if (tabEditor) tabEditor.click();
    }

    async carregarReceitaNoFormulario(receitaId) {
        try {
            const url = `${this.apiUrl}/${receitaId}`;
            const response = await fetch(url);
            
            if (!response.ok) throw new Error('Erro ao carregar receita');

            const receita = await response.json();
            this.receitaSelecionada = receita;

            // Preencher formulário
            document.getElementById('inputNomeReceita').value = receita.name || '';
            document.getElementById('textareaDescricaoReceita').value = receita.description || '';
            document.getElementById('inputEstiloReceita').value = receita.style || '';
            document.getElementById('inputVolumeReceita').value = receita.volume || 20;
            document.getElementById('inputOGReceita').value = receita.original_gravity || 50;
            document.getElementById('inputFGReceita').value = receita.final_gravity || 10;
            document.getElementById('inputIBUReceita').value = receita.ibu || 0;
            document.getElementById('inputBoilTimeReceita').value = receita.boil_time || 60;
            document.getElementById('selectPlantaReceita').value = receita.plant_id || '';

            // Limpar mash steps antigos
            document.getElementById('divMashSteps').innerHTML = '';

            // Adicionar mash steps
            if (receita.mash_steps && Array.isArray(receita.mash_steps)) {
                receita.mash_steps.forEach(step => {
                    this.adicionarMashStep(step.name, step.temperature, step.duration);
                });
            }

            // Mostrar botão de atualizar
            document.getElementById('btnSalvarReceita').innerHTML = '<i class="fas fa-save"></i> Atualizar Receita';

            this.atualizarResumoReceita();
            document.getElementById('tab-editor').click();
        } catch (error) {
            console.error('Erro ao carregar receita:', error);
            alert('Erro ao carregar receita: ' + error.message);
        }
    }

    adicionarMashStep(nome = '', temperatura = 65, duracao = 60) {
        const container = document.getElementById('divMashSteps');
        if (!container) {
            console.error('Container de mash steps não encontrado!');
            return;
        }
        
        const index = container.children.length;
        
        const item = document.createElement('div');
        item.className = 'list-group-item d-flex gap-2';
        item.innerHTML = `
            <input type="text" class="form-control" placeholder="Nome do passo (ex: Protein Rest)" 
                   value="${nome}" data-nome-${index}>
            <input type="number" class="form-control" placeholder="Temperatura (°C)" 
                   value="${temperatura}" data-temp-${index} min="30" max="78" step="1" style="max-width: 120px;">
            <input type="number" class="form-control" placeholder="Duração (min)" 
                   value="${duracao}" data-dur-${index} min="1" step="1" style="max-width: 100px;">
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="gerenciadorReceitas.removerMashStep(this)">
                <i class="fas fa-trash"></i>
            </button>
        `;
        container.appendChild(item);
    }

    removerMashStep(button) {
        button.closest('.list-group-item').remove();
    }

    coletarMashSteps() {
        const container = document.getElementById('divMashSteps');
        if (!container) {
            console.error('Container de mash steps não encontrado!');
            return [];
        }
        
        const steps = [];

        container.querySelectorAll('.list-group-item').forEach((item, index) => {
            const nomeInput = item.querySelector(`input[data-nome-${index}]`);
            const tempInput = item.querySelector(`input[data-temp-${index}]`);
            const durInput = item.querySelector(`input[data-dur-${index}]`);
            
            const nome = nomeInput?.value || '';
            const temp = parseInt(tempInput?.value || 65);
            const dur = parseInt(durInput?.value || 60);
            
            if (nome && dur > 0) {
                steps.push({
                    name: nome,
                    temperature: temp,
                    duration: dur
                });
            }
        });

        return steps;
    }

    async handleSubmitFormulario(e) {
        e.preventDefault();

        const nome = document.getElementById('inputNomeReceita').value.trim();
        
        if (!nome) {
            alert('Nome da receita é obrigatório');
            return;
        }

        const dados = {
            name: nome,
            description: document.getElementById('textareaDescricaoReceita').value.trim(),
            style: document.getElementById('inputEstiloReceita').value.trim(),
            original_gravity: parseInt(document.getElementById('inputOGReceita').value || 50),
            final_gravity: parseInt(document.getElementById('inputFGReceita').value || 10),
            ibu: parseInt(document.getElementById('inputIBUReceita').value || 0),
            volume: parseInt(document.getElementById('inputVolumeReceita').value || 20),
            boil_time: parseInt(document.getElementById('inputBoilTimeReceita').value || 60),
            mash_steps: this.coletarMashSteps(),
            plant_id: document.getElementById('selectPlantaReceita').value || null,
            ingredients: {
                grains: [],
                hops: [],
                yeast: {},
                misc: []
            },
            boil_additions: []
        };

        try {
            const isAtualizacao = this.receitaSelecionada != null;
            const url = isAtualizacao ? `${this.apiUrl}/${this.receitaSelecionada.id}` : this.apiUrl;
            const metodo = isAtualizacao ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: metodo,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao salvar receita');
            }

            const receita = await response.json();
            
            alert(isAtualizacao ? 'Receita atualizada com sucesso!' : 'Receita criada com sucesso!');
            
            this.limparFormulario();
            this.receitaSelecionada = null;
            await this.carregarReceitas();
            document.getElementById('tab-lista').click();
        } catch (error) {
            console.error('Erro ao salvar receita:', error);
            alert(`Erro: ${error.message}`);
        }
    }

    limparFormulario() {
        document.getElementById('formReceita').reset();
        document.getElementById('divMashSteps').innerHTML = '';
        document.getElementById('btnSalvarReceita').innerHTML = '<i class="fas fa-save"></i> Salvar Receita';
        document.getElementById('selectPlantaReceita').value = '';
        this.receitaSelecionada = null;
        this.atualizarResumoReceita();
    }

    atualizarResumoReceita() {
        const og = parseInt(document.getElementById('inputOGReceita').value || 50);
        const fg = parseInt(document.getElementById('inputFGReceita').value || 10);
        const ibu = parseInt(document.getElementById('inputIBUReceita').value || 0);
        const vol = parseInt(document.getElementById('inputVolumeReceita').value || 20);
        
        // Calcular ABV
        const ogDen = 1.0 + (og / 1000.0);
        const fgDen = 1.0 + (fg / 1000.0);
        const abv = Math.max(0, (ogDen - fgDen) * 131.25);
        
        const resumo = document.getElementById('divResumoReceita');
        if (resumo) {
            resumo.innerHTML = `
                <dl class="row">
                    <dt class="col-sm-6">Volume:</dt>
                    <dd class="col-sm-6"><strong>${vol}L</strong></dd>
                    <dt class="col-sm-6">OG:</dt>
                    <dd class="col-sm-6"><code>${ogDen.toFixed(3)}</code></dd>
                    <dt class="col-sm-6">FG:</dt>
                    <dd class="col-sm-6"><code>${fgDen.toFixed(3)}</code></dd>
                    <dt class="col-sm-6">ABV:</dt>
                    <dd class="col-sm-6"><strong>${abv.toFixed(2)}%</strong></dd>
                    <dt class="col-sm-6">IBU:</dt>
                    <dd class="col-sm-6"><strong>${ibu}</strong></dd>
                </dl>
            `;
        }
    }

    async exibirDetalhes(receitaId) {
        try {
            const response = await fetch(`${this.apiUrl}/${receitaId}`);
            if (!response.ok) throw new Error('Erro ao carregar receita');

            const receita = await response.json();
            this.receitaSelecionada = receita;

            const og = (receita.original_gravity / 1000.0 + 1.0).toFixed(3);
            const fg = (receita.final_gravity / 1000.0 + 1.0).toFixed(3);
            const abv = receita.abv || 0;

            const corpo = document.getElementById('modalCorpoReceita');
            corpo.innerHTML = `
                <h6>Nome:</h6>
                <p>${this.escapeHtml(receita.name)}</p>

                <h6>Descrição:</h6>
                <p>${receita.description ? this.escapeHtml(receita.description) : '<em class="text-muted">Sem descrição</em>'}</p>

                <h6>Parâmetros de Brassagem:</h6>
                <table class="table table-sm">
                    <tr><td>Estilo:</td><td>${receita.style || '-'}</td></tr>
                    <tr><td>OG:</td><td><code>${og}</code></td></tr>
                    <tr><td>FG:</td><td><code>${fg}</code></td></tr>
                    <tr><td>ABV:</td><td><strong>${abv.toFixed(2)}%</strong></td></tr>
                    <tr><td>IBU:</td><td><strong>${receita.ibu}</strong></td></tr>
                    <tr><td>Volume:</td><td>${receita.volume}L</td></tr>
                    <tr><td>Fervura:</td><td>${receita.boil_time}min</td></tr>
                </table>

                <h6>Etapas de Infusão:</h6>
                <table class="table table-sm">
                    <thead><tr><th>Passo</th><th>Temp (°C)</th><th>Duração (min)</th></tr></thead>
                    <tbody>
                        ${this.renderizarMashStepsTable(receita.mash_steps)}
                    </tbody>
                </table>

                <small class="text-muted">
                    Criada em: ${new Date(receita.created_at).toLocaleDateString('pt-BR')} às 
                    ${new Date(receita.created_at).toLocaleTimeString('pt-BR')}
                </small>
            `;

            this.modalDetalhes.show();
        } catch (error) {
            console.error('Erro ao carregar detalhes da receita:', error);
            alert('Erro ao carregar detalhes da receita: ' + error.message);
        }
    }

    renderizarMashStepsTable(steps) {
        if (!steps || steps.length === 0) {
            return '<tr><td colspan="3" class="text-center text-muted">Nenhum passo definido</td></tr>';
        }

        let html = '';
        steps.forEach(step => {
            html += `<tr><td>${this.escapeHtml(step.name)}</td><td>${step.temperature}°C</td><td>${step.duration}min</td></tr>`;
        });
        return html;
    }

    abrirDelecao(receitaId, nomeReceita) {
        this.receitaSelecionada = { id: receitaId };
        document.getElementById('nomeReceitaDelecao').textContent = nomeReceita;
        this.modalDelecao.show();
    }

    async confirmarDelecao() {
        if (!this.receitaSelecionada) {
            console.error('Nenhuma receita selecionada para deletar!');
            return;
        }

        try {
            const url = `${this.apiUrl}/${this.receitaSelecionada.id}`;
            
            const response = await fetch(url, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao deletar receita');
            }

            alert('Receita deletada com sucesso!');
            this.modalDelecao.hide();
            await this.carregarReceitas();
        } catch (error) {
            console.error('Erro ao deletar receita:', error);
            alert(`Erro: ${error.message}`);
        }
    }

    async clonarReceita(receitaId, nomeOriginal) {
        const novoNome = prompt(`Nova receita clonada de "${nomeOriginal}":\n\nDigite o novo nome:`, `${nomeOriginal} (cópia)`);
        
        if (!novoNome) return;

        try {
            const response = await fetch(`${this.apiUrl}/${receitaId}/clone`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: novoNome })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao clonar receita');
            }

            alert('Receita clonada com sucesso!');
            await this.carregarReceitas();
        } catch (error) {
            console.error('Erro ao clonar receita:', error);
            alert(`Erro: ${error.message}`);
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Instanciar globalmente
let gerenciadorReceitas;

document.addEventListener('DOMContentLoaded', () => {
    gerenciadorReceitas = new GerenciadorReceitas();
});
