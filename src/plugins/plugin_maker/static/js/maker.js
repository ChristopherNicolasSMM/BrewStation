(() => {
  const API = "/api/maker";
  const el = (id) => document.getElementById(id);

  function setErr(msg) {
    const b = el("err");
    if (!b) return;
    b.textContent = msg || "Erro";
    b.classList.remove("d-none");
    el("ok")?.classList.add("d-none");
  }
  function setOk() {
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
      headers: {
        "Accept": "application/json",
        ...(opts.headers || {}),
      },
    });

    const text = await r.text();
    let json = null;
    try {
      json = text ? JSON.parse(text) : null;
    } catch {
      console.error("Resposta não é JSON:", text.slice(0, 200));
    }

    if (!r.ok) {
      console.error("HTTP", r.status, text.slice(0, 200));
    }

    return { res: r, json };
  }

  function badge(status) {
    const c = status === "generated" ? "success" : "secondary";
    return `<span class="badge bg-${c}">${status || "draft"}</span>`;
  }

  function projectRow(p) {
    return `
    <tr class="clickable-row" data-href="/maker/projects/${p.id}" style="cursor:pointer;">
      <td>${p.id}</td>
      <td>${p.plugin_dir}</td>
      <td>${p.plugin_name}</td>
      <td>${p.label}</td>
      <td>${badge(p.status)}</td>
      <td>
        <a class="btn btn-sm btn-outline-secondary me-1" href="/maker/projects/${p.id}" title="Abrir">
          <i class="bi bi-box-arrow-up-right"></i>
        </a>
        <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${p.id}">
          <i class="bi bi-pencil"></i>
        </button>
        <button class="btn btn-sm btn-outline-success me-1" data-action="rebuild" data-id="${p.id}">
          <i class="bi bi-hammer"></i>
        </button>
        <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${p.id}">
          <i class="bi bi-trash"></i>
        </button>
      </td>
    </tr>
  `;
  }

  async function loadProjects() {
    const { res, json } = await getJson(`${API}/projects`);
    const tb = el("projects-tbody");
    tb.innerHTML = "";
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao carregar projetos");
      return;
    }
    (json.items || []).forEach((p) => tb.insertAdjacentHTML("beforeend", projectRow(p)));
  }

  async function loadPlugins() {
    const { res, json } = await getJson(`${API}/plugins`);
    const tb = el("plugins-tbody");
    tb.innerHTML = "";
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao carregar plugins");
      return;
    }
    (json.items || []).forEach((p) =>
      tb.insertAdjacentHTML(
        "beforeend",
        `<tr><td>${p.dir}</td><td>${p.name}</td><td>${p.label}</td><td>${p.version || ""} <button class="btn btn-sm btn-outline-primary btn-sm ms-2" data-action="import" data-plugin-dir="${p.dir}"><i class="bi bi-download"></i> Importar</button></td></tr>`
      )
    );
  }

  function openNew() {
    hideAlerts();
    el("projectId").value = "";
    el("projectModalLabel").textContent = "Novo Projeto";
    el("plugin_dir").value = "";
    el("plugin_name").value = "";
    el("label").value = "";
    el("version").value = "0.1.0";
    el("table_prefix").value = "";
    el("description").value = "";
    new bootstrap.Modal(el("projectModal")).show();
  }

  async function openEdit(id) {
    hideAlerts();
    const { res, json } = await getJson(`${API}/projects`);
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao carregar");
      return;
    }
    const p = (json.items || []).find((x) => x.id === id);
    if (!p) {
      alert("Projeto não encontrado");
      return;
    }

    el("projectId").value = p.id;
    el("projectModalLabel").textContent = `Editar Projeto #${p.id}`;
    el("plugin_dir").value = p.plugin_dir;
    el("plugin_name").value = p.plugin_name;
    el("label").value = p.label;
    el("version").value = p.version || "0.1.0";
    el("table_prefix").value = p.table_prefix || "";
    el("description").value = p.description || "";
    new bootstrap.Modal(el("projectModal")).show();
  }

  async function save() {
    hideAlerts();
    const id = el("projectId").value;

    const payload = {
      plugin_dir: el("plugin_dir").value.trim(),
      plugin_name: el("plugin_name").value.trim(),
      label: el("label").value.trim(),
      version: el("version").value.trim() || "0.1.0",
      table_prefix: el("table_prefix").value.trim() || null,
      description: el("description").value || null,
    };

    if (!payload.plugin_dir || !payload.plugin_name || !payload.label) {
      setErr("plugin_dir, plugin_name e label são obrigatórios.");
      return;
    }

    let url = `${API}/projects`;
    let method = "POST";
    if (id) {
      url = `${API}/projects/${id}`;
      method = "PUT";
      // no MVP, não trocamos plugin_dir/plugin_name para não quebrar geração
      delete payload.plugin_dir;
      delete payload.plugin_name;
    }

    const { res, json } = await getJson(url, {
      method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro ao salvar");
      return;
    }

    setOk();
    bootstrap.Modal.getInstance(el("projectModal"))?.hide();
    await loadProjects();
  }

  async function preview() {
    const id = el("projectId").value;
    if (!id) {
      setErr("Salve o projeto antes de preview.");
      return;
    }
    const { res, json } = await getJson(`${API}/projects/${id}/rebuild/preview`, { method: "POST" });
    if (!res.ok || !json?.ok) {
      setErr(json?.error || "Erro no preview");
      return;
    }
    alert(JSON.stringify(json.diff || {}, null, 2));
  }

  async function applyRebuild(id) {
    if (!confirm("Gerar/atualizar plugin no filesystem?")) return;
    const { res, json } = await getJson(`${API}/projects/${id}/rebuild/apply`, { method: "POST" });
    if (!res.ok || !json?.ok) {
      alert(json?.error || "Erro ao gerar");
      return;
    }
    alert(`Plugin gerado: ${json.plugin_dir}`);
    await loadProjects();
    await loadPlugins();
  }

  

async function importPlugin(pluginDir) {
  if (!pluginDir) return;
  if (!confirm(`Importar "${pluginDir}" para o Maker?`)) return;
  const { res, json } = await getJson(`${API}/projects/import`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ plugin_dir: pluginDir }),
  });
  if (!res.ok || !json?.ok) {
    alert(json?.error || "Erro ao importar");
    return;
  }
  // Atualiza lista e navega para o projeto importado
  await loadProjects();
  const id = json.item?.id;
  if (id) window.location.href = `/maker/projects/${id}`;
}

async function delProject(id) {
    if (!confirm("Excluir projeto do Maker?")) return;
    const { res, json } = await getJson(`${API}/projects/${id}`, { method: "DELETE" });
    if (!res.ok || !json?.ok) {
      alert(json?.error || "Erro");
      return;
    }
    await loadProjects();
  }

  function bind() {
    el("btnNewProject")?.addEventListener("click", openNew);
    el("btnRefresh")?.addEventListener("click", async () => {
      await loadProjects();
      await loadPlugins();
    });
    el("btnSaveProject")?.addEventListener("click", save);
    el("btnPreviewRebuild")?.addEventListener("click", preview);

    document.addEventListener("click", (ev) => {
      const tr = ev.target.closest("tr.clickable-row");
      if (!tr) return;

      // Se clicou em botão/link/ícone dentro do botão, não navega
      if (ev.target.closest("button, a, input, select, textarea")) return;

      const href = tr.getAttribute("data-href");
      if (href) window.location.href = href;
    });

    document.addEventListener("click", async (ev) => {
      const b = ev.target.closest("button[data-action]");
      if (!b) return;
      const action = b.getAttribute("data-action");
      const id = parseInt(b.getAttribute("data-id"), 10);
      if (action === "edit") await openEdit(id);
      if (action === "rebuild") await applyRebuild(id);
      if (action === "delete") await delProject(id);
      if (action === "import") {
        const pluginDir = b.getAttribute("data-plugin-dir");
        await importPlugin(pluginDir);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", async () => {
    bind();
    await loadProjects();
    await loadPlugins();
  });
})();