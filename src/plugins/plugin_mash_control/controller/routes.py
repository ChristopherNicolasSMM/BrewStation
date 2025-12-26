"""
Rotas web do plugin mash_control.
"""

from flask import Blueprint, render_template
from flask_login import login_required

plugin_mash_control_web = Blueprint('plugin_mash_control_web', __name__)


def render_plugin_template(template_name: str, **context):
    """Renderiza template do plugin."""
    return render_template(template_name, **context)


@plugin_mash_control_web.route("/mash_control/dashboard")
@login_required
def dashboard():
    """Dashboard principal."""
    return render_plugin_template("mash_control/dashboard.html")


@plugin_mash_control_web.route("/mash_control/recipes")
@login_required
def recipe_list():
    """Lista de receitas."""
    return render_plugin_template("mash_control/recipe_list.html")


@plugin_mash_control_web.route("/mash_control/recipes/new")
@plugin_mash_control_web.route("/mash_control/recipes/edit/<recipe_id>")
@login_required
def recipe_editor(recipe_id=None):
    """Editor de receitas."""
    return render_plugin_template("mash_control/recipe_editor.html", recipe_id=recipe_id)


@plugin_mash_control_web.route("/mash_control/sessions")
@plugin_mash_control_web.route("/mash_control/sessions/<session_id>")
@login_required
def session_control(session_id=None):
    """Controle de sessão."""
    return render_plugin_template("mash_control/session_control.html", session_id=session_id)


@plugin_mash_control_web.route("/mash_control/history")
@login_required
def session_history():
    """Histórico de sessões."""
    return render_plugin_template("mash_control/session_history.html")


@plugin_mash_control_web.route("/mash_control/settings")
@login_required
def settings():
    """Configurações."""
    return render_plugin_template("mash_control/settings.html")
