(() => {
  const el = (id) => document.getElementById(id);

  const API = {
    strains: "/api/yeast_bank/strains",
    items: "/api/yeast_bank/items",
    gcalConfig: "/api/yeast_bank/gcal/config",
    gcalCalendars: "/api/yeast_bank/gcal/calendars",
    plan: "/api/yeast_bank/gcal/plan",
    create: "/api/yeast_bank/gcal/create",
    auth: "/api/yeast_bank/gcal/auth"
  };

  function showBox(id, msg) {
    const b = el(id);
    if (!b) return;
    b.textContent = msg || "";
    b.classList.remove("d-none");
  }
  function hideBox(id) { el(id)?.classList.add("d-none"); }
  function clearAlerts() { ["ok", "warn", "err"].forEach(hideBox); }

  function esc(s) {
    return (s ?? "").toString().replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
  }

  function setPreviewRows(events) {
    const tb = el("previewRows");
    if (!tb) return;
    tb.innerHTML = "";
    if (!events || events.length === 0) {
      tb.innerHTML = `<tr><td colspan="3" class="text-muted">Nenhuma prévia ainda.</td></tr>`;
      return;
    }
    for (const ev of events) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${esc(ev.start || "—")}</td>
        <td>${esc(ev.summary || "—")}</td>
        <td><span class="badge bg-secondary">${esc(ev.kind || "event")}</span></td>
      `;
      tb.appendChild(tr);
    }
  }

  function setHtmlPreview(html) {
    const d = el("previewDesc");
    if (!d) return;
    d.innerHTML = html || "";
  }

  async function fetchJson(url, opts) {
    const r = await fetch(url, opts);
    const data = await r.json().catch(() => ({}));
    return { ok: r.ok, status: r.status, data };
  }

  function getFormPayload() {
    const strain_id = parseInt(el("strain_id")?.value || "0", 10) || null;
    const bank_item_id = parseInt(el("bank_item_id")?.value || "0", 10) || null;

    // data input dd/mm/yyyy in UI (pt-BR) -> normalize YYYY-MM-DD if possible
    const rawDate = (el("starter_date")?.value || "").trim();
    let starter_date = rawDate;
    if (/^\d{2}\/\d{2}\/\d{4}$/.test(rawDate)) {
      const [dd, mm, yyyy] = rawDate.split("/");
      starter_date = `${yyyy}-${mm}-${dd}`;
    }

    const viability_days = parseInt(el("viability_days")?.value || "0", 10) || 0;
    const review_days = parseInt(el("review_days")?.value || "0", 10) || 0;

    const calendar_mode = (el("calendar_mode")?.value || "yeastbank").trim();
    const calendar_id = (el("calendar_id")?.value || "").trim();

    return { strain_id, bank_item_id, starter_date, viability_days, review_days, calendar_mode, calendar_id };
  }

  function setCalendarModeUI(mode) {
    const wrap = el("calendarIdWrap");
    if (!wrap) return;
    wrap.classList.toggle("d-none", mode !== "by_id");
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

  async function loadGcalConfigAndCalendars() {
    const { ok, data } = await fetchJson(API.gcalCalendars);
    if (!ok || !data.ok) throw new Error(data.error || "Falha ao carregar config/calendários");
    const cfg = data.config || {};

    // calendar mode
    const modeSel = el("calendar_mode");
    if (modeSel && cfg.calendar_mode) modeSel.value = cfg.calendar_mode;
    setCalendarModeUI(modeSel?.value || "yeastbank");

    // calendar id list
    const idSel = el("calendar_id");
    if (idSel) {
      idSel.innerHTML = "";
      const items = data.items || [];
      for (const c of items) {
        const name = c.primary ? `${c.name} (primary)` : c.name;
        idSel.innerHTML += `<option value="${esc(c.id)}">${esc(name)}</option>`;
      }
      if (cfg.default_calendar_id) idSel.value = cfg.default_calendar_id;
    }

    // summaries
    const sums = cfg.event_summary_templates || {};
    if (el("sum_starter")) el("sum_starter").value = sums.starter || "";
    if (el("sum_viability")) el("sum_viability").value = sums.viability || "";
    if (el("sum_review")) el("sum_review").value = sums.review || "";
  }

  async function saveSummaries() {
    clearAlerts();
    const { ok, data } = await fetchJson(API.gcalConfig);
    if (!ok || !data.ok) {
      showBox("err", data.error || "Falha ao ler config");
      return;
    }
    const cfg = data.config || {};
    cfg.event_summary_templates = cfg.event_summary_templates || {};
    cfg.event_summary_templates.starter = (el("sum_starter")?.value || "").trim();
    cfg.event_summary_templates.viability = (el("sum_viability")?.value || "").trim();
    cfg.event_summary_templates.review = (el("sum_review")?.value || "").trim();

    const r = await fetchJson(API.gcalConfig, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cfg)
    });
    if (!r.ok || !r.data.ok) {
      showBox("err", r.data.error || "Falha ao salvar config");
      return;
    }
    showBox("ok", "Títulos salvos no config.");
  }

  async function doPlan() {
    clearAlerts();
    const payload = getFormPayload();

    if (!payload.strain_id) return showBox("warn", "Selecione uma cepa.");
    if (!payload.starter_date) return showBox("warn", "Informe a data do starter.");

    const r = await fetchJson(API.plan, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (!r.ok || !r.data.ok) {
      showBox("err", r.data.error || "Falha ao gerar prévia");
      return;
    }

    setPreviewRows(r.data.events || []);
    setHtmlPreview(r.data.preview_html || "");

    if (r.data.auth_required) {
      showBox("warn", "Google não autorizado ainda. Clique em “Autorizar Google”.");
    }
  }

  async function doCreate() {
    clearAlerts();
    const payload = getFormPayload();

    if (!payload.strain_id) return showBox("warn", "Selecione uma cepa.");
    if (!payload.starter_date) return showBox("warn", "Informe a data do starter.");

    const r = await fetchJson(API.create, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    if (r.status === 401 && r.data?.auth_required) {
      showBox("warn", "Google não autorizado. Clique em “Autorizar Google” e tente novamente.");
      return;
    }
    if (!r.ok || !r.data.ok) {
      showBox("err", r.data.error || "Falha ao criar eventos");
      return;
    }

    const cal = r.data.calendar || {};
    const extra = cal.created ? ` (agenda criada: ${cal.name})` : "";
    showBox("ok", `Eventos criados no Google Calendar${extra}.`);
    setPreviewRows(r.data.events || []);
    setHtmlPreview(r.data.preview_html || "");
  }

  function doAuth() {
    // o endpoint faz redirect para Google
    const next = encodeURIComponent("/yeast_bank/calendar");
    window.location.href = `${API.auth}?next=${next}`;
  }

  async function init() {
    try {
      await Promise.all([loadStrains(), loadItems(), loadGcalConfigAndCalendars()]);
    } catch (e) {
      showBox("err", e?.message || "Falha ao inicializar");
    }

    el("calendar_mode")?.addEventListener("change", (ev) => setCalendarModeUI(ev.target.value));
    el("btnSaveSummaries")?.addEventListener("click", saveSummaries);

    el("btnPlan")?.addEventListener("click", doPlan);
    el("btnCreate")?.addEventListener("click", doCreate);
    el("btnAuth")?.addEventListener("click", doAuth);
  }

  document.addEventListener("DOMContentLoaded", init);
})();
