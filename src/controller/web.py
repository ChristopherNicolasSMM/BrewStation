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
    """
    available_templates = current_app.jinja_env.list_templates()
    if template_name not in available_templates:
        logger.warning("Template %s não encontrado. Retornando 404.", template_name)
        abort(404)
    return render_template(template_name, **context)


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


@web_bp.route("/maltes")
@login_required
def maltes():
    return render_app_template("maltes.html")


@web_bp.route("/lupulos")
@login_required
def lupulos():
    return render_app_template("lupulos.html")


@web_bp.route("/leveduras")
@login_required
def leveduras():
    return render_app_template("leveduras.html")


@web_bp.route("/dispositivos")
@login_required
def dispositivos():
    return render_app_template("dispositivos.html")


@web_bp.route("/notifications")
@login_required
def notifications_page():
    return render_app_template("notifications.html")


@web_bp.route("/brewfather")
@login_required
def brewfather():
    return render_app_template("brewfather.html")


@web_bp.route("/receitas")
@login_required
def receitas():
    return render_app_template("receitas.html")


@web_bp.route("/calculos")
@login_required
def calculos():
    return render_app_template("calculos.html")


@web_bp.route("/calculos_envase")
@login_required
def calculos_envase():
    return render_app_template("calculos_envase.html")


@web_bp.route("/upload")
@login_required
def upload():
    return render_app_template("upload.html")


@web_bp.route("/relatorio-precos")
@login_required
def relatorio_precos():
    return render_app_template("relatorio_precos.html")


@web_bp.route("/relatorio-ingredientes")
@login_required
def relatorio_ingredientes():
    return render_app_template("relatorio_ingredientes.html")


@web_bp.route("/relatorios-brewfather")
@login_required
def relatorios_brewfather():
    return render_app_template("relatorios_brewfather.html")


@web_bp.route("/envase")
@login_required
def envase():
    return render_app_template("envase.html")


@web_bp.route("/estoque")
@login_required
def estoque():
    return render_app_template("estoque.html")


@web_bp.route("/profile")
@login_required
def profile():
    return render_app_template("profile.html")


@web_bp.route("/perfil")
@login_required
def perfil():
    return render_app_template("perfil.html")


@web_bp.errorhandler(404)
def not_found(error):
    return render_app_template("notFound.html"), 404


@web_bp.errorhandler(500)
def internal_error(error):
    return render_app_template("notFound.html"), 500


@web_bp.route("/notFound")
def not_found_page():
    return render_app_template("notFound.html")

