"""Rotas web do Plugin Maker."""
from flask import Blueprint, render_template
from flask_login import login_required

plugin_maker_web = Blueprint("plugin_maker_web", __name__)

@plugin_maker_web.route("/maker")
@login_required
def index():
    return render_template("maker/index.html")

@plugin_maker_web.route("/maker/projects/<int:project_id>")
@login_required
def project_detail(project_id: int):
    return render_template("maker/project.html", project_id=project_id)
