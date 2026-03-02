"""Rotas web do Plugin Maker."""
from flask import Blueprint, render_template
from flask_login import login_required

plugin_maker_web = Blueprint("plugin_maker_web", __name__)

@plugin_maker_web.route("/maker")
@login_required
def index():
    return render_template("maker/index.html")