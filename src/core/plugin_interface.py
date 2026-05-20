"""
Interface de abstração entre o core do sistema e os plugins.

Fornece funções e classes que os plugins podem usar sem depender diretamente
do core, evitando conflitos e facilitando a manutenção.
"""

from typing import Any, Optional

from flask import Blueprint, Flask

from db.database import db


class PluginContext:
    """
    Contexto fornecido aos plugins para acesso controlado ao core.
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.db = db
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Obtém uma configuração da aplicação."""
        return self.app.config.get(key, default)
    
    def register_blueprint(self, blueprint: Blueprint, url_prefix: Optional[str] = None):
        """Registra um blueprint na aplicação."""
        self.app.register_blueprint(blueprint, url_prefix=url_prefix)
    
    def get_user_model(self):
        """Retorna o modelo de usuário do core."""
        from model.user import User
        return User
    
    def get_db(self):
        """Retorna a instância do banco de dados."""
        return self.db


class CoreServices:
    """
    Serviços do core disponíveis para plugins.
    """
    
    @staticmethod
    def get_current_user():
        """Obtém o usuário atual autenticado."""
        from flask_login import current_user
        return current_user
    
    @staticmethod
    def require_login(func):
        """Decorator para exigir login (abstração do login_required)."""
        from flask_login import login_required
        return login_required(func)
    
    @staticmethod
    def render_template(template_name: str, **context):
        """Renderiza um template (abstração do Flask render_template)."""
        from flask import render_template
        return render_template(template_name, **context)
    
    @staticmethod
    def jsonify(data: Any, status_code: int = 200):
        """Retorna resposta JSON (abstração do Flask jsonify)."""
        from flask import jsonify as flask_jsonify
        return flask_jsonify(data), status_code

