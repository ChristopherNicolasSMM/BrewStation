"""
Rotas API do plugin device_manager.
"""

from .device_routes import device_bp
from .device_manager_routes import plugin_device_manager_api
from .function_routes import function_bp
from .actor_routes import actor_bp
from .mqtt_test_routes import mqtt_test_bp

all_blueprints = [device_bp, plugin_device_manager_api, function_bp, actor_bp, mqtt_test_bp]
