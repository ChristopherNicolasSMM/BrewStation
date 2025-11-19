// Sistema de Gerenciamento de Envase
class SistemaEnvase {
    constructor() {
        this.baseUrl = '/api/envase';
        this.dadosFormulario = {};
        this.envases = [];
        this.embalagens = [];
        this.tiposEmbalagem = [];
        this.filtrosEnvase = {
            lote: '',
            status: ''
        };
        // Verificar se Bootstrap está disponível
        if (typeof bootstrap === 'undefined') {
            console.error('❌ Bootstrap não está carregado!');
            this.mostrarErro('Bootstrap não está carregado. Verifique os imports.');
            return;
        }
        console.log('✅ Bootstrap carregado');

        this.init();
    }

    async init() {
        try {
            await this.carregarDadosFormulario();
            await this.carregarEnvases();
            await this.carregarEmbalagens();
            await this.carregarTiposEmbalagem();
            this.carregarResumo();
            this.configurarEventos();
        } catch (error) {
            console.error('Erro ao inicializar sistema de envase:', error);
            this.mostrarErro('Erro ao carregar sistema de envase');
        }
    }









    // ===== MÉTODOS DE FORMULÁRIO =====

    prepararFormularioEnvase(envaseId = null) {
        console.log('🔄 Preparando formulário para envaseId:', envaseId);

        const envaseIdInput = document.getElementById('envaseId');
        const dataInput = document.getElementById('dataEnvase');
        const selectLote = document.getElementById('selectLote');

        if (!envaseIdInput || !selectLote) {
            console.error('❌ Elementos do formulário não encontrados');
            return;
        }

        // Limpar apenas o ID do envase
        envaseIdInput.value = envaseId || '';

        if (envaseId) {
            // Modo edição - carregar dados existentes
            console.log('📝 Modo edição - carregando dados existentes');
            this.carregarDadosEnvase(envaseId);
        } else {
            // Modo novo - resetar campos mas PRESERVAR o select de lote
            console.log('➕ Modo novo - preparando formulário');
            const loteAtual = selectLote.value; // Guardar valor atual

            // Resetar outros campos
            document.getElementById('quantidadeLitros').value = '';
            document.getElementById('tipoEnvase').value = 'completo';
            document.getElementById('statusEnvase').value = 'planejado';
            document.getElementById('observacoesEnvase').value = '';

            // Restaurar data atual
            if (dataInput) {
                const hoje = new Date().toISOString().split('T')[0];
                dataInput.value = hoje;
                console.log('📅 Data definida para:', hoje);
            }

            // Restaurar seleção do lote se existir
            if (loteAtual && loteAtual !== '') {
                console.log('🔄 Restaurando seleção anterior do lote:', loteAtual);
                selectLote.value = loteAtual;
            } else {
                console.log('🔄 Nenhuma seleção anterior, resetando para primeira opção');
                selectLote.selectedIndex = 0; // Só resetar se não tinha seleção
            }

            // Se o lote tiver batch size, preencher quantidade automaticamente
            if (selectLote.value) {
                const selectedOption = selectLote.options[selectLote.selectedIndex];
                const batchSize = selectedOption?.dataset?.batchSize;
                console.log('📊 Batch size do lote selecionado:', batchSize);

                if (batchSize && batchSize > 0) {
                    const quantidade = parseFloat(batchSize).toFixed(1);
                    document.getElementById('quantidadeLitros').value = quantidade;
                    console.log('⚡ Quantidade preenchida automaticamente:', quantidade);
                }
            }

            console.log('✅ Formulário preparado - Lote atual:', selectLote.value);
        }
    }








    async carregarDadosFormulario() {
        try {
            const response = await fetch(`${this.baseUrl}/dados-formulario`);
            const data = await response.json();

            if (data.success) {
                this.dadosFormulario = data;
                this.preencherSelectsFormulario();
            }
        } catch (error) {
            console.error('Erro ao carregar dados do formulário:', error);
        }
    }

    preencherSelectsFormulario() {
        // Preencher select de lotes
        const selectLote = document.getElementById('selectLote');
        if (selectLote && this.dadosFormulario.lotes) {
            selectLote.innerHTML = '<option value="">Selecione um lote</option>';
            this.dadosFormulario.lotes.forEach(lote => {
                const option = document.createElement('option');
                console.log('Adicionando lote ao select:', lote);
                option.value = lote.id;
                option.textContent = lote.nome;
                option.dataset.batchSize = lote.batch_size || 0;
                selectLote.appendChild(option);
            });
        }

        this.preencherFiltrosEnvase();

        // Preencher select de tipos de embalagem
        const selectTipoEmbalagem = document.getElementById('tipoEmbalagemSelect');
        if (selectTipoEmbalagem && this.dadosFormulario.tipos_embalagem) {
            selectTipoEmbalagem.innerHTML = '<option value="">Selecione um tipo</option>';
            this.dadosFormulario.tipos_embalagem.forEach(tipo => {
                const option = document.createElement('option');
                option.value = tipo.id;
                option.textContent = `${tipo.nome}${tipo.capacidade_ml ? ` (${tipo.capacidade_ml}ml)` : ''}`;
                selectTipoEmbalagem.appendChild(option);
            });
        }

        // Preencher select de embalagens
        const selectEmbalagem = document.getElementById('embalagemSelect');
        if (selectEmbalagem && this.dadosFormulario.embalagens) {
            selectEmbalagem.innerHTML = '<option value="">Selecione uma embalagem</option>';
            this.dadosFormulario.embalagens.forEach(emb => {
                const option = document.createElement('option');
                option.value = emb.id;
                option.textContent = `${emb.tipo_embalagem_nome} - ${emb.fornecedor || 'Sem fornecedor'} (Estoque: ${emb.estoque_atual})`;
                option.dataset.capacidade = emb.tipo_embalagem_capacidade || 0;
                option.dataset.valorUnidade = emb.valor_unidade || 0;
                selectEmbalagem.appendChild(option);
            });
        }
    }

    async carregarResumo() {
        try {
            const envases = this.envases || [];
            const embalagens = this.embalagens || [];

            const totalEnvases = envases.length;
            const envasesConcluidos = envases.filter(e => e.status === 'concluido').length;
            const totalEmbalagens = embalagens.length;
            const embalagensBaixoEstoque = embalagens.filter(e => e.estoque_atual <= e.estoque_minimo).length;

            const mesAtual = new Date().getMonth();
            const litrosEnvasados = envases
                .filter(e => {
                    if (!e.data_envase) return false;
                    const dataEnvase = new Date(e.data_envase);
                    return dataEnvase.getMonth() === mesAtual && e.quantidade_litros;
                })
                .reduce((total, e) => total + parseFloat(e.quantidade_litros || 0), 0);

            const custoMedio = embalagens.length > 0
                ? embalagens.reduce((total, e) => total + parseFloat(e.valor_unidade || 0), 0) / embalagens.length
                : 0;

            const totalEnvasesEl = document.getElementById('totalEnvases');
            if (totalEnvasesEl) totalEnvasesEl.textContent = totalEnvases;

            const envasesConcluidosEl = document.getElementById('envasesConcluidos');
            if (envasesConcluidosEl) envasesConcluidosEl.textContent = envasesConcluidos;

            const totalEmbalagensEl = document.getElementById('totalEmbalagens');
            if (totalEmbalagensEl) totalEmbalagensEl.textContent = totalEmbalagens;

            const embalagensBaixoEstoqueEl = document.getElementById('embalagensBaixoEstoque');
            if (embalagensBaixoEstoqueEl) embalagensBaixoEstoqueEl.textContent = embalagensBaixoEstoque;

            const litrosEnvasadosEl = document.getElementById('litrosEnvasados');
            if (litrosEnvasadosEl) litrosEnvasadosEl.textContent = litrosEnvasados.toFixed(1) + 'L';

            const custoMedioEl = document.getElementById('custoMedio');
            if (custoMedioEl) custoMedioEl.textContent = this.formatarMoeda(custoMedio);

        } catch (error) {
            console.error('Erro ao carregar resumo:', error);
        }
    }

    async carregarEnvases() {
        try {
            const response = await fetch(`${this.baseUrl}/envases`);
            const data = await response.json();

            if (data.success) {
                this.envases = data.envases || [];
                this.renderizarTabelaEnvases(this.aplicarFiltrosEnvase());
                this.carregarResumo();
            }
        } catch (error) {
            console.error('Erro ao carregar envases:', error);
        }
    }

    async carregarEmbalagens() {
        try {
            const response = await fetch(`${this.baseUrl}/embalagens`);
            const data = await response.json();

            if (data.success) {
                this.embalagens = data.embalagens || [];
                this.renderizarTabelaEmbalagens(this.embalagens);
                this.carregarResumo();
            }
        } catch (error) {
            console.error('Erro ao carregar embalagens:', error);
        }
    }

    async carregarTiposEmbalagem() {
        try {
            const response = await fetch(`${this.baseUrl}/tipos-embalagem`);
            const data = await response.json();

            if (data.success) {
                this.tiposEmbalagem = data.tipos || [];
                this.renderizarTiposEmbalagem(this.tiposEmbalagem);
            }
        } catch (error) {
            console.error('Erro ao carregar tipos de embalagem:', error);
        }
    }

    renderizarTabelaEnvases(envases) {
        const tbody = document.getElementById('tabelaEnvases').querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!envases || envases.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="bi bi-inbox display-4"></i>
                        <p class="mt-2">Nenhum envase registrado</p>
                    </td>
                </tr>
            `;
            return;
        }

        envases.forEach(envase => {
            const tr = document.createElement('tr');
            const dataFormatada = envase.data_envase ? new Date(envase.data_envase).toLocaleDateString('pt-BR') : 'N/A';
            const statusClass = this.getStatusClass(envase.status);
            const statusTexto = this.getStatusTexto(envase.status);

            // Calcular total de embalagens
            const totalEmbalagens = envase.itens_envase ? envase.itens_envase.reduce((total, item) => total + (item.quantidade || 0), 0) : 0;

            tr.innerHTML = `
                <td>
                    <strong>${envase.lote_nome || 'N/A'}</strong>
                </td>
                <td>${dataFormatada}</td>
                <td>
                    <strong>${parseFloat(envase.quantidade_litros || 0).toFixed(1)}L</strong>
                </td>
                <td>${envase.tipo_envase || 'N/A'}</td>
                <td>
                    <span class="badge bg-${statusClass}">${statusTexto}</span>
                </td>
                <td>
                    <span class="badge bg-info">${totalEmbalagens} unidades</span>
                    ${envase.itens_envase && envase.itens_envase.length > 0 ? `
                        <br><small class="text-muted">
                            ${envase.itens_envase.map(item => `${item.embalagem_nome} (${item.quantidade})`).join(', ')}
                        </small>
                    ` : ''}
                </td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="sistemaEnvase.verDetalhesEnvase(${envase.id})" title="Ver detalhes">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="sistemaEnvase.editarEnvase(${envase.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="sistemaEnvase.excluirEnvase(${envase.id})" title="Excluir">
                        <i class="bi bi-trash"></i>
                    </button>
                </td>
            `;

            tbody.appendChild(tr);
        });
    }

    renderizarTabelaEmbalagens(embalagens) {
        const tbody = document.getElementById('tabelaEmbalagens').querySelector('tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        if (!embalagens || embalagens.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-muted py-4">
                        <i class="bi bi-inbox display-4"></i>
                        <p class="mt-2">Nenhuma embalagem cadastrada</p>
                    </td>
                </tr>
            `;
            return;
        }

        embalagens.forEach(emb => {
            const tr = document.createElement('tr');
            const estoqueClass = emb.estoque_atual <= emb.estoque_minimo ? 'text-danger fw-bold' : '';
            const estoqueTexto = emb.estoque_atual <= emb.estoque_minimo ? '⚠️ ' : '';

            tr.innerHTML = `
                <td>
                    <strong>${emb.tipo_embalagem_nome || 'N/A'}</strong>
                </td>
                <td>${emb.fornecedor || 'N/A'}</td>
                <td>${emb.referencia || 'N/A'}</td>
                <td class="${estoqueClass}">
                    ${estoqueTexto}${emb.estoque_atual} / ${emb.estoque_minimo || 0}
                </td>
                <td>${this.formatarMoeda(emb.valor_unidade || 0)}</td>
                <td>${this.formatarMoeda(emb.valor_lote || 0)}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="sistemaEnvase.verDetalhesEmbalagem(${emb.id})" title="Ver detalhes">
                        <i class="bi bi-eye"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-warning" onclick="sistemaEnvase.editarEmbalagem(${emb.id})" title="Editar">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${emb.link_referencia ? `
                        <a href="${emb.link_referencia}" target="_blank" class="btn btn-sm btn-outline-info" title="Ver referência">
                            <i class="bi bi-link"></i>
                        </a>
                    ` : ''}
                </td>
            `;

            tbody.appendChild(tr);
        });
    }

    renderizarTiposEmbalagem(tipos) {
        const container = document.getElementById('listaTiposEmbalagem');
        if (!container) return;

        container.innerHTML = '';

        if (!tipos || tipos.length === 0) {
            container.innerHTML = `
                <div class="col-12 text-center text-muted py-4">
                    <i class="bi bi-tags display-4"></i>
                    <p class="mt-2">Nenhum tipo de embalagem cadastrado</p>
                </div>
            `;
            return;
        }

        tipos.forEach(tipo => {
            const col = document.createElement('div');
            col.className = 'col-md-6 col-lg-4 mb-3';

            col.innerHTML = `
                <div class="card card-embalagem h-100">
                    <div class="card-body">
                        <h5 class="card-title">${tipo.nome}</h5>
                        ${tipo.descricao ? `<p class="card-text text-muted">${tipo.descricao}</p>` : ''}
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                ${tipo.capacidade_ml ? `<span class="badge badge-capacidade">${tipo.capacidade_ml}ml</span>` : ''}
                                ${tipo.material ? `<span class="badge bg-secondary ms-1">${tipo.material}</span>` : ''}
                                ${tipo.cor ? `<span class="badge bg-light text-dark ms-1">${tipo.cor}</span>` : ''}
                            </div>
                            <div>
                                <button class="btn btn-sm btn-outline-warning" onclick="sistemaEnvase.editarTipoEmbalagem(${tipo.id})">
                                    <i class="bi bi-pencil"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;

            container.appendChild(col);
        });
    }






    // ===== MODALS =====
    abrirModalEnvase(envaseId = null) {
        try {
            console.log('🔧 abrirModalEnvase chamado com envaseId:', envaseId);

            const modalElement = document.getElementById('modalEnvase');
            if (!modalElement) {
                console.error('❌ Modal não encontrado: modalEnvase');
                this.mostrarMensagem('Erro: Modal não encontrado', 'danger');
                return;
            }

            console.log('✅ Modal encontrado');

            // Configurar elementos do formulário
            const titulo = document.getElementById('modalEnvaseTitulo');
            const envaseIdInput = document.getElementById('envaseId');

            if (!titulo || !envaseIdInput) {
                console.error('❌ Elementos do formulário não encontrados');
                return;
            }

            // Preparar formulário ANTES de abrir o modal
            this.prepararFormularioEnvase(envaseId);

            if (envaseId) {
                titulo.textContent = 'Editar Envase';
                console.log('📝 Modo edição para envase:', envaseId);
            } else {
                titulo.textContent = 'Novo Envase';
                console.log('➕ Modo novo envase');
            }

            // Criar e mostrar modal - versão SIMPLES
            const modal = bootstrap.Modal.getOrCreateInstance(modalElement);

            // Adicionar evento para debug quando o modal for mostrado
            const handleShown = () => {
                console.log('✅ Modal totalmente aberto - estado final do select:');
                const selectLote = document.getElementById('selectLote');
                console.log('Valor:', selectLote.value);
                console.log('SelectedIndex:', selectLote.selectedIndex);
                console.log('Texto selecionado:', selectLote.options[selectLote.selectedIndex]?.text);

                // Remover o listener após execução
                modalElement.removeEventListener('shown.bs.modal', handleShown);
            };

            modalElement.addEventListener('shown.bs.modal', handleShown);
            modal.show();

            console.log('✅ Modal.show() executado');

        } catch (error) {
            console.error('❌ Erro inesperado ao abrir modal:', error);
            this.mostrarMensagem('Erro ao abrir formulário: ' + error.message, 'danger');
        }
    }
    // ADICIONE ESTAS NOVAS FUNÇÕES À CLASSE:

    prepararModalParaExibicao(modalElement) {
        console.log('🛠️ Preparando modal para exibição...');

        // Remover instância existente
        const existingModal = bootstrap.Modal.getInstance(modalElement);
        if (existingModal) {
            console.log('🔄 Removendo instância existente do modal');
            existingModal.dispose();
        }

        // Resetar completamente o estado do modal
        modalElement.style.display = 'none';
        modalElement.classList.remove('show');
        modalElement.setAttribute('aria-hidden', 'true');

        // Limpar backdrops existentes
        this.limparBackdrops();

        // Remover classe modal-open do body
        document.body.classList.remove('modal-open');

        console.log('✅ Modal preparado');
    }

    forcarLayoutModal(modalElement) {
        console.log('📐 Forçando layout do modal...');

        // Garantir que o modal-dialog tenha as classes corretas
        const modalDialog = modalElement.querySelector('.modal-dialog');
        if (modalDialog) {
            modalDialog.classList.add('modal-dialog-centered'); // Centralizar
            console.log('✅ Modal-dialog configurado');
        } else {
            console.error('❌ Modal-dialog não encontrado!');
        }

        // Garantir que o modal-content está visível
        const modalContent = modalElement.querySelector('.modal-content');
        if (modalContent) {
            modalContent.style.visibility = 'visible';
            modalContent.style.opacity = '1';
            console.log('✅ Modal-content configurado');
        }

        // Forçar reflow (relayout)
        modalElement.offsetHeight;
    }

    limparBackdrops() {
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.remove();
            console.log('🗑️ Backdrop removido');
        });
    }

    verificarERepararModal(modalElement) {
        console.log('🔍 Verificando e reparando modal...');

        const rect = modalElement.getBoundingClientRect();
        console.log('📏 Dimensões do modal:', {
            width: rect.width,
            height: rect.height,
            top: rect.top,
            left: rect.left
        });

        // Se o modal ainda não tem dimensões, forçar reparo
        if (rect.width === 0 || rect.height === 0) {
            console.warn('⚠️ Modal sem dimensões, aplicando reparo de emergência');
            this.reparoEmergenciaModal(modalElement);
        } else {
            console.log('✅ Modal com dimensões adequadas');
        }
    }

    reparoEmergenciaModal(modalElement) {
        console.log('🚨 APLICANDO REPARO DE EMERGÊNCIA');

        // 1. Remover completamente o modal do DOM
        const modalParent = modalElement.parentElement;
        const modalClone = modalElement.cloneNode(true);
        modalElement.remove();

        // 2. Reinserir o modal
        modalParent.appendChild(modalClone);

        // 3. Aplicar estilos de emergência
        const newModalElement = document.getElementById('modalEnvase');
        if (newModalElement) {
            newModalElement.style.display = 'block';
            newModalElement.style.visibility = 'visible';
            newModalElement.style.opacity = '1';
            newModalElement.style.position = 'fixed';
            newModalElement.style.top = '50%';
            newModalElement.style.left = '50%';
            newModalElement.style.transform = 'translate(-50%, -50%)';
            newModalElement.style.zIndex = '9999';
            newModalElement.style.background = 'white';
            newModalElement.style.padding = '20px';
            newModalElement.style.borderRadius = '8px';
            newModalElement.style.boxShadow = '0 10px 30px rgba(0,0,0,0.3)';
            newModalElement.style.minWidth = '600px';
            newModalElement.style.minHeight = '400px';

            console.log('✅ Reparo de emergência aplicado');

            // Criar backdrop manual
            this.criarBackdropManual();
        }
    }


    // Adicione estas funções auxiliares à classe:

    forcarExibicaoModal(modalElement) {
        console.log('🎨 Forçando exibição do modal...');

        // Remover quaisquer estilos inline problemáticos
        modalElement.style.removeProperty('display');
        modalElement.style.removeProperty('opacity');
        modalElement.style.removeProperty('visibility');

        // Garantir que as classes do Bootstrap estão presentes
        modalElement.classList.add('show');
        modalElement.style.display = 'block';
        modalElement.setAttribute('aria-hidden', 'false');

        // Adicionar backdrop manualmente se necessário
        this.criarBackdropManual();

        console.log('✅ Estilos forçados aplicados');
    }

    criarBackdropManual() {
        // Remover backdrops existentes
        const existingBackdrops = document.querySelectorAll('.modal-backdrop');
        existingBackdrops.forEach(backdrop => backdrop.remove());

        // Criar novo backdrop
        const backdrop = document.createElement('div');
        backdrop.className = 'modal-backdrop fade show';
        backdrop.style.zIndex = '1040'; // z-index padrão do Bootstrap para backdrop

        document.body.appendChild(backdrop);
        document.body.classList.add('modal-open');

        console.log('✅ Backdrop manual criado');
    }

    verificarVisibilidadeModal(modalElement) {
        console.log('👀 Verificando visibilidade do modal:');
        console.log(' - display:', window.getComputedStyle(modalElement).display);
        console.log(' - opacity:', window.getComputedStyle(modalElement).opacity);
        console.log(' - visibility:', window.getComputedStyle(modalElement).visibility);
        console.log(' - z-index:', window.getComputedStyle(modalElement).zIndex);
        console.log(' - classes:', modalElement.className);

        const backdrop = document.querySelector('.modal-backdrop');
        console.log(' - backdrop existe:', !!backdrop);
        if (backdrop) {
            console.log(' - backdrop z-index:', window.getComputedStyle(backdrop).zIndex);
        }

        // Verificar se o modal está realmente visível
        const rect = modalElement.getBoundingClientRect();
        console.log(' - bounding client rect:', rect);
        console.log(' - está na viewport:', rect.top >= 0 && rect.left >= 0);
    }

    abrirModalEmbalagem(embalagemId = null) {
        const modal = new bootstrap.Modal(document.getElementById('modalEmbalagem'));
        const titulo = document.getElementById('modalEmbalagemTitulo');

        document.getElementById('embalagemId').value = embalagemId || '';

        if (embalagemId) {
            titulo.textContent = 'Editar Embalagem';
            this.carregarDadosEmbalagem(embalagemId);
        } else {
            titulo.textContent = 'Nova Embalagem';
            // ⚠️ REMOVER: form.reset();
        }

        // Configurar cálculo automático do valor unitário
        this.configurarCalculoValorUnitario();

        modal.show();
    }

    abrirModalTipoEmbalagem(tipoId = null) {
        const modal = new bootstrap.Modal(document.getElementById('modalTipoEmbalagem'));
        const titulo = document.getElementById('modalTipoEmbalagemTitulo');

        document.getElementById('tipoEmbalagemId').value = tipoId || '';

        if (tipoId) {
            titulo.textContent = 'Editar Tipo de Embalagem';
            this.carregarDadosTipoEmbalagem(tipoId);
        } else {
            titulo.textContent = 'Novo Tipo de Embalagem';
            // ⚠️ REMOVER: form.reset();
        }

        modal.show();
    }

    configurarCalculoValorUnitario() {
        const valorLote = document.getElementById('valorLote');
        const frete = document.getElementById('frete');
        const loteCompra = document.getElementById('loteCompra');
        const valorUnitario = document.getElementById('valorUnitarioCalculado');

        const calcular = () => {
            const vl = parseFloat(valorLote.value) || 0;
            const fr = parseFloat(frete.value) || 0;
            const lc = parseFloat(loteCompra.value) || 0;

            if (lc > 0) {
                const valorUnit = (vl + fr) / lc;
                valorUnitario.textContent = this.formatarMoeda(valorUnit);
            } else {
                valorUnitario.textContent = this.formatarMoeda(0);
            }
        };

        valorLote.addEventListener('input', calcular);
        frete.addEventListener('input', calcular);
        loteCompra.addEventListener('input', calcular);
    }

    // ===== OPERAÇÕES CRUD =====

    async salvarEnvase() {
        try {


            const selectLote = document.getElementById('selectLote');

            // DEBUG COMPLETO
            console.log('=== DEBUG SELECT LOTES ===');
            console.log('Elemento select:', selectLote);
            console.log('Valor atual:', selectLote.value);
            console.log('SelectedIndex:', selectLote.selectedIndex);
            console.log('Quantidade de opções:', selectLote.options.length);

            // Listar todas as opções disponíveis
            console.log('Opções disponíveis:');
            for (let i = 0; i < selectLote.options.length; i++) {
                console.log(`Opção ${i}: valor="${selectLote.options[i].value}", texto="${selectLote.options[i].text}", selecionada=${selectLote.options[i].selected}`);
            }

            if (!selectLote.value) {
                this.mostrarMensagem('Selecione o lote importado do BrewFather antes de salvar.', 'warning');
                selectLote.focus();
                return;
            }
            const formData = {
                lote_id: document.getElementById('selectLote').value,
                quantidade_litros: document.getElementById('quantidadeLitros').value,
                data_envase: document.getElementById('dataEnvase').value,
                tipo_envase: document.getElementById('tipoEnvase').value,
                observacoes: document.getElementById('observacoesEnvase').value,
                status: document.getElementById('statusEnvase').value
            };

            if (!formData.lote_id) {
                this.mostrarMensagem('Erro: Lote não selecionado.', 'danger');
                return;
            }

            console.log('📤 Enviando dados do formulário:', formData);

            const envaseId = document.getElementById('envaseId').value;
            const url = envaseId ? `${this.baseUrl}/envases/${envaseId}` : `${this.baseUrl}/envases`;
            const method = envaseId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalEnvase')).hide();
                this.mostrarMensagem('Envase salvo com sucesso!', 'success');
                await this.carregarEnvases();
                await this.carregarResumo();
            } else {
                throw new Error(data.error || 'Erro desconhecido ao salvar envase');
            }

        } catch (error) {
            console.error('Erro ao salvar envase:', error);
            this.mostrarMensagem('Erro ao salvar envase: ' + error.message, 'danger');
        }
    }

    async salvarEmbalagem() {
        try {
            const formData = {
                tipo_embalagem_id: parseInt(document.getElementById('tipoEmbalagemSelect').value),
                fornecedor: document.getElementById('fornecedor').value,
                referencia: document.getElementById('referencia').value,
                link_referencia: document.getElementById('linkReferencia').value,
                lote_compra: parseInt(document.getElementById('loteCompra').value) || 0,
                frete: parseFloat(document.getElementById('frete').value) || 0,
                valor_lote: parseFloat(document.getElementById('valorLote').value) || 0,
                estoque_atual: parseInt(document.getElementById('estoqueAtual').value) || 0,
                estoque_minimo: parseInt(document.getElementById('estoqueMinimo').value) || 0,
                ativo: document.getElementById('embalagemAtiva').checked
            };

            const embalagemId = document.getElementById('embalagemId').value;
            const url = embalagemId ? `${this.baseUrl}/embalagens/${embalagemId}` : `${this.baseUrl}/embalagens`;
            const method = embalagemId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalEmbalagem')).hide();
                this.mostrarMensagem('Embalagem salva com sucesso!', 'success');
                await this.carregarEmbalagens();
                await this.carregarResumo();
            } else {
                throw new Error(data.error);
            }

        } catch (error) {
            console.error('Erro ao salvar embalagem:', error);
            this.mostrarMensagem('Erro ao salvar embalagem: ' + error.message, 'danger');
        }
    }

    async salvarTipoEmbalagem() {
        try {
            const formData = {
                nome: document.getElementById('nomeTipo').value,
                descricao: document.getElementById('descricaoTipo').value,
                capacidade_ml: document.getElementById('capacidadeMl').value,
                material: document.getElementById('material').value,
                cor: document.getElementById('cor').value
            };

            const tipoId = document.getElementById('tipoEmbalagemId').value;
            const url = tipoId ? `${this.baseUrl}/tipos-embalagem/${tipoId}` : `${this.baseUrl}/tipos-embalagem`;
            const method = tipoId ? 'PUT' : 'POST';

            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                bootstrap.Modal.getInstance(document.getElementById('modalTipoEmbalagem')).hide();
                this.mostrarMensagem('Tipo de embalagem salvo com sucesso!', 'success');
                await this.carregarTiposEmbalagem();
                await this.carregarDadosFormulario(); // Recarregar para atualizar selects
            } else {
                throw new Error(data.error);
            }

        } catch (error) {
            console.error('Erro ao salvar tipo de embalagem:', error);
            this.mostrarMensagem('Erro ao salvar tipo de embalagem: ' + error.message, 'danger');
        }
    }

    // ===== FUNÇÕES AUXILIARES =====

    getStatusClass(status) {
        const statusMap = {
            'planejado': 'secondary',
            'em_andamento': 'warning',
            'concluido': 'success',
            'cancelado': 'danger'
        };
        return statusMap[status] || 'secondary';
    }

    getStatusTexto(status) {
        const statusMap = {
            'planejado': 'Planejado',
            'em_andamento': 'Em Andamento',
            'concluido': 'Concluído',
            'cancelado': 'Cancelado'
        };
        return statusMap[status] || status;
    }

    formatarMoeda(valor) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(valor);
    }

    mostrarMensagem(mensagem, tipo) {
        // Remover mensagens existentes
        const alertasExistentes = document.querySelectorAll('.alert');
        alertasExistentes.forEach(alerta => alerta.remove());

        const alerta = document.createElement('div');
        alerta.className = `alert alert-${tipo} alert-dismissible fade show`;
        alerta.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 10000; min-width: 300px;';
        alerta.innerHTML = `
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;

        document.body.appendChild(alerta);

        setTimeout(() => {
            if (alerta.parentElement) {
                alerta.remove();
            }
        }, 5000);
    }

    mostrarErro(mensagem) {
        this.mostrarMensagem(mensagem, 'danger');
    }

    configurarEventos() {
        // Eventos das abas
        document.getElementById('embalagens-tab')?.addEventListener('click', () => {
            this.carregarEmbalagens();
        });

        document.getElementById('tipos-tab')?.addEventListener('click', () => {
            this.carregarTiposEmbalagem();
        });

        document.getElementById('filtroEnvaseLote')?.addEventListener('change', (event) => {
            this.filtrosEnvase.lote = event.target.value;
            this.renderizarTabelaEnvases(this.aplicarFiltrosEnvase());
        });

        document.getElementById('filtroEnvaseStatus')?.addEventListener('change', (event) => {
            this.filtrosEnvase.status = event.target.value;
            this.renderizarTabelaEnvases(this.aplicarFiltrosEnvase());
        });

        // Evento para calcular quantidade automática baseada no lote
        document.getElementById('selectLote')?.addEventListener('change', (e) => {
            const selectedOption = e.target.options[e.target.selectedIndex];
            const batchSize = selectedOption.dataset.batchSize;
            if (batchSize && batchSize > 0) {
                document.getElementById('quantidadeLitros').value = parseFloat(batchSize).toFixed(1);
            }
        });
    }

    // ===== MÉTODOS STUB (para implementar) =====

    async carregarDadosEnvase(envaseId) {
        console.log('📥 Carregando dados do envase:', envaseId);

        try {
            // Implementação temporária - buscar dados da API
            const response = await fetch(`${this.baseUrl}/envases/${envaseId}`);
            const data = await response.json();

            if (data.success && data.envase) {
                const envase = data.envase;

                // Preencher formulário com dados existentes
                document.getElementById('selectLote').value = envase.lote_id;
                document.getElementById('quantidadeLitros').value = envase.quantidade_litros;
                document.getElementById('dataEnvase').value = envase.data_envase;
                document.getElementById('tipoEnvase').value = envase.tipo_envase;
                document.getElementById('statusEnvase').value = envase.status;
                document.getElementById('observacoesEnvase').value = envase.observacoes || '';

                console.log('✅ Dados do envase carregados no formulário');
            } else {
                throw new Error(data.error || 'Erro ao carregar dados do envase');
            }
        } catch (error) {
            console.error('❌ Erro ao carregar dados do envase:', error);
            this.mostrarMensagem('Erro ao carregar dados: ' + error.message, 'danger');
        }
    }

    async carregarDadosEmbalagem(embalagemId) {
        // Implementar carregamento de dados da embalagem para edição
        console.log('Carregar dados da embalagem:', embalagemId);
    }

    async carregarDadosTipoEmbalagem(tipoId) {
        // Implementar carregamento de dados do tipo de embalagem para edição
        console.log('Carregar dados do tipo de embalagem:', tipoId);
    }

    verDetalhesEnvase(envaseId) {
        // Implementar visualização de detalhes do envase
        console.log('Ver detalhes do envase:', envaseId);
        this.mostrarMensagem('Funcionalidade em desenvolvimento', 'info');
    }

    editarEnvase(envaseId) {
        this.abrirModalEnvase(envaseId);
    }

    async excluirEnvase(envaseId) {
        if (confirm('Tem certeza que deseja excluir este envase?')) {
            try {
                const response = await fetch(`${this.baseUrl}/envases/${envaseId}`, {
                    method: 'DELETE'
                });

                const data = await response.json();

                if (data.success) {
                    this.mostrarMensagem('Envase excluído com sucesso!', 'success');
                    await this.carregarEnvases();
                    await this.carregarResumo();
                } else {
                    throw new Error(data.error);
                }
            } catch (error) {
                console.error('Erro ao excluir envase:', error);
                this.mostrarMensagem('Erro ao excluir envase: ' + error.message, 'danger');
            }
        }
    }

    verDetalhesEmbalagem(embalagemId) {
        // Implementar visualização de detalhes da embalagem
        console.log('Ver detalhes da embalagem:', embalagemId);
        this.mostrarMensagem('Funcionalidade em desenvolvimento', 'info');
    }

    editarEmbalagem(embalagemId) {
        this.abrirModalEmbalagem(embalagemId);
    }

    editarTipoEmbalagem(tipoId) {
        this.abrirModalTipoEmbalagem(tipoId);
    }

    preencherFiltrosEnvase() {
        const filtroLote = document.getElementById('filtroEnvaseLote');
        if (filtroLote) {
            const valorAtual = filtroLote.value;
            filtroLote.innerHTML = '<option value="">Todos os lotes</option>';
            (this.dadosFormulario.lotes || []).forEach(lote => {
                const option = document.createElement('option');
                option.value = lote.id;
                option.textContent = lote.nome;
                filtroLote.appendChild(option);
            });
            filtroLote.value = valorAtual;
        }
    }

    aplicarFiltrosEnvase() {
        return (this.envases || []).filter(envase => {
            const matchLote = this.filtrosEnvase.lote ? String(envase.lote_id) === String(this.filtrosEnvase.lote) : true;
            const matchStatus = this.filtrosEnvase.status ? envase.status === this.filtrosEnvase.status : true;
            return matchLote && matchStatus;
        });
    }
}

// Inicializar sistema
let sistemaEnvase;
document.addEventListener('DOMContentLoaded', () => {
    sistemaEnvase = new SistemaEnvase();
});

// Funções globais para os botões HTML
function abrirModalEnvase() {
    sistemaEnvase.abrirModalEnvase();
}

function abrirModalEmbalagem() {
    sistemaEnvase.abrirModalEmbalagem();
}

function abrirModalTipoEmbalagem() {
    sistemaEnvase.abrirModalTipoEmbalagem();
}

function salvarEnvase() {
    sistemaEnvase.salvarEnvase();
}

function salvarEmbalagem() {
    sistemaEnvase.salvarEmbalagem();
}

function salvarTipoEmbalagem() {
    sistemaEnvase.salvarTipoEmbalagem();
}



// Função para debug - descobrir todos os modais na página
function descobrirModais() {
    console.log('🔍 Procurando modais na página...');

    // Buscar por elementos com classe 'modal'
    const modais = document.querySelectorAll('.modal');
    console.log(`📋 ${modais.length} modais encontrados:`);

    modais.forEach((modal, index) => {
        console.log(`   ${index + 1}. ID: "${modal.id}" | Classes: "${modal.className}"`);
    });

    // Buscar por elementos com data-bs-toggle="modal"
    const botoesModal = document.querySelectorAll('[data-bs-toggle="modal"]');
    console.log(`🔘 ${botoesModal.length} botões de modal encontrados:`);

    botoesModal.forEach((botao, index) => {
        const target = botao.getAttribute('data-bs-target');
        console.log(`   ${index + 1}. Target: "${target}" | Texto: "${botao.textContent.trim()}"`);
    });
}

// Executar quando a página carregar
document.addEventListener('DOMContentLoaded', function () {
    descobrirModais();
});

// Antes de submeter, verifique se há um valor selecionado
function validarFormulario() {
    const selectLote = document.querySelector('#selectLote');

    if (!selectLote.value) {
        alert('Por favor, selecione um lote');
        selectLote.focus();
        return false;
    }

    return true;
}

// Adicionar ao evento de submit
document.querySelector('form').addEventListener('submit', function (e) {
    if (!validarFormulario()) {
        e.preventDefault();
    }
});


// Código de teste - executar no console
function testarSelecaoLote() {
    const selectLote = document.getElementById('selectLote');
    console.log('🔍 Estado atual do select:');
    console.log(' - Valor:', selectLote.value);
    console.log(' - Texto selecionado:', selectLote.options[selectLote.selectedIndex]?.text);
    console.log(' - Required:', selectLote.required);

    // Forçar seleção se estiver vazio
    if (!selectLote.value) {
        console.log('⚠️ Select vazio, selecionando primeiro lote...');
        selectLote.value = "1";
        console.log('✅ Novo valor:', selectLote.value);
    }
}

// Executar teste
//testarSelecaoLote();