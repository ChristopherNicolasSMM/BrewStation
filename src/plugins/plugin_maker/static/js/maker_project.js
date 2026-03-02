(() => {
  const API = "/api/maker";
  const projectId = window.MAKER_PROJECT_ID;

  const el = (id) => document.getElementById(id);

  let currentProject = null;
  let currentTableId = null;

  function showErr(msg){
    const b = el("err");
    b.textContent = msg || "Erro";
    b.classList.remove("d-none");
    el("ok")?.classList.add("d-none");
  }
  function showOk(msg){
    const b = el("ok");
    b.textContent = msg || "OK";
    b.classList.remove("d-none");
    el("err")?.classList.add("d-none");
  }
  function hideMainAlerts(){
    el("ok")?.classList.add("d-none");
    el("err")?.classList.add("d-none");
  }

  function setModalErr(modalId, msg){
    const b = el(modalId);
    if(!b) return;
    b.textContent = msg || "Erro";
    b.classList.remove("d-none");
  }
  function clearModalErr(modalId){
    el(modalId)?.classList.add("d-none");
  }

  async function getJson(url, opts){
    const res = await fetch(url, opts);
    const json = await res.json().catch(() => ({}));
    return {res, json};
  }

  function projHeader(p){
    el("projTitle").textContent = `${p.label}  (#${p.id})`;
    el("projMeta").textContent = `${p.plugin_dir} • ${p.plugin_name} • v${p.version || "0.1.0"} • status=${p.status || "draft"} • prefix=${p.table_prefix || ""}`;
  }

  function tableItem(t){
    const active = (t.id === currentTableId) ? "active" : "";
    return `
      <button type="button" class="list-group-item list-group-item-action ${active}"
              data-action="select-table" data-id="${t.id}">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <div class="fw-semibold">${t.label}</div>
            <div class="small text-muted">${t.name}</div>
          </div>
          <div class="d-flex gap-1">
            <button class="btn btn-sm btn-outline-primary" data-action="edit-table" data-id="${t.id}" title="Editar">
              <i class="bi bi-pencil"></i>
            </button>
            <button class="btn btn-sm btn-outline-danger" data-action="del-table" data-id="${t.id}" title="Excluir">
              <i class="bi bi-trash"></i>
            </button>
          </div>
        </div>
      </button>
    `;
  }

  function colRow(c){
    const yes = (v) => v ? "✅" : "";
    return `
      <tr>
        <td>${c.name}</td>
        <td>${c.label}</td>
        <td>${c.data_type}${c.length ? `(${c.length})` : ""}</td>
        <td class="text-center">${yes(c.required)}</td>
        <td class="text-center">${yes(c.unique)}</td>
        <td class="text-center">${yes(c.indexed)}</td>
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

  async function loadProject(){
    const {res, json} = await getJson(`${API}/projects/${projectId}`);
    if(!res.ok || !json.ok){
      showErr(json.error || "Falha ao carregar projeto");
      return null;
    }
    currentProject = json.item;
    projHeader(currentProject);
    return currentProject;
  }

  async function loadTables(selectFirst=true){
    const {res, json} = await getJson(`${API}/projects/${projectId}/tables`);
    if(!res.ok || !json.ok){
      showErr(json.error || "Falha ao carregar tabelas");
      return [];
    }
    const list = el("tablesList");
    list.innerHTML = "";
    const items = json.items || [];
    if(items.length === 0){
      el("tablesHint").textContent = "Nenhuma tabela. Clique em 'Nova Tabela' para começar.";
      currentTableId = null;
      el("btnNewColumn").disabled = true;
      el("columnsTbody").innerHTML = "";
      el("colsHint").textContent = "Selecione uma tabela para ver as colunas.";
      return items;
    }
    el("tablesHint").textContent = "";
    if(selectFirst && !currentTableId){
      currentTableId = items[0].id;
    }
    items.forEach(t => list.insertAdjacentHTML("beforeend", tableItem(t)));
    el("btnNewColumn").disabled = !currentTableId;
    return items;
  }

  async function loadColumns(){
    const tb = el("columnsTbody");
    tb.innerHTML = "";
    if(!currentTableId){
      el("colsHint").textContent = "Selecione uma tabela para ver as colunas.";
      el("btnNewColumn").disabled = true;
      return [];
    }
    const {res, json} = await getJson(`${API}/tables/${currentTableId}/columns`);
    if(!res.ok || !json.ok){
      showErr(json.error || "Falha ao carregar colunas");
      return [];
    }
    const items = json.items || [];
    if(items.length === 0){
      el("colsHint").textContent = "Nenhuma coluna. Clique em 'Nova Coluna' para adicionar.";
    }else{
      el("colsHint").textContent = "";
    }
    items.forEach(c => tb.insertAdjacentHTML("beforeend", colRow(c)));
    return items;
  }

  // ---- Project modal
  function openEditProject(){
    hideMainAlerts();
    clearModalErr("p_err");
    if(!currentProject) return;
    el("p_label").value = currentProject.label || "";
    el("p_version").value = currentProject.version || "0.1.0";
    el("p_table_prefix").value = currentProject.table_prefix || "";
    el("p_author").value = currentProject.author || "";
    el("p_status").value = currentProject.status || "draft";
    el("p_generation_mode").value = currentProject.generation_mode || "guarded_blocks";
    el("p_description").value = currentProject.description || "";
    new bootstrap.Modal(el("projectModal")).show();
  }

  async function saveProject(){
    clearModalErr("p_err");
    const payload = {
      label: el("p_label").value.trim(),
      version: el("p_version").value.trim() || "0.1.0",
      table_prefix: el("p_table_prefix").value.trim() || null,
      author: el("p_author").value.trim() || null,
      status: el("p_status").value,
      generation_mode: el("p_generation_mode").value,
      description: el("p_description").value || null,
    };
    if(!payload.label){
      setModalErr("p_err", "Label é obrigatório.");
      return;
    }
    const {res, json} = await getJson(`${API}/projects/${projectId}`, {
      method: "PUT",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
    if(!res.ok || !json.ok){
      setModalErr("p_err", json.error || "Erro ao salvar");
      return;
    }
    currentProject = json.item;
    projHeader(currentProject);
    showOk("Projeto atualizado.");
    bootstrap.Modal.getInstance(el("projectModal")).hide();
  }

  // ---- Table modal
  function openNewTable(){
    hideMainAlerts();
    clearModalErr("t_err");
    el("tableId").value = "";
    el("tableModalTitle").textContent = "Nova Tabela";
    el("t_name").value = "";
    el("t_label").value = "";
    el("t_description").value = "";
    el("t_pk_strategy").value = "int";
    el("t_timestamps").value = "true";
    el("t_soft_delete").value = "false";
    new bootstrap.Modal(el("tableModal")).show();
  }

  async function openEditTable(tableId){
    hideMainAlerts();
    clearModalErr("t_err");
    // carrega tabela atual via lista
    const {json} = await getJson(`${API}/projects/${projectId}/tables`);
    const t = (json.items || []).find(x => x.id === tableId);
    if(!t){ showErr("Tabela não encontrada"); return; }

    el("tableId").value = t.id;
    el("tableModalTitle").textContent = `Editar Tabela #${t.id}`;
    el("t_name").value = t.name || "";
    el("t_label").value = t.label || "";
    el("t_description").value = t.description || "";
    el("t_pk_strategy").value = t.pk_strategy || "int";
    el("t_timestamps").value = (t.timestamps ? "true" : "false");
    el("t_soft_delete").value = (t.soft_delete ? "true" : "false");
    new bootstrap.Modal(el("tableModal")).show();
  }

  async function saveTable(){
    clearModalErr("t_err");
    const tableId = el("tableId").value;
    const payload = {
      name: el("t_name").value.trim(),
      label: el("t_label").value.trim(),
      description: el("t_description").value || null,
      pk_strategy: el("t_pk_strategy").value,
      timestamps: el("t_timestamps").value === "true",
      soft_delete: el("t_soft_delete").value === "true",
    };
    if(!payload.name || !payload.label){
      setModalErr("t_err", "name e label são obrigatórios.");
      return;
    }

    let url = `${API}/projects/${projectId}/tables`;
    let method = "POST";
    if(tableId){
      url = `${API}/tables/${tableId}`;
      method = "PUT";
    }

    const {res, json} = await getJson(url, {
      method,
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload),
    });
    if(!res.ok || !json.ok){
      setModalErr("t_err", json.error || "Erro ao salvar");
      return;
    }
    if(!tableId){
      currentTableId = json.item.id;
    }
    await loadTables(false);
    await loadColumns();
    el("btnNewColumn").disabled = !currentTableId;
    showOk("Tabela salva.");
    bootstrap.Modal.getInstance(el("tableModal")).hide();
  }

  async function deleteTable(tableId){
    if(!confirm("Excluir tabela? Isso removerá também as colunas.")) return;
    const {res, json} = await getJson(`${API}/tables/${tableId}`, {method:"DELETE"});
    if(!res.ok || !json.ok){
      showErr(json.error || "Erro ao excluir");
      return;
    }
    if(currentTableId === tableId) currentTableId = null;
    await loadTables(true);
    await loadColumns();
    showOk("Tabela excluída.");
  }

  // ---- Column modal
  function openNewColumn(){
    hideMainAlerts();
    clearModalErr("c_err");
    if(!currentTableId){ showErr("Selecione uma tabela"); return; }
    el("columnId").value = "";
    el("columnModalTitle").textContent = "Nova Coluna";
    el("c_name").value = "";
    el("c_label").value = "";
    el("c_data_type").value = "string";
    el("c_length").value = "";
    el("c_required").value = "false";
    el("c_unique").value = "false";
    el("c_indexed").value = "false";
    new bootstrap.Modal(el("columnModal")).show();
  }

  async function openEditColumn(columnId){
    hideMainAlerts();
    clearModalErr("c_err");
    if(!currentTableId) return;
    const {json} = await getJson(`${API}/tables/${currentTableId}/columns`);
    const c = (json.items || []).find(x => x.id === columnId);
    if(!c){ showErr("Coluna não encontrada"); return; }

    el("columnId").value = c.id;
    el("columnModalTitle").textContent = `Editar Coluna #${c.id}`;
    el("c_name").value = c.name || "";
    el("c_label").value = c.label || "";
    el("c_data_type").value = c.data_type || "string";
    el("c_length").value = c.length || "";
    el("c_required").value = c.required ? "true" : "false";
    el("c_unique").value = c.unique ? "true" : "false";
    el("c_indexed").value = c.indexed ? "true" : "false";
    new bootstrap.Modal(el("columnModal")).show();
  }

  async function saveColumn(){
    clearModalErr("c_err");
    if(!currentTableId){ setModalErr("c_err", "Selecione uma tabela"); return; }

    const columnId = el("columnId").value;
    const payload = {
      name: el("c_name").value.trim(),
      label: el("c_label").value.trim(),
      data_type: el("c_data_type").value,
      length: el("c_length").value ? parseInt(el("c_length").value, 10) : null,
      required: el("c_required").value === "true",
      unique: el("c_unique").value === "true",
      indexed: el("c_indexed").value === "true",
    };
    if(!payload.name || !payload.label || !payload.data_type){
      setModalErr("c_err", "name, label e data_type são obrigatórios.");
      return;
    }

    let url = `${API}/tables/${currentTableId}/columns`;
    let method = "POST";
    if(columnId){
      url = `${API}/columns/${columnId}`;
      method = "PUT";
    }

    const {res, json} = await getJson(url, {
      method,
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload),
    });
    if(!res.ok || !json.ok){
      setModalErr("c_err", json.error || "Erro ao salvar");
      return;
    }
    await loadColumns();
    showOk("Coluna salva.");
    bootstrap.Modal.getInstance(el("columnModal")).hide();
  }

  async function deleteColumn(columnId){
    if(!confirm("Excluir coluna?")) return;
    const {res, json} = await getJson(`${API}/columns/${columnId}`, {method:"DELETE"});
    if(!res.ok || !json.ok){
      showErr(json.error || "Erro ao excluir");
      return;
    }
    await loadColumns();
    showOk("Coluna excluída.");
  }

  // ---- Generator
  async function rebuild(){
    if(!confirm("Gerar/atualizar plugin no filesystem?")) return;
    const {res, json} = await getJson(`${API}/projects/${projectId}/rebuild/apply`, {method:"POST"});
    if(!res.ok || !json.ok){
      showErr(json.error || "Erro ao gerar");
      return;
    }
    showOk(`Plugin gerado/atualizado: ${json.plugin_dir}`);
    await loadProject();
  }

  function bind(){
    el("btnBack").addEventListener("click", () => window.location.href = "/maker");
    el("btnReload").addEventListener("click", async () => { hideMainAlerts(); await loadProject(); await loadTables(false); await loadColumns(); });
    el("btnEditProject").addEventListener("click", openEditProject);
    el("btnSaveProject").addEventListener("click", saveProject);
    el("btnNewTable").addEventListener("click", openNewTable);
    el("btnSaveTable").addEventListener("click", saveTable);
    el("btnNewColumn").addEventListener("click", openNewColumn);
    el("btnSaveColumn").addEventListener("click", saveColumn);
    el("btnRebuild").addEventListener("click", rebuild);

    document.addEventListener("click", async (ev) => {
      const b = ev.target.closest("[data-action]");
      if(!b) return;
      const action = b.getAttribute("data-action");
      const id = parseInt(b.getAttribute("data-id") || "0", 10);

      if(action === "select-table"){
        currentTableId = id;
        await loadTables(false);
        el("btnNewColumn").disabled = false;
        await loadColumns();
      }
      if(action === "edit-table"){
        ev.preventDefault();
        ev.stopPropagation();
        await openEditTable(id);
      }
      if(action === "del-table"){
        ev.preventDefault();
        ev.stopPropagation();
        await deleteTable(id);
      }
      if(action === "edit-col") await openEditColumn(id);
      if(action === "del-col") await deleteColumn(id);
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    bind();
    hideMainAlerts();
    await loadProject();
    await loadTables(true);
    await loadColumns();
  });
})();