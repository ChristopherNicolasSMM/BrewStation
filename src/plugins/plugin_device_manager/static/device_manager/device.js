/**
 * JavaScript para gerenciamento de dispositivos IoT
 */

const API_BASE = '/api/device_manager';

// Função para debounce
function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Carregar lista de dispositivos
async function loadDevices() {
  const container = document.getElementById('devices-container');
  if (!container) return;
  
  container.innerHTML = '<div class="col-12 text-center"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>';
  
  try {
    // Obter filtros
    const type = document.getElementById('filter-type')?.value || '';
    const protocol = document.getElementById('filter-protocol')?.value || '';
    const search = document.getElementById('search-device')?.value || '';
    
    const params = new URLSearchParams();
    if (type) params.append('type', type);
    if (protocol) params.append('protocol', protocol);
    
    const response = await fetch(`${API_BASE}/devices?${params.toString()}`);
    const data = await response.json();
    
    if (data.success && data.devices) {
      renderDevices(data.devices, search);
    } else {
      container.innerHTML = '<div class="col-12"><div class="alert alert-warning">Nenhum dispositivo encontrado.</div></div>';
    }
  } catch (error) {
    console.error('Erro ao carregar dispositivos:', error);
    container.innerHTML = '<div class="col-12"><div class="alert alert-danger">Erro ao carregar dispositivos.</div></div>';
  }
}

// Renderizar dispositivos
function renderDevices(devices, searchTerm = '') {
  const container = document.getElementById('devices-container');
  if (!container) return;
  
  // Filtrar por termo de busca
  const filtered = searchTerm 
    ? devices.filter(d => d.name.toLowerCase().includes(searchTerm.toLowerCase()))
    : devices;
  
  if (filtered.length === 0) {
    container.innerHTML = '<div class="col-12"><div class="alert alert-info">Nenhum dispositivo encontrado.</div></div>';
    return;
  }
  
  container.innerHTML = filtered.map(device => {
    const state = device.state || {};
    const status = state.status || 'offline';
    const statusClass = status === 'online' ? 'success' : 'secondary';
    const statusIcon = status === 'online' ? 'bi-check-circle' : 'bi-x-circle';
    
    return `
      <div class="col-md-4 mb-3">
        <div class="card device-card">
          <div class="card-body">
            <div class="d-flex justify-content-between align-items-start mb-2">
              <h6 class="card-title mb-0">${escapeHtml(device.name)}</h6>
              <span class="badge bg-${statusClass}">
                <i class="bi ${statusIcon}"></i> ${status}
              </span>
            </div>
            <p class="text-muted small mb-2">
              <i class="bi bi-tag"></i> ${device.type || 'N/A'} | 
              <i class="bi bi-broadcast"></i> ${device.protocol || 'N/A'}
            </p>
            <div class="d-flex gap-2">
              <a href="/device_manager/view/${device.device_id}" class="btn btn-sm btn-outline-primary">
                <i class="bi bi-eye"></i> Ver
              </a>
              <a href="/device_manager/edit/${device.device_id}" class="btn btn-sm btn-outline-secondary">
                <i class="bi bi-pencil"></i> Editar
              </a>
              <button class="btn btn-sm btn-outline-danger" onclick="deleteDevice('${device.device_id}')">
                <i class="bi bi-trash"></i> Remover
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
}

// Adicionar porta ao formulário
function addPort() {
  const container = document.getElementById('ports-container');
  if (!container) return;
  
  const portItem = document.createElement('div');
  portItem.className = 'port-item mb-3 p-3 border rounded';
  portItem.innerHTML = `
    <div class="row">
      <div class="col-md-3">
        <label class="form-label">Nome da Porta</label>
        <input type="text" class="form-control port-name" placeholder="ex: GPIO_32" required>
      </div>
      <div class="col-md-2">
        <label class="form-label">Tipo</label>
        <select class="form-select port-type">
          <option value="sensor">Sensor</option>
          <option value="actuator">Atuador</option>
        </select>
      </div>
      <div class="col-md-2">
        <label class="form-label">Direção</label>
        <select class="form-select port-direction">
          <option value="input">Entrada</option>
          <option value="output">Saída</option>
        </select>
      </div>
      <div class="col-md-3">
        <label class="form-label">Função</label>
        <input type="text" class="form-control port-function" placeholder="ex: temperature">
      </div>
      <div class="col-md-2">
        <label class="form-label">&nbsp;</label>
        <button type="button" class="btn btn-danger w-100 remove-port">
          <i class="bi bi-trash"></i> Remover
        </button>
      </div>
    </div>
  `;
  
  container.appendChild(portItem);
  
  // Adicionar listener para remover
  portItem.querySelector('.remove-port').addEventListener('click', () => {
    portItem.remove();
  });
}

// Submeter formulário de dispositivo
async function handleSubmit(e) {
  e.preventDefault();
  
  const form = e.target;
  const formData = new FormData(form);
  
  // Coletar dados do formulário
  const deviceData = {
    name: formData.get('name'),
    type: formData.get('type'),
    protocol: formData.get('protocol'),
    connection: {},
    topics: {},
    ports: {}
  };
  
  // Coletar configuração MQTT
  if (deviceData.protocol === 'mqtt') {
    deviceData.connection = {
      broker: formData.get('connection.broker') || 'localhost:1883',
      client_id: formData.get('connection.client_id') || `brewstation_${Date.now()}`,
      username: formData.get('connection.username') || null,
      password: formData.get('connection.password') || null,
      keepalive: 60,
      qos: 1
    };
    
    deviceData.topics = {
      command: `brewstation/devices/${deviceData.name}/command`,
      status: `brewstation/devices/${deviceData.name}/status`,
      telemetry: `brewstation/devices/${deviceData.name}/telemetry`
    };
  }
  
  // Coletar portas
  const portItems = form.querySelectorAll('.port-item');
  portItems.forEach(item => {
    const portName = item.querySelector('.port-name').value;
    if (portName) {
      deviceData.ports[portName] = {
        type: item.querySelector('.port-type').value,
        direction: item.querySelector('.port-direction').value,
        function: item.querySelector('.port-function').value || null
      };
    }
  });
  
  try {
    const deviceId = form.dataset.deviceId;
    const url = deviceId 
      ? `${API_BASE}/devices/${deviceId}`
      : `${API_BASE}/devices`;
    const method = deviceId ? 'PUT' : 'POST';
    
    const response = await fetch(url, {
      method: method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(deviceData)
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert('Dispositivo salvo com sucesso!');
      window.location.href = '/device_manager';
    } else {
      alert('Erro ao salvar dispositivo: ' + (data.error || 'Erro desconhecido'));
    }
  } catch (error) {
    console.error('Erro ao salvar dispositivo:', error);
    alert('Erro ao salvar dispositivo.');
  }
}

// Deletar dispositivo
async function deleteDevice(deviceId) {
  if (!confirm('Tem certeza que deseja remover este dispositivo?')) {
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE}/devices/${deviceId}`, {
      method: 'DELETE'
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert('Dispositivo removido com sucesso!');
      loadDevices();
    } else {
      alert('Erro ao remover dispositivo: ' + (data.error || 'Erro desconhecido'));
    }
  } catch (error) {
    console.error('Erro ao remover dispositivo:', error);
    alert('Erro ao remover dispositivo.');
  }
}

// Carregar status MQTT
async function loadMQTTStatus() {
  try {
    const response = await fetch(`${API_BASE}/mqtt/status`);
    const data = await response.json();
    
    if (data.success) {
      const statusText = document.getElementById('mqtt-status-text');
      const statusAlert = document.getElementById('mqtt-status-alert');
      const btnStart = document.getElementById('btn-start-mqtt');
      const btnStop = document.getElementById('btn-stop-mqtt');
      
      if (data.running) {
        statusText.textContent = 'Servidor MQTT está rodando';
        statusAlert.className = 'alert alert-success';
        btnStart.style.display = 'none';
        btnStop.style.display = 'inline-block';
      } else {
        statusText.textContent = 'Servidor MQTT está parado';
        statusAlert.className = 'alert alert-warning';
        btnStart.style.display = 'inline-block';
        btnStop.style.display = 'none';
      }
    }
  } catch (error) {
    console.error('Erro ao carregar status MQTT:', error);
  }
}

// Carregar configuração MQTT
async function loadMQTTConfig() {
  try {
    const response = await fetch(`${API_BASE}/mqtt/config`);
    const data = await response.json();
    
    if (data.success && data.config) {
      const config = data.config;
      
      document.getElementById('mqtt-enabled').checked = config.enabled || false;
      document.getElementById('mqtt-host').value = config.host || '0.0.0.0';
      document.getElementById('mqtt-port').value = config.port || 1883;
      document.getElementById('auth-enabled').checked = config.authentication?.enabled || false;
      document.getElementById('mqtt-username').value = config.authentication?.username || '';
      document.getElementById('topic-base').value = config.topics?.base || 'brewstation/devices';
      
      if (config.authentication?.enabled) {
        document.getElementById('auth-fields').style.display = 'block';
      }
    }
  } catch (error) {
    console.error('Erro ao carregar configuração MQTT:', error);
  }
}

// Submeter configuração MQTT
async function handleMQTTConfigSubmit(e) {
  e.preventDefault();
  
  const form = e.target;
  const formData = new FormData(form);
  
  const config = {
    enabled: formData.get('enabled') === 'on',
    host: formData.get('host'),
    port: parseInt(formData.get('port')),
    authentication: {
      enabled: formData.get('authentication.enabled') === 'on',
      username: formData.get('authentication.username') || null,
      password: formData.get('authentication.password') || null
    },
    topics: {
      base: formData.get('topics.base')
    }
  };
  
  try {
    const response = await fetch(`${API_BASE}/mqtt/config`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(config)
    });
    
    const data = await response.json();
    
    if (data.success) {
      alert('Configuração salva com sucesso!');
      loadMQTTStatus();
      loadMQTTConfig();
    } else {
      alert('Erro ao salvar configuração: ' + (data.error || 'Erro desconhecido'));
    }
  } catch (error) {
    console.error('Erro ao salvar configuração MQTT:', error);
    alert('Erro ao salvar configuração.');
  }
}

// Função auxiliar para escape HTML
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

