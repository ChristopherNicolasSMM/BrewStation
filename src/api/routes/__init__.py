# routes/__init__.py
from .config_routes import config_bp
from .ingredientes_routes import ingredientes_bp
from .receitas_routes import receitas_bp
from .calculos_routes import calculos_bp
from .upload_routes import upload_bp
from .dispositivos_routes import dispositivos_bp
from .notifications_routes import notifications_bp
from .brewfather_routes import brewfather_bp
from .register import register_bp 


# Lista de todos os blueprints para facilitar o registro
all_blueprints = [
    config_bp,
    ingredientes_bp,
    receitas_bp,
    calculos_bp,
    upload_bp,
    dispositivos_bp,
    notifications_bp,
    brewfather_bp,
    register_bp
]