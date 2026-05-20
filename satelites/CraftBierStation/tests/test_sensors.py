from src.sensors.dht_sensor import DHTSensor


def test_dht_read_logic():
    config = {'type': 'dht22', 'pin_logical': 'TEST'}
    sensor = DHTSensor('mostura', config, 4)
    # Teste de estrutura de retorno
    assert 'status' in sensor.read()
