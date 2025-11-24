"""
BrewStation - Sistema de Precificação de Cervejas.
"""

from __future__ import annotations

import os
from pathlib import Path

import click
from dotenv import load_dotenv
from flask import Flask
from flask.cli import with_appcontext
from flask_cors import CORS
from flask_login import LoginManager

from logs.setup_logging import configure_logging

# Carregar variáveis de ambiente
load_dotenv(Path("src") / ".env")


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

    init_db(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Por favor, faça login para acessar esta página."
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id):
        from model.user import User

        return User.query.get(int(user_id))

    CORS(app)
    register_blueprints(app)
    register_context_processors(app)
    register_cli_commands(app)

    return app


def register_blueprints(app):
    """Registra todos os blueprints da aplicação."""
    try:
        from api.routes import all_blueprints as legacy_api_blueprints
        from controller.api import api_bp
        from controller.auth import auth_bp
        from controller.web import web_bp

        app.register_blueprint(web_bp)
        app.register_blueprint(api_bp, url_prefix="/api")

        for bp in legacy_api_blueprints:
            app.register_blueprint(bp, url_prefix="/api")

        app.register_blueprint(auth_bp, url_prefix="/auth")

        app.logger.info("Blueprints registrados com sucesso.")
    except Exception as exc:  # pragma: no cover
        app.logger.exception("Erro ao registrar blueprints: %s", exc)
        raise


def register_context_processors(app):
    """Registra context processors."""

    @app.context_processor
    def inject_notifications_count():
        from flask_login import current_user

        try:
            if current_user.is_authenticated:
                from model.notification import Notification

                unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
                return {"unread_notifications_count": unread}
        except Exception as exc:  # pragma: no cover
            app.logger.debug("Erro no context processor de notificações: %s", exc)
        return {"unread_notifications_count": 0}


def register_cli_commands(app):
    """Registra comandos personalizados via Flask CLI."""

    @app.cli.command("init-admin")
    @click.option("--username", default="admin", show_default=True)
    @click.option("--email", default="admin@brew-station.com", show_default=True)
    @click.option("--password", default="admin123", show_default=True)
    @with_appcontext
    def init_admin(username, email, password):
        from db.database import db
        from model.config import Configuracao
        from model.user import User

        admin = User.query.filter_by(username=username).first()
        if admin:
            click.echo(f"Usuário {username} já existe.")
            return

        admin = User(username=username, email=email, is_admin=True, is_active=True)
        admin.set_password(password)
        db.session.add(admin)
        Configuracao.initialize_default_configs()
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