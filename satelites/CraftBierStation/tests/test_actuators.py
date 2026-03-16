from src.actuators.gpio_actuator import GPIOActuator
from tests.fixtures.mock_gpio import get_mock

def test_actuator_toggle():
    mock = get_mock()
    act = GPIOActuator('heater', {}, 23, 'off')
    act.turn_on()
    assert mock.pins[23]['value'] == 1
