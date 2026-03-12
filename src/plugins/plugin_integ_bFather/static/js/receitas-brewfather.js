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

    atualizarTotaisIngredientes(totalMaltes, totalLupulos, totalLeveduras, totalOutros) {
        const totalGeral = totalMaltes + totalLupulos + totalLeveduras + totalOutros;
        const volume = this.receitaAtual.volume_litros || 1;
        const custoPorLitro = totalGeral / volume;
        
        document.getElementById('total-custo-maltes').textContent = `R$ ${totalMaltes.toFixed(2)}`;
        document.getElementById('total-custo-lupulos').textContent = `R$ ${totalLupulos.toFixed(2)}`;
        document.getElementById('total-custo-leveduras').textContent = `R$ ${totalLeveduras.toFixed(2)}`;
        document.getElementById('total-custo-outros').textContent = `R$ ${totalOutros.toFixed(2)}`;
        document.getElementById('custo-total-ingredientes').textContent = `R$ ${totalGeral.toFixed(2)}`;
        document.getElementById('custo-por-litro').textContent = `R$ ${custoPorLitro.toFixed(2)}`;
    }

    habilitarCalculo() {
        document.getElementById('btn-calcular').disabled = false;
    }

    async calcularPreco(event) {
        event.preventDefault();
        
        if (!this.receitaAtual) {
            this.mostrarAlerta('Selecione uma receita primeiro!', 'warning');
            return;
        }

        try {
            const dadosCalculo = this.obterDadosCalculo();
            
            console.log('Enviando dados para cálculo:', {
                receita_id: this.receitaAtual.id,
                ...dadosCalculo
            });
            
            const response = await fetch('/api/calcular', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    receita_id: this.receitaAtual.id,
                    ...dadosCalculo
                })
            });
            
            console.log('Status da resposta:', response.status);
            
            if (!response.ok) {
                const errorText = await response.text();
                console.error('Erro na resposta:', errorText);
                throw new Error(`Erro HTTP: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Dados recebidos do cálculo:', data);
            
            if (data.success) {
                this.exibirResultadosCalculo(data);
                if (data.detalhes_ingredientes) {
                    this.atualizarCustosIngredientes(data.detalhes_ingredientes);
                }
                this.mostrarAlerta('Cálculo realizado com sucesso!', 'success');
            } else {
                throw new Error(data.error || 'Erro no cálculo');
            }
        } catch (error) {
            console.error('Erro ao calcular preço:', error);
            this.mostrarAlerta('Erro ao calcular preço: ' + error.message, 'danger');
        }
    }

    obterDadosCalculo() {
        return {
            quantidade_ml: parseInt(document.getElementById('quantidade-ml').value),
            tipo_embalagem: document.getElementById('tipo-embalagem').value,
            custo_embalagem: parseFloat(document.getElementById('custo-embalagem').value),
            custo_impressao: parseFloat(document.getElementById('custo-impressao').value),
            custo_tampinha: parseFloat(document.getElementById('custo-tampinha').value),
            percentual_lucro: parseFloat(document.getElementById('percentual-lucro').value),
            margem_cartao: parseFloat(document.getElementById('margem-cartao').value),
            percentual_sanitizacao: parseFloat(document.getElementById('percentual-sanitizacao').value),
            percentual_impostos: parseFloat(document.getElementById('percentual-impostos').value),
            nome_produto: this.receitaAtual.nome
        };
    }

    atualizarCustosIngredientes(ingredientesCalculados) {
        if (!ingredientesCalculados) return;

        let totalMaltes = 0, totalLupulos = 0, totalLeveduras = 0, totalOutros = 0;

        ingredientesCalculados.forEach(ingrediente => {
            let custo = ingrediente.custo_total || 0;
            
            switch(ingrediente.tipo) {
                case 'malte':
                    totalMaltes += custo;
                    this.atualizarLinhaTabela('maltes', ingrediente.nome, custo);
                    break;
                case 'lupulo':
                    totalLupulos += custo;
                    this.atualizarLinhaTabela('lupulos', ingrediente.nome, custo);
                    break;
                case 'levedura':
                    totalLeveduras += custo;
                    this.atualizarLinhaTabela('leveduras', ingrediente.nome, custo);
                    break;
                default:
                    totalOutros += custo;
            }
        });

        this.atualizarTotaisIngredientes(totalMaltes, totalLupulos, totalLeveduras, totalOutros);
    }

    atualizarLinhaTabela(tipo, nomeIngrediente, custo) {
        const tbody = document.getElementById(`${tipo}-table-body`);
        
        for (let tr of tbody.children) {
            const cells = tr.children;
            const nomeCelula = cells[0].textContent;
            
            if (nomeCelula === nomeIngrediente) {
                const custoCelula = cells[cells.length - 1];
                custoCelula.textContent = `R$ ${custo.toFixed(2)}`;
                break;
            }
        }
    }

    exibirResultadosCalculo(data) {
        const resultado = data.resultado;
        const resumo = data.resumo || {};
        const resultadosDiv = document.getElementById('resultados-calculo');
        
        // Atualizar detalhes do cálculo
        document.getElementById('detalhe-custo-ingredientes').textContent = `R$ ${resultado.custo_ingredientes.toFixed(2)}`;
        document.getElementById('detalhe-custo-embalagem').textContent = `R$ ${resultado.custo_embalagem.toFixed(2)}`;
        document.getElementById('detalhe-custo-impressao').textContent = `R$ ${resultado.custo_impressao.toFixed(2)}`;
        document.getElementById('detalhe-custo-tampinha').textContent = `R$ ${resultado.custo_tampinha.toFixed(2)}`;
        document.getElementById('detalhe-subtotal').textContent = `R$ ${resultado.subtotal.toFixed(2)}`;
        
        // Percentuais e valores calculados
        document.getElementById('percent-sanitizacao').textContent = data.percentual_sanitizacao || '0';
        document.getElementById('percent-lucro').textContent = data.percentual_lucro || '0';
        document.getElementById('percent-impostos').textContent = data.percentual_impostos || '0';
        document.getElementById('percent-cartao').textContent = data.margem_cartao || '0';
        
        document.getElementById('detalhe-sanitizacao').textContent = `R$ ${resultado.valor_sanitizacao.toFixed(2)}`;
        document.getElementById('detalhe-lucro').textContent = `R$ ${resultado.valor_lucro.toFixed(2)}`;
        document.getElementById('detalhe-impostos').textContent = `R$ ${resultado.valor_impostos.toFixed(2)}`;
        document.getElementById('detalhe-cartao').textContent = `R$ ${resultado.margem_cartao.toFixed(2)}`;
        
        // Preços finais
        document.getElementById('valor-venda-final').textContent = `R$ ${resultado.valor_venda_final.toFixed(2)}`;
        document.getElementById('valor-litro-base').textContent = `R$ ${resultado.custo_total_litro.toFixed(2)}`;
        
        // Volume e resumo
        document.getElementById('volume-receita').textContent = this.receitaAtual.volume_litros.toFixed(1);
        
        // Preço por litro
        const precoPorLitro = (resultado.valor_venda_final / (data.quantidade_ml / 1000)).toFixed(2);
        document.getElementById('preco-por-litro').textContent = `(R$ ${precoPorLitro} por litro)`;
        
        // Unidade de venda
        const unidade = this.obterUnidadeVenda(data.quantidade_ml);
        document.getElementById('unidade-venda').textContent = unidade;
        
        // Margem de lucro real
        document.getElementById('margem-lucro-real').textContent = `${resumo.margem_lucro || data.percentual_lucro || '0'}%`;
        
        resultadosDiv.style.display = 'block';
    }

    obterUnidadeVenda(quantidadeMl) {
        if (quantidadeMl >= 1000) {
            return `${quantidadeMl / 1000}L`;
        }
        return `${quantidadeMl}ml`;
    }

    atualizarQuantidadeML(event) {
        const selectedOption = event.target.options[event.target.selectedIndex];
        const ml = selectedOption.dataset.ml;
        document.getElementById('quantidade-ml').value = ml;
    }

    async sincronizarReceitas() {
        try {
            this.mostrarLoading('Sincronizando receitas com BrewFather...');
            
            const response = await fetch('/api/brewfather/sync/recipes', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.mostrarAlerta(`Sincronização concluída: ${data.message}`, 'success');
                setTimeout(() => this.carregarReceitas(), 1000);
            } else {
                throw new Error(data.error || 'Erro na sincronização');
            }
        } catch (error) {
            console.error('Erro na sincronização:', error);
            this.mostrarAlerta('Erro na sincronização: ' + error.message, 'danger');
        } finally {
            this.esconderLoading();
        }
    }

    // MÉTODOS AUXILIARES CORRIGIDOS
    mostrarAlerta(mensagem, tipo) {
        const alertArea = document.getElementById('alert-area');
        const alert = document.createElement('div');
        alert.className = `alert alert-${tipo} alert-dismissible fade show`;
        alert.innerHTML = `
            ${mensagem}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertArea.appendChild(alert);
        
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }

    mostrarLoading(mensagem) {
        const alertArea = document.getElementById('alert-area');
        const loadingAlert = document.createElement('div');
        loadingAlert.className = 'alert alert-info alert-dismissible fade show';
        loadingAlert.innerHTML = `
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Carregando...</span>
            </div>
            ${mensagem}
        `;
        loadingAlert.id = 'loading-alert';
        alertArea.appendChild(loadingAlert);
    }

    esconderLoading() {
        const loadingAlert = document.getElementById('loading-alert');
        if (loadingAlert) {
            loadingAlert.remove();
        }
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    new ReceitasBrewFather();
});     