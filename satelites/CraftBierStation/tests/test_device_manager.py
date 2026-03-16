from src.core.device_manager import DeviceManager
from src.core.config_manager import ConfigManager

def test_manager_registration(config_path):
    mgr = DeviceManager(ConfigManager(config_path))
    assert 'aquecedor' in mgr.actuators
