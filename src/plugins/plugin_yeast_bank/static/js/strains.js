(() => {
  const API = "/api/yeast_bank/strains";

  let dataTable = null;
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

  function rowHtml(s) {
    return `
      <tr>
        <td>${s.id}</td>
        <td>${s.code || ""}</td>
        <td>${s.name || ""}</td>
        <td>${s.family || ""}</td>
        <td>${s.supplier || ""}</td>
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

  async function loadStrains() {
    const table = el("strains-table");
    if (!table) return;

    let tbody = el("strains-tbody");
    if (!tbody) {
      tbody = document.createElement("tbody");
      tbody.id = "strains-tbody";
      table.appendChild(tbody);
    }

    const res = await fetch(API);
    const json = await res.json();

    tbody.innerHTML = "";
    (json.items || []).forEach(s => {
      tbody.insertAdjacentHTML("beforeend", rowHtml(s));
    });

    if (dataTable) {
      try { dataTable.destroy(); } catch (_) {}
      dataTable = null;
    }

    dataTable = new simpleDatatables.DataTable("#strains-table", {
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
    const clearBtn = document.querySelector(".clear-filters");

    inputs.forEach(input => {
      input.addEventListener("keyup", function () {
        dataTable.filterColumn(this.getAttribute("data-column"), this.value);
      });
    });

    clearBtn?.addEventListener("click", () => {
      inputs.forEach(i => i.value = "");
      dataTable.clearFilters();
    });
  }

  function bindExportButtons() {
    el("export-csv")?.addEventListener("click", () => {
      window.location.href = "/api/yeast_bank/strains/export/csv";
    });

    el("export-json")?.addEventListener("click", () => {
      fetch("/api/yeast_bank/strains/export/json")
        .then(r => r.json())
        .then(data => {
          const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = "yeast_bank_strains.json";
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
      alert("Nenhuma cepa encontrada no JSON.");
      return;
    } 

    for (const it of items) {
      const payload = {
        code: it.code || null,
        name: (it.name || "").trim(),
        family: it.family || null,
        supplier: it.supplier || null,
        notes: it.notes || null
      };
      if (!payload.name) continue;

      await fetch(API, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
    }

    alert("Importação concluída.");
    await loadStrains();
  }

  async function openCreateModal() {
    clearError();
    el("strainId").value = "";
    el("strainModalLabel").textContent = "Nova cepa";

    el("code").value = "";
    el("name").value = "";
    el("family").value = "";
    el("supplier").value = "";
    el("notes").value = "";

    new bootstrap.Modal(el("strainModal")).show();
  }

  async function openEditModal(strainId) {
    clearError();

    const res = await fetch(API);
    const json = await res.json();
    const strain = (json.items || []).find(x => x.id === strainId);
    if (!strain) {
      alert("Cepa não encontrada para edição.");
      return;
    }

    el("strainId").value = strain.id;
    el("strainModalLabel").textContent = `Editar cepa #${strain.id}`;

    el("code").value = strain.code || "";
    el("name").value = strain.name || "";
    el("family").value = strain.family || "";
    el("supplier").value = strain.supplier || "";
    el("notes").value = strain.notes || "";

    new bootstrap.Modal(el("strainModal")).show();
  }

  async function saveStrain() {
    clearError();

    const strainId = el("strainId").value;
    const payload = {
      code: el("code").value || null,
      name: (el("name").value || "").trim(),
      family: el("family").value || null,
      supplier: el("supplier").value || null,
      notes: el("notes").value || null
    };

    if (!payload.name) {
      showError("O campo Nome é obrigatório.");
      return;
    }

    const url = strainId ? `${API}/${strainId}` : API;
    const method = strainId ? "PUT" : "POST";

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

    bootstrap.Modal.getInstance(el("strainModal")).hide();
    await loadStrains();
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
      if (!confirm("Excluir esta cepa? (só se não tiver itens no banco)")) return;

      const res = await fetch(`${API}/${id}`, { method: "DELETE" });

      let json;
      try { json = await res.json(); }
      catch { alert("Erro no servidor ao excluir. Veja o log."); return; }

      if (!res.ok || !json.ok) {
        alert(json.error || "Erro ao excluir");
        return;
      }

      await loadStrains();
      return;
    }

    if (action === "edit") {
      await openEditModal(parseInt(id, 10));
      return;
    }
  }

  function bindTopButtons() {
    el("btnNewStrain")?.addEventListener("click", openCreateModal);
    el("btnSaveStrain")?.addEventListener("click", saveStrain);

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
    await loadStrains();
  });
})();