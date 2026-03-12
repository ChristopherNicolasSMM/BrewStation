// receitas-brewfather.js
class ReceitasBrewFather {
    constructor() {
        this.receitaAtual = null;
        this.ingredientesProcessados = [];
        this.init();
    }

    init() {
        this.carregarReceitas();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('btn-sync-receitas').addEventListener('click', () => this.sincronizarReceitas());
        document.getElementById('btn-refresh-receitas').addEventListener('click', () => this.carregarReceitas());
        document.getElementById('btn-carregar-receita').addEventListener('click', () => this.carregarReceitaSelecionada());
        document.getElementById('search-recipe').addEventListener('input', (e) => this.filtrarReceitas(e.target.value));
        document.getElementById('form-calculo').addEventListener('submit', (e) => this.calcularPreco(e));
        document.getElementById('tipo-embalagem').addEventListener('change', (e) => this.atualizarQuantidadeML(e));
    }

    async carregarReceitas() {
        try {
            this.mostrarLoading('Carregando receitas...');
            
            const response = await fetch('/api/receitas');
            const data = await response.json();
            
            if (response.ok) {
                this.preencherSelectReceitas(data.receitas);
                this.esconderLoading();
                this.mostrarAlerta('Receitas carregadas com sucesso!', 'success');
            } else {
                throw new Error(data.error || 'Erro ao carregar receitas');
            }
        } catch (error) {
            console.error('Erro ao carregar receitas:', error);
            this.mostrarAlerta('Erro ao carregar receitas: ' + error.message, 'danger');
            this.esconderLoading();
        }
    }

    preencherSelectReceitas(receitas) {
        const select = document.getElementById('brewfather-recipe-select');
        select.innerHTML = '<option value="">Selecione uma receita...</option>';
        
        receitas.forEach(receita => {
            const option = document.createElement('option');
            option.value = receita.id;
            option.textContent = `${receita.nome} - ${receita.estilo || 'Sem estilo'} (${receita.abv}% ABV)`;
            option.dataset.receita = JSON.stringify(receita);
            select.appendChild(option);
        });
    }

    filtrarReceitas(termo) {
        const options = document.getElementById('brewfather-recipe-select').options;
        termo = termo.toLowerCase();
        
        for (let i = 0; i < options.length; i++) {
            const option = options[i];
            const texto = option.textContent.toLowerCase();
            option.style.display = texto.includes(termo) ? '' : 'none';
        }
    }

    async carregarReceitaSelecionada() {
        const select = document.getElementById('brewfather-recipe-select');
        const selectedOption = select.options[select.selectedIndex];
        
        if (!selectedOption.value) {
            this.mostrarAlerta('Selecione uma receita primeiro!', 'warning');
            return;
        }

        try {
            this.mostrarLoading('Carregando receita...');
            
            const receitaData = JSON.parse(selectedOption.dataset.receita);
            const response = await fetch(`/api/receitas/${receitaData.id}`);
            const data = await response.json();
            
            if (response.ok) {
                this.receitaAtual = data.receita;
                this.exibirInformacoesReceita();
                this.exibirIngredientes();
                this.habilitarCalculo();
                this.esconderLoading();
                this.mostrarAlerta('Receita carregada com sucesso!', 'success');
            } else {
                throw new Error(data.error || 'Erro ao carregar receita');
            }
        } catch (error) {
            console.error('Erro ao carregar receita:', error);
            this.mostrarAlerta('Erro ao carregar receita: ' + error.message, 'danger');
            this.esconderLoading();
        }
    }

    exibirInformacoesReceita() {
        const info = document.getElementById('recipe-info');
        const receita = this.receitaAtual;
        
        document.getElementById('info-estilo').textContent = receita.estilo || 'Não informado';
        document.getElementById('info-abv').textContent = receita.abv ? receita.abv.toFixed(1) : '-';
        document.getElementById('info-ibu').textContent = receita.ibu ? receita.ibu.toFixed(0) : '-';
        document.getElementById('info-cor').textContent = receita.cor ? receita.cor.toFixed(0) : '-';
        document.getElementById('info-volume').textContent = receita.volume_litros ? receita.volume_litros.toFixed(1) : '-';
        document.getElementById('info-og').textContent = receita.og ? receita.og.toFixed(3) : '-';
        document.getElementById('info-fg').textContent = receita.fg ? receita.fg.toFixed(3) : '-';
        document.getElementById('info-eficiencia').textContent = receita.eficiencia ? receita.eficiencia.toFixed(1) : '-';
        document.getElementById('info-avaliacao').textContent = receita.avaliacao ? receita.avaliacao.toFixed(1) : '-';
        
        if (receita.notas) {
            document.getElementById('info-notas').textContent = receita.notas;
            document.getElementById('recipe-notes').style.display = 'block';
        }
        
        info.style.display = 'block';
    }

    exibirIngredientes() {
        document.getElementById('no-recipe-alert').style.display = 'none';
        document.getElementById('ingredients-section').style.display = 'block';
        
        this.limparTabelasIngredientes();
        this.processarIngredientesParaTabelas();
    }

    processarIngredientesParaTabelas() {
        const ingredientes = this.receitaAtual.ingredientes;
        if (!ingredientes) return;

        // Processar maltes
        if (ingredientes.fermentables) {
            ingredientes.fermentables.forEach(fermentable => {
                this.adicionarLinhaTabela('maltes', {
                    nome: fermentable.name,
                    fabricante: fermentable.supplier || '',
                    quantidade: (fermentable.amount || 0).toFixed(2),
                    rendimento: (fermentable.yield || 0).toFixed(1),
                    cor: (fermentable.color || 0).toFixed(0),
                    custo: 'Calculando...'
                });
            });
        }

        // Processar lúpulos
        if (ingredientes.hops) {
            ingredientes.hops.forEach(hop => {
                const quantidadeGramas = (hop.amount || 0).toFixed(0);
                this.adicionarLinhaTabela('lupulos', {
                    nome: hop.name,
                    fabricante: hop.supplier || '',
                    quantidade: quantidadeGramas,
                    alpha: (hop.alpha || 0).toFixed(1),
                    uso: hop.use || '',
                    tempo: (hop.time || 0).toFixed(0),
                    custo: 'Calculando...'
                });
            });
        }

        // Processar leveduras
        if (ingredientes.yeasts) {
            ingredientes.yeasts.forEach(yeast => {
                this.adicionarLinhaTabela('leveduras', {
                    nome: yeast.name,
                    fabricante: yeast.supplier || '',
                    quantidade: (yeast.amount || 0).toFixed(0),
                    atenuacao: (yeast.attenuation || 0).toFixed(1),
                    formato: yeast.type || '',
                    custo: 'Calculando...'
                });
            });
        }

        // Inicializar totais como zero
        this.atualizarTotaisIngredientes(0, 0, 0, 0);
    }

    adicionarLinhaTabela(tipo, dados) {
        const tbody = document.getElementById(`${tipo}-table-body`);
        const tr = document.createElement('tr');
        
        Object.values(dados).forEach(valor => {
            const td = document.createElement('td');
            td.textContent = valor;
            tr.appendChild(td);
        });
        
        tbody.appendChild(tr);
    }

    limparTabelasIngredientes() {
        ['maltes', 'lupulos', 'leveduras', 'outros'].forEach(tipo => {
            document.getElementById(`${tipo}-table-body`).innerHTML = '';
        });
    }