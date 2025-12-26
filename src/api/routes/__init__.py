# routes/__init__.py
# NOTA: As rotas principais foram movidas para o plugin plugin_integ_bFather
# Este arquivo mantém apenas a rota de registro e notifications que são parte do core

from .register import register_bp
from .notifications_routes import notifications_bp

# Lista de todos os blueprints do core (registro e notifications)
all_blueprints = [
    register_bp,
    notifications_bp
]

# Blueprints antigos foram movidos para plugins/plugin_integ_bFather/api/routes/
# Eles são carregados automaticamente pelo plugin manager