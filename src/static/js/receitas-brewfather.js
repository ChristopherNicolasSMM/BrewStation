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
        // Sincronizar receitas
        document.getElementById('btn-sync-receitas').addEventListener('click', () => this.sincronizarReceitas());
        document.getElementById('btn-refresh-receitas').addEventListener('click', () => this.carregarReceitas());
        
        // Carregar receita selecionada
        document.getElementById('btn-carregar-receita').addEventListener('click', () => this.carregarReceitaSelecionada());
        
        // Busca de receitas
        document.getElementById('search-recipe').addEventListener('input', (e) => this.filtrarReceitas(e.target.value));
        
        // Cálculo de preço
        document.getElementById('form-calculo').addEventListener('submit', (e) => this.calcularPreco(e));
        
        // Tipo de embalagem
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
                this.ingredientesProcessados = data.receita.ingredientes_processados || [];
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
        
        // Preencher informações básicas
        document.getElementById('info-estilo').textContent = receita.estilo || 'Não informado';
        document.getElementById('info-abv').textContent = receita.abv ? receita.abv.toFixed(1) : '-';
        document.getElementById('info-ibu').textContent = receita.ibu ? receita.ibu.toFixed(0) : '-';
        document.getElementById('info-cor').textContent = receita.cor ? receita.cor.toFixed(0) : '-';
        document.getElementById('info-volume').textContent = receita.volume_litros ? receita.volume_litros.toFixed(1) : '-';
        document.getElementById('info-og').textContent = receita.og ? receita.og.toFixed(3) : '-';
        document.getElementById('info-fg').textContent = receita.fg ? receita.fg.toFixed(3) : '-';
        document.getElementById('info-eficiencia').textContent = receita.eficiencia ? receita.eficiencia.toFixed(1) : '-';
        document.getElementById('info-avaliacao').textContent = receita.avaliacao ? receita.avaliacao.toFixed(1) : '-';
        
        // Notas
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
        this.calcularCustosIngredientes();
    }

    processarIngredientesParaTabelas() {
        const ingredientes = this.receitaAtual.ingredientes;
        if (!ingredientes) return;

        // Processar maltes
        if (ingredientes.fermentables) {
            ingredientes.fermentables.forEach(fermentable => {
                const custo = this.calcularCustoIngrediente('malte', fermentable);
                this.adicionarLinhaTabela('maltes', {
                    nome: fermentable.name,
                    fabricante: fermentable.supplier || '',
                    quantidade: (fermentable.amount || 0).toFixed(2),
                    rendimento: (fermentable.yield || 0).toFixed(1),
                    cor: (fermentable.color || 0).toFixed(0),
                    custo: custo.toFixed(2)
                });
            });
        }

        // Processar lúpulos
        if (ingredientes.hops) {
            ingredientes.hops.forEach(hop => {
                const custo = this.calcularCustoIngrediente('lupulo', hop);
                this.adicionarLinhaTabela('lupulos', {
                    nome: hop.name,
                    fabricante: hop.supplier || '',
                    quantidade: ((hop.amount || 0) * 1000).toFixed(0), // converter kg para g
                    alpha: (hop.alpha || 0).toFixed(1),
                    uso: hop.use || '',
                    tempo: (hop.time || 0).toFixed(0),
                    custo: custo.toFixed(2)
                });
            });
        }

        // Processar leveduras
        if (ingredientes.yeasts) {
            ingredientes.yeasts.forEach(yeast => {
                const custo = this.calcularCustoIngrediente('levedura', yeast);
                this.adicionarLinhaTabela('leveduras', {
                    nome: yeast.name,
                    fabricante: yeast.supplier || '',
                    quantidade: (yeast.amount || 0).toFixed(0),
                    atenuacao: (yeast.attenuation || 0).toFixed(1),
                    formato: yeast.type || '',
                    custo: custo.toFixed(2)
                });
            });
        }
    }

    calcularCustoIngrediente(tipo, ingrediente) {
        // Buscar nos ingredientes processados
        const processado = this.ingredientesProcessados.find(
            item => item.nome === ingrediente.name && item.tipo === tipo
        );
        
        if (processado && processado.custo) {
            return processado.custo;
        }
        
        // Calcular custo aproximado baseado em preços padrão
        const quantidade = ingrediente.amount || 0;
        let precoUnitario = 0;
        
        switch(tipo) {
            case 'malte':
                precoUnitario = 8.00; // R$/kg
                return quantidade * precoUnitario;
            case 'lupulo':
                precoUnitario = 120.00; // R$/kg
                return quantidade * precoUnitario;
            case 'levedura':
                precoUnitario = 25.00; // R$/unidade
                return quantidade * precoUnitario;
            default:
                return 0;
        }
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

    calcularCustosIngredientes() {
        let totalMaltes = 0, totalLupulos = 0, totalLeveduras = 0, totalOutros = 0;
        
        // Calcular totais (em uma implementação real, isso viria do backend)
        totalMaltes = this.calcularTotalTabela('maltes');
        totalLupulos = this.calcularTotalTabela('lupulos');
        totalLeveduras = this.calcularTotalTabela('leveduras');
        
        const totalGeral = totalMaltes + totalLupulos + totalLeveduras + totalOutros;
        const volume = this.receitaAtual.volume_litros || 1;
        const custoPorLitro = totalGeral / volume;
        
        // Atualizar totais
        document.getElementById('total-custo-maltes').textContent = `R$ ${totalMaltes.toFixed(2)}`;
        document.getElementById('total-custo-lupulos').textContent = `R$ ${totalLupulos.toFixed(2)}`;
        document.getElementById('total-custo-leveduras').textContent = `R$ ${totalLeveduras.toFixed(2)}`;
        document.getElementById('total-custo-outros').textContent = `R$ ${totalOutros.toFixed(2)}`;
        document.getElementById('custo-total-ingredientes').textContent = `R$ ${totalGeral.toFixed(2)}`;
        document.getElementById('custo-por-litro').textContent = `R$ ${custoPorLitro.toFixed(2)}`;
        
        return totalGeral;
    }

    calcularTotalTabela(tipo) {
        const tbody = document.getElementById(`${tipo}-table-body`);
        let total = 0;
        
        for (let tr of tbody.children) {
            const cells = tr.children;
            const custo = parseFloat(cells[cells.length - 1].textContent) || 0;
            total += custo;
        }
        
        return total;
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
            const custoIngredientes = this.calcularCustosIngredientes();
            
            const response = await fetch(`/api/receitas/${this.receitaAtual.id}/calcular-preco`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...dadosCalculo,
                    custo_ingredientes: custoIngredientes
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.exibirResultadosCalculo(data);
            } else {
                throw new Error(data.error || 'Erro ao calcular preço');
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
            percentual_impostos: parseFloat(document.getElementById('percentual-impostos').value)
        };
    }

    exibirResultadosCalculo(data) {
        const calculo = data.calculo;
        const resultados = document.getElementById('resultados-calculo');
        
        // Atualizar detalhes
        document.getElementById('detalhe-custo-ingredientes').textContent = `R$ ${data.custo_ingredientes.toFixed(2)}`;
        document.getElementById('detalhe-custo-embalagem').textContent = `R$ ${calculo.custo_embalagem.toFixed(2)}`;
        document.getElementById('detalhe-custo-impressao').textContent = `R$ ${calculo.custo_impressao.toFixed(2)}`;
        document.getElementById('detalhe-custo-tampinha').textContent = `R$ ${calculo.custo_tampinha.toFixed(2)}`;
        document.getElementById('detalhe-subtotal').textContent = `R$ ${calculo.valor_total.toFixed(2)}`;
        
        // Percentuais
        document.getElementById('percent-sanitizacao').textContent = calculo.percentual_sanitizacao;
        document.getElementById('percent-lucro').textContent = calculo.percentual_lucro;
        document.getElementById('percent-impostos').textContent = calculo.percentual_impostos;
        document.getElementById('percent-cartao').textContent = calculo.margem_cartao;
        
        // Preços
        document.getElementById('valor-venda-final').textContent = `R$ ${calculo.valor_venda_final.toFixed(2)}`;
        document.getElementById('valor-litro-base').textContent = `R$ ${calculo.valor_litro_base.toFixed(2)}`;
        
        // Volume
        document.getElementById('volume-receita').textContent = this.receitaAtual.volume_litros.toFixed(1);
        
        // Preço por litro
        const precoPorLitro = (calculo.valor_venda_final / (calculo.quantidade_ml / 1000)).toFixed(2);
        document.getElementById('preco-por-litro').textContent = `(R$ ${precoPorLitro} por litro)`;
        
        // Unidade de venda
        const unidade = this.obterUnidadeVenda(calculo.quantidade_ml);
        document.getElementById('unidade-venda').textContent = unidade;
        
        resultados.style.display = 'block';
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
            
            const response = await fetch('api/brewfather/sync/recipes', {
                method: 'POST'
            });
            console.log(response.json())
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.mostrarAlerta(`Sincronização concluída: ${data.message}`, 'success');
                // Recarregar a lista de receitas após sincronização
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

    // Métodos auxiliares
    mostrarAlerta(mensagem, tipo) {
        const alertArea = document.getElementById('alert-area');
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
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
        // Implementar loading spinner
        console.log('Loading:', mensagem);
    }

    esconderLoading() {
        // Esconder loading spinner
        console.log('Loading completo');
    }
}

// Inicializar quando o DOM estiver carregado
document.addEventListener('DOMContentLoaded', function() {
    new ReceitasBrewFather();
});