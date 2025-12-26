"""
Rotas web do plugin meu_plugin.
"""

from flask import Blueprint, render_template
from flask_login import login_required
from pathlib import Path

plugin_meu_plugin_web = Blueprint('plugin_meu_plugin_web', __name__)


def render_plugin_template(template_name: str, **context):
    """Renderiza template do plugin."""
    return render_template(template_name, **context)


@plugin_meu_plugin_web.route("/meu_plugin")
@login_required
def index():
    """Página principal do plugin."""
    return render_plugin_template("meu_plugin.html")
