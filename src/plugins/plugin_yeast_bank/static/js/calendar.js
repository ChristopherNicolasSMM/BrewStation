(() => {
  const el = (id) => document.getElementById(id);

  const API = {
    strains: "/api/yeast_bank/strains",
    items: "/api/yeast_bank/items",
    gcalConfig: "/api/yeast_bank/gcal/config",
    plan: "/api/yeast_bank/gcal/plan",
    create: "/api/yeast_bank/gcal/create",
    auth: "/api/yeast_bank/gcal/auth",
    calendars: "/api/yeast_bank/gcal/calendars"
  };

  function showBox(id, msg) {
    const b = el(id);
    if (!b) return;
    b.textContent = msg || "";
    b.classList.remove("d-none");
  }
  function hideBox(id) { el(id)?.classList.add("d-none"); }
  function clearAlerts() { ["ok","warn","err"].forEach(hideBox); }

  function setPreviewRows(events) {
    const tb = el("previewRows");
    if (!tb) return;
    tb.innerHTML = "";
    if (!events || events.length === 0) {
      tb.innerHTML = `<tr><td colspan="3" class="text-muted">Nenhuma prévia.</td></tr>`;
      return;
    }
    for (const ev of events) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${ev.start || "—"}</td>
        <td>${(ev.summary || "—").replaceAll("<","&lt;")}</td>
        <td><span class="badge bg-secondary">${ev.kind || "event"}</span></td>
      `;
      tb.appendChild(tr);
    }
  }

  function setHtmlPreview(html) {
    const box = el("previewDesc");
    if (!box) return;
    box.innerHTML = html || "<span class='text-muted'>—</span>";
  }

  async function loadStrains() {
    const sel = el("strain_id");
    if (!sel) return;
    sel.innerHTML = `<option value="">Carregando...</option>`;
    const res = await fetch(API.strains);
    const json = await res.json();
    if (!json.ok) {
      sel.innerHTML = `<option value="">(erro)</option>`;
      return;
    }
    sel.innerHTML = `<option value="">(selecione)</option>`;
    for (const s of (json.items || [])) {
      const opt = document.createElement("option");
      opt.value = s.id;
      opt.textContent = `${s.code ? (s.code + " — ") : ""}${s.name}`;
      sel.appendChild(opt);
    }
  }

  async function loadItems() {
    const sel = el("bank_item_id");
    if (!sel) return;
    // keep first option (opcional)
    sel.innerHTML = `<option value="">(opcional)</option>`;
    const res = await fetch(API.items);
    const json = await res.json();
    if (!json.ok) return;
    for (const it of (json.items || [])) {
      const opt = document.createElement("option");
      opt.value = it.id;
      const label = it.label || it.storage_type || "Item";
      opt.textContent = `#${it.id} — ${label}${it.batch ? (" ("+it.batch+")") : ""}`;
      sel.appendChild(opt);
    }
  }

  function applyCalendarModeVisibility() {
  const mode = (el("calendar_mode")?.value || "yeastbank").toLowerCase();
  const wrap = el("calendarPickWrap");
  if (!wrap) return;
  wrap.classList.toggle("d-none", mode !== "by_id");
}

async function loadCalendarOptions() {
  const modeSel = el("calendar_mode");
  const calSel = el("calendar_id");

  // default UI state
  if (calSel) calSel.innerHTML = `<option value="">(selecione)</option>`;

  // 1) load config (local json)
  let cfg = {};
  try {
    const resCfg = await fetch(API.gcalConfig);
    const jsonCfg = await resCfg.json();
    if (jsonCfg?.ok) cfg = jsonCfg.config || {};
  } catch (e) {}

  // set default mode from config
  if (modeSel) {
    const m = (cfg.calendar_mode || "yeastbank").toLowerCase();
    modeSel.value = ["primary","yeastbank","by_id"].includes(m) ? m : "yeastbank";
    modeSel.addEventListener("change", applyCalendarModeVisibility);
  }
  applyCalendarModeVisibility();

  // 2) try to load live calendars from Google (requires auth)
  let liveItems = null;
  try {
    const res = await fetch(API.calendars);
    if (res.status === 401) {
      liveItems = null;
    } else {
      const json = await res.json();
      if (json?.ok) liveItems = json.items || [];
    }
  } catch (e) {
    liveItems = null;
  }

  // 3) populate dropdown for by_id
  if (!calSel) return;

  const items = (liveItems && liveItems.length)
    ? liveItems.map(c => ({ id: c.id, name: (c.primary ? "Principal" : c.summary) }))
    : (cfg.calendars || []);

  if (!items || items.length === 0) {
    calSel.innerHTML = `<option value="">(nenhuma agenda)</option>`;
    return;
  }

  calSel.innerHTML = `<option value="">(selecione)</option>`;
  for (const c of items) {
    const opt = document.createElement("option");
    opt.value = c.id || "";
    opt.textContent = c.name || c.summary || c.id || "(agenda)";
    calSel.appendChild(opt);
  }

  // pick default id if any
  if (cfg.default_calendar_id) calSel.value = cfg.default_calendar_id;
}

function getFormPayload() {
  const calendar_mode = (el("calendar_mode")?.value || "yeastbank").toLowerCase();
  const calendar_id = (el("calendar_id")?.value || "").trim();

  return {
    strain_id: Number(el("strain_id")?.value || 0) || null,
    bank_item_id: Number(el("bank_item_id")?.value || 0) || null,
    starter_date: (el("starter_date")?.value || "").trim(),
    viability_days: Number(el("viability_days")?.value || 0) || 0,
    review_days: Number(el("review_days")?.value || 0) || 0,
    calendar_mode,
    // only required when calendar_mode=by_id
    calendar_id: calendar_mode === "by_id" ? calendar_id : ""
  };
}

async function plan() {
    clearAlerts();
    const payload = getFormPayload();
    if (!payload.strain_id) return showBox("err", "Selecione uma cepa.");
    if (!payload.starter_date) return showBox("err", "Informe a data do starter.");

    const res = await fetch(API.plan, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (!json.ok) {
      showBox("err", json.error || "Erro ao gerar prévia.");
      setPreviewRows([]);
      setHtmlPreview("");
      return;
    }

    setPreviewRows(json.events || []);
    setHtmlPreview(json.preview_html || "");
    if (json.auth_required) {
      showBox("warn", "Google não autorizado ainda. Clique em “Autorizar Google”.");
    }
  }

  async function create() {
    clearAlerts();
    const payload = getFormPayload();
    if (payload.calendar_mode === "by_id" && !payload.calendar_id) {
      return showBox("err", "Selecione uma agenda (modo: Outra agenda).");
    }
    const res = await fetch(API.create, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    const json = await res.json();

    if (!json.ok) {
      if (json.auth_required) {
        showBox("warn", "Google não autorizado. Clique em “Autorizar Google” e tente novamente.");
        return;
      }
      showBox("err", json.error || "Erro ao criar eventos.");
      return;
    }
    showBox("ok", "Eventos criados no Google Calendar.");
    setPreviewRows(json.events || []);
    if (json.preview_html) setHtmlPreview(json.preview_html);
  }

  function auth() {
    // Abrir autorização em nova aba/janela e manter página atual
    const next = encodeURIComponent(window.location.pathname);
    window.open(`${API.auth}?next=${next}`, "_blank");
  }

  async function init() {
    await Promise.all([loadStrains(), loadItems(), loadCalendarOptions()]);
    const sd = el("starter_date");
    if (sd && !sd.value) {
      const d = new Date();
      const yyyy = d.getFullYear();
      const mm = String(d.getMonth()+1).padStart(2,"0");
      const dd = String(d.getDate()).padStart(2,"0");
      sd.value = `${yyyy}-${mm}-${dd}`;
    }
    el("btnPlan")?.addEventListener("click", (e) => { e.preventDefault(); plan(); });
    el("btnCreate")?.addEventListener("click", (e) => { e.preventDefault(); create(); });
    el("btnAuth")?.addEventListener("click", (e) => { e.preventDefault(); auth(); });
    el("btnReloadCalendars")?.addEventListener("click", (e) => { e.preventDefault(); loadCalendarOptions(); });
  }

  document.addEventListener("DOMContentLoaded", init);
})();