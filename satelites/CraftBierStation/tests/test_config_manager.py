from src.core.config_manager import ConfigManager
def test_config_loading(config_path):
    cfg = ConfigManager(config_path)
    assert cfg.get_gpio_pin('SENSOR_TEMP_MOSTURA') == 4
