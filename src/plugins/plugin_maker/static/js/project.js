(() => {
  const API = "/api/maker";
  const pid = window.__MAKER_PROJECT_ID__;
  const el = (id) => document.getElementById(id);

  function setErr(msg) {
    const b = el("err");
    if (!b) return;
    b.textContent = msg || "Erro";
    b.classList.remove("d-none");
    el("ok")?.classList.add("d-none");
  }
  function setOk(msg) {
    const b = el("ok");
    if (b && msg) b.textContent = msg;
    el("ok")?.classList.remove("d-none");
    el("err")?.classList.add("d-none");
  }
  function hideAlerts() {
    el("ok")?.classList.add("d-none");
    el("err")?.classList.add("d-none");
  }

  async function getJson(url, opts = {}) {
    const r = await fetch(url, {
      ...opts,
      headers: { "Accept": "application/json", ...(opts.headers || {}) },
    });
    const text = await r.text();
    let json = null;
    try {
      json = text ? JSON.parse(text) : null;
    } catch {
      console.error("Resposta não é JSON:", text.slice(0, 200));
    }
    if (!r.ok) console.error("HTTP", r.status, text.slice(0, 200));
    return { res: r, json };
  }

  let project = null;
  let tables = [];
  let activeTableId = null;
  let columns = [];

  function tableRow(t) {
    const active = t.id === activeTableId ? "table-primary" : "";
    return `
      <tr class="${active}" data-table-id="${t.id}" style="cursor:pointer">
        <td>${t.name}</td>
        <td>${t.label}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary me-1" data-action="edit-table" data-id="${t.id}">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" data-action="del-table" data-id="${t.id}">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }

  function colRow(c) {
    const yes = (v) => (v ? "✓" : "");
    return `
      <tr>
        <td>${c.name}</td>
        <td>${c.label}</td>
        <td>${c.data_type}${c.length ? `(${c.length})` : ""}</td>
        <td>${yes(c.required)}</td>
        <td>${yes(c.unique)}</td>
        <td>${yes(c.indexed)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary me-1" data-action="edit-col" data-id="${c.id}">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" data-action="del-col" data-id="${c.id}">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
  }

  async function loadProject() {
    const { res, json } = await getJson(`${API}/projects/${pid}`);
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Projeto não encontrado");
      return;
    }
    project = json.item;
    // preencher modal (campos read-only de dir/name)
    el("projectId").value = project.id;
    el("plugin_dir").value = project.plugin_dir;
    el("plugin_name").value = project.plugin_name;
    el("label").value = project.label || "";
    el("version").value = project.version || "0.1.0";
    el("table_prefix").value = project.table_prefix || "";
    el("description").value = project.description || "";
  }

  async function loadTables() {
    const { res, json } = await getJson(`${API}/projects/${pid}/tables`);
    const tb = el("tables-tbody");
    tb.innerHTML = "";
    if (!res.ok || !json?.ok) {
      tb.innerHTML = `<tr><td colspan="3" class="text-danger">${json?.error || "Erro ao carregar tabelas"}</td></tr>`;
      return;
    }
    tables = json.items || [];
    if (!tables.length) {
      tb.innerHTML = `<tr><td colspan="3" class="text-muted">Nenhuma tabela. Clique em "Nova Tabela" para começar.</td></tr>`;
      activeTableId = null;
      el("btnNewColumn").disabled = true;
      await loadColumns(null);
      return;
    }
    tables.forEach(t => tb.insertAdjacentHTML("beforeend", tableRow(t)));
    // manter seleção
    if (!activeTableId || !tables.some(t => t.id === activeTableId)) {
      activeTableId = tables[0].id;
    }
    renderTablesHighlight();
    el("btnNewColumn").disabled = false;
    await loadColumns(activeTableId);
  }

  function renderTablesHighlight() {
    const tb = el("tables-tbody");
    [...tb.querySelectorAll("tr[data-table-id]")].forEach(tr => {
      const tid = parseInt(tr.getAttribute("data-table-id"), 10);
      tr.classList.toggle("table-primary", tid === activeTableId);
    });
  }

  async function loadColumns(tableId) {
    const tb = el("columns-tbody");
    tb.innerHTML = "";
    if (!tableId) {
      tb.innerHTML = `<tr><td colspan="7" class="text-muted">Selecione uma tabela para ver as colunas.</td></tr>`;
      columns = [];
      return;
    }
    const { res, json } = await getJson(`${API}/tables/${tableId}/columns`);
    if (!res.ok || !json?.ok) {
      tb.innerHTML = `<tr><td colspan="7" class="text-danger">${json?.error || "Erro ao carregar colunas"}</td></tr>`;
      return;
    }
    columns = json.items || [];
    if (!columns.length) {
      tb.innerHTML = `<tr><td colspan="7" class="text-muted">Nenhuma coluna. Clique em "Nova Coluna".</td></tr>`;
      return;
    }
    columns.forEach(c => tb.insertAdjacentHTML("beforeend", colRow(c)));
  }

  function openEditProject() {
    hideAlerts();
    new bootstrap.Modal(el("projectModal")).show();
  }

  async function saveProject() {
    hideAlerts();
    const payload = {
      label: el("label").value.trim(),
      version: el("version").value.trim() || "0.1.0",
      table_prefix: el("table_prefix").value.trim() || null,
      description: el("description").value || null,
    };
    if (!payload.label) {
      setErr("label é obrigatório.");
      return;
    }
    const { res, json } = await getJson(`${API}/projects/${pid}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao salvar");
      return;
    }
    setOk("Projeto atualizado.");
  }

  function openNewTable() {
    hideAlerts();
    el("tableId").value = "";
    el("tableModalLabel").textContent = "Nova Tabela";
    el("tableName").value = "";
    el("tableLabel").value = "";
    el("tableDesc").value = "";
    new bootstrap.Modal(el("tableModal")).show();
  }

  function openEditTable(id) {
    hideAlerts();
    const t = tables.find(x => x.id === id);
    if (!t) return;
    el("tableId").value = t.id;
    el("tableModalLabel").textContent = `Editar Tabela: ${t.name}`;
    el("tableName").value = t.name || "";
    el("tableLabel").value = t.label || "";
    el("tableDesc").value = t.description || "";
    new bootstrap.Modal(el("tableModal")).show();
  }

  async function saveTable() {
    hideAlerts();
    const tid = el("tableId").value;
    const payload = {
      name: el("tableName").value.trim(),
      label: el("tableLabel").value.trim(),
      description: el("tableDesc").value || null,
    };
    if (!payload.name || !payload.label) {
      setErr("name e label são obrigatórios.");
      return;
    }
    let url = `${API}/projects/${pid}/tables`;
    let method = "POST";
    if (tid) {
      url = `${API}/tables/${tid}`;
      method = "PUT";
    }
    const { res, json } = await getJson(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao salvar tabela");
      return;
    }
    setOk("Tabela salva.");
    bootstrap.Modal.getInstance(el("tableModal"))?.hide();
    await loadTables();
  }

  async function delTable(id) {
    if (!confirm("Excluir tabela e suas colunas?")) return;
    const { res, json } = await getJson(`${API}/tables/${id}`, { method: "DELETE" });
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao excluir tabela");
      return;
    }
    setOk("Tabela excluída.");
    await loadTables();
  }

  function openNewColumn() {
    hideAlerts();
    if (!activeTableId) return;
    el("columnId").value = "";
    el("columnModalLabel").textContent = "Nova Coluna";
    el("colName").value = "";
    el("colLabel").value = "";
    el("colType").value = "";
    el("colLength").value = "";
    el("colRequired").checked = false;
    el("colUnique").checked = false;
    el("colIndexed").checked = false;
    new bootstrap.Modal(el("columnModal")).show();
  }

  function openEditColumn(id) {
    hideAlerts();
    const c = columns.find(x => x.id === id);
    if (!c) return;
    el("columnId").value = c.id;
    el("columnModalLabel").textContent = `Editar Coluna: ${c.name}`;
    el("colName").value = c.name || "";
    el("colLabel").value = c.label || "";
    el("colType").value = c.data_type || "";
    el("colLength").value = c.length ?? "";
    el("colRequired").checked = !!c.required;
    el("colUnique").checked = !!c.unique;
    el("colIndexed").checked = !!c.indexed;
    new bootstrap.Modal(el("columnModal")).show();
  }

  async function saveColumn() {
    hideAlerts();
    if (!activeTableId) return;
    const cid = el("columnId").value;
    const payload = {
      name: el("colName").value.trim(),
      label: el("colLabel").value.trim(),
      data_type: el("colType").value.trim(),
      length: el("colLength").value ? parseInt(el("colLength").value, 10) : null,
      required: el("colRequired").checked,
      unique: el("colUnique").checked,
      indexed: el("colIndexed").checked,
    };
    if (!payload.name || !payload.label || !payload.data_type) {
      setErr("name, label e tipo são obrigatórios.");
      return;
    }
    let url = `${API}/tables/${activeTableId}/columns`;
    let method = "POST";
    if (cid) {
      url = `${API}/columns/${cid}`;
      method = "PUT";
    }
    const { res, json } = await getJson(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao salvar coluna");
      return;
    }
    setOk("Coluna salva.");
    bootstrap.Modal.getInstance(el("columnModal"))?.hide();
    await loadColumns(activeTableId);
  }

  async function delColumn(id) {
    if (!confirm("Excluir coluna?")) return;
    const { res, json } = await getJson(`${API}/columns/${id}`, { method: "DELETE" });
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao excluir coluna");
      return;
    }
    setOk("Coluna excluída.");
    await loadColumns(activeTableId);
  }

  async function generate() {
    if (!confirm("Gerar/atualizar plugin no filesystem?")) return;
    hideAlerts();
    const { res, json } = await getJson(`${API}/projects/${pid}/rebuild/apply`, { method: "POST" });
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao gerar");
      return;
    }
    setOk(`Plugin gerado: ${json.plugin_dir}`);
    await loadProject();
    await loadTables();
  }

  function bind() {
    el("btnRefreshProject")?.addEventListener("click", async () => {
      hideAlerts();
      await loadProject();
      await loadTables();
    });
    el("btnEditProject")?.addEventListener("click", openEditProject);
    el("btnSaveProject")?.addEventListener("click", saveProject);
    el("btnGenerate")?.addEventListener("click", generate);

    el("btnNewTable")?.addEventListener("click", openNewTable);
    el("btnSaveTable")?.addEventListener("click", saveTable);

    el("btnNewColumn")?.addEventListener("click", openNewColumn);
    el("btnSaveColumn")?.addEventListener("click", saveColumn);

    // clicks
    document.addEventListener("click", async (ev) => {
      const tr = ev.target.closest("tr[data-table-id]");
      if (tr && !ev.target.closest("button[data-action]")) {
        activeTableId = parseInt(tr.getAttribute("data-table-id"), 10);
        renderTablesHighlight();
        el("btnNewColumn").disabled = false;
        await loadColumns(activeTableId);
        return;
      }

      const b = ev.target.closest("button[data-action]");
      if (!b) return;
      const action = b.getAttribute("data-action");
      const id = parseInt(b.getAttribute("data-id"), 10);

      if (action === "edit-table") openEditTable(id);
      if (action === "del-table") await delTable(id);
      if (action === "edit-col") openEditColumn(id);
      if (action === "del-col") await delColumn(id);
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    bind();
    await loadProject();
    await loadTables();
  });
})();
