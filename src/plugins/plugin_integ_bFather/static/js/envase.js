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

    prepararFormularioEnvase(envaseId = null) {
        console.log('🔄 Preparando formulário para envaseId:', envaseId);

        const envaseIdInput = document.getElementById('envaseId');
        const dataInput = document.getElementById('dataEnvase');
        const selectLote = document.getElementById('selectLote');

        if (!envaseIdInput || !selectLote) {
            console.error('❌ Elementos do formulário não encontrados');
            return;
        }

        // Limpar itens de embalagem existentes
        this.limparItensEmbalagem();

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

    limparItensEmbalagem() {
        const container = document.getElementById('itensEmbalagemContainer');
        if (container) {
            container.innerHTML = '';
        }
        this.atualizarCalculos();
    }

    async carregarDadosFormulario() {