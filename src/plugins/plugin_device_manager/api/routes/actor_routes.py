"""
Rotas API para gerenciamento de atores de dispositivos.
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required

logger = logging.getLogger(__name__)

actor_bp = Blueprint('plugin_device_manager_actor_api', __name__)


def get_actor_manager():
    """Obtém instância do ActorManager."""
    from flask import current_app

    from plugins.plugin_device_manager.utils.actor_manager import ActorManager
    
    plugin_manager = current_app.plugin_manager
    plugin = plugin_manager.get_plugin('device_manager')
    if plugin:
        return ActorManager(plugin.plugin_path)
    return None


@actor_bp.route('/actors', methods=['GET'])
@login_required
def list_actors():
    """Lista atores com filtros."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        # Filtros
        device_id = request.args.get('device_id')
        plugin_name = request.args.get('plugin_name')
        plugin_entity_id = request.args.get('plugin_entity_id')
        actor_type = request.args.get('actor_type')
        
        if device_id:
            actors = manager.get_actors_by_device(device_id)
        elif plugin_name:
            actors = manager.get_actors_by_plugin(plugin_name, plugin_entity_id)
        elif actor_type:
            actors = manager.get_actors_by_type(actor_type, plugin_name)
        else:
            # Listar todos (usar modelo diretamente)
            from plugins.plugin_device_manager.utils.model_loader import \
                get_device_actor
            DeviceActor = get_device_actor()
            if not DeviceActor:
                return jsonify({'error': 'Modelo DeviceActor não disponível'}), 500
            
            actors_list = DeviceActor.query.all()
            actors = [actor.to_dict() for actor in actors_list]
        
        return jsonify({
            'success': True,
            'actors': actors,
            'total': len(actors)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar atores: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/<actor_id>', methods=['GET'])
@login_required
def get_actor(actor_id):
    """Obtém ator específico."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        actor = manager.get_actor(actor_id)
        if not actor:
            return jsonify({'error': 'Ator não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'actor': actor
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter ator {actor_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors', methods=['POST'])
@login_required
def create_actor():
    """Cria novo ator."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Validar campos obrigatórios
        required_fields = ['device_id', 'port_name', 'function_id', 'actor_type', 'name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório faltando: {field}'}), 400
        
        actor_id = manager.create_actor(
            device_id=data['device_id'],
            port_name=data['port_name'],
            function_id=data['function_id'],
            actor_type=data['actor_type'],
            name=data['name'],
            description=data.get('description'),
            config=data.get('config')
        )
        
        if not actor_id:
            return jsonify({'error': 'Erro ao criar ator'}), 500
        
        actor = manager.get_actor(actor_id)
        
        return jsonify({
            'success': True,
            'actor': actor,
            'message': 'Ator criado com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar ator: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/<actor_id>', methods=['PUT'])
@login_required
def update_actor(actor_id):
    """Atualiza ator."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        success = manager.update_actor(actor_id, data)
        if not success:
            return jsonify({'error': 'Ator não encontrado ou erro ao atualizar'}), 404
        
        actor = manager.get_actor(actor_id)
        
        return jsonify({
            'success': True,
            'actor': actor,
            'message': 'Ator atualizado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar ator {actor_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/<actor_id>', methods=['DELETE'])
@login_required
def delete_actor(actor_id):
    """Remove ator."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        success = manager.delete_actor(actor_id)
        if not success:
            return jsonify({'error': 'Ator não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Ator removido com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao deletar ator {actor_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/<actor_id>/execute', methods=['POST'])
@login_required
def execute_actor(actor_id):
    """Executa ação do ator."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        data = request.get_json()
        if not data or 'value' not in data:
            return jsonify({'error': 'Valor não fornecido'}), 400
        
        value = data['value']
        success = manager.execute_actor_action(actor_id, value)
        
        if not success:
            return jsonify({'error': 'Erro ao executar ação do ator'}), 500
        
        return jsonify({
            'success': True,
            'message': 'Ação executada com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao executar ação do ator {actor_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/<actor_id>/read', methods=['GET'])
@login_required
def read_actor(actor_id):
    """Lê valor do sensor."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        value = manager.read_actor_sensor(actor_id)
        
        return jsonify({
            'success': True,
            'value': value
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao ler valor do ator {actor_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/device/<device_id>', methods=['GET'])
@login_required
def list_actors_by_device(device_id):
    """Lista atores de um device."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        actors = manager.get_actors_by_device(device_id)
        
        return jsonify({
            'success': True,
            'actors': actors,
            'total': len(actors)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar atores do device {device_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/plugin/<plugin_name>', methods=['GET'])
@login_required
def list_actors_by_plugin(plugin_name):
    """Lista atores de um plugin."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        plugin_entity_id = request.args.get('plugin_entity_id')
        actors = manager.get_actors_by_plugin(plugin_name, plugin_entity_id)
        
        return jsonify({
            'success': True,
            'actors': actors,
            'total': len(actors)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar atores do plugin {plugin_name}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@actor_bp.route('/actors/<actor_id>/link', methods=['POST'])
@login_required
def link_actor_to_plugin(actor_id):
    """Associa ator a entidade de outro plugin."""
    try:
        manager = get_actor_manager()
        if not manager:
            return jsonify({'error': 'ActorManager não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        plugin_name = data.get('plugin_name')
        plugin_entity_id = data.get('plugin_entity_id')
        
        if not plugin_name:
            return jsonify({'error': 'plugin_name é obrigatório'}), 400
        
        success = manager.link_actor_to_plugin(actor_id, plugin_name, plugin_entity_id)
        
        if not success:
            return jsonify({'error': 'Ator não encontrado ou erro ao associar'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Ator associado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao associar ator {actor_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
