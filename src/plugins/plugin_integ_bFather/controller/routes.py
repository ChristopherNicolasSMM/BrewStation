"""
Rotas web do plugin brewstation_core.
"""

from flask import Blueprint, render_template
from flask_login import login_required
from pathlib import Path

web_plugin_bp = Blueprint(
    'plugin_brewstation_core_web',
    __name__,
    static_folder='../static',
    static_url_path='/plugin_integ_bfather_static',
    template_folder='../templates'
)


def render_plugin_template(template_name: str, **context):
    """Renderiza template do plugin."""
    # Templates do plugin estão em plugins/brewstation_core/templates/
    # O template loader customizado já cuida disso
    return render_template(template_name, **context)


@web_plugin_bp.route("/dashboard")
@login_required
def dashboard():
    """Dashboard do plugin."""
    return render_plugin_template("dashboard.html")


@web_plugin_bp.route("/maltes")
@login_required
def maltes():
    return render_plugin_template("maltes.html")


@web_plugin_bp.route("/lupulos")
@login_required
def lupulos():
    return render_plugin_template("lupulos.html")


@web_plugin_bp.route("/leveduras")
@login_required
def leveduras():
    return render_plugin_template("leveduras.html")


@web_plugin_bp.route("/dispositivos")
@login_required
def dispositivos():
    return render_plugin_template("dispositivos.html")


@web_plugin_bp.route("/notifications")
@login_required
def notifications_page():
    return render_plugin_template("notifications.html")


@web_plugin_bp.route("/brewfather")
@login_required
def brewfather():
    return render_plugin_template("brewfather.html")


@web_plugin_bp.route("/receitas")
@login_required
def receitas():
    return render_plugin_template("receitas.html")


@web_plugin_bp.route("/calculos")
@login_required
def calculos():
    return render_plugin_template("calculos.html")


@web_plugin_bp.route("/calculos_envase")
@login_required
def calculos_envase():
    return render_plugin_template("calculos_envase.html")


@web_plugin_bp.route("/upload")
@login_required
def upload():
    return render_plugin_template("upload.html")


@web_plugin_bp.route("/relatorio-precos")
@login_required
def relatorio_precos():
    return render_plugin_template("relatorio_precos.html")


@web_plugin_bp.route("/relatorio-ingredientes")
@login_required
def relatorio_ingredientes():
    return render_plugin_template("relatorio_ingredientes.html")


@web_plugin_bp.route("/relatorios-brewfather")
@login_required
def relatorios_brewfather():
    return render_plugin_template("relatorios_brewfather.html")


@web_plugin_bp.route("/envase")
@login_required
def envase():
    return render_plugin_template("envase.html")


@web_plugin_bp.route("/estoque")
@login_required
def estoque():
    return render_plugin_template("estoque.html")


@web_plugin_bp.route("/profile")
@login_required
def profile():
    return render_plugin_template("profile.html")


@web_plugin_bp.route("/perfil")
@login_required
def perfil():
    return render_plugin_template("perfil.html")


@web_plugin_bp.route("/fermentacao")
@login_required
def fermentacao():
    return render_plugin_template("controle_fermentacao.html")


@web_plugin_bp.route("/brassagem")
@login_required
def brassagem():
    return render_plugin_template("controle_dispositivos_brasagem.html")


@web_plugin_bp.route("/ispindel")
@login_required
def ispindel():
    return render_plugin_template("ispindel_graficos.html")

