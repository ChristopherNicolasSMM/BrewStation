"""
Rotas web do plugin maker.
"""

from flask import Blueprint, render_template
from flask_login import login_required
from pathlib import Path

plugin_maker_web = Blueprint('plugin_maker_web', __name__)


def render_plugin_template(template_name: str, **context):
    """Renderiza template do plugin."""
    return render_template(template_name, **context)


@plugin_maker_web.route("/maker")
@login_required
def index():
    """Página principal do plugin."""
    return render_plugin_template("maker.html")
