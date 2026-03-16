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
