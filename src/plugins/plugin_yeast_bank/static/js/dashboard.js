(async function () {

  console.log("YeastBank dashboard script loaded");
  const API = "/api/yeast_bank/dashboard";

  const el = (id) => document.getElementById(id);

  function safeText(node, value) {
    if (!node) return;
    node.textContent = (value === null || value === undefined || value === "") ? "—" : String(value);
  }

  function fmtDate(s) {
    if (!s) return "";
    return s; // ISO YYYY-MM-DD já ok (depois dá pra formatar pt-BR)
  }

  function strainLabel(item) {
    const s = item?.strain || {};
    const code = (s.code || "").trim();
    const name = (s.name || "").trim();
    return (code || name) ? `${code ? code + " " : ""}${name}`.trim() : `Cepa #${item?.strain_id ?? "?"}`;
  }

  function clearTbody(tbody) {
    while (tbody.firstChild) tbody.removeChild(tbody.firstChild);
  }

  function addRow(tbody, cols) {
    const tr = document.createElement("tr");
    tr.innerHTML = cols.map((c) => `<td>${c ?? ""}</td>`).join("");
    tbody.appendChild(tr);
  }

  async function load() {
    const res = await fetch(API, {
      cache: "no-store",
      mode: "same-origin",
      credentials: "same-origin",
      headers: {
        "Accept": "application/json"
      }
    });
    const contentType = res.headers.get('content-type') || '';
    if (!res.ok) {
      const body = await res.text();
      throw new Error(`Dashboard API ${res.status}: ${body.slice(0, 200)}`);
    }
    if (!contentType.includes('application/json')) {
      const body = await res.text();
      throw new Error(`Resposta não-JSON: ${body.slice(0, 200)}`);
    }
    const json = await res.json();
    if (!json.ok) return;

    const k = json.kpis || {};

    safeText(el("kpiStrains"), k.strains_count);
    safeText(el("kpiItems"), k.items_total);
    safeText(el("kpiRenewSoon"), k.items_renew_soon);
    safeText(el("kpiExpired"), k.items_expired);

    safeText(el("kpiMasters"), k.masters_count);
    safeText(el("kpiWork"), k.work_count);
    safeText(el("kpiPlate"), k.plate_count);
    safeText(el("kpiSaline"), k.saline_count);


    const storageWrap = el("storageCards");
    if (storageWrap) {
      storageWrap.innerHTML = "";
      const cards = json.storage_cards || [];
      if (!cards.length) {
        storageWrap.innerHTML = '<div class="col-12 text-muted">Nenhum equipamento cadastrado.</div>'
      } else {
        cards.forEach((d) => {
          const col = document.createElement("div");
          col.className = "col-xl-4 col-md-6";
          const temp = (d.current_temperature_c === null || d.current_temperature_c === undefined) ? '—' : `${Number(d.current_temperature_c).toFixed(1)} °C`;
          const badgeMap = { ok: 'success', alert_low: 'danger', alert_high: 'danger', stale: 'warning', inactive: 'secondary', no_data: 'warning' };
          const badge = badgeMap[d.status] || 'secondary';
          const spark = (d.recent_temps || []).join(', ');
          col.innerHTML = `
            <div class="border rounded p-3 h-100">
              <div class="d-flex justify-content-between align-items-start">
                <div><div class="fw-bold">${d.name}</div><div class="small text-muted">${d.device_type}</div></div>
                <span class="badge bg-${badge}">${d.status}</span>
              </div>
              <div class="mt-2 fs-5 fw-bold">${temp}</div>
              <div class="small text-muted">Faixa: ${d.temperature_min_c ?? '—'} a ${d.temperature_max_c ?? '—'} °C</div>
              <div class="small text-muted">Última leitura: ${d.last_temperature_at ? new Date(d.last_temperature_at).toLocaleString('pt-BR') : '—'}</div>
              <div class="small mt-2"><strong>Últimas:</strong> ${spark || 'sem dados'}</div>
            </div>`;
          storageWrap.appendChild(col);
        });
      }
    }

    // expiring table
    const expT = el("tblExpiring");
    clearTbody(expT);

    const exp = json.expiring_items || [];
    if (exp.length === 0) {
      addRow(expT, [`<span class="text-muted">Nenhum item vencendo no período.</span>`, "", "", "", "", ""]);
    } else {
      exp.forEach((i) => {
        addRow(expT, [
          i.id,
          strainLabel(i),
          i.storage_type || "",
          i.label || "",
          fmtDate(i.expiry_date),
          i.status || ""
        ]);
      });
    }

    // starters table
    const stT = el("tblStarters");
    clearTbody(stT);

    const sts = json.upcoming_starters || [];
    if (sts.length === 0) {
      addRow(stT, [`<span class="text-muted">Nenhum starter planejado.</span>`, "", "", ""]);
    } else {
      sts.forEach((s) => {
        addRow(stT, [
          s.id,
          s.bank_item_id,
          fmtDate(s.start_date),
          fmtDate(s.brew_date)
        ]);
      });
    }

    const meta = json.meta || {};
    safeText(el("metaInfo"), `Hoje: ${meta.today || "—"} • Janela: ${meta.renew_window_days || 30} dias`);
  }

  try {
    await load();
  } catch (e) {
    // silencioso para não quebrar a tela
    console.error("YeastBank dashboard load error:", e);
  }
})();