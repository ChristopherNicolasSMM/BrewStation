"""
Fixtures compartilhadas para testes do BrewStation.

Fornece um app Flask configurado com banco SQLite em memória
e o modelo Plant registrado para testes unitários.
"""

import os
import sys

import pytest
from flask import Flask
from flask_login import LoginManager

# Garantir que src/ esteja no path
_src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _src not in sys.path:
    sys.path.insert(0, _src)

from db.database import db as _db


@pytest.fixture(scope='session')
def app():
    """Cria uma aplicação Flask para testes."""
    flask_app = Flask(__name__)
    flask_app.config['TESTING'] = True
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    flask_app.config['SECRET_KEY'] = 'test-secret-key'
    flask_app.config['WTF_CSRF_ENABLED'] = False
    flask_app.config['LOGIN_DISABLED'] = True  # Desabilita autenticação

    # Inicializar extensões
    _db.init_app(flask_app)

    # Configurar Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(flask_app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return None

    with flask_app.app_context():
        # Importar e criar tabelas core
        _db.create_all()

        yield flask_app


@pytest.fixture(scope='function')
def db(app):
    """Fornece uma sessão limpa de banco para cada teste."""
    with app.app_context():
        # Criar todas as tabelas que os modelos do mash_control precisam
        _db.create_all()

        yield _db

        # Rollback e drop all após cada teste
        _db.session.rollback()
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    """Fornece um cliente de teste."""
    return app.test_client()


@pytest.fixture
def plant_service():
    """Fornece uma instância de PlantService."""
    from plugins.plugin_mash_control.services.plant_service import PlantService
    return PlantService()
