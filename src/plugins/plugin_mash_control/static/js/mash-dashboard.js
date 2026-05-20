/**
 * Mash Dashboard - Frontend para o dashboard de mostura ao vivo.
 *
 * Gerencia o polling de estado da sessão ativa, renderização da timeline,
 * indicadores de temperatura/PID, logs e controles da sessão.
 */

const MashDashboard = (function () {

  'use strict';

  // ─── Estado ────────────────────────────────────────────────────────────
  let state = {
    sessionId: null,
    status: 'idle',
    pollingInterval: null,
    isPolling: false,
  };

  // ─── DOM refs ──────────────────────────────────────────────────────────
  const $ = (id) => document.getElementById(id);
  const qs = (sel, ctx) => (ctx || document).querySelector(sel);

  // ─── Init ──────────────────────────────────────────────────────────────
  const API_BASE = '/api/mash_control';

  function init() {
    loadRecentSessions();
    setupSidebarTabs();
    checkForActiveSession();
  }

  async function checkForActiveSession() {
    try {
      const resp = await fetch(`${API_BASE}/mash-dashboard/active`);
      const data = await resp.json();
      if (data.sessions && data.sessions.length > 0) {
        // Reconnectar à sessão mais recente
        const s = data.sessions[0];
        if (s.status === 'running' || s.status === 'paused') {
          setSession(s.session_id);
        }
      }
    } catch (e) {
      console.warn('Nenhuma sessão ativa encontrada.');
    }
  }

  // ─── Sidebar tabs ──────────────────────────────────────────────────────
  function setupSidebarTabs() {
    document.querySelectorAll('.sidebar-tab').forEach((btn) => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.sidebar-tab').forEach((b) => b.classList.remove('active'));
        btn.classList.add('active');
        document.querySelectorAll('.tab-panel').forEach((p) => (p.style.display = 'none'));
        const panel = $(`panel-${btn.dataset.tab}`);
        if (panel) panel.style.display = '';
        if (btn.dataset.tab === 'sessions') loadRecentSessions();
      });
    });
  }

  // ─── Gerenciamento de sessão ──────────────────────────────────────────
  function setSession(sessionId) {
    state.sessionId = sessionId;
    startPolling();
  }

  function clearSession() {
    stopPolling();
    state.sessionId = null;
    state.status = 'idle';
    renderIdle();
  }

  // ─── Polling ───────────────────────────────────────────────────────────
  function startPolling() {
    if (state.isPolling) return;
    state.isPolling = true;
    poll();
    state.pollingInterval = setInterval(poll, 1500);
  }

  function stopPolling() {
    state.isPolling = false;
    if (state.pollingInterval) {
      clearInterval(state.pollingInterval);
      state.pollingInterval = null;
    }
  }

  async function poll() {
    if (!state.sessionId) return;
    try {
      const resp = await fetch(`${API_BASE}/mash-dashboard/${state.sessionId}/status`);
      if (resp.status === 404) {
        clearSession();
        return;
      }
      const data = await resp.json();
      if (data.status === 'completed' || data.status === 'stopped' || data.status === 'error') {
        stopPolling();
      }
      renderAll(data);
    } catch (e) {
      console.error('Erro no polling:', e);
    }
  }

  // ─── Controles ─────────────────────────────────────────────────────────
  async function control(action) {
    if (!state.sessionId) return;
    try {
      const resp = await fetch(`${API_BASE}/mash-dashboard/${state.sessionId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      if (!resp.ok) {
        const err = await resp.json();
        alert(`Erro: ${err.error}`);
      }
    } catch (e) {
      console.error('Erro no controle:', e);
    }
  }

  // ─── Modal de início ───────────────────────────────────────────────────
  async function promptStart() {
    const overlay = $('start-modal-overlay');
    overlay.style.display = 'flex';
    const select = $('start-recipe-select');
    select.innerHTML = '<option value="">Carregando...</option>';
    const plantSelect = $('start-plant-select');
    plantSelect.innerHTML = '<option value="">Carregando...</option>';
    try {
      // Carregar receitas
      const resp = await fetch(`${API_BASE}/mash-dashboard/recipes-with-steps`);
      const data = await resp.json();
      select.innerHTML = '<option value="">-- Selecione uma receita --</option>';
      (data.recipes || []).forEach((r) => {
        const opt = document.createElement('option');
        opt.value = r.id;
        opt.textContent = `${r.name} (${r.step_count} etapas, ${r.style || ''})`;
        select.appendChild(opt);
      });
      // Carregar plantas
      const plantResp = await fetch(`${API_BASE}/mash-dashboard/plants`);
      const plantData = await plantResp.json();
      plantSelect.innerHTML = '<option value="">-- Selecione --</option>';
      (plantData.plants || []).forEach((p) => {
        const opt = document.createElement('option');
        opt.value = p.id;
        const deviceCount = p.device_count || 0;
        opt.textContent = `${p.name} (${deviceCount} dispositivo${deviceCount !== 1 ? 's' : ''})`;
        plantSelect.appendChild(opt);
      });
    } catch (e) {
      select.innerHTML = '<option value="">Erro ao carregar receitas</option>';
      plantSelect.innerHTML = '<option value="">Erro ao carregar plantas</option>';
    }
  }

  function closeStartModal() {
    $('start-modal-overlay').style.display = 'none';
  }

  async function confirmStart() {
    const recipeId = $('start-recipe-select').value;
    const plantId = $('start-plant-select').value;
    const sessionName = $('start-session-name').value.trim();
    if (!recipeId) { alert('Selecione uma receita.'); return; }

    try {
      const body = { recipe_id: recipeId, name: sessionName || undefined };
      if (plantId) body.plant_id = plantId;
      const resp = await fetch(`${API_BASE}/mash-dashboard/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      if (!resp.ok) {
        const err = await resp.json();
        alert(`Erro ao iniciar: ${err.error}`);
        return;
      }
      const data = await resp.json();
      closeStartModal();
      setSession(data.session_id);
    } catch (e) {
      alert('Erro de conexão ao iniciar mostura.');
    }
  }

  // ─── Render ────────────────────────────────────────────────────────────
  function renderAll(data) {
    state.status = data.status;
    renderStatusBadge(data);
    renderTimeline(data);
    renderTemperature(data);
    renderPid(data);
    renderActuators(data);
    renderLogs(data);
    renderStepsSidebar(data);
    renderAlarms(data);
    renderControls(data);
    updateSidebarInfo(data);
    updateStatBar(data);
  }

  function renderIdle() {
    $('session-status-badge').className = 'status-badge idle';
    qs('.status-dot', $('session-status-badge')).style.display = '';
    $('session-status-text').textContent = 'Inativo';
    $('stat-step').textContent = '--';
    $('stat-temp').textContent = '--';
    $('stat-pid').textContent = '--';
    $('temp-current').textContent = '--';
    $('temp-target').textContent = '--';
    $('pid-bar-fill').style.width = '0%';
    $('pid-value-text').textContent = '0%';
    $('timeline-steps').innerHTML = '<div style="color:var(--text-secondary);font-size:.9rem;">Inicie uma mostura para ver as etapas.</div>';
    $('steps-detail-list').innerHTML = '<p style="color:var(--text-secondary);font-size:.9rem;">Nenhuma sessão ativa.</p>';
    $('alarms-list').innerHTML = '<p style="color:var(--text-secondary);font-size:.9rem;">Nenhum alarme registrado.</p>';
    $('sidebar-recipe-name').textContent = 'Nenhuma sessão ativa';
    const mappedDevices = $('mapped-devices-list');
    if (mappedDevices) { mappedDevices.style.display = 'none'; mappedDevices.innerHTML = ''; }
    $('btn-start').style.display = '';
    $('btn-pause').style.display = 'none';
    $('btn-resume').style.display = 'none';
    $('btn-advance').style.display = 'none';
    $('btn-stop').style.display = 'none';
  }

  function renderStatusBadge(data) {
    const badge = $('session-status-badge');
    const text = $('session-status-text');
    const statusMap = {
      idle: 'Inativo',
      running: 'Em Andamento',
      paused: 'Pausado',
      completed: 'Concluído',
      stopped: 'Parado',
      error: 'Erro',
    };
    badge.className = `status-badge ${data.status || 'idle'}`;
    text.textContent = statusMap[data.status] || data.status;
  }

  function renderTimeline(data) {
    const container = $('timeline-steps');
    if (!data.mash_steps || !data.mash_steps.length) {
      container.innerHTML = '<div style="color:var(--text-secondary);font-size:.9rem;">Nenhuma etapa definida.</div>';
      return;
    }
    const current = data.current_step_index || 0;
    let html = '';
    data.mash_steps.forEach((step, i) => {
      let cls = '';
      if (i < current && data.status !== 'error') cls = 'completed';
      else if (i === current) cls = data.status === 'error' ? 'error' : 'active';
      else if (i === current && data.status === 'error') cls = 'error';
      html += `
        <div class="timeline-step ${cls}">
          <div class="step-indicator">${i + 1}</div>
          <div class="step-name">${escapeHtml(step.name || `Etapa ${i + 1}`)}</div>
        </div>`;
    });
    container.innerHTML = html;
  }

  function renderTemperature(data) {
    const temps = data.temperatures || {};
    const currentTemp = temps.current != null ? temps.current : '--';
    $('temp-current').textContent = typeof currentTemp === 'number' ? currentTemp.toFixed(1) : currentTemp;

    // Temperatura alvo = etapa atual
    const steps = data.mash_steps || [];
    const idx = data.current_step_index || 0;
    let targetTemp = '--';
    if (steps[idx]) {
      targetTemp = steps[idx].temperature !== undefined ? steps[idx].temperature :
                   steps[idx].temp !== undefined ? steps[idx].temp : '--';
    }
    $('temp-target').textContent = typeof targetTemp === 'number' ? targetTemp.toFixed(1) : targetTemp;
  }

  function renderPid(data) {
    const pid = data.pid_output != null ? data.pid_output : 0;
    const pct = Math.min(100, Math.max(0, pid * 100));
    $('pid-bar-fill').style.width = `${pct}%`;
    $('pid-value-text').textContent = `${pct.toFixed(0)}%`;
  }

  function renderActuators(data) {
    const actuators = data.actuator_states || {};
    const grid = $('actuators-grid');
    const items = grid.querySelectorAll('.actuator-item');

    // Heater
    if (items[0]) {
      const heaterOn = actuators.heater || actuators.aquecedor || false;
      items[0].classList.toggle('active', !!heaterOn);
      qs('.actuator-status', items[0]).textContent = heaterOn ? 'Ligado' : 'Desligado';
    }
    // Pump
    if (items[1]) {
      const pumpOn = actuators.pump || actuators.bomba || false;
      items[1].classList.toggle('active', !!pumpOn);
      qs('.actuator-status', items[1]).textContent = pumpOn ? 'Ligado' : 'Desligado';
    }

    // Dispositivos mapeados adicionais (do equipment_mapping)
    renderMappedDevices(data);
  }

  function renderMappedDevices(data) {
    const deviceStatuses = data.device_statuses || {};
    const equipmentMapping = data.equipment_mapping || {};
    const container = $('mapped-devices-list');
    if (!container) return;

    const entries = Object.entries(equipmentMapping);
    if (!entries.length) {
      container.style.display = 'none';
      return;
    }
    container.style.display = '';

    let html = '';
    // Roles que já têm card fixo (heater, pump) não duplicar
    const skipRoles = new Set(['heater', 'pump', 'temperature_sensor']);
    const statusLabels = {
      'online': 'Online',
      'offline': 'Offline',
      'error': 'Falha'
    };

    const roleNames = {
      'temperature_sensor': 'Sensor de Temperatura',
      'heater': 'Aquecedor',
      'pump': 'Bomba Recirculação',
    };

    for (const [role, actorId] of entries) {
      if (skipRoles.has(role)) continue;
      const status = deviceStatuses[role] || {};
      const isOnline = status.status === 'online' || status.online === true;
      const value = status.value != null ? status.value : status.status || 'desconhecido';
      const roleLabel = roleNames[role] || role.replace(/_/g, ' ');

      html += `
        <div class="actuator-item ${isOnline ? 'active' : ''}">
          <div class="actuator-icon">${role.includes('pump') ? '🔃' : role.includes('temp') ? '🌡' : '⚙'}</div>
          <div class="actuator-name">${roleLabel}</div>
          <div class="actuator-status">${isOnline ? value : statusLabels[status.status] || 'Offline'}</div>
        </div>`;
    }
    container.innerHTML = html;
  }

  function renderLogs(data) {
    const container = $('logs-list');
    const logs = data.logs || [];
    if (!logs.length) {
      container.innerHTML = '<div style="color:var(--text-secondary);font-size:.85rem;">Nenhum log disponível.</div>';
      return;
    }
    let html = '';
    // Últimos 50 logs
    const recent = logs.slice(-50);
    recent.forEach((log) => {
      const time = log.timestamp ? formatTime(log.timestamp) : '';
      html += `<div class="log-entry ${log.level || 'info'}">
        <span class="log-time">${escapeHtml(time)}</span>
        <span class="log-msg">${escapeHtml(log.message)}</span>
      </div>`;
    });
    container.innerHTML = html;
    container.scrollTop = container.scrollHeight;
  }

  function renderStepsSidebar(data) {
    const container = $('steps-detail-list');
    const steps = data.mash_steps || [];
    const current = data.current_step_index || 0;
    if (!steps.length) {
      container.innerHTML = '<p style="color:var(--text-secondary);font-size:.9rem;">Nenhuma etapa definida.</p>';
      return;
    }
    let html = '';
    steps.forEach((step, i) => {
      let statusText = 'Pendente';
      let cls = '';
      if (i < current) { statusText = 'Concluída'; cls = 'completed'; }
      else if (i === current) { statusText = 'Ativa'; cls = 'active'; }

      const temp = step.temperature !== undefined ? step.temperature :
                   step.temp !== undefined ? step.temp : '--';
      const duration = step.duration !== undefined ? step.duration :
                       step.time !== undefined ? step.time : '--';
      const tempStr = typeof temp === 'number' ? `${temp}°C` : temp;
      const durStr = typeof duration === 'number' ? `${duration} min` : duration;

      html += `
        <div class="step-detail-card ${cls}">
          <div class="step-detail-header">
            <span class="step-detail-name">${escapeHtml(step.name || `Etapa ${i + 1}`)}</span>
            <span class="step-detail-status">${statusText}</span>
          </div>
          <div class="step-detail-desc">${escapeHtml(step.description || '')}</div>
          <div class="step-detail-meta">
            <span>🌡 ${tempStr}</span>
            <span>⏱ ${durStr}</span>
          </div>
        </div>`;
    });
    container.innerHTML = html;
  }

  function renderAlarms(data) {
    const container = $('alarms-list');
    const alarms = data.alarms || [];
    if (!alarms.length) {
      container.innerHTML = '<p style="color:var(--text-secondary);font-size:.9rem;">Nenhum alarme registrado.</p>';
      return;
    }
    let html = '';
    alarms.slice().reverse().forEach((alarm) => {
      const time = alarm.timestamp ? formatTime(alarm.timestamp) : '';
      const icon = alarm.level === 'error' ? '🔴' : alarm.level === 'warning' ? '🟡' : '🔵';
      html += `
        <div class="alarm-item">
          <span class="alarm-icon">${icon}</span>
          <span class="alarm-msg">${escapeHtml(alarm.message || alarm.msg || '')}</span>
          <span class="alarm-time">${escapeHtml(time)}</span>
        </div>`;
    });
    container.innerHTML = html;
  }

  function renderControls(data) {
    const isActive = data.status === 'running' || data.status === 'paused';
    $('btn-start').style.display = isActive ? 'none' : '';
    $('btn-pause').style.display = data.status === 'running' ? '' : 'none';
    $('btn-resume').style.display = data.status === 'paused' ? '' : 'none';
    $('btn-advance').style.display = data.status === 'running' ? '' : 'none';
    $('btn-stop').style.display = isActive ? '' : 'none';
  }

  function updateSidebarInfo(data) {
    $('sidebar-recipe-name').textContent = data.recipe_name || 'Sessão sem nome';
  }

  function updateStatBar(data) {
    const idx = (data.current_step_index || 0) + 1;
    const total = data.total_steps || (data.mash_steps ? data.mash_steps.length : 0);
    $('stat-step').textContent = total > 0 ? idx : '--';
    // Update stat-step text
    const statStepEl = $('stat-step');
    statStepEl.textContent = total > 0 ? idx : '--';
    // Hack to update the unit span next to it - the unit is in a sibling span.unit
    const stepParent = statStepEl.parentNode;
    if (stepParent) {
      const unitSpan = stepParent.querySelector('.unit');
      if (unitSpan) unitSpan.textContent = total > 0 ? `/ ${total}` : '';
    }
    // Fix / N text
    // Actually the structure is: <span class="value" id="stat-step">--</span> <span class="unit">/ --</span>
    // Let's use the parent
    const statBar = $('session-status-badge');
    // Update stat-temp
    const temps = data.temperatures || {};
    $('stat-temp').textContent = temps.current != null ? temps.current.toFixed(1) : '--';
    // Update stat-pid
    const pid = data.pid_output != null ? (data.pid_output * 100).toFixed(0) : '--';
    $('stat-pid').textContent = pid;
  }

  // ─── Histórico ─────────────────────────────────────────────────────────
  async function loadRecentSessions() {
    const container = $('recent-sessions-list');
    try {
      const resp = await fetch(`${API_BASE}/mash-dashboard/recent`);
      const data = await resp.json();
      const sessions = data.sessions || [];
      if (!sessions.length) {
        container.innerHTML = '<p style="color:var(--text-secondary);font-size:.9rem;">Nenhuma sessão anterior.</p>';
        return;
      }
      let html = '';
      sessions.forEach((s) => {
        const date = s.start_time ? formatDate(s.start_time) : '';
        const statusMap = { running: 'Em andamento', paused: 'Pausado', completed: 'Concluído', stopped: 'Parado', error: 'Erro' };
        const statusText = statusMap[s.status] || s.status;
        html += `
          <div class="session-list-item" onclick="MashDashboard.loadSession('${escapeHtml(s.id)}')">
            <div>
              <div class="session-list-name">${escapeHtml(s.name || 'Sessão')}</div>
              <div class="session-list-meta">${escapeHtml(date)}</div>
            </div>
            <div class="status-badge ${s.status}" style="font-size:.7rem;padding:2px 8px;">
              ${statusText}
            </div>
          </div>`;
      });
      container.innerHTML = html;
    } catch (e) {
      container.innerHTML = '<p style="color:var(--text-secondary);font-size:.9rem;">Erro ao carregar histórico.</p>';
    }
  }

  async function loadSession(sessionId) {
    // Se a sessão já terminou, só mostra dados estáticos
    try {
      const resp = await fetch(`${API_BASE}/mash-dashboard/${sessionId}/status`);
      if (!resp.ok) return;
      const data = await resp.json();
      if (data.status === 'completed' || data.status === 'stopped' || data.status === 'error') {
        renderAll(data);
        stopPolling();
        state.status = data.status;
        state.sessionId = sessionId;
      } else {
        setSession(sessionId);
      }
    } catch (e) {
      console.error(e);
    }
  }

  // ─── Helpers ───────────────────────────────────────────────────────────
  function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  function formatTime(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch (e) {
      return iso;
    }
  }

  function formatDate(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    } catch (e) {
      return iso;
    }
  }

  // ─── Public API ────────────────────────────────────────────────────────
  return {
    init,
    control,
    promptStart,
    closeStartModal,
    confirmStart,
    loadSession,
  };

})();

document.addEventListener('DOMContentLoaded', () => MashDashboard.init());

// Close modal on overlay click
document.addEventListener('click', (e) => {
  if (e.target.id === 'start-modal-overlay') {
    MashDashboard.closeStartModal();
  }
});
