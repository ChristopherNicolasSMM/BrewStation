(() => {
  const API_STARTERS = "/api/yeast_bank/starters";
  const API_ITEMS = "/api/yeast_bank/items";

  let dataTable = null;
  let bankItemsCache = []; // para mapear item -> cepa label

  const el = (id) => document.getElementById(id);

  function showError(msg) {
    const box = el("st_err");
    if (!box) return;
    box.textContent = msg || "Erro";
    box.classList.remove("d-none");
  }
  function clearError() {
    const box = el("st_err");
    if (!box) return;
    box.classList.add("d-none");
    box.textContent = "";
  }

  function addDays(dateObj, days) {
    const d = new Date(dateObj.getTime());
    d.setDate(d.getDate() + days);
    return d;
  }
  function toISO(dateObj) {
    const yyyy = dateObj.getFullYear();
    const mm = String(dateObj.getMonth() + 1).padStart(2, "0");
    const dd = String(dateObj.getDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }

  function badgeStatus(status) {
    const map = {
      planned: "secondary",
      running: "warning",
      done: "success",
      canceled: "danger",
      completed: "success",
      cancelled: "danger",
      contaminated: "danger",
      discarded: "dark",
      failed: "danger"
    };
    const c = map[status] || "secondary";
    const txt = status || "—";
    return `<span class="badge bg-${c}">${txt}</span>`;
  }

  function strainLabelFromItem(item) {
    const s = item?.strain || {};
    const code = (s.code || "").trim();
    const name = (s.name || "").trim();
    return (code || name) ? `${code ? code + " " : ""}${name}`.trim() : `Cepa #${item?.strain_id ?? "?"}`;
  }

  async function loadBankItemsCache() {
    const res = await fetch(API_ITEMS);
    const json = await res.json();
    bankItemsCache = (json.items || []);
  }

  function getItemLabel(bankItemId) {
    const it = bankItemsCache.find(x => x.id === bankItemId);
    if (!it) return `#${bankItemId}`;
    const strain = strainLabelFromItem(it);
    const storage = it.storage_type || "";
    const label = it.label ? ` • ${it.label}` : "";
    const loc = it.location ? ` • ${it.location}` : "";
    return `#${it.id} — ${strain} (${storage})${label}${loc}`;
  }

  function getStrainLabel(bankItemId) {
    const it = bankItemsCache.find(x => x.id === bankItemId);
    return it ? strainLabelFromItem(it) : "—";
  }

  async function loadBankItemsIntoSelect() {
    await loadBankItemsCache();
    const sel = el("st_bank_item_id");
    if (!sel) return;
    sel.innerHTML = "";

    if (bankItemsCache.length === 0) {
      const opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Nenhum item cadastrado no Banco";
      sel.appendChild(opt);
      return;
    }

    bankItemsCache.forEach(i => {
      const opt = document.createElement("option");
      opt.value = i.id;
      opt.textContent = getItemLabel(i.id);
      sel.appendChild(opt);
    });
  }

  function rowHtml(s) {
    const bid = s.bank_item_id;
    const strain = getStrainLabel(bid);

    return `
      <tr>
        <td>${s.id}</td>
        <td>${bid}</td>
        <td>${strain}</td>
        <td>${s.start_date || ""}</td>
        <td>${s.brew_date || ""}</td>
        <td>${s.target_volume_l ?? ""}</td>
        <td>${s.objective || ""}</td>
        <td>${badgeStatus(s.status)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${s.id}" type="button">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${s.id}" type="button">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }

  async function loadStarters() {
    const table = el("st_starters-table");
    if (!table) return;

    let tbody = el("st_starters-tbody");
    if (!tbody) {
      tbody = document.createElement("tbody");
      tbody.id = "st_starters-tbody";
      table.appendChild(tbody);
    }

    // cache items (para coluna cepa)
    await loadBankItemsCache();

    const res = await fetch(API_STARTERS);
    const json = await res.json();

    tbody.innerHTML = "";
    (json.items || []).forEach(s => {
      tbody.insertAdjacentHTML("beforeend", rowHtml(s));
    });

    // datatable é opcional; se o plugin base / CDN não carregar, a tela segue funcional.
    if (dataTable) {
      try { dataTable.destroy(); } catch (_) {}
      dataTable = null;
    }

    if (window.simpleDatatables && window.simpleDatatables.DataTable) {
      dataTable = new window.simpleDatatables.DataTable("#st_starters-table", {
        searchable: true,
        fixedHeight: true,
        perPage: 10,
        perPageSelect: [5, 10, 15, 20],
        labels: {
          placeholder: "Buscar...",
          perPage: "{select} itens por página",
          noRows: "Nenhum registro encontrado",
          info: "Mostrando {start} a {end} de {rows} registros"
        }
      });
    }

    bindFilters();
  }

  function applyFallbackFilters() {
    const inputs = [...document.querySelectorAll(".st_filter-input")];
    const selects = [...document.querySelectorAll(".st_filter-select")];
    const rows = [...document.querySelectorAll("#st_starters-tbody tr")];

    rows.forEach(row => {
      const cells = [...row.children].map(td => (td.textContent || "").toLowerCase());
      const matchesInputs = inputs.every(input => {
        const col = Number(input.getAttribute("data-column"));
        const term = (input.value || "").trim().toLowerCase();
        return !term || (cells[col] || "").includes(term);
      });
      const matchesSelects = selects.every(select => {
        const col = Number(select.getAttribute("data-column"));
        const term = (select.value || "").trim().toLowerCase();
        return !term || (cells[col] || "").includes(term);
      });
      row.style.display = (matchesInputs && matchesSelects) ? "" : "none";
    });
  }

  function bindFilters() {
    const inputs = document.querySelectorAll(".st_filter-input");
    const selects = document.querySelectorAll(".st_filter-select");
    const clearBtn = document.querySelector(".st_clear-filters");

    inputs.forEach(input => {
      input.onkeyup = function () {
        if (dataTable) dataTable.filterColumn(this.getAttribute("data-column"), this.value);
        else applyFallbackFilters();
      };
    });

    selects.forEach(select => {
      select.onchange = function () {
        if (dataTable) dataTable.filterColumn(this.getAttribute("data-column"), this.value);
        else applyFallbackFilters();
      };
    });

    if (clearBtn) {
      clearBtn.onclick = () => {
        inputs.forEach(i => i.value = "");
        selects.forEach(s => s.selectedIndex = 0);
        if (dataTable && dataTable.clearFilters) dataTable.clearFilters();
        else applyFallbackFilters();
      };
    }
  }

  function bindExportButtons() {
    el("st_export-csv")?.addEventListener("click", () => {
      window.location.href = "/api/yeast_bank/starters/export/csv";
    });

    el("st_export-json")?.addEventListener("click", () => {
      fetch("/api/yeast_bank/starters/export/json")
        .then(r => r.json())
        .then(data => {
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "yeast_bank_starters.json";
          document.body.appendChild(a);
          a.click();
          a.remove();
          URL.revokeObjectURL(url);
        })
        .catch(() => alert("Falha ao exportar JSON"));
    });
  }

  async function importJson(file) {
    if (!file) return;
    const text = await file.text();

    let data;
    try { data = JSON.parse(text); }
    catch { alert("JSON inválido."); return; }

    const items = Array.isArray(data) ? data : (data.items || []);
    if (!Array.isArray(items) || items.length === 0) {
      alert("Nenhum starter encontrado no JSON.");
      return;
    }

    // import simples: cria tudo como POST
    for (const it of items) {
      const payload = {
        bank_item_id: it.bank_item_id,
        brew_date: it.brew_date || null,
        start_date: it.start_date || null,
        target_volume_l: it.target_volume_l ?? null,
        status: it.status || "planned",
        notes: it.notes || null
      };

      await fetch(API_STARTERS, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    alert("Importação concluída.");
    await loadStarters();
  }

  function tryAutoSetStartDate(force = false) {
    const auto = el("st_auto_start")?.checked;
    if (!auto && !force) return;

    const brew = el("st_brew_date").value;
    if (!brew) return;

    const brewDate = new Date(brew + "T00:00:00");
    const start = addDays(brewDate, -7);
    el("st_start_date").value = toISO(start);
  }

  async function openCreateModal() {
    clearError();
    el("st_starterId").value = "";
    el("st_starterModalLabel").textContent = "Novo starter";

    el("st_brew_date").value = "";
    el("st_start_date").value = "";
    el("st_target_volume_l").value = "";
    el("st_status").value = "planned";
    el("st_objective").value = "brew";
    el("st_result_viability_percent").value = "";
    el("st_contamination_detected").value = "false";
    el("st_bank_item_status_action").value = "";
    el("st_notes").value = "";
    el("st_auto_start").checked = true;

    await loadBankItemsIntoSelect();

    el("st_brew_date").onchange = () => tryAutoSetStartDate();
    el("st_btnRecalcStart").onclick = () => tryAutoSetStartDate(true);

    bootstrap.Modal.getOrCreateInstance(el("st_starterModal")).show();
  }

  async function openEditModal(starterId) {
    clearError();
    await loadBankItemsIntoSelect();

    const res = await fetch(API_STARTERS);
    const json = await res.json();
    const starter = (json.items || []).find(x => x.id === starterId);
    if (!starter) {
      alert("Starter não encontrado para edição.");
      return;
    }

    el("st_starterId").value = starter.id;
    el("st_starterModalLabel").textContent = `Editar starter #${starter.id}`;

    el("st_bank_item_id").value = starter.bank_item_id;
    el("st_brew_date").value = starter.brew_date || "";
    el("st_start_date").value = starter.start_date || "";
    el("st_target_volume_l").value = starter.target_volume_l ?? "";
    el("st_status").value = starter.status || "planned";
    el("st_objective").value = starter.objective || "brew";
    el("st_result_viability_percent").value = starter.result_viability_percent ?? "";
    el("st_contamination_detected").value = starter.contamination_detected ? "true" : "false";
    el("st_bank_item_status_action").value = starter.action_on_bank_item || "";
    el("st_notes").value = starter.notes || "";
    el("st_auto_start").checked = false;

    el("st_brew_date").onchange = () => tryAutoSetStartDate();
    el("st_btnRecalcStart").onclick = () => tryAutoSetStartDate(true);

    bootstrap.Modal.getOrCreateInstance(el("st_starterModal")).show();
  }

  async function saveStarter() {
    clearError();

    const bankItemId = el("st_bank_item_id").value;
    if (!bankItemId) {
      showError("Selecione um item do banco válido.");
      return;
    }

    const starterId = el("st_starterId").value;

    const payload = {
      bank_item_id: parseInt(bankItemId, 10),
      brew_date: el("st_brew_date").value || null,
      start_date: el("st_start_date").value || null,
      target_volume_l: el("st_target_volume_l").value ? parseFloat(el("st_target_volume_l").value) : null,
      objective: el("st_objective").value || "brew",
      status: el("st_status").value || "planned",
      result_viability_percent: el("st_result_viability_percent").value ? parseFloat(el("st_result_viability_percent").value) : null,
      contamination_detected: (el("st_contamination_detected").value || "false") === "true",
      bank_item_status_action: el("st_bank_item_status_action").value || null,
      notes: el("st_notes").value || null
    };

    const url = starterId ? `${API_STARTERS}/${starterId}` : API_STARTERS;
    const method = starterId ? "PUT" : "POST";

    const res = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    let json;
    try { json = await res.json(); }
    catch { showError("Resposta inválida do servidor."); return; }

    if (!res.ok || !json.ok) {
      showError(json.error || "Erro ao salvar");
      return;
    }

    bootstrap.Modal.getOrCreateInstance(el("st_starterModal")).hide();
    await loadStarters();
  }

  function bindTableActions() {
    document.removeEventListener("click", onTableClick);
    document.addEventListener("click", onTableClick);
  }

  async function onTableClick(ev) {
    const btn = ev.target.closest('button[data-action]');
    if (!btn) return;

    const action = btn.getAttribute("data-action");
    const id = btn.getAttribute("data-id");
    if (!action || !id) return;

    if (action === "delete") {
      if (!confirm("Excluir este starter?")) return;

      const res = await fetch(`${API_STARTERS}/${id}`, { method: "DELETE" });

      let json;
      try { json = await res.json(); }
      catch { alert("Erro no servidor ao excluir. Veja o log."); return; }

      if (!res.ok || !json.ok) {
        alert(json.error || "Erro ao excluir");
        return;
      }

      await loadStarters();
      return;
    }

    if (action === "edit") {
      await openEditModal(parseInt(id, 10));
      return;
    }
  }

  function bindTopButtons() {
    el("st_btnNewStarter")?.addEventListener("click", openCreateModal);
    el("st_btnSaveStarter")?.addEventListener("click", saveStarter);

    const btnImport = el("st_btnImportJson");
    const inputFile = el("st_importJsonFile");
    if (btnImport && inputFile) {
      btnImport.addEventListener("click", () => inputFile.click());
      inputFile.addEventListener("change", async (ev) => {
        const file = ev.target.files?.[0];
        await importJson(file);
        ev.target.value = "";
      });
    }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    bindTopButtons();
    bindExportButtons();
    bindTableActions();
    await loadStarters();
  });
})();