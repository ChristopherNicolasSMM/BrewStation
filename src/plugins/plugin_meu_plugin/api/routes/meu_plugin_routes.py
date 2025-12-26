"""
Rotas API do plugin meu_plugin.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

# IMPORTANTE: Se você usar modelos SQLAlchemy nesta rota, use model_loader:
# from plugins.plugin_meu_plugin.utils.model_loader import get_meu_modelo
# MeuModelo = get_meu_modelo()
# Veja docs/PLUGIN_MODEL_LOADER.md para mais detalhes

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


# Exemplo de rota que usa modelo (descomente e ajuste quando criar modelos):
# @plugin_meu_plugin_api.route('/meu_plugin/dados', methods=['GET'])
# @login_required
# def get_dados():
#     """Retorna dados do modelo."""
#     # Usar model_loader para garantir prefixo correto
#     from plugins.plugin_meu_plugin.utils.model_loader import get_meu_modelo
#     MeuModelo = get_meu_modelo()
#     
#     dados = MeuModelo.query.all()
#     return jsonify([d.to_dict() for d in dados]), 200
