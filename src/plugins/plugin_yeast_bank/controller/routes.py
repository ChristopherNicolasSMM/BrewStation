"""
Rotas web do plugin yeast_bank.
"""
from flask import Blueprint, render_template
from flask_login import login_required

plugin_yeast_bank_web = Blueprint("plugin_yeast_bank_web", __name__)

def render_plugin_template(template_name: str, **context):
    return render_template(template_name, **context)

@plugin_yeast_bank_web.route("/yeast_bank")
@plugin_yeast_bank_web.route("/yeast_bank/dashboard")
@login_required
def dashboard():
    return render_plugin_template("yeast_bank/dashboard.html")

@plugin_yeast_bank_web.route("/yeast_bank/strains")
@login_required
def strains():
    return render_plugin_template("yeast_bank/strains.html")

@plugin_yeast_bank_web.route("/yeast_bank/items")
@login_required
def bank_items():
    return render_plugin_template("yeast_bank/bank_items.html")

@plugin_yeast_bank_web.route("/yeast_bank/starters")
@login_required
def starters():
    return render_plugin_template("yeast_bank/starters.html")

@plugin_yeast_bank_web.route("/yeast_bank/config")
@login_required
def config():
    return render_plugin_template("yeast_bank/config.html")