"""
Rotas API do plugin device_manager.
"""

from .device_routes import device_bp
from .device_manager_routes import plugin_device_manager_api

all_blueprints = [device_bp, plugin_device_manager_api]
