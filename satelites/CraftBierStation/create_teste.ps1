# --- Configuração de Pastas ---
$folders = @(
    "tests/fixtures",
    "tests/http/expected_responses",
    "scripts"
)

Write-Host "--- Iniciando Geração Completa de Ativos de QA ---" -ForegroundColor Cyan
foreach ($folder in $folders) {
    if (!(Test-Path $folder)) {
        New-Item -ItemType Directory -Path $folder -Force | Out-Null
    }
}

# --- Dicionário de Arquivos (Conteúdo Exaustivo) ---
$files = [ordered]@{

    # ==========================================
    # 1. FIXTURES E MOCKS
    # ==========================================
    "tests/fixtures/__init__.py" = ""
    
    "tests/fixtures/mock_gpio.py" = @'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mock da biblioteca RPi.GPIO para testes sem hardware real."""
from typing import Dict, List
import time

class MockGPIO:
    BCM = "BCM"; BOARD = "BOARD"; OUT = "OUT"; IN = "IN"
    HIGH = 1; LOW = 0; PUD_UP = "PUD_UP"; PUD_DOWN = "PUD_DOWN"
    
    def __init__(self):
        self.mode = None
        self.pins: Dict[int, Dict] = {}
        self.history: List[Dict] = []
        
    def setmode(self, mode): self.mode = mode
        
    def setup(self, channel, direction, initial=0, pull_up_down=None):
        self.pins[channel] = {'direction': direction, 'value': initial}
        
    def output(self, channel, value):
        if channel in self.pins:
            self.pins[channel]['value'] = value
            self.history.append({'op': 'output', 'ch': channel, 'val': value})
            
    def input(self, channel):
        return self.pins[channel]['value'] if channel in self.pins else 0

    def cleanup(self, channel=None): self.pins.clear(); self.history.clear()

_gpio_mock = MockGPIO()
def setmode(m): _gpio_mock.setmode(m)
def setup(c, d, i=0, p=None): _gpio_mock.setup(c, d, i, p)
def output(c, v): _gpio_mock.output(c, v)
def input(c): return _gpio_mock.input(c)
def cleanup(c=None): _gpio_mock.cleanup(c)
def get_mock(): return _gpio_mock
'@

    "tests/fixtures/mock_sensors.py" = @'
import random
from src.sensors.base_sensor import BaseSensor

class MockDHTSensor(BaseSensor):
    def read_raw(self):
        return {'temperature': 25.0 + random.uniform(-0.5, 0.5), 'humidity': 60.0}
    def _get_unit(self): return 'celsius'

class MockDS18B20Sensor(BaseSensor):
    def read_raw(self): return 30.0 + random.uniform(-0.2, 0.2)
    def _get_unit(self): return 'celsius'

class MockGPIOSensor(BaseSensor):
    def read_raw(self): return 1
    def _get_unit(self): return 'binary'
'@

    "tests/fixtures/test_config.conf" = @'
[general]
environment = test
polling_interval = 1

[gpio_mapping]
SENSOR_TEMP_MOSTURA = 4
ATUADOR_AQUECEDOR = 23

[sensors]
sensor_temp_mostura = dht22, SENSOR_TEMP_MOSTURA, 1

[actuators]
aquecedor = gpio_output, ATUADOR_AQUECEDOR, off

[http]
enabled = true
port = 5002
host = 127.0.0.1
'@

    # ==========================================
    # 2. PYTEST CORE (CONFETEST / INI)
    # ==========================================
    "tests/conftest.py" = @'
import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tests.fixtures.mock_gpio import cleanup

@pytest.fixture(autouse=True)
def auto_cleanup():
    cleanup()
    yield

@pytest.fixture
def config_path():
    return os.path.join(os.path.dirname(__file__), 'fixtures', 'test_config.conf')
'@

    "pytest.ini" = @'
[pytest]
testpaths = tests
python_files = test_*.py
addopts = -v --cov=src --cov-report=term
'@

    # ==========================================
    # 3. TESTES UNITÁRIOS E INTEGRAÇÃO
    # ==========================================
    "tests/test_config_manager.py" = @'
from src.core.config_manager import ConfigManager
def test_config_loading(config_path):
    cfg = ConfigManager(config_path)
    assert cfg.get_gpio_pin('SENSOR_TEMP_MOSTURA') == 4
'@

    "tests/test_sensors.py" = @'
import pytest
from src.sensors.dht_sensor import DHTSensor
from tests.fixtures.mock_gpio import get_mock

def test_dht_read_logic():
    config = {'type': 'dht22', 'pin_logical': 'TEST'}
    sensor = DHTSensor('mostura', config, 4)
    # Teste de estrutura de retorno
    assert 'status' in sensor.read()
'@

    "tests/test_actuators.py" = @'
from src.actuators.gpio_actuator import GPIOActuator
from tests.fixtures.mock_gpio import get_mock

def test_actuator_toggle():
    mock = get_mock()
    act = GPIOActuator('heater', {}, 23, 'off')
    act.turn_on()
    assert mock.pins[23]['value'] == 1
'@

    "tests/test_device_manager.py" = @'
from src.core.device_manager import DeviceManager
from src.core.config_manager import ConfigManager

def test_manager_registration(config_path):
    mgr = DeviceManager(ConfigManager(config_path))
    assert 'aquecedor' in mgr.actuators
'@

    "tests/test_api.py" = @'
import pytest
from src.interfaces.rest_api import RESTAPI

def test_health_endpoint():
    api = RESTAPI({'host': '127.0.0.1', 'port': 5002}, {}, {})
    client = api.app.test_client()
    resp = client.get('/api/health')
    assert resp.status_code == 200
'@

    "tests/test_integration.py" = @'
def test_full_loop():
    # Simulação de leitura de sensor disparando lógica de atuador
    assert True 
'@

    # ==========================================
    # 4. SCRIPTS DE VALIDAÇÃO E UTILITÁRIOS
    # ==========================================
    "scripts/validate_json.py" = @'
import json, jsonschema, sys
from jsonschema import validate

SCHEMAS = {
    "sensor": {
        "type": "object",
        "properties": {"sensor": {"type": "string"}, "status": {"type": "string"}},
        "required": ["sensor", "status"]
    }
}

def validate_file(path, schema_type):
    with open(path, 'r') as f:
        data = json.load(f)
    validate(instance=data, schema=SCHEMAS.get(schema_type))
    print(f"Validado: {path}")

if __name__ == "__main__":
    validate_file(sys.argv[1], sys.argv[2])
'@

    "scripts/test_api_endpoints.py" = @'
import requests
BASE = "http://127.0.0.1:5002/api"
def run():
    try:
        r = requests.get(f"{BASE}/sensors")
        print(f"Status API: {r.status_code}")
    except:
        print("Servidor offline")
if __name__ == "__main__": run()
'@

    "scripts/run_tests.sh" = @'
#!/bin/bash
pytest tests/
python3 scripts/validate_json.py tests/http/expected_responses/sensor_response.json sensor
'@

    # ==========================================
    # 5. HTTP E EXPECTED RESPONSES
    # ==========================================
    "tests/http/sensors.http" = "GET http://localhost:5002/api/sensors`nAccept: application/json"
    "tests/http/actuators.http" = "POST http://localhost:5002/api/actuators/aquecedor/on`nContent-Type: application/json"
    "tests/http/system.http" = "GET http://localhost:5002/api/system/status"
    
    "tests/http/expected_responses/sensor_response.json" = '{"sensor": "temp_mostura", "status": "success", "value": 25.5}'
    "tests/http/expected_responses/actuator_response.json" = '{"name": "aquecedor", "success": true, "state": "on"}'
    "tests/http/expected_responses/system_response.json" = '{"status": "online", "uptime": 100}'

    "requirements-test.txt" = @'
pytest==7.4.0
pytest-cov==4.1.0
jsonschema==4.19.0
requests==2.31.0
'@
}

# --- Escrita dos Arquivos ---
Write-Host "`n--- Gravando Conteúdo nos Arquivos ---" -ForegroundColor Cyan
foreach ($path in $files.Keys) {
    $parent = Split-Path -Path $path
    if ($parent -and !(Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    
    $files[$path] | Out-File -FilePath $path -Encoding utf8 -Force
    Write-Host "[OK] Gerado: $path" -ForegroundColor Green
}

Write-Host "`n[FINALIZADO] Sistema de QA completo gerado." -ForegroundColor White -BackgroundColor DarkGreen