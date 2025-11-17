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
        const filtros = {
            tipo: document.getElementById('filtroTipo').value,
            status: document.getElementById('filtroStatus').value,
            nome: document.getElementById('filtroNome')?.value?.trim()
        };
        this.carregarEstoqueAtual(filtros);
    }

    abrirModalMovimentacao(ingredienteId = null) {
        const modalEl = document.getElementById('modalMovimentacao');
        if (!modalEl) return;

        const form = document.getElementById('formMovimentacao');
        form?.reset();
        this.preencherSelectIngredientes();

        if (ingredienteId) {
            document.getElementById('ingredienteSelect').value = ingredienteId;
            this.atualizarCamposIngrediente(ingredienteId);
        } else {
            this.atualizarCamposIngrediente(document.getElementById('ingredienteSelect').value);
        }

        new bootstrap.Modal(modalEl).show();
    }

    async salvarMovimentacao() {
        try {
            const formData = {
                ingrediente_id: document.getElementById('ingredienteSelect').value,
                tipo_ingrediente: document.getElementById('tipoIngrediente').value,
                tipo_movimentacao: document.getElementById('tipoMovimentacao').value,
                quantidade: parseFloat(document.getElementById('quantidade').value) || 0,
                unidade_medida: document.getElementById('unidadeMedida').value,
                custo_unitario: parseFloat(document.getElementById('custoUnitario').value) || null,
                lote_fornecedor: document.getElementById('loteFornecedor').value,
                data_validade: document.getElementById('dataValidade').value,
                observacoes: document.getElementById('observacoesMovimentacao').value
            };

            const response = await fetch(`${this.baseUrl}/movimentacoes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalMovimentacao'))?.hide();
                this.mostrarMensagem('Movimentação registrada com sucesso!', 'success');
                await Promise.all([this.carregarEstoqueAtual(), this.carregarResumo()]);
                if (document.getElementById('movimentacoes-tab')?.classList.contains('active')) {
                    this.carregarMovimentacoes();
                }
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Erro ao salvar movimentação:', error);
            this.mostrarErro(`Erro ao salvar movimentação: ${error.message}`);
        }
    }

    async carregarMovimentacoes(filtros = {}) {
        try {
            const params = new URLSearchParams(filtros);
            const response = await fetch(`${this.baseUrl}/movimentacoes?${params.toString()}`);
            const data = await response.json();

            if (data.success) {
                this.movimentacoes = data.movimentacoes || [];
                this.renderizarMovimentacoes(this.movimentacoes);
            }
        } catch (error) {
            console.error('Erro ao carregar movimentações:', error);
        }
    }

    renderizarMovimentacoes(movimentacoes) {
        const tbody = document.querySelector('#tabelaMovimentacoes tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!movimentacoes.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted py-4">
                        <i class="bi bi-inbox display-4"></i>
                        <p class="mt-2 mb-0">Nenhuma movimentação registrada</p>
                    </td>
                </tr>`;
            return;
        }

        movimentacoes.forEach(mov => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${mov.data_movimentacao ? new Date(mov.data_movimentacao).toLocaleDateString('pt-BR') : '-'}</td>
                <td>${mov.ingrediente_nome || '-'}</td>
                <td>${this.formatarTipo(mov.ingrediente_tipo)}</td>
                <td>${mov.quantidade} ${mov.unidade_medida}</td>
                <td>${this.formatarMoeda(mov.custo_unitario || 0)}</td>
                <td>${this.formatarMoeda(mov.custo_total || 0)}</td>
                <td>${mov.lote_fornecedor || '-'}</td>
                <td>${mov.usuario_nome || '-'}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    verHistorico(ingredienteId) {
        const ingrediente = (this.dadosFormulario.ingredientes || []).find(i => i.id === ingredienteId);
        const filtros = { ingrediente_id: ingredienteId };
        if (ingrediente) filtros.tipo_ingrediente = ingrediente.tipo;

        const tabTrigger = document.querySelector('#movimentacoes-tab');
        if (tabTrigger) new bootstrap.Tab(tabTrigger).show();

        this.carregarMovimentacoes(filtros);
    }

    async carregarCustosProducao() {
        try {
            const response = await fetch(`${this.baseUrl}/custos-producao`);
            const data = await response.json();

            if (data.success) {
                this.custos = data.custos || [];
                this.renderizarCustos(this.custos);
            }
        } catch (error) {
            console.error('Erro ao carregar custos de produção:', error);
        }
    }

    renderizarCustos(custos) {
        const tbody = document.querySelector('#tabelaCustos tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!custos.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="10" class="text-center text-muted py-4">
                        <i class="bi bi-inbox display-4"></i>
                        <p class="mt-2 mb-0">Nenhum custo calculado</p>
                    </td>
                </tr>`;
            return;
        }

        custos.forEach(custo => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${custo.lote_nome || '-'}</td>
                <td>${custo.quantidade_produzida || 0} L</td>
                <td>${this.formatarMoeda(custo.custo_ingredientes)}</td>
                <td>${this.formatarMoeda(custo.custo_embalagens)}</td>
                <td>${this.formatarMoeda(custo.custo_operacional)}</td>
                <td><strong>${this.formatarMoeda(custo.custo_total)}</strong></td>
                <td>${this.formatarMoeda(custo.custo_por_litro || 0)}</td>
                <td>${this.formatarMoeda(custo.preco_venda_sugerido || 0)}</td>
                <td>${custo.margem_lucro || 0}%</td>
                <td class="table-actions">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="sistemaEstoque.recalcularCusto(${custo.lote_id})">
                        <i class="bi bi-arrow-repeat"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-secondary" onclick="sistemaEstoque.abrirModalCustoProducao(${custo.id})">
                        <i class="bi bi-eye"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    abrirModalCustoProducao(custoId) {
        const modalEl = document.getElementById('modalCustoProducao');
        if (!modalEl) return;

        const custo = this.custos.find(c => c.id === custoId);
        if (!custo) {
            this.mostrarErro('Não foi possível localizar os dados do custo.');
            return;
        }

        document.getElementById('custoProducaoId').value = custo.id;
        document.getElementById('custoProducaoLoteId').value = custo.lote_id;
        document.getElementById('custoProducaoLoteNome').value = custo.lote_nome || '';
        document.getElementById('quantidadeProduzida').value = custo.quantidade_produzida || '';
        document.getElementById('custoIngredientes').value = custo.custo_ingredientes || '';
        document.getElementById('custoEmbalagens').value = custo.custo_embalagens || '';
        document.getElementById('custoOperacional').value = custo.custo_operacional || '';
        document.getElementById('custoMaoObra').value = custo.custo_mao_obra || '';
        document.getElementById('custoDepreciacao').value = custo.custo_depreciacao || '';
        document.getElementById('margemLucro').value = custo.margem_lucro || 0;
        document.getElementById('custoTotalCalculado').value = this.formatarMoeda(custo.custo_total || 0);
        document.getElementById('custoPorLitroCalculado').textContent = this.formatarMoeda(custo.custo_por_litro || 0);
        document.getElementById('precoVendaSugerido').textContent = this.formatarMoeda(custo.preco_venda_sugerido || 0);

        new bootstrap.Modal(modalEl).show();
    }

    async salvarCustoProducao() {
        try {
            const custoId = document.getElementById('custoProducaoId').value;
            if (!custoId) return;

            const formData = {
                quantidade_produzida: parseFloat(document.getElementById('quantidadeProduzida').value) || 0,
                custo_ingredientes: parseFloat(document.getElementById('custoIngredientes').value) || 0,
                custo_embalagens: parseFloat(document.getElementById('custoEmbalagens').value) || 0,
                custo_operacional: parseFloat(document.getElementById('custoOperacional').value) || 0,
                custo_mao_obra: parseFloat(document.getElementById('custoMaoObra').value) || 0,
                custo_depreciacao: parseFloat(document.getElementById('custoDepreciacao').value) || 0,
                margem_lucro: parseFloat(document.getElementById('margemLucro').value) || 0
            };

            const response = await fetch(`${this.baseUrl}/custos-producao/${custoId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalCustoProducao'))?.hide();
                this.mostrarMensagem('Custo atualizado com sucesso!', 'success');
                await Promise.all([this.carregarCustosProducao(), this.carregarResumo()]);
            } else {
                throw new Error(data.error);
            }
        } catch (error) {
            console.error('Erro ao salvar custo de produção:', error);
            this.mostrarErro(`Erro ao salvar custo: ${error.message}`);
        }
    }

    async recalcularCusto(loteId, showToast = true) {
        try {
            const response = await fetch(`${this.baseUrl}/calcular-custo/${loteId}`);
            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error);
            }

            if (showToast) {
                this.mostrarMensagem('Custo recalculado com sucesso!', 'success');
            }
            await Promise.all([this.carregarCustosProducao(), this.carregarResumo()]);
        } catch (error) {
            console.error('Erro ao recalcular custo:', error);
            this.mostrarErro('Erro ao recalcular custo');
        }
    }

    async calcularTodosCustos() {
        const button = document.querySelector('#custos button[onclick="calcularTodosCustos()"]');
        if (button) button.disabled = true;

        try {
            for (const lote of this.dadosFormulario.lotes || []) {
                await this.recalcularCusto(lote.id, false);
            }
            this.mostrarMensagem('Custos recalculados com sucesso!', 'success');
            await this.carregarCustosProducao();
        } catch (error) {
            console.error('Erro ao recalcular todos os custos:', error);
            this.mostrarErro('Erro ao recalcular todos os custos');
        } finally {
            if (button) button.disabled = false;
        }
    }

    async carregarRelatorios() {
        await Promise.all([
            this.carregarGraficoValorEstoque(),
            this.carregarGraficoStatusEstoque(),
            this.carregarRelatorioReposicao()
        ]);
    }

    async carregarGraficoValorEstoque() {
        try {
            const response = await fetch(`${this.baseUrl}/relatorios/valor-estoque`);
            const data = await response.json();

            if (data.success) {
                this.renderizarGraficoValorEstoque(data.dados);
            }
        } catch (error) {
            console.error('Erro ao carregar gráfico de valor:', error);
        }
    }

    renderizarGraficoValorEstoque(dados) {
        const container = document.getElementById('graficoValorEstoque');
        if (!container) return;
        container.innerHTML = '<canvas></canvas>';
        const ctx = container.querySelector('canvas').getContext('2d');

        this.charts.valor?.destroy();
        this.charts.valor = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: dados.map(item => this.formatarTipo(item.tipo)),
                datasets: [{
                    data: dados.map(item => item.valor_total),
                    backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                const valor = context.raw;
                                const total = dados.reduce((sum, item) => sum + item.valor_total, 0);
                                const percentual = total ? ((valor / total) * 100).toFixed(1) : 0;
                                return `${context.label}: ${this.formatarMoeda(valor)} (${percentual}%)`;
                            }
                        }
                    }
                }
            }
        });
    }

    async carregarGraficoStatusEstoque() {
        if (!this.estoqueAtual.length) {
            await this.carregarEstoqueAtual();
        }

        const statusCounts = this.estoqueAtual.reduce((acc, item) => {
            acc[item.status_estoque] = (acc[item.status_estoque] || 0) + 1;
            return acc;
        }, {});

        const container = document.getElementById('graficoStatusEstoque');
        if (!container) return;
        container.innerHTML = '<canvas></canvas>';
        const ctx = container.querySelector('canvas').getContext('2d');

        this.charts.status?.destroy();
        this.charts.status = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(statusCounts).map(status => this.formatarStatusEstoque(status)),
                datasets: [{
                    data: Object.values(statusCounts),
                    backgroundColor: ['#28a745', '#ffc107', '#dc3545', '#6c757d']
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { position: 'bottom' } }
            }
        });
    }

    async carregarRelatorioReposicao() {
        if (!this.estoqueAtual.length) {
            await this.carregarEstoqueAtual();
        }

        const itens = this.estoqueAtual.filter(item => ['critico', 'baixo', 'esgotado'].includes(item.status_estoque));
        const tbody = document.querySelector('#tabelaReposicao tbody');
        if (!tbody) return;
        tbody.innerHTML = '';

        if (!itens.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        Todos os estoques estão saudáveis 🎉
                    </td>
                </tr>`;
            return;
        }

        itens.forEach(item => {
            const deficit = Math.max((item.estoque_minimo || 0) - (item.quantidade_atual || 0), 0);
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${item.ingrediente_nome}</td>
                <td>${item.quantidade_atual} ${item.unidade_medida}</td>
                <td>${item.estoque_minimo || 0} ${item.unidade_medida}</td>
                <td>${deficit.toFixed(2)} ${item.unidade_medida}</td>
                <td>${item.detalhes?.ultima_compra || '-'}</td>
                <td>${item.detalhes?.fornecedor || '-'}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="abrirModalMovimentacao(${item.ingrediente_id})">
                        Solicitar
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    }

    formatarTipo(tipo) {
        const tipos = { malte: 'Malte', lupulo: 'Lúpulo', levedura: 'Levedura', adjunto: 'Adjunto' };
        return tipos[tipo] || (tipo ? tipo.charAt(0).toUpperCase() + tipo.slice(1) : '-');
    }

    formatarStatusEstoque(status) {
        const mapa = { ok: 'OK', baixo: 'Baixo', critico: 'Crítico', esgotado: 'Esgotado' };
        return mapa[status] || status;
    }

    formatarMoeda(valor) {
        return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(valor || 0);
    }

    mostrarMensagem(mensagem, tipo) {
        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
        alerta.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 1055; min-width: 300px;';
        alerta.innerHTML = `
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(alerta);
        setTimeout(() => alerta.remove(), 5000);
    }

    mostrarErro(mensagem) {
        this.mostrarMensagem(mensagem, 'danger');
    }
}

let sistemaEstoque;
document.addEventListener('DOMContentLoaded', () => {
    sistemaEstoque = new SistemaEstoque();
});

function abrirModalMovimentacao(ingredienteId = null) {
    sistemaEstoque?.abrirModalMovimentacao(ingredienteId);
}

function calcularTodosCustos() {
    sistemaEstoque?.calcularTodosCustos();
}

