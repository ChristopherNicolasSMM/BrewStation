import pytest
from src.sensors.dht_sensor import DHTSensor
from tests.fixtures.mock_gpio import get_mock

def test_dht_read_logic():
    config = {'type': 'dht22', 'pin_logical': 'TEST'}
    sensor = DHTSensor('mostura', config, 4)
    # Teste de estrutura de retorno
    assert 'status' in sensor.read()
