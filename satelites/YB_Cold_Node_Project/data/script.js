const tabs = document.querySelectorAll('.tab-link');
const panels = document.querySelectorAll('.tab-panel');

function byId(id) {
  return document.getElementById(id);
}

function setText(id, value) {
  const el = byId(id);
  if (el) el.textContent = value;
}

function setValue(id, value) {
  const el = byId(id);
  if (el && value !== undefined && value !== null) el.value = value;
}

function setChecked(selector, checked) {
  const el = document.querySelector(selector);
  if (el) el.checked = !!checked;
}

function showToast(message) {
  window.alert(message);
}

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    const target = tab.dataset.tab;
    tabs.forEach(btn => btn.classList.remove('active'));
    panels.forEach(panel => panel.classList.remove('active'));
    tab.classList.add('active');
    byId(target)?.classList.add('active');
  });
});

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    },
    ...options
  });

  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch (err) {
    throw new Error('Resposta inválida do firmware');
  }

  if (!response.ok || data.ok === false) {
    throw new Error(data.error || 'Falha ao comunicar com o firmware');
  }
  return data;
}

function bindForms() {
  const forms = document.querySelectorAll('form');
  forms.forEach((form, index) => {
    form.addEventListener('submit', async (event) => {
      event.preventDefault();

      try {
        if (index === 0) {
          await saveWifi();
          return;
        }
        if (index === 2) {
          await saveTemperature();
          return;
        }
        if (index === 6) {
          await saveDevice();
          return;
        }
        if (index === 7) {
          showToast('Administração ainda não implementada neste MVP. Use factory reset ou reinício.');
          return;
        }

        showToast('Esta aba já está no portal visual, mas ainda não foi ligada ao firmware deste MVP.');
      } catch (error) {
        showToast(error.message);
      }
    });
  });
}

async function refreshStatus() {
  try {
    const status = await api('/api/status', { method: 'GET' });

    const sensor1 = status.sensors?.[0];
    const sensor2 = status.sensors?.[1];
    setText('temp-main', sensor1?.valid ? `${sensor1.temperature_c.toFixed(1)} °C` : 'Erro');
    setText('temp-secondary', sensor2?.valid ? `${sensor2.temperature_c.toFixed(1)} °C` : 'N/D');
    setText('relay-main', status.relay_on ? 'Ligado' : 'Desligado');
    setText('wifi-rssi', status.wifi_connected ? 'Conectado' : 'AP local');
    setText('last-api', status.uptime || '---');
    setText('next-defrost', 'Não implementado');

    const statusPill = document.querySelector('.status-pill');
    if (statusPill) {
      statusPill.textContent = status.wifi_connected ? 'Online' : 'AP local';
      statusPill.classList.toggle('online', !!status.wifi_connected);
    }

    const summaryItems = document.querySelectorAll('.summary-list li strong');
    if (summaryItems.length >= 5) {
      summaryItems[0].textContent = status.relay_on ? 'Refrigeração ativa' : 'Aguardando histerese';
      summaryItems[1].textContent = status.sensor_alarm ? 'Falha / atenção' : 'Normal';
      summaryItems[2].textContent = `${status.sensors?.length || 0} conectados`;
      summaryItems[3].textContent = 'Ativo';
      summaryItems[4].textContent = 'v1.0.0-esp32-mvp';
    }

    const logView = byId('logView');
    if (logView) {
      const logs = await api('/api/logs', { method: 'GET' });
      logView.textContent = (logs.logs || []).join('\n');
    }
  } catch (error) {
    console.warn(error);
  }
}

async function loadConfig() {
  try {
    const cfg = await api('/api/config', { method: 'GET' });
    setValue('wifi_ssid', cfg.wifi_ssid || '');
    setValue('wifi_password', '');
    setValue('wifi_hostname', cfg.wifi_hostname || '');
    setValue('ap_name', cfg.ap_ssid || '');
    setValue('ap_password', '');

    setValue('setpoint', cfg.setpoint_c);
    setValue('hysteresis', cfg.hysteresis_c);
    setValue('sampling_interval', cfg.sample_interval_ms);
    setValue('device_name', cfg.device_name);
    setValue('brightness', 100);

    const controlSensor = byId('control_sensor');
    if (controlSensor) {
      controlSensor.selectedIndex = Number(cfg.control_sensor_index || 0);
    }

    setChecked('#temperature input[type="checkbox"]', cfg.relay_enabled);
  } catch (error) {
    console.warn(error);
  }
}

async function saveWifi() {
  await api('/api/config/wifi', {
    method: 'POST',
    body: JSON.stringify({
      wifi_ssid: byId('wifi_ssid')?.value || '',
      wifi_password: byId('wifi_password')?.value || '',
      wifi_hostname: byId('wifi_hostname')?.value || '',
      ap_ssid: byId('ap_name')?.value || '',
      ap_password: byId('ap_password')?.value || ''
    })
  });
  showToast('Configuração Wi‑Fi salva. O ESP32 tentará conectar na nova rede.');
}

async function saveTemperature() {
  const relayEnabledCheckbox = document.querySelector('#temperature input[type="checkbox"]');
  await api('/api/config/temperature', {
    method: 'POST',
    body: JSON.stringify({
      setpoint_c: Number(byId('setpoint')?.value || 0),
      hysteresis_c: Number(byId('hysteresis')?.value || 1),
      control_sensor_index: Number(byId('control_sensor')?.selectedIndex || 0),
      relay_enabled: !!relayEnabledCheckbox?.checked,
      sample_interval_ms: Number(byId('sampling_interval')?.value || 2000)
    })
  });
  showToast('Controle térmico salvo no dispositivo.');
}

async function saveDevice() {
  await api('/api/config/device', {
    method: 'POST',
    body: JSON.stringify({
      device_name: byId('device_name')?.value || '',
      beep_on_alarm: false
    })
  });
  showToast('Configuração do dispositivo salva.');
}

function bindActionButtons() {
  const rebootBtn = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Reiniciar'));
  if (rebootBtn) {
    rebootBtn.addEventListener('click', async () => {
      try {
        await api('/api/action/reboot', { method: 'POST', body: '{}' });
      } catch (error) {
        showToast(error.message);
      }
    });
  }

  const resetBtn = Array.from(document.querySelectorAll('button')).find(btn => btn.textContent.includes('Factory reset'));
  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      if (!window.confirm('Apagar configuração salva e reiniciar o ESP32?')) return;
      try {
        await api('/api/action/factory-reset', { method: 'POST', body: '{}' });
      } catch (error) {
        showToast(error.message);
      }
    });
  }
}

bindForms();
bindActionButtons();
loadConfig();
refreshStatus();
setInterval(refreshStatus, 4000);
