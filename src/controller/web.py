"""
Rotas voltadas para páginas HTML.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from flask import Blueprint, current_app, redirect, render_template, url_for, abort, flash
from flask_login import current_user, login_required

logger = logging.getLogger(__name__)

web_bp = Blueprint("web", __name__)

TEMPLATE_ROOT = Path("src") / "templates"


def render_app_template(template_name: str, **context):
    """
    Helper centralizado que garante que o template existe antes de renderizar.
    Tenta primeiro nos templates do core, depois nos templates dos plugins ativos.
    """
    # O template loader customizado já cuida de buscar nos plugins
    # Então podemos usar render_template diretamente
    try:
        return render_template(template_name, **context)
    except Exception as e:
        logger.warning("Template %s não encontrado: %s. Retornando 404.", template_name, e)
        abort(404)


@web_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web_bp.route("/login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return render_app_template("login.html")


@web_bp.route("/register")
def register():
    if current_user.is_authenticated:
        return redirect(url_for("web.dashboard"))
    return render_app_template("register.html")


@web_bp.route("/register/request")
def register_request():
    return render_app_template("register_request.html")


@web_bp.route("/dashboard")
@login_required
def dashboard():
    return render_app_template("dashboard.html")


@web_bp.route("/config")
@login_required
def config():
    return render_app_template("config.html")


@web_bp.route("/profile")
@login_required
def profile():
    return render_app_template("profile.html")


@web_bp.route("/perfil")
@login_required
def perfil():
    return render_app_template("perfil.html")


# Rotas removidas - agora são gerenciadas pelos plugins
# As rotas específicas serão registradas pelos plugins através de seus blueprints


@web_bp.errorhandler(404)
def not_found(error):
    return render_app_template("notFound.html"), 404


@web_bp.errorhandler(500)
def internal_error(error):
    return render_app_template("notFound.html"), 500


@web_bp.route("/notFound")
def not_found_page():
    return render_app_template("notFound.html")

