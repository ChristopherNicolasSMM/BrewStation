(() => {
  // =========================
  // Endpoints da API
  // =========================
  const API_DEVICES = '/api/yeast_bank/storage/devices';
  const API_READINGS = '/api/yeast_bank/storage/readings';

  // Atalho para buscar elementos no DOM
  const el = (id) => document.getElementById(id);

  // Estado local da página
  let devices = [];
  let chart = null;
  let loading = false;
  let autoRefreshId = null;

  // Guarda qual equipamento está selecionado para o gráfico
  // Assim o auto refresh não volta sempre para o primeiro item da lista
  let selectedDeviceId = null;

  // =========================
  // Modal de cadastro/edição
  // =========================
  const modalEl = el('deviceModal');
  const hasBootstrapModal = !!(window.bootstrap && modalEl);
  const modal = hasBootstrapModal ? new window.bootstrap.Modal(modalEl) : null;

  function modalShow() {
    // Se Bootstrap modal estiver disponível, usa a API nativa dele
    if (modal) return modal.show();

    // Fallback manual caso Bootstrap JS não esteja disponível
    if (!modalEl) return;

    modalEl.classList.add('show');
    modalEl.style.display = 'block';
    modalEl.removeAttribute('aria-hidden');
    modalEl.setAttribute('aria-modal', 'true');
    document.body.classList.add('modal-open');

    let backdrop = document.getElementById('deviceModalBackdrop');
    if (!backdrop) {
      backdrop = document.createElement('div');
      backdrop.id = 'deviceModalBackdrop';
      backdrop.className = 'modal-backdrop fade show';
      document.body.appendChild(backdrop);
    }
  }

  function modalHide() {
    if (modal) return modal.hide();
    if (!modalEl) return;

    modalEl.classList.remove('show');
    modalEl.style.display = 'none';
    modalEl.setAttribute('aria-hidden', 'true');
    modalEl.removeAttribute('aria-modal');
    document.body.classList.remove('modal-open');

    const backdrop = document.getElementById('deviceModalBackdrop');
    if (backdrop) backdrop.remove();
  }

  // =========================
  // Helpers visuais / formatação
  // =========================
  function badge(status) {
    const map = {
      ok: 'success',
      inactive: 'secondary',
      no_data: 'warning',
      alert_low: 'danger',
      alert_high: 'danger',
      active: 'success',
      maintenance: 'warning',
      alert: 'danger',
      stale: 'warning'
    };

    const cls = map[status] || 'secondary';
    return `<span class="badge bg-${cls}">${status}</span>`;
  }

  function fmtDt(v) {
    return v ? new Date(v).toLocaleString('pt-BR') : '—';
  }

  function num(v) {
    return (v === null || v === undefined || v === '') ? '—' : Number(v).toFixed(1);
  }

  function showErr(id, msg) {
    const box = el(id);
    if (!box) return;
    box.textContent = msg;
    box.classList.remove('d-none');
  }

  function clearErr(id) {
    const box = el(id);
    if (!box) return;
    box.classList.add('d-none');
    box.textContent = '';
  }

  // =========================
  // Preenche o select de leituras
  // =========================
  function fillSelects() {
    const sel = el('reading_device_id');
    if (!sel) return;

    sel.innerHTML = '';

    devices.forEach((d) => {
      const o = document.createElement('option');
      o.value = d.id;
      o.textContent = `${d.name} (${d.device_type})`;
      sel.appendChild(o);
    });

    // Mantém o equipamento selecionado no formulário, se houver
    if (selectedDeviceId) {
      sel.value = String(selectedDeviceId);
    }
  }

  // =========================
  // Carrega / atualiza gráfico
  // =========================
  async function loadDeviceChart(deviceId) {
    if (!deviceId) return;

    const res = await fetch(`${API_DEVICES}/${deviceId}/readings?limit=30`, {
      cache: 'no-store',
      credentials: 'same-origin',
      headers: { 'Accept': 'application/json' }
    });

    const json = await res.json();

    const labels = (json.items || []).map((r) =>
      new Date(r.recorded_at).toLocaleString('pt-BR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    );

    const data = (json.items || []).map((r) => r.temperature_c);

    const ctx = el('deviceChart');
    if (!ctx) return;

    // Cria o gráfico apenas uma vez
    // Nas próximas atualizações, apenas troca os dados
    if (!chart) {
      chart = new Chart(ctx, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: '°C',
              data,
              tension: 0.25,
              borderWidth: 2,
              fill: false
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false, // evita repintura "pesada"
          plugins: {
            legend: { display: false }
          }
        }
      });
    } else {
      chart.data.labels = labels;
      chart.data.datasets[0].data = data;
      chart.update('none'); // atualiza sem animação
    }

    const meta = el('deviceChartMeta');
    if (meta) {
      meta.textContent = json.device
        ? `${json.device.name} • ${json.items.length} leitura(s)`
        : 'Sem dados';
    }
  }

  // =========================
  // Render da tabela e KPIs
  // =========================
  function render() {
    if (el('kpiDevices')) el('kpiDevices').textContent = devices.length;
    if (el('kpiActive')) el('kpiActive').textContent = devices.filter((d) => d.is_active).length;
    if (el('kpiAlert')) el('kpiAlert').textContent = devices.filter((d) => ['alert_low', 'alert_high'].includes(d.health_status)).length;
    if (el('kpiNoData')) el('kpiNoData').textContent = devices.filter((d) => !d.last_temperature_at).length;

    const tbody = el('devicesTbody');
    if (!tbody) return;

    // Limpa antes de redesenhar, evitando duplicação de linhas
    tbody.innerHTML = '';

    devices.forEach((d) => {
      const tr = document.createElement('tr');

      // IMPORTANTE:
      // Troquei href="" por href="#"
      // Isso reduz chance de navegação/reload indesejado
      tr.innerHTML = `
        <td>
          <a href="#" data-select="${d.id}">${d.name}</a>
          <div class="small text-muted">${d.virtual_address || ''}</div>
        </td>
        <td>${d.device_type}</td>
        <td>${badge(d.health_status || d.status)}</td>
        <td>${num(d.current_temperature_c)} °C</td>
        <td>${fmtDt(d.last_temperature_at)}</td>
        <td>
          <button class="btn btn-sm btn-outline-primary" data-edit="${d.id}">
            <i class="bi bi-pencil"></i>
          </button>
          <button class="btn btn-sm btn-outline-danger" data-off="${d.id}">
            <i class="bi bi-power"></i>
          </button>
        </td>
      `;

      tbody.appendChild(tr);
    });

    fillSelects();
  }

  // =========================
  // Carrega lista principal
  // =========================
  async function load() {
    // Evita concorrência:
    // se uma carga já está em andamento, não inicia outra
    if (loading) return;

    loading = true;

    try {
      const res = await fetch(API_DEVICES, {
        cache: 'no-store',
        credentials: 'same-origin',
        headers: { 'Accept': 'application/json' }
      });

      const json = await res.json();
      devices = json.items || [];
      render();

      // Se ainda não houver item selecionado, pega o primeiro
      if (!selectedDeviceId && devices[0]) {
        selectedDeviceId = devices[0].id;
      }

      // Carrega o gráfico do item selecionado, e não sempre do primeiro
      if (selectedDeviceId) {
        await loadDeviceChart(selectedDeviceId);
      }
    } finally {
      loading = false;
    }
  }

  // =========================
  // Abrir modal novo
  // =========================
  function openNew() {
    [
      'device_id',
      'name',
      'description',
      'brand',
      'model',
      'serial_number',
      'physical_location',
      'virtual_address',
      'target_temperature_c',
      'temperature_min_c',
      'temperature_max_c'
    ].forEach((id) => {
      const field = el(id);
      if (field) field.value = '';
    });

    el('device_type').value = 'freezer';
    el('status').value = 'active';
    el('is_active').value = 'true';

    clearErr('deviceErr');
    el('deviceModalLabel').textContent = 'Novo equipamento';
    modalShow();
  }

  // =========================
  // Abrir modal edição
  // =========================
  function openEdit(id) {
    const d = devices.find((x) => x.id == id);
    if (!d) return;

    Object.entries({
      device_id: d.id,
      name: d.name,
      description: d.description || '',
      brand: d.brand || '',
      model: d.model || '',
      serial_number: d.serial_number || '',
      physical_location: d.physical_location || '',
      virtual_address: d.virtual_address || '',
      target_temperature_c: d.target_temperature_c ?? '',
      temperature_min_c: d.temperature_min_c ?? '',
      temperature_max_c: d.temperature_max_c ?? ''
    }).forEach(([k, v]) => {
      const field = el(k);
      if (field) field.value = v;
    });

    el('device_type').value = d.device_type;
    el('status').value = d.status;
    el('is_active').value = String(d.is_active);

    clearErr('deviceErr');
    el('deviceModalLabel').textContent = 'Editar equipamento';
    modalShow();
  }

  // =========================
  // Salvar equipamento
  // =========================
  async function saveDevice() {
    clearErr('deviceErr');

    const id = el('device_id').value;

    const payload = {
      name: el('name').value.trim(),
      device_type: el('device_type').value,
      status: el('status').value,
      is_active: el('is_active').value === 'true',
      description: el('description').value,
      brand: el('brand').value,
      model: el('model').value,
      serial_number: el('serial_number').value,
      physical_location: el('physical_location').value,
      virtual_address: el('virtual_address').value,
      target_temperature_c: el('target_temperature_c').value || null,
      temperature_min_c: el('temperature_min_c').value || null,
      temperature_max_c: el('temperature_max_c').value || null
    };

    if (!payload.name) {
      return showErr('deviceErr', 'Nome é obrigatório.');
    }

    const res = await fetch(id ? `${API_DEVICES}/${id}` : API_DEVICES, {
      method: id ? 'PUT' : 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const json = await res.json();

    if (!res.ok || !json.ok) {
      return showErr('deviceErr', json.error || 'Erro ao salvar');
    }

    modalHide();
    await load();
  }

  // =========================
  // Salvar leitura de temperatura
  // =========================
  async function saveReading() {
    clearErr('readingErr');

    const payload = {
      device_id: Number(el('reading_device_id').value),
      temperature_c: el('temperature_c').value,
      recorded_at: el('recorded_at').value || null,
      humidity_percent: el('humidity_percent').value || null,
      source_type: el('source_type').value,
      notes: el('reading_notes').value
    };

    const res = await fetch(API_READINGS, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const json = await res.json();

    if (!res.ok || !json.ok) {
      return showErr('readingErr', json.error || 'Erro ao salvar leitura');
    }

    // Limpa campos
    el('temperature_c').value = '';
    el('humidity_percent').value = '';
    el('reading_notes').value = '';

    // Mantém o equipamento da leitura como selecionado
    selectedDeviceId = payload.device_id;

    await load();

    // Atualiza gráfico do equipamento salvo
    if (payload.device_id) {
      await loadDeviceChart(payload.device_id);
    }
  }

  // =========================
  // Clique global da página
  // =========================
  document.addEventListener('click', async (ev) => {
    // Novo equipamento
    const bNew = ev.target.closest('#btnNewDevice');
    if (bNew) {
      openNew();
      return;
    }

    // Editar equipamento
    const bEdit = ev.target.closest('[data-edit]');
    if (bEdit) {
      openEdit(bEdit.dataset.edit);
      return;
    }

    // Inativar equipamento
    const bOff = ev.target.closest('[data-off]');
    if (bOff) {
      if (confirm('Inativar equipamento?')) {
        await fetch(`${API_DEVICES}/${bOff.dataset.off}`, { method: 'DELETE' });
        await load();
      }
      return;
    }

    // Selecionar equipamento para o gráfico / formulário
    const bSel = ev.target.closest('[data-select]');
    if (bSel) {
      ev.preventDefault();

      selectedDeviceId = Number(bSel.dataset.select);

      const readingSelect = el('reading_device_id');
      if (readingSelect) {
        readingSelect.value = String(selectedDeviceId);
      }

      await loadDeviceChart(selectedDeviceId);
    }
  });

  // =========================
  // Botões principais
  // =========================
  el('btnSaveDevice')?.addEventListener('click', saveDevice);
  el('btnSaveReading')?.addEventListener('click', saveReading);

  // =========================
  // Fechamento manual do modal
  // =========================
  document.addEventListener('click', (ev) => {
    if (ev.target.matches('[data-bs-dismiss="modal"]') || ev.target.closest('[data-bs-dismiss="modal"]')) {
      modalHide();
    }
  });

  // Clique no fundo do modal fecha
  if (modalEl) {
    modalEl.addEventListener('click', (ev) => {
      if (ev.target === modalEl) modalHide();
    });
  }

  // =========================
  // Carga inicial
  // =========================
  load().catch((err) => console.error('Storage load error:', err));

  // =========================
  // Auto refresh
  // =========================
  // Recomendo começar com 30s.
  // Se quiser testar sem refresh automático, comente este bloco inteiro.
  /*
  if (!autoRefreshId) {
    autoRefreshId = setInterval(() => {
      load().catch((err) => console.error('Storage auto-refresh error:', err));
    }, 30000);
  }
  */
})();