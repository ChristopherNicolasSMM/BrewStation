class SistemaEstoque {
    constructor() {
        this.baseUrl = '/api/estoque';
        this.dadosFormulario = { ingredientes: [], lotes: [] };
        this.estoqueAtual = [];
        this.movimentacoes = [];
        this.custos = [];
        this.charts = { valor: null, status: null };
        this.init();
    }

    async init() {
        try {
            await this.carregarDadosFormulario();
            await Promise.all([
                this.carregarResumo(),
                this.carregarEstoqueAtual()
            ]);
            this.configurarEventos();
        } catch (error) {
            console.error('Erro ao inicializar sistema de estoque:', error);
            this.mostrarErro('Erro ao carregar sistema de estoque');
        }
    }

    async carregarDadosFormulario() {
        try {
            const response = await fetch(`${this.baseUrl}/dados-formulario`);
            const data = await response.json();

            if (data.success) {
                this.dadosFormulario = data;
                this.preencherSelectIngredientes();
            }
        } catch (error) {
            console.error('Erro ao carregar dados do formulário:', error);
        }
    }

    preencherSelectIngredientes() {
        const select = document.getElementById('ingredienteSelect');
        if (!select) return;

        select.innerHTML = '<option value="">Selecione um ingrediente</option>';

        (this.dadosFormulario.ingredientes || []).forEach(ingrediente => {
            const option = document.createElement('option');
            option.value = ingrediente.id;
            option.textContent = `${ingrediente.nome} (${this.formatarTipo(ingrediente.tipo)})`;
            option.dataset.tipo = ingrediente.tipo;
            option.dataset.unidade = ingrediente.unidade_medida;
            select.appendChild(option);
        });
    }

    atualizarCamposIngrediente(ingredienteId) {
        const ingrediente = (this.dadosFormulario.ingredientes || []).find(i => i.id == ingredienteId);
        const tipoInput = document.getElementById('tipoIngrediente');
        const unidadeSelect = document.getElementById('unidadeMedida');

        if (tipoInput) tipoInput.value = ingrediente ? ingrediente.tipo : '';
        if (unidadeSelect && ingrediente?.unidade_medida) {
            unidadeSelect.value = ingrediente.unidade_medida;
        }
    }

    async carregarResumo() {
        try {
            const response = await fetch(`${this.baseUrl}/relatorios/resumo`);
            const data = await response.json();

            if (data.success) {
                const resumo = data.resumo;
                document.getElementById('totalItens').textContent = resumo.total_ingredientes;
                document.getElementById('itensBaixoEstoque').textContent = resumo.itens_estoque_baixo;
                document.getElementById('valorTotalEstoque').textContent = this.formatarMoeda(resumo.valor_total_estoque);
                document.getElementById('itensEsgotados').textContent = resumo.itens_esgotados;
                document.getElementById('movimentacoesMes').textContent = resumo.movimentacoes_30_dias;
                document.getElementById('itensCriticos').textContent = resumo.itens_estoque_baixo;
            }
        } catch (error) {
            console.error('Erro ao carregar resumo:', error);
        }
    }

    async carregarEstoqueAtual(filtros = {}) {
        try {
            const params = new URLSearchParams();
            Object.entries(filtros).forEach(([key, value]) => {
                if (value !== undefined && value !== null && value !== '') {
                    params.append(key, value);
                }
            });
            const query = params.toString();
            const url = query ? `${this.baseUrl}/atual?${query}` : `${this.baseUrl}/atual`;
            const response = await fetch(url);
            const data = await response.json();

            if (data.success) {
                this.estoqueAtual = data.estoque || [];
                this.renderizarTabelaEstoque(this.estoqueAtual);
            }
        } catch (error) {
            console.error('Erro ao carregar estoque atual:', error);
        }
    }

    renderizarTabelaEstoque(estoque) {
        const tbody = document.querySelector('#tabelaEstoque tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!estoque.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">
                        <i class="bi bi-inbox display-4"></i>
                        <p class="mt-2 mb-0">Nenhum item em estoque</p>
                    </td>
                </tr>`;
            return;
        }

        estoque.forEach(item => {
            const tr = document.createElement('tr');
            tr.className = `estoque-${item.status_estoque}`;
            const statusClass = {
                ok: 'success',
                baixo: 'warning',
                critico: 'danger',
                esgotado: 'secondary'
            }[item.status_estoque] || 'secondary';

            tr.innerHTML = `
                <td>
                    <strong>${item.ingrediente_nome}</strong>
                    ${item.ingrediente_tipo ? `<br><small class="text-muted">${this.formatarTipo(item.ingrediente_tipo)}</small>` : ''}
                </td>
                <td>${this.formatarTipo(item.ingrediente_tipo)}</td>
                <td>
                    <div class="d-flex align-items-center">
                        <strong>${item.quantidade_atual} ${item.unidade_medida}</strong>
                        ${item.estoque_minimo > 0 ? `
                            <div class="progress ms-2" style="width: 80px; height: 6px;">
                                <div class="progress-bar bg-${statusClass}" style="width: ${Math.min((item.quantidade_atual / item.estoque_minimo) * 100, 100)}%"></div>
                            </div>
                        ` : ''}
                    </div>
                </td>
                <td>${item.estoque_minimo} ${item.unidade_medida}</td>
                <td>${this.formatarMoeda(item.custo_medio)}/${item.unidade_medida}</td>
                <td><strong>${this.formatarMoeda(item.valor_total_estoque)}</strong></td>
                <td>
                    <span class="badge bg-${statusClass}">${this.formatarStatusEstoque(item.status_estoque)}</span>
                </td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="abrirModalMovimentacao(${item.ingrediente_id})" title="Registrar movimentação">
                        <i class="bi bi-arrow-left-right"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-info" onclick="sistemaEstoque.verHistorico(${item.ingrediente_id})" title="Ver histórico">
                        <i class="bi bi-clock-history"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    configurarEventos() {
        document.getElementById('filtroTipo')?.addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtroStatus')?.addEventListener('change', () => this.aplicarFiltros());
        document.getElementById('filtroNome')?.addEventListener('input', () => this.aplicarFiltros());
        document.getElementById('ingredienteSelect')?.addEventListener('change', (e) => this.atualizarCamposIngrediente(e.target.value));

        document.getElementById('movimentacoes-tab')?.addEventListener('click', () => this.carregarMovimentacoes());
        document.getElementById('custos-tab')?.addEventListener('click', () => this.carregarCustosProducao());
        document.getElementById('relatorios-tab')?.addEventListener('click', () => this.carregarRelatorios());

        this.configurarCalculoCustoTotal();
    }

    configurarCalculoCustoTotal() {
        const quantidade = document.getElementById('quantidade');
        const custoUnitario = document.getElementById('custoUnitario');
        const custoTotalEl = document.getElementById('custoTotalCalculado');

        if (!quantidade || !custoUnitario || !custoTotalEl) return;

        const atualizar = () => {
            const qtd = parseFloat(quantidade.value) || 0;
            const custo = parseFloat(custoUnitario.value) || 0;
            custoTotalEl.textContent = this.formatarMoeda(qtd * custo);
        };

        quantidade.oninput = atualizar;
        custoUnitario.oninput = atualizar;
    }

    aplicarFiltros() {
        const filtros = {}}