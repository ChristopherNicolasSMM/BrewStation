# routes/__init__.py
import sys
from pathlib import Path

# Adicionar src ao path para imports
# Usar resolve() para garantir caminho absoluto
# De src/plugins/plugin_integ_bFather/api/routes/__init__.py para src/
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# notifications_routes não existe no plugin, está em src/api/routes/
# from .notifications_routes import notifications_bp
from .brewfather_routes import brewfather_bp
from .calculos_routes import calculos_bp
from .config_routes import config_bp
from .dashboard_routes import dashboard_bp
# upload_routes não existe no plugin, está em src/api/routes/
# from .upload_routes import upload_bp
from .dispositivos_routes import dispositivos_bp
from .envase_routes import envase_bp
from .estoque_routes import estoque_bp
from .ingredientes_routes import ingredientes_bp
from .receitas_routes import receitas_bp
from .report_routes import report_bp
from .upload_routes import upload_bp

# Lista de todos os blueprints para facilitar o registro
all_blueprints = [
    config_bp,
    ingredientes_bp,
    receitas_bp,
    calculos_bp,
    # upload_bp,  # Removido - não existe no plugin
    dispositivos_bp,
    # notifications_bp,  # Removido - não existe no plugin
    brewfather_bp,
    dashboard_bp,
    envase_bp,
    estoque_bp,
    report_bp,
    upload_bp
]

