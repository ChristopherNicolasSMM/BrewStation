(() => {
  "use strict";

  /**
   * YeastBank - Starter & Contagem
   * -----------------------------------------------------------------
   * Tela unificada para:
   * - starters
   * - vínculo com amostras / itens do banco
   * - contagem de células
   * - viabilidade real / estimada
   * - histórico e gráfico
   *
   * Regras de manutenção:
   * 1) O arquivo deve degradar com segurança. Se uma área do DOM não existir,
   *    o restante da página deve continuar funcional.
   * 2) IDs do HTML e este JS devem permanecer sincronizados.
   * 3) A tela principal é starters.html. A rota /tools também usa esta mesma tela.
   * 4) Se novos botões forem adicionados, ligue-os com safeBind().
   */

  const API = {
    starters: "/api/yeast_bank/starters",
    starterExportCsv: "/api/yeast_bank/starters/export/csv",
    starterExportJson: "/api/yeast_bank/starters/export/json",
    items: "/api/yeast_bank/items",
    strains: "/api/yeast_bank/strains",
    calcs: "/api/yeast_bank/tools/calcs",
    run: "/api/yeast_bank/tools/run",
    history: "/api/yeast_bank/tools/history",
    recalculateViability: "/api/yeast_bank/viability/recalculate"
  };

  const DEBUG = true;

  const state = {
    starters: [],
    items: [],
    strains: [],
    catalog: {
      cell_count_methods: [],
      viability_methods: [],
      viability_models: []
    },
    chart: null,
    initialized: false,
    lastResults: {
      cells_per_ml: null,
      viability_percent: null,
      estimated_viability_percent: null
    }
  };

  const el = (id) => document.getElementById(id);

  function log(...args) {
    if (DEBUG) console.log("[YeastBank:Starter]", ...args);
  }

  function warn(...args) {
    console.warn("[YeastBank:Starter]", ...args);
  }

  function errorLog(...args) {
    console.error("[YeastBank:Starter]", ...args);
  }

  function esc(value) {
    return (value ?? "").toString()
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;");
  }

  function setText(id, value) {
    const node = el(id);
    if (!node) return;
    node.textContent = value ?? "";
  }

  function setHtml(id, value) {
    const node = el(id);
    if (!node) return;
    node.innerHTML = value ?? "";
  }

  function showBox(id, msg) {
    const node = el(id);
    if (!node) return;
    node.textContent = msg || "";
    node.classList.remove("d-none");
  }

  function hideBox(id) {
    const node = el(id);
    if (!node) return;
    node.classList.add("d-none");
  }

  function clearAlerts() {
    ["ok", "warn", "err", "starterErr"].forEach(hideBox);
  }

  async function fetchJson(url, opts = {}) {
    let response;
    try {
      response = await fetch(url, opts);
    } catch (err) {
      throw new Error(`Falha de rede ao acessar ${url}`);
    }

    let data = {};
    try {
      data = await response.json();
    } catch (_) {
      data = {};
    }

    return { ok: response.ok, status: response.status, data };
  }

  function fmtPct(n) {
    if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
    const v = Math.max(0, Math.min(100, Number(n)));
    return `${v.toFixed(2)}%`;
  }

  function fmtNum(n) {
    if (n === null || n === undefined || Number.isNaN(Number(n))) return "—";
    const v = Number(n);
    if (!Number.isFinite(v)) return "—";
    if (Math.abs(v) >= 1e6 || (Math.abs(v) < 1e-3 && v !== 0)) return v.toExponential(3);
    return v.toLocaleString(undefined, { maximumFractionDigits: 3 });
  }

  function strainLabel(item) {
    const s = item?.strain || {};
    return [s.code, s.name].filter(Boolean).join(" — ") || `Cepa #${item?.strain_id ?? "?"}`;
  }

  function itemLabel(item) {
    if (!item) return "—";
    const parts = [`#${item.id}`, strainLabel(item), item.storage_type || ""];
    if (item.label) parts.push(item.label);
    if (item.location) parts.push(item.location);
    if (item.storage_slot) parts.push(item.storage_slot);
    return parts.filter(Boolean).join(" • ");
  }

  function statusBadge(status) {
    const map = {
      planned: "secondary",
      running: "warning",
      completed: "success",
      done: "success",
      canceled: "secondary",
      cancelled: "secondary",
      contaminated: "danger",
      discarded: "dark",
      failed: "danger"
    };
    const klass = map[status] || "secondary";
    return `<span class="badge bg-${klass}">${esc(status || "—")}</span>`;
  }

  function objectiveLabel(value) {
    return {
      brew: "Brassagem",
      propagation: "Propagação",
      test: "Teste",
      recovery: "Recuperação"
    }[value] || (value || "—");
  }

  function itemById(id) {
    return state.items.find(x => Number(x.id) === Number(id));
  }

  function currentStrainIdFromItem() {
    const bankItemId = Number(el("bank_item_id")?.value || 0);
    if (!bankItemId) return null;
    return itemById(bankItemId)?.strain_id || null;
  }

  function syncStrainFromItemSelection() {
    const bankItemId = Number(el("bank_item_id")?.value || 0);
    const item = itemById(bankItemId);
    const strainSelect = el("strain_id");
    if (item?.strain_id && strainSelect) {
      strainSelect.value = String(item.strain_id);
    }
  }

  function populateSelect(selectId, items, makeLabel, placeholder = "(selecione)") {
    const select = el(selectId);
    if (!select) return;

    select.innerHTML = `<option value="">${esc(placeholder)}</option>`;
    for (const item of items) {
      select.insertAdjacentHTML(
        "beforeend",
        `<option value="${esc(item.id)}">${esc(makeLabel(item))}</option>`
      );
    }
  }

  function safeBind(elementId, eventName, handler) {
    const node = el(elementId);
    if (!node) {
      warn(`Elemento #${elementId} não encontrado para bind de ${eventName}.`);
      return;
    }

    const key = `bind_${eventName}_${elementId}`;
    if (node.dataset[key] === "1") return;

    node.addEventListener(eventName, handler);
    node.dataset[key] = "1";
  }

  function addDays(dateObj, days) {
    const d = new Date(dateObj.getTime());
    d.setDate(d.getDate() + days);
    return d;
  }

  function toISO(dateObj) {
    return dateObj.toISOString().slice(0, 10);
  }

  function tryAutoSetStartDate(force = false) {
    const auto = el("auto_start")?.checked;
    if (!auto && !force) return;

    const brew = el("brew_date")?.value;
    const startNode = el("start_date");
    if (!brew || !startNode) return;

    const brewDate = new Date(`${brew}T00:00:00`);
    startNode.value = toISO(addDays(brewDate, -7));
  }

  function starterModal() {
    const modalEl = el("starterModal");
    if (!modalEl) {
      throw new Error("Elemento #starterModal não encontrado no HTML.");
    }

    if (typeof bootstrap === "undefined" || !bootstrap.Modal) {
      throw new Error("Bootstrap Modal não está disponível na página.");
    }

    return bootstrap.Modal.getOrCreateInstance(modalEl);
  }

  function resetStarterForm() {
    hideBox("starterErr");

    if (el("starterId")) el("starterId").value = "";
    if (el("starterModalLabel")) el("starterModalLabel").textContent = "Novo starter";
    if (el("starter_bank_item_id")) el("starter_bank_item_id").value = "";
    if (el("brew_date")) el("brew_date").value = "";
    if (el("start_date")) el("start_date").value = "";
    if (el("target_volume_l")) el("target_volume_l").value = "";
    if (el("objective")) el("objective").value = "brew";
    if (el("status")) el("status").value = "planned";
    if (el("starter_notes")) el("starter_notes").value = "";
    if (el("auto_start")) el("auto_start").checked = true;
    if (el("starter_contamination_detected")) el("starter_contamination_detected").value = "false";
    if (el("starter_result_action")) el("starter_result_action").value = "";
  }

  function openStarterModal(starter = null) {
    try {
      log("Abrindo modal de starter:", starter);
      hideBox("starterErr");

      if (!starter) {
        resetStarterForm();
      } else {
        if (el("starterId")) el("starterId").value = starter.id || "";
        if (el("starterModalLabel")) el("starterModalLabel").textContent = `Editar starter #${starter.id}`;
        if (el("starter_bank_item_id")) el("starter_bank_item_id").value = starter.bank_item_id ? String(starter.bank_item_id) : "";
        if (el("brew_date")) el("brew_date").value = starter.brew_date || "";
        if (el("start_date")) el("start_date").value = starter.start_date || "";
        if (el("target_volume_l")) el("target_volume_l").value = starter.target_volume_l ?? "";
        if (el("objective")) el("objective").value = starter.objective || "brew";
        if (el("status")) el("status").value = starter.status || "planned";
        if (el("starter_notes")) el("starter_notes").value = starter.notes || "";
        if (el("auto_start")) el("auto_start").checked = false;
        if (el("starter_contamination_detected")) el("starter_contamination_detected").value = String(Boolean(starter.contamination_detected));
        if (el("starter_result_action")) el("starter_result_action").value = starter.action_on_bank_item || starter.result_action || "";
      }

      starterModal().show();
    } catch (err) {
      errorLog("Falha ao abrir modal:", err);
      showBox("err", err.message || "Falha ao abrir o modal de starter.");
    }
  }

  async function loadBaseData() {
    const [startersRes, itemsRes, strainsRes] = await Promise.all([
      fetchJson(API.starters),
      fetchJson(API.items),
      fetchJson(API.strains)
    ]);

    if (!startersRes.ok || !startersRes.data.ok) {
      throw new Error(startersRes.data.error || "Falha ao carregar starters");
    }
    if (!itemsRes.ok || !itemsRes.data.ok) {
      throw new Error(itemsRes.data.error || "Falha ao carregar itens do banco");
    }
    if (!strainsRes.ok || !strainsRes.data.ok) {
      throw new Error(strainsRes.data.error || "Falha ao carregar cepas");
    }

    state.starters = startersRes.data.items || [];
    state.items = itemsRes.data.items || [];
    state.strains = strainsRes.data.items || [];

    populateSelect("strain_id", state.strains, s => (s.code ? `${s.code} — ${s.name}` : s.name), "(selecione)");
    populateSelect("bank_item_id", state.items, itemLabel, "(opcional)");
    populateSelect("starter_bank_item_id", state.items, itemLabel, "(selecione)");

    const starterSel = el("starter_link_id");
    if (starterSel) {
      starterSel.innerHTML = `<option value="">(opcional)</option>`;
      for (const s of state.starters) {
        const item = itemById(s.bank_item_id);
        starterSel.insertAdjacentHTML(
          "beforeend",
          `<option value="${s.id}">#${s.id} — ${esc(strainLabel(item))} — ${esc(s.start_date || s.brew_date || "sem data")}</option>`
        );
      }
    }

    log(`Base carregada: ${state.items.length} item(ns), ${state.strains.length} cepa(s), ${state.starters.length} starter(s).`);
  }

  function renderStartersTable() {
    const tbody = el("starters-tbody");
    if (!tbody) return;

    const fStrain = (el("stFilterStrain")?.value || "").trim().toLowerCase();
    const fStatus = (el("stFilterStatus")?.value || "").trim().toLowerCase();
    const fBrewday = (el("stFilterBrewday")?.value || "").trim().toLowerCase();
    const fStart = (el("stFilterStart")?.value || "").trim().toLowerCase();

    const filtered = state.starters.filter(s => {
      const item = itemById(s.bank_item_id);
      const strain = strainLabel(item).toLowerCase();
      const status = (s.status || "").toLowerCase();
      const brew = (s.brew_date || "").toLowerCase();
      const start = (s.start_date || "").toLowerCase();

      return (!fStrain || strain.includes(fStrain))
        && (!fStatus || status.includes(fStatus))
        && (!fBrewday || brew.includes(fBrewday))
        && (!fStart || start.includes(fStart));
    });

    if (!filtered.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="text-muted">Nenhum starter encontrado.</td></tr>`;
      return;
    }

    tbody.innerHTML = filtered.map(s => {
      const item = itemById(s.bank_item_id);
      return `
        <tr>
          <td>${s.id}</td>
          <td>${esc(item ? itemLabel(item) : `#${s.bank_item_id}`)}</td>
          <td>${esc(strainLabel(item))}</td>
          <td>${esc(s.start_date || "")}</td>
          <td>${esc(s.brew_date || "")}</td>
          <td>${esc(s.target_volume_l ?? "")}</td>
          <td>${esc(objectiveLabel(s.objective))}</td>
          <td>${statusBadge(s.status)}</td>
          <td>
            <div class="d-flex gap-2">
              <button class="btn btn-sm btn-outline-primary" data-action="edit" data-id="${s.id}" type="button"><i class="bi bi-pencil"></i></button>
              <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${s.id}" type="button"><i class="bi bi-trash"></i></button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  }

  async function saveStarter() {
    hideBox("starterErr");

    const starterId = el("starterId")?.value || "";
    const bankItemId = Number(el("starter_bank_item_id")?.value || 0);
    if (!bankItemId) {
      showBox("starterErr", "Selecione um item do banco válido.");
      return;
    }

    const payload = {
      bank_item_id: bankItemId,
      brew_date: el("brew_date")?.value || null,
      start_date: el("start_date")?.value || null,
      target_volume_l: el("target_volume_l")?.value ? Number(el("target_volume_l").value) : null,
      objective: el("objective")?.value || null,
      status: el("status")?.value || "planned",
      notes: el("starter_notes")?.value || null,
      contamination_detected: el("starter_contamination_detected")?.value === "true",
      action_on_bank_item: el("starter_result_action")?.value || null
    };

    const endpoint = starterId ? `${API.starters}/${starterId}` : API.starters;
    const method = starterId ? "PUT" : "POST";

    const { ok, data } = await fetchJson(endpoint, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!ok || !data.ok) {
      showBox("starterErr", data.error || "Falha ao salvar starter");
      return;
    }

    try {
      starterModal().hide();
    } catch (err) {
      warn("Modal não pôde ser fechado após salvar:", err);
    }

    await reloadEverything();
    showBox("ok", starterId ? "Starter atualizado." : "Starter criado.");
  }

  async function deleteStarter(id) {
    if (!window.confirm("Excluir este starter?")) return;

    const { ok, data } = await fetchJson(`${API.starters}/${id}`, { method: "DELETE" });
    if (!ok || !data.ok) {
      showBox("err", data.error || "Falha ao excluir starter");
      return;
    }

    await reloadEverything();
    showBox("ok", "Starter excluído.");
  }

  async function exportJson() {
    const { ok, data } = await fetchJson(API.starterExportJson);
    if (!ok || !data.ok) {
      showBox("err", data.error || "Falha ao exportar JSON");
      return;
    }

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "yeast_bank_starters.json";
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  }

  async function importJson(file) {
    if (!file) return;

    let parsed;
    try {
      parsed = JSON.parse(await file.text());
    } catch (_) {
      showBox("err", "JSON inválido.");
      return;
    }

    const items = Array.isArray(parsed) ? parsed : (parsed.items || []);
    if (!Array.isArray(items) || !items.length) {
      showBox("warn", "Nenhum starter encontrado no JSON.");
      return;
    }

    for (const item of items) {
      await fetchJson(API.starters, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          bank_item_id: item.bank_item_id,
          brew_date: item.brew_date || null,
          start_date: item.start_date || null,
          target_volume_l: item.target_volume_l ?? null,
          objective: item.objective || null,
          status: item.status || "planned",
          notes: item.notes || null,
          contamination_detected: Boolean(item.contamination_detected),
          action_on_bank_item: item.action_on_bank_item || null
        })
      });
    }

    await reloadEverything();
    showBox("ok", "Importação concluída.");
  }

  function buildInputs(containerId, method, defaults = {}) {
    const box = el(containerId);
    if (!box) return;

    box.innerHTML = "";
    for (const inp of (method?.inputs || [])) {
      const id = `${containerId}_${inp.key}`;
      const label = inp.label || inp.key;
      const type = inp.type || "number";
      const wrap = document.createElement("div");
      wrap.className = "mb-2";

      if (type === "list_number") {
        wrap.innerHTML = `
          <label class="form-label">${esc(label)}</label>
          <input id="${esc(id)}" class="form-control" placeholder="ex: 120, 135, 110" value="${esc(defaults[inp.key] || "")}">
          <div class="form-text">Separe por vírgula.</div>
        `;
      } else {
        wrap.innerHTML = `
          <label class="form-label">${esc(label)}</label>
          <input id="${esc(id)}" type="number" step="any" class="form-control" value="${esc(defaults[inp.key] ?? "")}">
        `;
      }
      box.appendChild(wrap);
    }
  }

  function readInputs(containerId, method) {
    const out = {};
    for (const inp of (method?.inputs || [])) {
      const raw = (el(`${containerId}_${inp.key}`)?.value || "").trim();
      if (inp.type === "list_number") {
        out[inp.key] = raw.split(",").map(x => Number(x.trim())).filter(Number.isFinite);
      } else {
        out[inp.key] = Number(raw);
      }
    }
    return out;
  }

  function setMetricOutputs() {
    setText("out_cells_per_ml", fmtNum(state.lastResults.cells_per_ml));
    setText("out_viability", fmtPct(state.lastResults.viability_percent));
    setText("out_estimated_viability", fmtPct(state.lastResults.estimated_viability_percent));

    if (state.lastResults.cells_per_ml != null && state.lastResults.viability_percent != null) {
      const viable = (Number(state.lastResults.cells_per_ml) * Number(state.lastResults.viability_percent)) / 100;
      setText("out_viable_cells_per_ml", fmtNum(viable));
    } else {
      setText("out_viable_cells_per_ml", "—");
    }
  }

  function ensureSelectFallbacks() {
    const placeholders = [
      ["count_method", "Carregando métodos de contagem..."],
      ["viab_method", "Carregando métodos de viabilidade..."],
      ["viab_model", "Carregando modelos..."],
      ["starter_bank_item_id", "Carregando itens do banco..."],
      ["bank_item_id", "Carregando itens do banco..."],
      ["strain_id", "Carregando cepas..."],
      ["starter_link_id", "(opcional)"]
    ];

    for (const [id, text] of placeholders) {
      const node = el(id);
      if (!node) continue;
      if (!node.options.length) {
        node.innerHTML = `<option value="">${esc(text)}</option>`;
      }
    }
  }

  async function loadCatalog() {
    const { ok, data } = await fetchJson(API.calcs);
    if (!ok || !data.ok) {
      throw new Error(data.error || "Falha ao carregar catálogo");
    }

    state.catalog = data.catalog || {
      cell_count_methods: [],
      viability_methods: [],
      viability_models: []
    };

    const countMethods = state.catalog.cell_count_methods || [];
    const viabMethods = state.catalog.viability_methods || [];
    const models = state.catalog.viability_models || [];

    const countSelect = el("count_method");
    const viabSelect = el("viab_method");
    const modelSelect = el("viab_model");
    const histMethod = el("hist_calc_method");

    if (countSelect) {
      countSelect.innerHTML = countMethods.length
        ? countMethods.map(m => `<option value="${esc(m.id)}">${esc(m.name || m.id)}</option>`).join("")
        : `<option value="">Nenhum método de contagem disponível</option>`;
    }

    if (viabSelect) {
      viabSelect.innerHTML = viabMethods.length
        ? viabMethods.map(m => `<option value="${esc(m.id)}">${esc(m.name || m.id)}</option>`).join("")
        : `<option value="">Nenhum método de viabilidade disponível</option>`;
    }

    if (modelSelect) {
      modelSelect.innerHTML = models.length
        ? models.map(m => `<option value="${esc(m.id)}">${esc(m.name || m.id)}</option>`).join("")
        : `<option value="">Nenhum modelo disponível</option>`;
    }

    if (histMethod) {
      histMethod.innerHTML = `<option value="">(todos)</option>` + countMethods.map(m => `<option value="${esc(m.id)}">${esc(m.name || m.id)}</option>`).join("");
    }

    if (countSelect && countMethods.length) {
      const selected = countMethods.find(m => m.id === countSelect.value) || countMethods[0];
      buildInputs("countInputs", selected, { dilution: 100 });
    }

    if (viabSelect && viabMethods.length) {
      const selected = viabMethods.find(m => m.id === viabSelect.value) || viabMethods[0];
      buildInputs("viabInputs", selected, {});
    }

    if (modelSelect && models.length) {
      const selected = models.find(m => m.id === modelSelect.value) || models[0];
      buildInputs("modelInputs", selected, { v0: 96, days: 0 });
    }

    log(`Catálogo carregado: ${countMethods.length} método(s) de contagem, ${viabMethods.length} método(s) de viabilidade, ${models.length} modelo(s).`);
  }

  async function runCalc(kind, calcId, inputs) {
    const { ok, data } = await fetchJson(API.run, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, calc_id: calcId, inputs })
    });

    if (!ok || !data.ok) {
      throw new Error(data.error || "Falha no cálculo");
    }

    return data.result || {};
  }

  async function doCountCalc() {
    clearAlerts();
    try {
      const calcId = el("count_method")?.value;
      const method = (state.catalog.cell_count_methods || []).find(m => m.id === calcId);
      if (!calcId || !method) {
        showBox("warn", "Selecione um método de contagem válido.");
        return;
      }

      const inputs = readInputs("countInputs", method);
      const result = await runCalc("cell_count", calcId, inputs);
      state.lastResults.cells_per_ml = result.cells_per_ml ?? null;
      setMetricOutputs();
      showBox("ok", "Contagem calculada.");
    } catch (err) {
      errorLog("Erro na contagem:", err);
      showBox("err", err.message || "Erro na contagem");
    }
  }

  async function doViabilityCalc() {
    clearAlerts();
    try {
      const calcId = el("viab_method")?.value;
      const method = (state.catalog.viability_methods || []).find(m => m.id === calcId);
      if (!calcId || !method) {
        showBox("warn", "Selecione um método de viabilidade válido.");
        return;
      }

      const inputs = readInputs("viabInputs", method);
      const result = await runCalc("viability", calcId, inputs);
      state.lastResults.viability_percent = result.viability_percent ?? null;
      setMetricOutputs();
      showBox("ok", "Viabilidade calculada.");
    } catch (err) {
      errorLog("Erro na viabilidade:", err);
      showBox("err", err.message || "Erro na viabilidade");
    }
  }

  async function doModelCalc() {
    clearAlerts();
    try {
      const calcId = el("viab_model")?.value;
      const method = (state.catalog.viability_models || []).find(m => m.id === calcId);
      if (!calcId || !method) {
        showBox("warn", "Selecione um modelo de viabilidade válido.");
        return;
      }

      const inputs = readInputs("modelInputs", method);
      const result = await runCalc("viability_model", calcId, inputs);
      state.lastResults.estimated_viability_percent = result.estimated_viability_percent ?? null;
      setMetricOutputs();
      showBox("ok", "Viabilidade estimada calculada.");
    } catch (err) {
      errorLog("Erro na viabilidade estimada:", err);
      showBox("err", err.message || "Erro na viabilidade estimada");
    }
  }

  async function saveHistory() {
    clearAlerts();

    const bankItemId = Number(el("bank_item_id")?.value || 0) || null;
    const derivedStrainId = currentStrainIdFromItem();
    const strainId = Number(el("strain_id")?.value || 0) || derivedStrainId;

    if (!strainId) {
      showBox("warn", "Selecione uma cepa ou item do banco.");
      return;
    }

    if (!el("sample_date")?.value) {
      showBox("warn", "Informe a data da amostra.");
      return;
    }

    if (state.lastResults.cells_per_ml == null) {
      showBox("warn", "Calcule a contagem antes de salvar.");
      return;
    }

    const payload = {
      strain_id: strainId,
      bank_item_id: bankItemId,
      starter_id: Number(el("starter_link_id")?.value || 0) || null,
      lot_code: el("lot_code")?.value || null,
      sample_date: el("sample_date")?.value,
      calc_method_id: el("count_method")?.value,
      cells_per_ml: state.lastResults.cells_per_ml,
      viability_percent: state.lastResults.viability_percent,
      viable_cells_per_ml: state.lastResults.cells_per_ml != null && state.lastResults.viability_percent != null
        ? Number(state.lastResults.cells_per_ml) * Number(state.lastResults.viability_percent) / 100
        : null,
      estimated_viability_percent: state.lastResults.estimated_viability_percent,
      contamination_detected: el("contamination_detected")?.value === "true",
      bank_item_status_action: el("result_action")?.value || null,
      notes: el("notes")?.value || null,
      raw_inputs: {
        count_method: el("count_method")?.value || null,
        viability_method: el("viab_method")?.value || null,
        viability_model: el("viab_model")?.value || null
      }
    };

    const { ok, data } = await fetchJson(API.history, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!ok || !data.ok) {
      showBox("err", data.error || "Falha ao salvar histórico");
      return;
    }

    showBox("ok", "Registro salvo no histórico.");
    await reloadEverything();
  }

  function renderHistoryTable(items) {
    const tbody = el("histRows");
    if (!tbody) return;

    if (!items.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-muted">Sem dados.</td></tr>`;
      return;
    }

    tbody.innerHTML = items.map(r => `
      <tr>
        <td>${esc(r.sample_date || "")}</td>
        <td>${esc(r.lot_code || "")}</td>
        <td>${esc(r.calc_method_id || "")}</td>
        <td>${fmtNum(r.cells_per_ml)}</td>
        <td>${fmtPct(r.viability_percent)}</td>
        <td>${fmtPct(r.estimated_viability_percent)}</td>
      </tr>
    `).join("");
  }

  function drawChart(items) {
    const canvas = el("viabChart");
    if (!canvas) return;

    if (typeof Chart === "undefined") {
      warn("Chart.js não carregado; gráfico não será exibido.");
      return;
    }

    if (state.chart) {
      state.chart.destroy();
      state.chart = null;
    }

    state.chart = new Chart(canvas, {
      type: "line",
      data: {
        labels: items.map(i => i.sample_date),
        datasets: [
          {
            label: "Viabilidade real (%)",
            data: items.map(i => i.viability_percent ?? null),
            tension: 0.25,
            spanGaps: true
          },
          {
            label: "Viabilidade estimada (%)",
            data: items.map(i => i.estimated_viability_percent ?? null),
            tension: 0.25,
            spanGaps: true
          }
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

    const bankItemId = Number(el("bank_item_id")?.value || 0) || null;
    const strainId = Number(el("strain_id")?.value || 0) || currentStrainIdFromItem();

    if (!strainId && !bankItemId) {
      showBox("warn", "Selecione uma cepa ou item para carregar o histórico.");
      return;
    }

    const params = new URLSearchParams();
    if (strainId) params.set("strain_id", String(strainId));
    if (bankItemId) params.set("bank_item_id", String(bankItemId));
    if (el("hist_lot_code")?.value) params.set("lot_code", el("hist_lot_code").value);
    if (el("hist_calc_method")?.value) params.set("calc_method_id", el("hist_calc_method").value);
    if (el("starter_link_id")?.value) params.set("starter_id", el("starter_link_id").value);

    const { ok, data } = await fetchJson(`${API.history}?${params.toString()}`);
    if (!ok || !data.ok) {
      showBox("err", data.error || "Falha ao carregar histórico");
      return;
    }

    const items = data.items || [];
    renderHistoryTable(items);
    drawChart(items);
    showBox("ok", `Histórico carregado: ${items.length} registro(s).`);
  }

  async function recalculateViability() {
    clearAlerts();

    const { ok, data } = await fetchJson(API.recalculateViability, { method: "POST" });
    if (!ok || !data.ok) {
      showBox("err", data.error || "Falha ao recalcular viabilidade.");
      return;
    }

    await reloadEverything();
    showBox("ok", `Recalculo concluído. Atualizados: ${data.updated || 0}; sem referência: ${data.items_without_reference || 0}.`);
  }

  async function reloadEverything() {
    await loadBaseData();
    renderStartersTable();
    syncStrainFromItemSelection();
  }

  function bindStarterTableActions() {
    const tbody = el("starters-tbody");
    if (!tbody) return;
    if (tbody.dataset.boundClick === "1") return;
    tbody.dataset.boundClick = "1";

    tbody.addEventListener("click", async (ev) => {
      const btn = ev.target.closest("button[data-action]");
      if (!btn) return;

      const id = Number(btn.getAttribute("data-id") || 0);
      if (!id) return;

      const action = btn.getAttribute("data-action");
      if (action === "edit") {
        const starter = state.starters.find(s => Number(s.id) === id);
        if (starter) openStarterModal(starter);
        return;
      }

      if (action === "delete") {
        await deleteStarter(id);
      }
    });
  }

  function bindEvents() {
    log("Ligando eventos da tela...");

    safeBind("btnNewStarter", "click", () => openStarterModal(null));
    safeBind("btnSaveStarter", "click", saveStarter);
    safeBind("btnRecalcStart", "click", () => tryAutoSetStartDate(true));
    safeBind("brew_date", "change", () => tryAutoSetStartDate(false));
    safeBind("btnCountCalc", "click", doCountCalc);
    safeBind("btnViabCalc", "click", doViabilityCalc);
    safeBind("btnModelCalc", "click", doModelCalc);
    safeBind("btnSaveHistory", "click", saveHistory);
    safeBind("btnLoadHistory", "click", loadHistory);
    safeBind("btnRecalculateViability", "click", recalculateViability);
    safeBind("export-csv", "click", () => { window.location.href = API.starterExportCsv; });
    safeBind("export-json", "click", exportJson);
    safeBind("btnImportJson", "click", () => el("importJsonFile")?.click());

    safeBind("importJsonFile", "change", async (ev) => {
      await importJson(ev.target.files?.[0]);
      ev.target.value = "";
    });

    ["stFilterStrain", "stFilterStatus", "stFilterBrewday", "stFilterStart"].forEach(id => {
      const eventName = id === "stFilterStatus" ? "change" : "input";
      safeBind(id, eventName, renderStartersTable);
    });

    safeBind("btnClearStarterFilters", "click", () => {
      ["stFilterStrain", "stFilterStatus", "stFilterBrewday", "stFilterStart"].forEach(id => {
        if (el(id)) el(id).value = "";
      });
      renderStartersTable();
    });

    safeBind("count_method", "change", () => {
      const calcId = el("count_method")?.value;
      const method = (state.catalog?.cell_count_methods || []).find(m => m.id === calcId);
      buildInputs("countInputs", method, { dilution: 100 });
    });

    safeBind("viab_method", "change", () => {
      const calcId = el("viab_method")?.value;
      const method = (state.catalog?.viability_methods || []).find(m => m.id === calcId);
      buildInputs("viabInputs", method, {});
    });

    safeBind("viab_model", "change", () => {
      const calcId = el("viab_model")?.value;
      const method = (state.catalog?.viability_models || []).find(m => m.id === calcId);
      buildInputs("modelInputs", method, { v0: 96, days: 0 });
    });

    safeBind("bank_item_id", "change", syncStrainFromItemSelection);

    safeBind("starter_link_id", "change", () => {
      const starterId = Number(el("starter_link_id")?.value || 0);
      const starter = state.starters.find(s => Number(s.id) === starterId);
      if (starter && starter.bank_item_id && el("bank_item_id")) {
        el("bank_item_id").value = String(starter.bank_item_id);
        syncStrainFromItemSelection();
      }
    });

    bindStarterTableActions();
  }

  async function init() {
    if (state.initialized) {
      log("Init já executado anteriormente; ignorando nova inicialização.");
      return;
    }

    state.initialized = true;
    log("Inicializando página Starter & Contagem...");

    clearAlerts();
    ensureSelectFallbacks();
    bindEvents();

    try {
      await loadBaseData();
    } catch (err) {
      errorLog("Erro em loadBaseData:", err);
      showBox("err", err.message || "Falha ao carregar starters / itens / cepas.");
    }

    try {
      await loadCatalog();
    } catch (err) {
      errorLog("Erro em loadCatalog:", err);
      showBox("warn", "Catálogo de cálculos não pôde ser carregado. Algumas ferramentas podem ficar indisponíveis.");
    }

    try {
      renderStartersTable();
      setMetricOutputs();

      if (el("sample_date") && !el("sample_date").value) {
        el("sample_date").value = new Date().toISOString().slice(0, 10);
      }

      log("Página inicializada com sucesso.");
    } catch (err) {
      errorLog("Erro ao renderizar página:", err);
      showBox("err", "A página carregou parcialmente, mas houve erro ao montar a interface.");
    }
  }

  window.addEventListener("load", init);
})();
