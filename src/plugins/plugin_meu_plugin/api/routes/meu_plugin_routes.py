"""
Rotas API do plugin meu_plugin.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

plugin_meu_plugin_api = Blueprint('plugin_meu_plugin_api', __name__)


@plugin_meu_plugin_api.route('/meu_plugin/info', methods=['GET'])
@login_required
def get_info():
    """Retorna informações do plugin."""
    return jsonify({
        'name': 'meu_plugin',
        'status': 'active',
        'message': 'Plugin funcionando corretamente!'
    }), 200
