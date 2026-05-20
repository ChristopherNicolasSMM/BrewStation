/**
 * Gerenciamento de Plantas (Equipamentos de Brassagem)
 * 
 * Interface para criar, editar, listar e deletar plants no Mash Control.
 * Uma plant representa um equipamento físico com sensores e atuadores mapeados
 * para funções lógicas.
 */

class GerenciadorPlants {
    constructor() {
        this.apiUrl = '/api/mash_control/plants';
        this.actorsApiUrl = '/api/device_manager/actors';
        this.plantSelecionada = null;
        this.modalDetalhes = null;
        this.modalDelecao = null;
        this.actors = [];       // cache de atores disponíveis
        this.inicializar();
    }

    inicializar() {
        try {
            // Inicializar modais
            const modalDetalhesEl = document.getElementById('modalDetalhesPlanta');
            const modalDelecaoEl = document.getElementById('modalConfirmarDelecao');

            this.modalDetalhes = new bootstrap.Modal(modalDetalhesEl);
            this.modalDelecao = new bootstrap.Modal(modalDelecaoEl);

            // Registrar event listeners
            this.registrarEventos();

            // Carregar atores disponíveis primeiro, depois plantas
            this.carregarAtoresDisponiveis();
        } catch (error) {
            console.error('Erro ao inicializar GerenciadorPlants:', error);
        }
    }

    /**
     * Busca todos os atores disponíveis via DeviceAPI e armazena em cache.
     */
    async carregarAtoresDisponiveis() {
        try {
            const response = await fetch(this.actorsApiUrl);
            if (response.ok) {
                const data = await response.json();
                this.actors = data.actors || [];
            } else {
                console.warn('Não foi possível carregar atores do Device Manager');
                this.actors = [];
            }
        } catch (error) {
            console.warn('Erro ao carregar atores:', error);
            this.actors = [];
        }

        // Carregar plantas (independente do resultado dos atores)
        this.carregarPlants();
    }

    /**
     * Retorna HTML de um <select> populado com os atores disponíveis,
     * filtrados opcionalmente por tipo.
     */
    renderizarDropdownAtores(selectedDeviceId = '', role = 'temperature_sensor') {
        if (!this.actors || this.actors.length === 0) {
            return `<input type="text" class="form-control" placeholder="ID do Dispositivo (ex: dev_001)"
                           value="${this.escapeHtml(selectedDeviceId)}" data-device>`;
        }

        let html = `<select class="form-select" data-role-device-select="${role}">
                        <option value="">— Selecione um ator —</option>`;

        // Agrupar atores por tipo
        const atoresPorTipo = {};
        for (const actor of this.actors) {
            if (!actor.is_active) continue;
            const tipo = actor.actor_type || 'outro';
            if (!atoresPorTipo[tipo]) atoresPorTipo[tipo] = [];
            atoresPorTipo[tipo].push(actor);
        }

        const rotulos = { sensor: 'Sensores', actuator: 'Atuadores', rule_trigger: 'Gatilhos', hybrid: 'Híbridos' };

        for (const [tipo, atores] of Object.entries(atoresPorTipo)) {
            html += `<optgroup label="${rotulos[tipo] || tipo}">`;
            for (const actor of atores) {
                const selected = actor.id === selectedDeviceId || actor.device_id === selectedDeviceId ? 'selected' : '';
                html += `<option value="${actor.id}" ${selected}>
                            ${this.escapeHtml(actor.name)} (${actor.id})
                         </option>`;
            }
            html += `</optgroup>`;
        }

        html += `</select>`;
        return html;
    }

    registrarEventos() {
        try {
            const btnNovaPlanta = document.getElementById('btnNovaPlanta');
            const linkNovaPlantaVazio = document.getElementById('linkNovaPlantaVazio');
            const formPlanta = document.getElementById('formPlanta');
            const btnLimparFormulario = document.getElementById('btnLimparFormulario');
            const btnAdicionarMapeamento = document.getElementById('btnAdicionarMapeamento');
            const btnEditarNaModal = document.getElementById('btnEditarNaModal');
            const btnConfirmarDelecao = document.getElementById('btnConfirmarDelecao');
            
            // Botão nova planta
            if (btnNovaPlanta) {
                btnNovaPlanta.addEventListener('click', () => {
                    this.abrirNovaPlanta();
                });
            }
            
            if (linkNovaPlantaVazio) {
                linkNovaPlantaVazio.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.abrirNovaPlanta();
                });
            }

            // Formulário
            if (formPlanta) {
                formPlanta.addEventListener('submit', (e) => {
                    this.handleSubmitFormulario(e);
                });
            }
            
            if (btnLimparFormulario) {
                btnLimparFormulario.addEventListener('click', () => {
                    this.limparFormulario();
                });
            }
            
            if (btnAdicionarMapeamento) {
                btnAdicionarMapeamento.addEventListener('click', () => {
                    this.adicionarMapeamento();
                });
            }

            // Modal de edição
            if (btnEditarNaModal) {
                btnEditarNaModal.addEventListener('click', () => {
                    if (this.plantSelecionada) {
                        this.carregarPlantaNoFormulario(this.plantSelecionada);
                        this.modalDetalhes.hide();
                        // Mudar para aba editor
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
        } catch (error) {
            console.error('Erro ao registrar eventos de plantas:', error);
        }
    }

    async carregarPlants() {
        try {
            const response = await fetch(this.apiUrl);
            
            if (!response.ok) {
                console.error('Erro ao carregar plantas. Status:', response.status);
                return;
            }

            const plants = await response.json();
            
            const divCarregando = document.getElementById('divCarregandoPlants');
            const divVazio = document.getElementById('divPlantasVazio');
            
            if (divCarregando) divCarregando.style.display = 'none';

            if (plants.length === 0) {
                if (divVazio) divVazio.style.display = 'block';
            } else {
                if (divVazio) divVazio.style.display = 'none';
                this.renderizarPlants(plants);
            }
        } catch (error) {
            console.error('Erro ao carregar plantas:', error);
            const div = document.getElementById('divCarregandoPlants');
            if (div) {
                div.innerHTML = '<div class="alert alert-danger">Erro ao carregar plantas. Tente novamente.</div>';
            }
        }
    }

    renderizarPlants(plants) {
        const div = document.getElementById('divPlantas');
        
        if (!div) {
            console.error('Elemento divPlantas não encontrado!');
            return;
        }
        
        div.innerHTML = '';
        
        plants.forEach((plant, index) => {
            const card = document.createElement('div');
            card.className = 'card mb-3';
            card.innerHTML = `
                <div class="card-header d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="mb-0">${this.escapeHtml(plant.name)}</h5>
                        <small class="text-muted">${plant.description || 'Sem descrição'}</small>
                    </div>
                    <div>
                        <span class="badge ${plant.is_active ? 'bg-success' : 'bg-danger'}">
                            ${plant.is_active ? 'Ativa' : 'Inativa'}
                        </span>
                    </div>
                </div>
                <div class="card-body">
                    <h6>Mapeamento de Dispositivos:</h6>
                    <dl class="row">
                        ${this.renderizarDeviceRoles(plant.device_roles)}
                    </dl>
                    <small class="text-muted">
                        Criada em: ${new Date(plant.created_at).toLocaleDateString('pt-BR')}
                    </small>
                </div>
                <div class="card-footer">
                    <button class="btn btn-sm btn-info" onclick="gerenciador.exibirDetalhes('${plant.id}')">
                        <i class="fas fa-eye"></i> Detalhes
                    </button>
                    <button class="btn btn-sm btn-warning" onclick="gerenciador.carregarPlantaNoFormulario('${plant.id}')">
                        <i class="fas fa-edit"></i> Editar
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="gerenciador.abrirDelecao('${plant.id}', '${this.escapeHtml(plant.name)}')">
                        <i class="fas fa-trash"></i> Deletar
                    </button>
                </div>
            `;
            div.appendChild(card);
        });
    }

    renderizarDeviceRoles(deviceRoles) {
        if (!deviceRoles || Object.keys(deviceRoles).length === 0) {
            return '<dt class="col-sm-6">Nenhum mapeamento</dt><dd class="col-sm-6"><span class="badge bg-warning">Configure agora</span></dd>';
        }

        let html = '';
        for (const [role, deviceId] of Object.entries(deviceRoles)) {
            html += `<dt class="col-sm-6">${this.escapeHtml(role)}</dt><dd class="col-sm-6"><code>${this.escapeHtml(deviceId)}</code></dd>`;
        }
        return html;
    }

    abrirNovaPlanta() {
        this.plantSelecionada = null;
        this.limparFormulario();
        const tabEditor = document.getElementById('tab-editor');
        if (tabEditor) tabEditor.click();
    }

    async carregarPlantaNoFormulario(plantId) {
        try {
            const url = `${this.apiUrl}/${plantId}`;
            const response = await fetch(url);
            
            if (!response.ok) throw new Error('Erro ao carregar plant');

            const plant = await response.json();
            this.plantSelecionada = plant;

            // Preencher formulário
            document.getElementById('inputNomePlanta').value = plant.name || '';
            document.getElementById('textareaDescricaoPlanta').value = plant.description || '';
            document.getElementById('inputStatusPlanta').value = plant.is_active ? 'true' : 'false';

            // Limpar mapeamentos antigos
            document.getElementById('divMapeamentosDispositivos').innerHTML = '';

            // Adicionar mapeamentos
            if (plant.device_roles && typeof plant.device_roles === 'object') {
                for (const [role, deviceId] of Object.entries(plant.device_roles)) {
                    this.adicionarMapeamento(role, deviceId);
                }
            }

            // Mostrar botão de atualizar
            document.getElementById('btnSalvarPlanta').innerHTML = '<i class="fas fa-save"></i> Atualizar Planta';

            // Ir para aba editor
            document.getElementById('tab-editor').click();
        } catch (error) {
            console.error('Erro ao carregar plant:', error);
            alert('Erro ao carregar plant: ' + error.message);
        }
    }

    adicionarMapeamento(role = '', deviceId = '') {
        const container = document.getElementById('divMapeamentosDispositivos');
        if (!container) {
            console.error('Container de mapeamentos não encontrado!');
            return;
        }

        const index = container.children.length;

        const item = document.createElement('div');
        item.className = 'list-group-item d-flex gap-2 align-items-center';
        item.innerHTML = `
            <input type="text" class="form-control" placeholder="Função (ex: temperature_sensor)"
                   value="${role}" data-role="${index}" style="max-width: 250px;">
            ${this.renderizarDropdownAtores(deviceId, role)}
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="gerenciador.removerMapeamento(this)">
                <i class="fas fa-trash"></i>
            </button>
        `;
        container.appendChild(item);
    }

    removerMapeamento(button) {
        button.closest('.list-group-item').remove();
    }

    coletarMapeamentos() {
        const container = document.getElementById('divMapeamentosDispositivos');
        if (!container) {
            console.error('Container de mapeamentos não encontrado!');
            return {};
        }

        const mapeamentos = {};

        container.querySelectorAll('.list-group-item').forEach((item) => {
            const roleInput = item.querySelector('input[data-role]');
            const deviceSelect = item.querySelector('select[data-role-device-select]');
            const deviceInput = item.querySelector('input[data-device]');

            const role = roleInput?.value?.trim() || '';
            let device = '';

            if (deviceSelect) {
                device = deviceSelect.value;
            } else if (deviceInput) {
                device = deviceInput.value?.trim() || '';
            }

            if (role && device) {
                mapeamentos[role] = device;
            }
        });

        return mapeamentos;
    }

    async handleSubmitFormulario(e) {
        e.preventDefault();

        const nome = document.getElementById('inputNomePlanta').value.trim();
        
        if (!nome) {
            alert('Nome da planta é obrigatório');
            return;
        }

        const dados = {
            name: nome,
            description: document.getElementById('textareaDescricaoPlanta').value.trim(),
            device_roles: this.coletarMapeamentos(),
            is_active: document.getElementById('inputStatusPlanta').value === 'true'
        };

        try {
            const isAtualizacao = this.plantSelecionada != null;
            const url = isAtualizacao ? `${this.apiUrl}/${this.plantSelecionada.id}` : this.apiUrl;
            const metodo = isAtualizacao ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: metodo,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao salvar plant');
            }

            const plant = await response.json();
            
            alert(isAtualizacao ? 'Plant atualizada com sucesso!' : 'Plant criada com sucesso!');
            
            this.limparFormulario();
            this.plantSelecionada = null;
            await this.carregarPlants();
            document.getElementById('tab-lista').click();
        } catch (error) {
            console.error('Erro ao salvar plant:', error);
            alert(`Erro: ${error.message}`);
        }
    }

    limparFormulario() {
        document.getElementById('formPlanta').reset();
        document.getElementById('divMapeamentosDispositivos').innerHTML = '';
        document.getElementById('btnSalvarPlanta').innerHTML = '<i class="fas fa-save"></i> Salvar Planta';
        this.plantSelecionada = null;
    }

    async exibirDetalhes(plantId) {
        try {
            const response = await fetch(`${this.apiUrl}/${plantId}`);
            if (!response.ok) throw new Error('Erro ao carregar plant');

            const plant = await response.json();
            this.plantSelecionada = plant;

            const corpo = document.getElementById('modalCorpo');
            corpo.innerHTML = `
                <h6>Nome:</h6>
                <p>${this.escapeHtml(plant.name)}</p>

                <h6>Descrição:</h6>
                <p>${plant.description ? this.escapeHtml(plant.description) : '<em class="text-muted">Sem descrição</em>'}</p>

                <h6>Status:</h6>
                <p>
                    <span class="badge ${plant.is_active ? 'bg-success' : 'bg-danger'}">
                        ${plant.is_active ? 'Ativa' : 'Inativa'}
                    </span>
                </p>

                <h6>Mapeamento de Dispositivos:</h6>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Função</th>
                            <th>Dispositivo</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.renderizarDeviceRolesEmTabela(plant.device_roles)}
                    </tbody>
                </table>

                <small class="text-muted">
                    Criada em: ${new Date(plant.created_at).toLocaleDateString('pt-BR')} às 
                    ${new Date(plant.created_at).toLocaleTimeString('pt-BR')}
                </small>
            `;

            this.modalDetalhes.show();
        } catch (error) {
            console.error('Erro ao carregar detalhes da plant:', error);
            alert('Erro ao carregar detalhes da plant: ' + error.message);
        }
    }

    renderizarDeviceRolesEmTabela(deviceRoles) {
        if (!deviceRoles || Object.keys(deviceRoles).length === 0) {
            return '<tr><td colspan="2" class="text-center text-muted">Nenhum mapeamento</td></tr>';
        }

        let html = '';
        for (const [role, deviceId] of Object.entries(deviceRoles)) {
            html += `<tr><td>${this.escapeHtml(role)}</td><td><code>${this.escapeHtml(deviceId)}</code></td></tr>`;
        }
        return html;
    }

    abrirDelecao(plantId, nomePlanta) {
        this.plantSelecionada = { id: plantId };
        document.getElementById('nomePlantaDelecao').textContent = nomePlanta;
        this.modalDelecao.show();
    }

    async confirmarDelecao() {
        if (!this.plantSelecionada) {
            console.error('Nenhuma planta selecionada para deletar!');
            return;
        }

        try {
            const url = `${this.apiUrl}/${this.plantSelecionada.id}`;
            
            const response = await fetch(url, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || 'Erro ao deletar plant');
            }

            alert('Plant deletada com sucesso!');
            this.modalDelecao.hide();
            await this.carregarPlants();
        } catch (error) {
            console.error('Erro ao deletar plant:', error);
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
let gerenciador;

document.addEventListener('DOMContentLoaded', () => {
    gerenciador = new GerenciadorPlants();
});