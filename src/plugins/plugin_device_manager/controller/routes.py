"""
Rotas web do plugin device_manager.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

plugin_device_manager_web = Blueprint('plugin_device_manager_web', __name__)


def render_plugin_template(template_name: str, **context):
    """Renderiza template do plugin."""
    return render_template(template_name, **context)


def get_registry():
    """Obtém instância do DeviceRegistry."""
    from plugins.plugin_device_manager.utils.device_registry import DeviceRegistry
    from flask import current_app
    
    plugin_manager = current_app.plugin_manager
    plugin = plugin_manager.get_plugin('device_manager')
    if plugin:
        return DeviceRegistry(plugin.plugin_path)
    return None


@plugin_device_manager_web.route("/device_manager")
@login_required
def device_list():
    """Lista todos os dispositivos."""
    return render_plugin_template("device_manager.html")


@plugin_device_manager_web.route("/device_manager/add")
@login_required
def device_add():
    """Formulário de cadastro de dispositivo."""
    return render_plugin_template("device_form.html", device=None, action="add")


@plugin_device_manager_web.route("/device_manager/edit/<device_id>")
@login_required
def device_edit(device_id):
    """Formulário de edição de dispositivo."""
    registry = get_registry()
    if not registry:
        flash("Erro ao carregar dispositivo", "error")
        return redirect(url_for('plugin_device_manager_web.device_list'))
    
    device = registry.get_device(device_id)
    if not device:
        flash("Dispositivo não encontrado", "error")
        return redirect(url_for('plugin_device_manager_web.device_list'))
    
    return render_plugin_template("device_form.html", device=device, action="edit", device_id=device_id)


@plugin_device_manager_web.route("/device_manager/view/<device_id>")
@login_required
def device_view(device_id):
    """Visualização detalhada de dispositivo."""
    registry = get_registry()
    if not registry:
        flash("Erro ao carregar dispositivo", "error")
        return redirect(url_for('plugin_device_manager_web.device_list'))
    
    device = registry.get_device(device_id)
    state = registry.get_state(device_id)
    
    if not device:
        flash("Dispositivo não encontrado", "error")
        return redirect(url_for('plugin_device_manager_web.device_list'))
    
    return render_plugin_template("device_view.html", device=device, state=state)


@plugin_device_manager_web.route("/device_manager/mqtt")
@login_required
def mqtt_config():
    """Configuração do broker MQTT."""
    return render_plugin_template("mqtt_config.html")


@plugin_device_manager_web.route("/device_manager/logs")
@login_required
def status_logs():
    """Logs e monitoramento."""
    return render_plugin_template("status_logs.html")


@plugin_device_manager_web.route("/device_manager/mqtt/monitor")
@login_required
def mqtt_monitor():
    """Monitoramento e testes MQTT."""
    return render_plugin_template("mqtt_monitor.html")
