"""
Rotas API do plugin maker.
"""

from flask import Blueprint, jsonify
from flask_login import login_required

# IMPORTANTE: Se você usar modelos SQLAlchemy nesta rota, use model_loader:
# from plugins.plugin_maker.utils.model_loader import get_meu_modelo
# MeuModelo = get_meu_modelo()
# Veja docs/PLUGIN_MODEL_LOADER.md para mais detalhes

plugin_maker_api = Blueprint('plugin_maker_api', __name__)


@plugin_maker_api.route('/maker/info', methods=['GET'])
@login_required
def get_info():
    """Retorna informações do plugin."""
    return jsonify({
        'name': 'maker',
        'status': 'active',
        'message': 'Plugin funcionando corretamente!'
    }), 200


# Exemplo de rota que usa modelo (descomente e ajuste quando criar modelos):
# @plugin_maker_api.route('/maker/dados', methods=['GET'])
# @login_required
# def get_dados():
#     """Retorna dados do modelo."""
#     # Usar model_loader para garantir prefixo correto
#     from plugins.plugin_maker.utils.model_loader import get_meu_modelo
#     MeuModelo = get_meu_modelo()
#     
#     dados = MeuModelo.query.all()
#     return jsonify([d.to_dict() for d in dados]), 200
