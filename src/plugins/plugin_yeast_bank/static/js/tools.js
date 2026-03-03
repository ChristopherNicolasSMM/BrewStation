(() => {
  const el = (id) => document.getElementById(id);

  const API = {
    strains: "/api/yeast_bank/strains",
    items: "/api/yeast_bank/items",
    calcs: "/api/yeast_bank/tools/calcs",
    run: "/api/yeast_bank/tools/run",
    saveHist: "/api/yeast_bank/tools/history",
    listHist: "/api/yeast_bank/tools/history"
  };

  let catalog = null;
  let lastResults = {
    cells_per_ml: null,
    viability_percent: null,
    estimated_viability_percent: null
  };

  let chart = null;

  function showBox(id, msg) {
    const b = el(id);
    if (!b) return;
    b.textContent = msg || "";
    b.classList.remove("d-none");
  }
  function hideBox(id) { el(id)?.classList.add("d-none"); }
  function clearAlerts() { ["ok","warn","err"].forEach(hideBox); }

  function esc(s) {
    return (s ?? "").toString().replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
  }

  async function fetchJson(url, opts) {
    const r = await fetch(url, opts);
    const data = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, data };
  }

  function fmtSci(n) {
    if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
    const v = Number(n);
    if (!Number.isFinite(v)) return "—";
    // scientific-ish, but readable
    if (v === 0) return "0";
    const abs = Math.abs(v);
    if (abs >= 1e6 || abs < 1e-3) return v.toExponential(3);
    return v.toLocaleString(undefined, { maximumFractionDigits: 3 });
  }

  function fmtPct(n) {
    if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
    const v = Math.max(0, Math.min(100, Number(n)));
    return `${v.toFixed(2)}%`;
  }

  function setOut() {
    el("out_cells_per_ml").textContent = fmtSci(lastResults.cells_per_ml);
    el("out_viability").textContent = fmtPct(lastResults.viability_percent);
    el("out_estimated_viability").textContent = fmtPct(lastResults.estimated_viability_percent);

    if (lastResults.cells_per_ml != null && lastResults.viability_percent != null) {
      const viable = (Number(lastResults.cells_per_ml) * Number(lastResults.viability_percent)) / 100.0;
      el("out_viable_cells_per_ml").textContent = fmtSci(viable);
    } else {
      el("out_viable_cells_per_ml").textContent = "—";
    }
  }

  function buildInputs(containerId, method, defaults = {}) {
    const box = el(containerId);
    box.innerHTML = "";
    const inputs = method.inputs || [];
    for (const inp of inputs) {
      const key = inp.key;
      const label = inp.label || key;
      const type = inp.type || "number";

      const wrap = document.createElement("div");
      wrap.className = "mb-2";

      const id = `${containerId}_${key}`;
      if (type === "list_number") {
        wrap.innerHTML = `
          <label class="form-label">${esc(label)}</label>
          <input id="${esc(id)}" class="form-control" placeholder="ex: 120, 135, 110, 128, 140" value="${esc(defaults[key] || "")}">
          <div class="form-text">Separe por vírgula.</div>
        `;
      } else {
        const min = inp.min != null ? `min="${inp.min}"` : "";
        const max = inp.max != null ? `max="${inp.max}"` : "";
        wrap.innerHTML = `
          <label class="form-label">${esc(label)}</label>
          <input id="${esc(id)}" type="number" step="any" class="form-control" ${min} ${max} value="${esc(defaults[key] ?? "")}">
        `;
      }
      box.appendChild(wrap);
    }
  }

  function readInputs(containerId, method) {
    const out = {};
    for (const inp of (method.inputs || [])) {
      const id = `${containerId}_${inp.key}`;
      const raw = (el(id)?.value || "").trim();
      if (inp.type === "list_number") {
        const parts = raw.split(",").map(s => s.trim()).filter(Boolean);
        out[inp.key] = parts.map(x => Number(x)).filter(n => Number.isFinite(n));
      } else {
        out[inp.key] = Number(raw);
      }
    }
    return out;
  }

  function populateSelect(selId, methods, defaultId) {
    const sel = el(selId);
    sel.innerHTML = "";
    for (const m of methods) {
      sel.innerHTML += `<option value="${esc(m.id)}">${esc(m.name || m.id)}</option>`;
    }
    if (defaultId) sel.value = defaultId;
  }

  async function loadStrains() {
    const { ok, data } = await fetchJson(API.strains);
    if (!ok || !data.ok) throw new Error(data.error || "Falha ao carregar cepas");
    const sel = el("strain_id");
    sel.innerHTML = `<option value="">(selecione)</option>`;
    for (const s of (data.items || [])) {
      sel.innerHTML += `<option value="${s.id}">${esc(s.code ? `${s.code} — ${s.name}` : s.name)}</option>`;
    }
  }

  async function loadItems() {
    const { ok, data } = await fetchJson(API.items);
    if (!ok || !data.ok) throw new Error(data.error || "Falha ao carregar itens");
    const sel = el("bank_item_id");
    sel.innerHTML = `<option value="">(opcional)</option>`;
    for (const it of (data.items || [])) {
      const strainName = it.strain?.code || it.strain?.name || `Cepa #${it.strain_id}`;
      const label = it.label ? ` — ${it.label}` : "";
      sel.innerHTML += `<option value="${it.id}">${esc(strainName + label)}</option>`;
    }
  }

  async function loadCatalog() {
    const { ok, data } = await fetchJson(API.calcs);
    if (!ok || !data.ok) throw new Error(data.error || "Falha ao carregar catálogo");
    catalog = data.catalog;

    const defaults = catalog.defaults || {};

    populateSelect("count_method", catalog.cell_count_methods || [], defaults.cell_count);
    populateSelect("viab_method", catalog.viability_methods || [], (catalog.viability_methods?.[0]?.id));
    populateSelect("viab_model", catalog.viability_models || [], defaults.viability_model);

    // history: allow filter by count method
    const histSel = el("hist_calc_method");
    histSel.innerHTML = `<option value="">(todos)</option>`;
    for (const m of (catalog.cell_count_methods || [])) {
      histSel.innerHTML += `<option value="${esc(m.id)}">${esc(m.name || m.id)}</option>`;
    }

    // build default input UIs
    const countM = (catalog.cell_count_methods || []).find(m => m.id === el("count_method").value);
    const viabM = (catalog.viability_methods || []).find(m => m.id === el("viab_method").value);
    const modelM = (catalog.viability_models || []).find(m => m.id === el("viab_model").value);

    buildInputs("countInputs", countM, { dilution: 100 });
    buildInputs("viabInputs", viabM, {});
    buildInputs("modelInputs", modelM, { v0: 100, days: 0 });
  }

  async function runCalc(kind, calcId, inputs) {
    const { ok, data } = await fetchJson(API.run, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, calc_id: calcId, inputs })
    });
    if (!ok || !data.ok) throw new Error(data.error || "Falha no cálculo");
    return data.result || {};
  }

  async function doCountCalc() {
    clearAlerts();
    const calcId = el("count_method").value;
    const method = (catalog.cell_count_methods || []).find(m => m.id === calcId);
    const inputs = readInputs("countInputs", method);
    // validation
    if (method.inputs?.some(i => i.key === "counts")) {
      if (!inputs.counts || inputs.counts.length === 0) return showBox("warn", "Informe ao menos 1 contagem.");
    }
    if (!Number.isFinite(inputs.dilution) || inputs.dilution <= 0) return showBox("warn", "Diluição inválida.");

    try {
      const res = await runCalc("cell_count", calcId, inputs);
      lastResults.cells_per_ml = res.cells_per_ml ?? null;
      setOut();
      showBox("ok", "Contagem calculada.");
    } catch (e) {
      showBox("err", e?.message || "Erro no cálculo");
    }
  }

  async function doViabCalc() {
    clearAlerts();
    const calcId = el("viab_method").value;
    const method = (catalog.viability_methods || []).find(m => m.id === calcId);
    const inputs = readInputs("viabInputs", method);

    if (!Number.isFinite(inputs.total_cells) || inputs.total_cells <= 0) return showBox("warn", "Total inválido.");
    if (!Number.isFinite(inputs.dead_cells) || inputs.dead_cells < 0) return showBox("warn", "Mortas inválido.");

    try {
      const res = await runCalc("viability", calcId, inputs);
      lastResults.viability_percent = res.viability_percent ?? null;
      setOut();
      showBox("ok", "Viabilidade calculada.");
    } catch (e) {
      showBox("err", e?.message || "Erro no cálculo");
    }
  }

  async function doModelCalc() {
    clearAlerts();
    const calcId = el("viab_model").value;
    const method = (catalog.viability_models || []).find(m => m.id === calcId);
    const inputs = readInputs("modelInputs", method);

    if (!Number.isFinite(inputs.v0) || inputs.v0 < 0 || inputs.v0 > 100) return showBox("warn", "v0 inválido (0-100).");
    if (!Number.isFinite(inputs.days) || inputs.days < 0) return showBox("warn", "days inválido.");

    try {
      const res = await runCalc("viability_model", calcId, inputs);
      lastResults.estimated_viability_percent = res.estimated_viability_percent ?? null;
      setOut();
      showBox("ok", "Viabilidade estimada calculada.");
    } catch (e) {
      showBox("err", e?.message || "Erro no cálculo");
    }
  }

  function getSavePayload() {
    const strain_id = parseInt(el("strain_id").value || "0", 10) || null;
    const bank_item_id = parseInt(el("bank_item_id").value || "0", 10) || null;
    const lot_code = (el("lot_code").value || "").trim() || null;
    const sample_date = (el("sample_date").value || "").trim();

    const count_method = el("count_method").value;
    const viab_method = el("viab_method").value;
    const viab_model = el("viab_model").value;

    const countM = (catalog.cell_count_methods || []).find(m => m.id === count_method);
    const viabM = (catalog.viability_methods || []).find(m => m.id === viab_method);
    const modelM = (catalog.viability_models || []).find(m => m.id === viab_model);

    const countInputs = readInputs("countInputs", countM);
    const viabInputs = readInputs("viabInputs", viabM);
    const modelInputs = readInputs("modelInputs", modelM);

    const viable_cells_per_ml = (lastResults.cells_per_ml != null && lastResults.viability_percent != null)
      ? (Number(lastResults.cells_per_ml) * Number(lastResults.viability_percent)) / 100.0
      : null;

    return {
      strain_id,
      bank_item_id,
      lot_code,
      sample_date,
      calc_method_id: count_method,
      cells_per_ml: lastResults.cells_per_ml,
      viability_percent: lastResults.viability_percent,
      viable_cells_per_ml,
      estimated_viability_percent: lastResults.estimated_viability_percent,
      notes: (el("notes").value || "").trim() || null,
      raw_inputs: {
        count_method, countInputs,
        viab_method, viabInputs,
        viab_model, modelInputs
      }
    };
  }

  async function saveHistory() {
    clearAlerts();
    const p = getSavePayload();
    if (!p.strain_id) return showBox("warn", "Selecione uma cepa.");
    if (!p.sample_date) return showBox("warn", "Informe a data da amostra.");
    if (p.cells_per_ml == null) return showBox("warn", "Calcule a contagem antes de salvar.");

    const { ok, data } = await fetchJson(API.saveHist, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(p)
    });
    if (!ok || !data.ok) return showBox("err", data.error || "Falha ao salvar histórico");

    showBox("ok", "Registro salvo no histórico.");
  }

  function renderHistoryTable(items) {
    const tb = el("histRows");
    tb.innerHTML = "";
    if (!items || items.length === 0) {
      tb.innerHTML = `<tr><td colspan="6" class="text-muted">Sem dados.</td></tr>`;
      return;
    }
    for (const r of items) {
      tb.innerHTML += `
        <tr>
          <td>${esc(r.sample_date || "")}</td>
          <td>${esc(r.lot_code || "")}</td>
          <td>${esc(r.calc_method_id || "")}</td>
          <td>${fmtSci(r.cells_per_ml)}</td>
          <td>${fmtPct(r.viability_percent)}</td>
          <td>${fmtPct(r.estimated_viability_percent)}</td>
        </tr>
      `;
    }
  }

  function drawChart(items) {
    const ctx = el("viabChart");
    if (!ctx || typeof Chart === "undefined") return;

    const labels = items.map(i => i.sample_date);
    const real = items.map(i => (i.viability_percent != null ? Number(i.viability_percent) : null));
    const est = items.map(i => (i.estimated_viability_percent != null ? Number(i.estimated_viability_percent) : null));

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: "line",
      data: {
        labels,
        datasets: [
          { label: "Viabilidade real (%)", data: real, spanGaps: true, tension: 0.25 },
          { label: "Viabilidade estimada (%)", data: est, spanGaps: true, tension: 0.25 }
        ]
      },
      options: {
        responsive: true,
        scales: {
          y: { min: 0, max: 100 }
        }
      }
    });
  }

  async function loadHistory() {
    clearAlerts();
    const strain_id = parseInt(el("strain_id").value || "0", 10) || null;
    if (!strain_id) return showBox("warn", "Selecione uma cepa.");

    const lot_code = (el("hist_lot_code").value || "").trim();
    const calc_method_id = (el("hist_calc_method").value || "").trim();

    const params = new URLSearchParams({ strain_id: String(strain_id) });
    if (lot_code) params.set("lot_code", lot_code);
    if (calc_method_id) params.set("calc_method_id", calc_method_id);

    const { ok, data } = await fetchJson(`${API.listHist}?${params.toString()}`);
    if (!ok || !data.ok) return showBox("err", data.error || "Falha ao carregar histórico");

    renderHistoryTable(data.items || []);
    drawChart(data.items || []);
    showBox("ok", `Histórico carregado: ${data.items?.length || 0} registro(s).`);
  }

  function bindEvents() {
    el("count_method").addEventListener("change", () => {
      const m = (catalog.cell_count_methods || []).find(x => x.id === el("count_method").value);
      buildInputs("countInputs", m, { dilution: 100 });
    });
    el("viab_method").addEventListener("change", () => {
      const m = (catalog.viability_methods || []).find(x => x.id === el("viab_method").value);
      buildInputs("viabInputs", m, {});
    });
    el("viab_model").addEventListener("change", () => {
      const m = (catalog.viability_models || []).find(x => x.id === el("viab_model").value);
      buildInputs("modelInputs", m, { v0: 100, days: 0 });
    });

    el("btnCountCalc").addEventListener("click", doCountCalc);
    el("btnViabCalc").addEventListener("click", doViabCalc);
    el("btnModelCalc").addEventListener("click", doModelCalc);
    el("btnSaveHistory").addEventListener("click", saveHistory);
    el("btnLoadHistory").addEventListener("click", loadHistory);

    // default date today
    const d = new Date();
    const iso = d.toISOString().slice(0,10);
    if (el("sample_date") && !el("sample_date").value) el("sample_date").value = iso;
  }

  async function init() {
    try {
      await Promise.all([loadStrains(), loadItems()]);
      await loadCatalog();
      bindEvents();
      setOut();
    } catch (e) {
      showBox("err", e?.message || "Falha ao inicializar");
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();
