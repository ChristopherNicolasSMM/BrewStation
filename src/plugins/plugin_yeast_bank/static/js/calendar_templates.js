(() => {
  const el = (id) => document.getElementById(id);

  const API = {
    cfg: "/api/yeast_bank/gcal/config",
    tplList: "/api/yeast_bank/gcal/templates",
    tplGet: (name) => `/api/yeast_bank/gcal/templates/${encodeURIComponent(name)}`,
    tplSave: "/api/yeast_bank/gcal/templates/save",
    tplPreview: "/api/yeast_bank/gcal/templates/preview",
  };

  function showOk(msg) {
    el("ok").textContent = msg || "Salvo.";
    el("ok").classList.remove("d-none");
    el("err").classList.add("d-none");
  }
  function showErr(msg) {
    el("err").textContent = msg || "Erro.";
    el("err").classList.remove("d-none");
    el("ok").classList.add("d-none");
  }
  function hideAlerts() {
    el("ok")?.classList.add("d-none");
    el("err")?.classList.add("d-none");
  }

  async function loadCfg() {
    hideAlerts();
    const res = await fetch(API.cfg);
    const json = await res.json();
    if (!json.ok) return showErr(json.error || "Falha ao carregar config.");
    el("cfgJson").value = JSON.stringify(json.config || {}, null, 2);
  }

  async function saveCfg() {
    hideAlerts();
    let obj = null;
    try {
      obj = JSON.parse(el("cfgJson").value || "{}");
    } catch (e) {
      return showErr("JSON inválido.");
    }

    const res = await fetch(API.cfg, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(obj)
    });
    const json = await res.json();
    if (!json.ok) return showErr(json.error || "Falha ao salvar.");
    showOk("Config salva.");
    el("cfgJson").value = JSON.stringify(json.config || obj, null, 2);
  }

  async function listTemplates() {
    const res = await fetch(API.tplList);
    const json = await res.json();
    if (!json.ok) {
      el("listBox").innerHTML = "<span class='text-danger'>Falha ao listar templates.</span>";
      return;
    }
    const names = json.items || [];
    if (names.length === 0) {
      el("listBox").innerHTML = "<span class='text-muted'>(nenhum template salvo ainda)</span>";
      return;
    }
    el("listBox").innerHTML = "Salvos: " + names.map(n => `<code>${n}</code>`).join(", ");
  }

  async function loadTemplate() {
    hideAlerts();
    const name = (el("tplName").value || "").trim();
    if (!name) return showErr("Informe o nome do template.");
    const res = await fetch(API.tplGet(name));
    const json = await res.json();
    if (!json.ok) return showErr(json.error || "Falha ao carregar template.");
    el("tplHtml").value = json.html || "";
    showOk("Template carregado.");
  }

  async function saveTemplate() {
    hideAlerts();
    const name = (el("tplName").value || "").trim();
    if (!name) return showErr("Informe o nome do template.");
    const html = el("tplHtml").value || "";
    const res = await fetch(API.tplSave, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ name, html })
    });
    const json = await res.json();
    if (!json.ok) return showErr(json.error || "Falha ao salvar template.");
    showOk("Template salvo.");
    await listTemplates();
  }

  async function previewTemplate() {
    hideAlerts();
    const html = el("tplHtml").value || "";
    const res = await fetch(API.tplPreview, {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({ html })
    });
    const json = await res.json();
    if (!json.ok) return showErr(json.error || "Falha ao gerar preview.");
    el("previewBox").innerHTML = json.preview_html || "";
  }

  function init() {
    el("btnReloadCfg")?.addEventListener("click", (e) => { e.preventDefault(); loadCfg(); });
    el("btnSaveCfg")?.addEventListener("click", (e) => { e.preventDefault(); saveCfg(); });

    el("btnList")?.addEventListener("click", (e) => { e.preventDefault(); listTemplates(); });
    el("btnLoadTpl")?.addEventListener("click", (e) => { e.preventDefault(); loadTemplate(); });
    el("btnSaveTpl")?.addEventListener("click", (e) => { e.preventDefault(); saveTemplate(); });
    el("btnPreview")?.addEventListener("click", (e) => { e.preventDefault(); previewTemplate(); });

    loadCfg();
    listTemplates();

    // starter default template suggestion
    if (!el("tplName").value) el("tplName").value = "starter_event.html";
    if (!el("tplHtml").value) {
      el("tplHtml").value = `
<div>
  <h3>Starter — {{ strain_name }}</h3>
  <p><strong>Data:</strong> {{ starter_date }}</p>
  {% if bank_item_label %}<p><strong>Amostra:</strong> {{ bank_item_label }}</p>{% endif %}
  <ul>
    <li>Viabilidade estimada: {{ viability_date }}</li>
    <li>Revisão / próximo passo: {{ review_date }}</li>
  </ul>
</div>
`.trim();
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();