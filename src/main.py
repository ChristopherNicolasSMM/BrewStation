"""
BrewStation - Sistema de Precificação de Cervejas.
"""

from __future__ import annotations

import os
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask, url_for
from flask.cli import with_appcontext
from flask_cors import CORS
from flask_login import LoginManager

from logs.setup_logging import configure_logging

# Carregar variáveis de ambiente
# Se ENV_FILE estiver definido (executado via run.py), usar esse caminho
# Caso contrário, usar caminho relativo padrão
env_file = os.getenv("ENV_FILE")
if env_file:
    load_dotenv(env_file)
else:
    # Tentar caminho relativo (quando executado de src/)
    env_path = Path(".env")
    if not env_path.exists():
        # Se não encontrar, tentar caminho absoluto (quando executado de raiz)
        env_path = Path("src") / ".env"
    load_dotenv(env_path)


def create_app():
    """Factory function para criar a aplicação Flask."""
    app = Flask(__name__, template_folder="templates", static_folder="static")

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    app.config["DEBUG"] = os.getenv("DEBUG", "True").lower() == "true"
    app.config["UPLOAD_FOLDER"] = os.getenv("UPLOAD_FOLDER", "uploads")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH", 16777216))
    app.config["FLASK_ENV"] = os.getenv("FLASK_ENV", "DEV")

    configure_logging(app)

    from db.database import init_db
    from utils.dev_setup import ensure_dev_admin

    init_db(app)
    
    # Garantir admin em desenvolvimento
    with app.app_context():
        ensure_dev_admin()

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from model.user import User
        from db.database import db

        return db.session.get(User, int(user_id))

    CORS(app)
    
    # Inicializar sistema de plugins
    from pathlib import Path
    from core.plugin_manager import PluginManager
    from core.cli import register_plugin_commands
    
    # Detectar se estamos em src/ ou na raiz
    current_dir = Path.cwd()
    if current_dir.name == 'src':
        # Já estamos em src/, usar caminho relativo
        plugins_dir = Path("plugins")
        plugins_config = Path("plugins/plugins.json")
    else:
        # Estamos na raiz, usar caminho com src/
        plugins_dir = Path("src/plugins")
        plugins_config = Path("src/plugins/plugins.json")
    
    # Criar diretório de plugins se não existir
    plugins_dir.mkdir(parents=True, exist_ok=True)
    
    # Inicializar plugin manager
    plugin_manager = PluginManager(app, plugins_dir, plugins_config)
    app.plugin_manager = plugin_manager  # Tornar acessível globalmente
    
    # Garantir que o plugin core está instalado e ativo
    # O sistema descobre plugins pelo nome do diretório, mas usa o nome do install.json internamente
    # Verificar se há plugin com nome 'brewstation_core' no install.json
    core_plugin = None
    for plugin_name, plugin in plugin_manager.plugins.items():
        if plugin.name == 'brewstation_core':
            core_plugin = plugin
            break
    
    # Se não encontrou pelo nome, tentar pelo diretório plugin_integ_bFather
    if not core_plugin:
        core_plugin = plugin_manager.get_plugin('plugin_integ_bFather')
    
    if core_plugin:
        if not core_plugin.is_installed:
            app.logger.info(f"Instalando plugin {core_plugin.name}...")
            plugin_manager.install_plugin(core_plugin.name if hasattr(core_plugin, 'name') else 'brewstation_core')
        if not core_plugin.is_active:
            app.logger.info(f"Ativando plugin {core_plugin.name}...")
            plugin_manager.activate_plugin(core_plugin.name if hasattr(core_plugin, 'name') else 'brewstation_core')
    
    # Registrar blueprints core (apenas auth e web básico)
    register_core_blueprints(app)
    
    # Registrar context processors
    register_context_processors(app)
    
    # Registrar comandos CLI
    register_cli_commands(app)
    register_plugin_commands(app)

    return app


def register_core_blueprints(app):
    """Registra apenas os blueprints core (auth, web básico e registro)."""
    try:
        from controller.auth import auth_bp
        from controller.web import web_bp
        from api.routes.register import register_bp

        app.register_blueprint(web_bp)
        app.register_blueprint(auth_bp, url_prefix="/auth")
        app.register_blueprint(register_bp, url_prefix="/api")  # Registro é parte do core

        app.logger.info("Blueprints core registrados com sucesso.")
    except Exception as exc:  # pragma: no cover
        app.logger.exception("Erro ao registrar blueprints core: %s", exc)
        raise


def register_context_processors(app):
    """Registra context processors."""

    @app.context_processor
    def inject_notifications_count():
        from flask_login import current_user

        try:
            if current_user.is_authenticated:
                # Tentar importar Notification se o plugin estiver ativo
                try:
                    from model.notification import Notification
                    unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
                    return {"unread_notifications_count": unread}
                except ImportError:
                    # Plugin de notificações não está instalado
                    pass
        except Exception as exc:  # pragma: no cover
            app.logger.debug("Erro no context processor de notificações: %s", exc)
        return {"unread_notifications_count": 0}
    
    @app.context_processor
    def inject_plugin_menu():
        """Injeta itens de menu dos plugins ativos."""
        from werkzeug.routing import BuildError
        
        def safe_url_for(endpoint, **values):
            """Helper para construir URLs de forma segura."""
            if not endpoint:
                return '#'
            try:
                # url_for já funciona dentro do contexto do template, mas vamos garantir
                return url_for(endpoint, **values)
            except (BuildError, Exception) as e:
                # Em modo debug, listar endpoints disponíveis para ajudar no troubleshooting
                if app.debug or app.logger.level <= 10:  # DEBUG level
                    try:
                        from flask import has_request_context
                        if has_request_context():
                            available = [str(rule.endpoint) for rule in app.url_map.iter_rules()]
                            app.logger.debug(f"Endpoint '{endpoint}' não encontrado. Endpoints disponíveis: {', '.join(sorted(set(available)))}")
                    except Exception:
                        pass
                app.logger.debug(f"Erro ao construir URL para endpoint '{endpoint}': {e}")
                return '#'
        
        try:
            if hasattr(app, 'plugin_manager'):
                menu_items = app.plugin_manager.get_menu_items()
                # Adicionar helper para templates
                return {
                    "plugin_menu_items": menu_items,
                    "safe_url_for": safe_url_for
                }
        except Exception as exc:
            app.logger.debug("Erro no context processor de menu: %s", exc)
        return {"plugin_menu_items": [], "safe_url_for": lambda x, **kwargs: '#'}


def register_cli_commands(app):
    """Registra comandos personalizados via Flask CLI."""

    @app.cli.command("init-admin")
    @click.option("--username", default="admin", show_default=True)
    @click.option("--email", default="admin@brew-station.com", show_default=True)
    @click.option("--password", default="admin123", show_default=True)
    @with_appcontext
    def init_admin(username, email, password):
        from db.database import db
        from model.user import User

        admin = User.query.filter_by(username=username).first()
        if admin:
            click.echo(f"Usuário {username} já existe.")
            return

        admin = User(username=username, email=email, is_admin=True, is_active=True)
        admin.set_password(password)
        db.session.add(admin)
        
        # Tentar inicializar configurações se o plugin estiver instalado
        try:
            from model.config import Configuracao
            Configuracao.initialize_default_configs()
        except ImportError:
            pass  # Plugin de configurações não está instalado
        
        db.session.commit()
        click.echo(f"Usuário {username} criado com sucesso.")

    @app.cli.command("test-db")
    @with_appcontext
    def test_db():
        from db.database import test_connection

        if test_connection():
            click.echo("Conexão com o banco OK.")
        else:
            click.echo("Falha ao conectar com o banco.", err=True)


app = create_app()

if __name__ == "__main__":

    #app.logger.info("Processo iniciado")
    #app.logger.warning("Algo fora do esperado")
    #app.logger.error("Falha ao processar requisição", exc_info=True)
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("DEBUG", "True").lower() == "true"

    app.logger.info("Iniciando BrewStation em http://%s:%s (debug=%s)", host, port, debug)
    app.run(host=host, port=port, debug=debug)