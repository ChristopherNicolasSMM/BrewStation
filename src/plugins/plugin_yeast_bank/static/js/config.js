(() => {
  const API = "/api/yeast_bank/config";
  const el = (id) => document.getElementById(id);

  function setText(id, value) {
    const n = el(id);
    if (!n) return;
    n.textContent = (value === null || value === undefined || value === "") ? "—" : String(value);
  }

  function showOk() {
    el("ok")?.classList.remove("d-none");
    el("err")?.classList.add("d-none");
  }

  function showErr(msg) {
    const box = el("err");
    if (!box) return;
    box.textContent = msg || "Erro ao salvar";
    box.classList.remove("d-none");
    el("ok")?.classList.add("d-none");
  }

  function hideAlerts() {
    el("ok")?.classList.add("d-none");
    el("err")?.classList.add("d-none");
  }

  function applyToKpis(c) {
    setText("kpi_master", c.expiry_master_days || 365);
    setText("kpi_work", c.expiry_work_days || 180);
    setText("kpi_plate", c.expiry_plate_days || 30);
    setText("kpi_saline", c.expiry_saline_days || 90);
  }

  async function load() {
    hideAlerts();
    const res = await fetch(API);
    const json = await res.json();
    if (!json.ok) return;

    const c = json.config || {};
    el("expiry_master_days").value = c.expiry_master_days || 365;
    el("expiry_work_days").value = c.expiry_work_days || 180;
    el("expiry_plate_days").value = c.expiry_plate_days || 30;
    el("expiry_saline_days").value = c.expiry_saline_days || 90;

    applyToKpis(c);
  }

  async function save() {
    hideAlerts();

    const payload = {
      expiry_master_days: el("expiry_master_days").value || null,
      expiry_work_days: el("expiry_work_days").value || null,
      expiry_plate_days: el("expiry_plate_days").value || null,
      expiry_saline_days: el("expiry_saline_days").value || null
    };

    const btn = el("btnSave");
    if (btn) btn.disabled = true;

    try {
      const res = await fetch(API, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const json = await res.json();
      if (!res.ok || !json.ok) {
        showErr(json.error || "Erro ao salvar");
        return;
      }

      showOk();
      await load();
    } catch (e) {
      showErr("Falha ao salvar (verifique o servidor).");
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  document.addEventListener("DOMContentLoaded", async () => {
    el("btnSave")?.addEventListener("click", save);
    await load();
  });
})();