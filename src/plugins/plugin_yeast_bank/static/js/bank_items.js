// Yeast Bank - Bank Items page
(() => {
    const API_ITEMS = "/api/yeast_bank/items";
    const API_STRAINS = "/api/yeast_bank/strains";
    const API_CONFIG = "/api/yeast_bank/config";
    const API_STORAGE = "/api/yeast_bank/storage/devices";

    let dataTable = null;
    let expiryRules = {
        slant_master_a: 365,
        slant_master_b: 365,
        slant_work: 180,
        plate: 30,
        saline: 90
    };

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

    function formatStrainLabel(s) {
        const code = (s.code || "").trim();
        const name = (s.name || "").trim();
        const fam = (s.family || "").trim();
        const sup = (s.supplier || "").trim();
        let base = `${code ? code + " — " : ""}${name}`;
        let meta = [fam, sup].filter(Boolean).join(" · ");
        return meta ? `${base} (${meta})` : base;
    }

    function badgeStatus(status) {
        const map = {
            ok: "success",
            renew_soon: "warning",
            expired: "danger",
            contaminated: "danger",
            retired: "secondary"
        };
        const c = map[status] || "secondary";
        const txt = status || "—";
        return `<span class="badge bg-${c}">${txt}</span>`;
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

    async function loadConfig() {
        try {
            const res = await fetch(API_CONFIG);
            const json = await res.json();
            if (json.ok && json.config) {
                const c = json.config;
                expiryRules.slant_master_a = c.expiry_master_days || 365;
                expiryRules.slant_master_b = c.expiry_master_days || 365;
                expiryRules.slant_work = c.expiry_work_days || 180;
                expiryRules.plate = c.expiry_plate_days || 30;
                expiryRules.saline = c.expiry_saline_days || 90;
            }
        } catch (_) {
            // fallback silencioso
        }
    }

    function autoSetExpiry(force = false) {
        const auto = el("auto_expiry")?.checked;
        if (!auto && !force) return;

        const prepared = el("prepared_date").value;
        const storage = el("storage_type").value;
        if (!prepared) return;

        const days = expiryRules[storage];
        if (!days) return;

        const preparedDate = new Date(prepared + "T00:00:00");
        const expiry = addDays(preparedDate, days);
        el("expiry_date").value = toISO(expiry);
    }

    async function loadStorageDevices() {
        const sel = el("storage_device_id");
        if (!sel) return;
        const res = await fetch(API_STORAGE);
        const json = await res.json();
        sel.innerHTML = `<option value="">— Nenhum / texto livre —</option>`;
        (json.items || []).forEach(d => {
            const opt = document.createElement("option");
            opt.value = d.id;
            const code = d.machcode ? `${d.machcode} — ` : '';
            opt.textContent = `${code}${d.name} (${d.device_type})`;
            sel.appendChild(opt);
        });
    }

    async function loadStrains() {
        const res = await fetch(API_STRAINS);
        const json = await res.json();
        const sel = el("strain_id");
        sel.innerHTML = "";

        const items = (json.items || []);
        if (items.length === 0) {
            const opt = document.createElement("option");
            opt.value = "";
            opt.textContent = "Nenhuma cepa cadastrada";
            sel.appendChild(opt);
            return;
        }

        items.forEach(s => {
            const opt = document.createElement("option");
            opt.value = s.id;
            opt.textContent = formatStrainLabel(s);
            sel.appendChild(opt);
        });
    }

    function rowHtml(i) {
        const strainName = (i.strain && (i.strain.code || i.strain.name))
            ? `${i.strain.code || ""} ${i.strain.name || ""}`.trim()
            : `#${i.strain_id}`;
        const storageLabel = i.storage_device ? `${i.storage_device.name}${i.storage_slot ? ` / ${i.storage_slot}` : ""}` : (i.location || "");

        return `
      <tr>
        <td>${i.id}</td>
        <td>${strainName}</td>
        <td>${i.storage_type || ""}</td>
        <td>${i.label || ""}</td>
        <td>${storageLabel}</td>
        <td>${i.prepared_date || ""}</td>
        <td>${i.expiry_date || ""}</td>
        <td>${badgeStatus(i.status)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary me-1" data-action="edit" data-id="${i.id}" type="button">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" data-action="delete" data-id="${i.id}" type="button">
            <i class="bi bi-trash"></i>
          </button>
        </td>
      </tr>
    `;
    }

    async function loadItems() {
        const table = el("items-table");
        if (!table) {
            console.warn("[YeastBank] items-table não encontrado.");
            return;
        }

        // garante tbody
        let tbody = el("items-tbody");
        if (!tbody) {
            // recria tbody se sumiu
            tbody = document.createElement("tbody");
            tbody.id = "items-tbody";
            table.appendChild(tbody);
        }

        const res = await fetch(API_ITEMS);
        const json = await res.json();

        tbody.innerHTML = "";
        (json.items || []).forEach(i => {
            tbody.insertAdjacentHTML("beforeend", rowHtml(i));
        });

        // (re)inicializa DataTable
        if (dataTable) {
            try { dataTable.destroy(); } catch (_) { }
            dataTable = null;
        }

        dataTable = new simpleDatatables.DataTable("#items-table", {
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

        // filtros precisam ser rebindados porque recriamos datatable
        bindFilters();
    }


    /*
    function bindTableActions() {
        const tbody = document.getElementById("items-tbody");
        if (!tbody) {
            console.warn("[YeastBank] items-tbody não encontrado; bindTableActions ignorado.");
            return;
        }

        // importante: remover listeners duplicados
        tbody.onclick = async (ev) => {
            const btn = ev.target.closest("button");
            if (!btn) return;

            if (btn.dataset.action === "delete") {
                const id = btn.dataset.id;
                if (!confirm("Excluir este item do banco?")) return;

                const res = await fetch(`${API_ITEMS}/${id}`, { method: "DELETE" });
                const json = await res.json();
                if (!json.ok) {
                    alert(json.error || "Erro ao excluir");
                    return;
                }
                await loadItems();
            }
        };
    }

    */

    function bindTableActions() {
        // remove handler antigo (se existir) para evitar duplicar
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
            if (!confirm("Excluir este item do banco?")) return;

            const res = await fetch(`${API_ITEMS}/${id}`, { method: "DELETE" });

            let json;
            try { json = await res.json(); }
            catch {
                alert("Erro no servidor ao excluir (resposta não-JSON). Veja o log do servidor.");
                return;
            }

            if (!res.ok || !json.ok) {
                alert(json.error || "Erro ao excluir");
                return;
            }

            await loadItems(); // ✅ sempre recarrega
            return;
        }

        if (action === "edit") {
            await openEditModal(parseInt(id, 10));
            return;
        }
    }




    function bindExportButtons() {
        const csvBtn = document.getElementById("export-csv");
        const jsonBtn = document.getElementById("export-json");

        console.log("[YeastBank] bindExportButtons", { csvBtn: !!csvBtn, jsonBtn: !!jsonBtn });

        if (csvBtn) {
            csvBtn.addEventListener("click", () => {
                console.log("[YeastBank] export CSV");
                window.location.href = "/api/yeast_bank/items/export/csv";
            });
        }

        if (jsonBtn) {
            jsonBtn.addEventListener("click", () => {
                console.log("[YeastBank] export JSON");
                // força download (em vez de abrir no browser)
                fetch("/api/yeast_bank/items/export/json")
                    .then(r => r.json())
                    .then(data => {
                        const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
                        const url = URL.createObjectURL(blob);
                        const a = document.createElement("a");
                        a.href = url;
                        a.download = "yeast_bank_items.json";
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        URL.revokeObjectURL(url);
                    })
                    .catch(err => {
                        console.error("Export JSON falhou:", err);
                        alert("Falha ao exportar JSON");
                    });
            });
        }
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

    async function openCreateModal() {
        clearError();
        el("itemId").value = "";
        el("itemModalLabel").textContent = "Novo item";

        el("label").value = "";
        el("storage_device_id").value = "";
        el("storage_slot").value = "";
        el("location").value = "";
        el("prepared_date").value = "";
        el("expiry_date").value = "";
        el("status").value = "ok";
        el("viability_notes").value = "";
        el("storage_type").value = "slant_work";
        el("auto_expiry").checked = true;

        await loadStrains();
        await loadStorageDevices();
        await loadConfig();

        // listeners de auto cálculo
        el("storage_type").onchange = () => autoSetExpiry();
        el("prepared_date").onchange = () => autoSetExpiry();
        el("btnRecalcExpiry").onclick = () => autoSetExpiry(true);

        // abre modal
        const modal = new bootstrap.Modal(el("itemModal"));
        modal.show();
    }

    async function openEditModal(itemId) {
        clearError();

        // carrega strains/config
        await loadStrains();
        await loadStorageDevices();
        await loadConfig();

        // busca item atual
        const res = await fetch(API_ITEMS);
        const json = await res.json();
        const item = (json.items || []).find(x => x.id === itemId);

        if (!item) {
            alert("Item não encontrado para edição.");
            return;
        }

        el("itemId").value = item.id;
        el("itemModalLabel").textContent = `Editar item #${item.id}`;

        el("strain_id").value = item.strain_id;
        el("storage_type").value = item.storage_type || "slant_work";
        el("label").value = item.label || "";
        el("storage_device_id").value = item.storage_device_id || "";
        el("storage_slot").value = item.storage_slot || "";
        el("location").value = item.location || "";
        el("prepared_date").value = item.prepared_date || "";
        el("expiry_date").value = item.expiry_date || "";
        el("status").value = item.status || "ok";
        el("viability_notes").value = item.viability_notes || "";
        el("auto_expiry").checked = false; // em edição, não mexe sozinho

        // listeners
        el("storage_type").onchange = () => autoSetExpiry();
        el("prepared_date").onchange = () => autoSetExpiry();
        el("btnRecalcExpiry").onclick = () => autoSetExpiry(true);

        const modal = new bootstrap.Modal(el("itemModal"));
        modal.show();
    }


    async function saveItem() {
        clearError();

        const strainId = el("strain_id").value;
        if (!strainId) {
            showError("Selecione uma cepa válida.");
            return;
        }

        const itemId = el("itemId").value; // vazio = novo

        const payload = {
            strain_id: parseInt(strainId, 10),
            storage_type: el("storage_type").value,
            label: el("label").value || null,
            storage_device_id: el("storage_device_id").value ? parseInt(el("storage_device_id").value, 10) : null,
            storage_slot: el("storage_slot").value || null,
            location: el("location").value || null,
            prepared_date: el("prepared_date").value || null,
            expiry_date: el("expiry_date").value || null,
            status: el("status").value || "ok",
            viability_notes: el("viability_notes").value || null
        };

        const url = itemId ? `${API_ITEMS}/${itemId}` : API_ITEMS;
        const method = itemId ? "PUT" : "POST";

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

        bootstrap.Modal.getInstance(el("itemModal")).hide();
        await loadItems(); // ✅ sempre recarrega
    }

    async function importJson(file) {
        if (!file) return;
        const text = await file.text();

        let data;
        try {
            data = JSON.parse(text);
        } catch (e) {
            alert("JSON inválido.");
            return;
        }

        const items = Array.isArray(data) ? data : (data.items || []);
        if (!Array.isArray(items) || items.length === 0) {
            alert("Nenhum item encontrado no JSON.");
            return;
        }

        // Import simples: POST item por item
        for (const it of items) {
            const payload = {
                strain_id: it.strain_id,
                storage_type: it.storage_type,
                label: it.label || null,
                storage_device_id: it.storage_device_id || null,
                storage_slot: it.storage_slot || null,
                location: it.location || null,
                prepared_date: it.prepared_date || null,
                expiry_date: it.expiry_date || null,
                status: it.status || "ok",
                viability_notes: it.viability_notes || null
            };

            await fetch(API_ITEMS, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
        }

        alert("Importação concluída.");
        await loadItems();
    }

    function bindTopButtons() {

        const btnImport = document.getElementById("btnImportJson");
        const inputFile = document.getElementById("importJsonFile");

        if (btnImport && inputFile) {
            btnImport.addEventListener("click", () => inputFile.click());
        }


        el("btnNewItem").addEventListener("click", openCreateModal);
        el("btnSaveItem").addEventListener("click", saveItem);

        el("importJsonFile").addEventListener("change", async (ev) => {
            const file = ev.target.files?.[0];
            await importJson(file);
            ev.target.value = "";
        });
    }

    document.addEventListener("DOMContentLoaded", async () => {
        bindTopButtons();
        bindExportButtons();
        bindTableActions();  // ✅ uma vez
        await loadItems();   // ✅ sempre recarrega de forma robusta
    });
})();