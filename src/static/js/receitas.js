(() => {
  const el = (id) => document.getElementById(id);
  const fmt = (v) => (isNaN(v) ? 'R$ 0,00' : v.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }));

  let receitaAtual = null; // {id, nome, ...}
  let cacheIngredientes = { malte: [], lupulo: [], levedura: [] };

  function alertMsg(message, type = 'success') {
    const area = document.getElementById('alert-area');
    if (!area) return;
    area.innerHTML = `<div class="alert alert-${type} alert-dismissible fade show" role="alert">${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button></div>`;
  }

  async function carregarCatalogos(tipo) {
    if (cacheIngredientes[tipo] && cacheIngredientes[tipo].length) return cacheIngredientes[tipo];
    const url = tipo === 'malte' ? '/api/maltes' : tipo === 'lupulo' ? '/api/lupulos' : '/api/leveduras';
    const resp = await fetch(url);
    if (!resp.ok) throw new Error('Falha ao carregar ingredientes');
    const data = await resp.json();
    cacheIngredientes[tipo] = data;
    return data;
  }

  function preencherSelectIngredientes(lista) {
    const sel = el('ingrediente-select');
    sel.innerHTML = '';
    for (const item of lista) {
      const opt = document.createElement('option');
      opt.value = item.id;
      opt.textContent = `${item.nome} ${item.fabricante ? '(' + item.fabricante + ')' : ''}`;
      sel.appendChild(opt);
    }
  }

  async function atualizarSelectPorTipo() {
    const tipo = el('tipo-ingrediente').value;
    const lista = await carregarCatalogos(tipo);
    preencherSelectIngredientes(lista);
  }

  function linhaIngredienteHTML(item, catalogoAtual) {
    const found = catalogoAtual.find((i) => i.id === item.ingrediente_id) || {};
    const precoUnit = item.tipo_ingrediente === 'levedura' ? found.preco_unidade : found.preco_kg;
    const custo = item.tipo_ingrediente === 'levedura'
      ? (item.quantidade || 0) * (precoUnit || 0)
      : ((item.quantidade || 0) * (precoUnit || 0)) / 1000;
    return {
      html: `
        <tr data-id="${item.id}" data-tipo="${item.tipo_ingrediente}" data-ing="${item.ingrediente_id}">
          <td class="text-capitalize">${item.tipo_ingrediente}</td>
          <td>${found.nome || item.ingrediente_id}</td>
          <td>
            <input type="number" class="form-control form-control-sm quantidade" value="${item.quantidade || 0}" step="1" min="0">
          </td>
          <td>${fmt(precoUnit || 0)}</td>
          <td class="custo">${fmt(custo)}</td>
          <td>
            <button class="btn btn-sm btn-outline-primary salvar"><i class="bi bi-save"></i></button>
            <button class="btn btn-sm btn-outline-danger remover"><i class="bi bi-trash"></i></button>
          </td>
        </tr>
      `,
      custo
    };
  }

  async function carregarIngredientesTabela() {
    if (!receitaAtual) return;
    const resp = await fetch(`/api/receitas/${receitaAtual.id}/ingredientes`);
    if (!resp.ok) return;
    const itens = await resp.json();
    const tbody = document.querySelector('#tabela-ingredientes tbody');
    tbody.innerHTML = '';
    let total = 0;
    // Preparar catálogos
    await Promise.all([
      carregarCatalogos('malte'),
      carregarCatalogos('lupulo'),
      carregarCatalogos('levedura')
    ]);
    for (const item of itens) {
      const cat = cacheIngredientes[item.tipo_ingrediente] || [];
      const { html, custo } = linhaIngredienteHTML(item, cat);
      total += custo;
      tbody.insertAdjacentHTML('beforeend', html);
    }
    el('custo-total-ingredientes').textContent = fmt(total);
  }

  async function salvarReceita(e) {
    e.preventDefault();
    const dados = {
      nome: el('receita-nome').value.trim(),
      descricao: el('receita-descricao').value.trim(),
      volume_litros: Number(el('receita-volume').value || 0),
      eficiencia: Number(el('receita-eficiencia').value || 75)
    };
    if (!dados.nome || !dados.volume_litros) return alertMsg('Preencha nome e volume.', 'warning');
    let resp;
    if (receitaAtual?.id) {
      resp = await fetch(`/api/receitas/${receitaAtual.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dados) });
    } else {
      resp = await fetch('/api/receitas', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dados) });
    }
    if (!resp.ok) return alertMsg('Erro ao salvar receita.', 'danger');
    const data = await resp.json();
    receitaAtual = data.receita;
    alertMsg('Receita salva com sucesso.');
    carregarIngredientesTabela();
  }

  async function adicionarIngrediente() {
    if (!receitaAtual?.id) return alertMsg('Salve a receita antes de adicionar ingredientes.', 'warning');
    const tipo = el('tipo-ingrediente').value;
    const ingrediente_id = Number(el('ingrediente-select').value);
    const quantidade = Number(el('ingrediente-quantidade').value || 0);
    if (!ingrediente_id) return alertMsg('Selecione um ingrediente.', 'warning');
    const resp = await fetch(`/api/receitas/${receitaAtual.id}/ingredientes`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tipo_ingrediente: tipo, ingrediente_id, quantidade })
    });
    if (!resp.ok) return alertMsg('Erro ao adicionar ingrediente.', 'danger');
    alertMsg('Ingrediente adicionado.');
    await carregarIngredientesTabela();
  }

  function bindTabelaEventos() {
    const tbody = document.querySelector('#tabela-ingredientes tbody');
    tbody.addEventListener('click', async (e) => {
      const btnSalvar = e.target.closest('.salvar');
      const btnRemover = e.target.closest('.remover');
      const tr = e.target.closest('tr');
      if (!tr) return;
      const itemId = tr.getAttribute('data-id');
      if (btnSalvar) {
        const quantidade = Number(tr.querySelector('input.quantidade').value || 0);
        const resp = await fetch(`/api/receitas/${receitaAtual.id}/ingredientes/${itemId}`, {
          method: 'PUT', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ quantidade })
        });
        if (!resp.ok) return alertMsg('Erro ao salvar item.', 'danger');
        alertMsg('Ingrediente atualizado.');
        await carregarIngredientesTabela();
      } else if (btnRemover) {
        const resp = await fetch(`/api/receitas/${receitaAtual.id}/ingredientes/${itemId}`, { method: 'DELETE' });
        if (!resp.ok) return alertMsg('Erro ao remover item.', 'danger');
        alertMsg('Ingrediente removido.');
        tr.remove();
      }
    });
  }

  async function calcular(e) {
    e.preventDefault();
    if (!receitaAtual?.id) return alertMsg('Salve a receita antes de calcular.', 'warning');
    const sel = el('tipo-embalagem');
    const selected = sel.options[sel.selectedIndex];
    const data = {
      receita_id: receitaAtual.id,
      quantidade_ml: Number(el('quantidade-ml').value || selected.getAttribute('data-ml') || 1000),
      custo_embalagem: Number(el('custo-embalagem').value || 0),
      custo_impressao: Number(el('custo-impressao').value || 0),
      custo_tampinha: Number(el('custo-tampinha').value || 0),
      percentual_lucro: Number(el('percentual-lucro').value || 0),
      margem_cartao: Number(el('margem-cartao').value || 0),
      percentual_sanitizacao: Number(el('percentual-sanitizacao').value || 0),
      percentual_impostos: Number(el('percentual-impostos').value || 0),
      tipo_embalagem: sel.value,
      nome_produto: el('receita-nome').value.trim()
    };
    const resp = await fetch('/api/calcular', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
    if (!resp.ok) return alertMsg('Erro ao calcular.', 'danger');
    const res = await resp.json();
    const resultado = res.resultado;
    el('valor-litro-base').textContent = fmt(res.valor_litro_base);
    el('subtotal').textContent = fmt(resultado.resultado?.subtotal || resultado.subtotal);
    el('valor-impostos').textContent = fmt(resultado.resultado?.valor_impostos || resultado.valor_impostos);
    el('valor-venda-final').textContent = fmt(resultado.resultado?.valor_venda_final || resultado.valor_venda_final);
  }

  function bindEnvaseAutoML() {
    const sel = el('tipo-embalagem');
    sel.addEventListener('change', () => {
      const opt = sel.options[sel.selectedIndex];
      const ml = Number(opt.getAttribute('data-ml') || 1000);
      el('quantidade-ml').value = ml;
    });
  }

  // Inicialização
  document.addEventListener('DOMContentLoaded', async () => {
    await atualizarSelectPorTipo();
    el('tipo-ingrediente').addEventListener('change', atualizarSelectPorTipo);
    el('form-receita').addEventListener('submit', salvarReceita);
    el('btn-add-ingrediente').addEventListener('click', adicionarIngrediente);
    bindTabelaEventos();
    el('form-calculo').addEventListener('submit', calcular);
    bindEnvaseAutoML();
  });
})();


