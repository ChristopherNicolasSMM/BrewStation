(() => {
  const API_STARTERS = "/api/yeast_bank/starters";
  const API_ITEMS = "/api/yeast_bank/items";

  let dataTable = null;
  let bankItemsCache = []; // para mapear item -> cepa label

  const el = (id) => document.getElementById(id);

  function showError(msg) {
    const box = el("err");
    if (!box) return;
    box.textContent = msg || "Erro";
    box.classList.remove("d-none");
  }
  function clearError() {
    const box = el("err");
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
      canceled: "danger"
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
    const sel = el("bank_item_id");
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
    const table = el("starters-table");
    if (!table) return;

    let tbody = el("starters-tbody");
    if (!tbody) {
      tbody = document.createElement("tbody");
      tbody.id = "starters-tbody";
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

    // datatable
    if (dataTable) {
      try { dataTable.destroy(); } catch (_) {}
      dataTable = null;
    }

    dataTable = new simpleDatatables.DataTable("#starters-table", {
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

    bindFilters();
  }

  function bindFilters() {
    const inputs = document.querySelectorAll(".filter-input");
    const selects = document.querySelectorAll(".filter-select");
    const clearBtn = document.querySelector(".clear-filters");

    inputs.forEach(input => {
      input.addEventListener("keyup", function () {
        dataTable.filterColumn(this.getAttribute("data-column"), this.value);
      });
    });

    selects.forEach(select => {
      select.addEventListener("change", function () {
        dataTable.filterColumn(this.getAttribute("data-column"), this.value);
      });
    });

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        inputs.forEach(i => i.value = "");
        selects.forEach(s => s.selectedIndex = 0);
        dataTable.clearFilters();
      });
    }
  }

  function bindExportButtons() {
    el("export-csv")?.addEventListener("click", () => {
      window.location.href = "/api/yeast_bank/starters/export/csv";
    });

    el("export-json")?.addEventListener("click", () => {
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
    const auto = el("auto_start")?.checked;
    if (!auto && !force) return;

    const brew = el("brew_date").value;
    if (!brew) return;

    const brewDate = new Date(brew + "T00:00:00");
    const start = addDays(brewDate, -7);
    el("start_date").value = toISO(start);
  }

  async function openCreateModal() {
    clearError();
    el("starterId").value = "";
    el("starterModalLabel").textContent = "Novo starter";

    el("brew_date").value = "";
    el("start_date").value = "";
    el("target_volume_l").value = "";
    el("status").value = "planned";
    el("notes").value = "";
    el("auto_start").checked = true;

    await loadBankItemsIntoSelect();

    el("brew_date").onchange = () => tryAutoSetStartDate();
    el("btnRecalcStart").onclick = () => tryAutoSetStartDate(true);

    new bootstrap.Modal(el("starterModal")).show();
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

    el("starterId").value = starter.id;
    el("starterModalLabel").textContent = `Editar starter #${starter.id}`;

    el("bank_item_id").value = starter.bank_item_id;
    el("brew_date").value = starter.brew_date || "";
    el("start_date").value = starter.start_date || "";
    el("target_volume_l").value = starter.target_volume_l ?? "";
    el("status").value = starter.status || "planned";
    el("notes").value = starter.notes || "";
    el("auto_start").checked = false;

    el("brew_date").onchange = () => tryAutoSetStartDate();
    el("btnRecalcStart").onclick = () => tryAutoSetStartDate(true);

    new bootstrap.Modal(el("starterModal")).show();
  }

  async function saveStarter() {
    clearError();

    const bankItemId = el("bank_item_id").value;
    if (!bankItemId) {
      showError("Selecione um item do banco válido.");
      return;
    }

    const starterId = el("starterId").value;

    const payload = {
      bank_item_id: parseInt(bankItemId, 10),
      brew_date: el("brew_date").value || null,
      start_date: el("start_date").value || null,
      target_volume_l: el("target_volume_l").value ? parseFloat(el("target_volume_l").value) : null,
      status: el("status").value || "planned",
      notes: el("notes").value || null
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

    bootstrap.Modal.getInstance(el("starterModal")).hide();
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
    el("btnNewStarter")?.addEventListener("click", openCreateModal);
    el("btnSaveStarter")?.addEventListener("click", saveStarter);

    const btnImport = el("btnImportJson");
    const inputFile = el("importJsonFile");
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