"""
Rotas web do plugin yeast_bank.

Observação de manutenção:
- A experiência principal de Starter + Contagem foi unificada em starters.html.
- As rotas /yeast_bank/tools e /yeast_bank/starters continuam existindo por compatibilidade,
  mas ambas apontam para a mesma tela para evitar duplicidade funcional.
"""
from flask import Blueprint, render_template
from flask_login import login_required
from plugins.plugin_yeast_bank.utils.schema import ensure_storage_schema

plugin_yeast_bank_web = Blueprint("plugin_yeast_bank_web", __name__)


@plugin_yeast_bank_web.before_request
def _bootstrap_schema():
    ensure_storage_schema()


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


@plugin_yeast_bank_web.route("/yeast_bank/storage")
@login_required
def storage():
    return render_plugin_template("yeast_bank/storage.html")


@plugin_yeast_bank_web.route("/yeast_bank/config")
@login_required
def config():
    return render_plugin_template("yeast_bank/config.html")


@plugin_yeast_bank_web.route("/yeast_bank/tools")
@login_required
def tools():
    return render_plugin_template("yeast_bank/starters.html")
