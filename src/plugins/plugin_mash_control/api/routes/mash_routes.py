"""
Rotas API para controle de brassagem e sessões.
"""

import json
import logging

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from plugins.plugin_mash_control.services.dashboard_builder import \
    DashboardBuilderService
from plugins.plugin_mash_control.services.device_integration import \
    DeviceIntegrationService
from plugins.plugin_mash_control.services.mash_session_service import \
    get_mash_session_service
from plugins.plugin_mash_control.services.plant_service import PlantService
from plugins.plugin_mash_control.services.process_control import \
    ProcessControlService
from plugins.plugin_mash_control.services.recipe_service import RecipeService
from plugins.plugin_mash_control.utils.model_loader import (
    get_brew_session, get_dashboard_layout)

logger = logging.getLogger(__name__)

mash_bp = Blueprint('plugin_mash_control_mash_api', __name__)


def get_process_control():
    """Obtém instância do ProcessControlService."""
    try:
        from flask import current_app
        if hasattr(current_app, 'plugin_manager'):
            plugin_manager = current_app.plugin_manager
            # Tentar buscar pelo nome do diretório primeiro
            plugin = plugin_manager.get_plugin('plugin_mash_control')
            if not plugin:
                # Tentar pelo nome do plugin
                plugin = plugin_manager.get_plugin('mash_control')
            if plugin:
                return ProcessControlService(plugin.plugin_path)
        # Fallback: usar caminho padrão
        from pathlib import Path
        plugin_path = Path(__file__).parent.parent.parent
        return ProcessControlService(plugin_path)
    except Exception as e:
        logger.error(f"Erro ao obter ProcessControlService: {e}")
        return None


def get_dashboard_builder():
    """Obtém instância do DashboardBuilderService."""
    try:
        from flask import current_app
        if hasattr(current_app, 'plugin_manager'):
            plugin_manager = current_app.plugin_manager
            # Tentar buscar pelo nome do diretório primeiro
            plugin = plugin_manager.get_plugin('plugin_mash_control')
            if not plugin:
                # Tentar pelo nome do plugin
                plugin = plugin_manager.get_plugin('mash_control')
            if plugin:
                return DashboardBuilderService(plugin.plugin_path)
        # Fallback: usar caminho padrão
        from pathlib import Path
        plugin_path = Path(__file__).parent.parent.parent
        return DashboardBuilderService(plugin_path)
    except Exception as e:
        logger.error(f"Erro ao obter DashboardBuilderService: {e}")
        return None


def get_plant_service():
    """Obtém instância do PlantService."""
    return PlantService()


def get_recipe_service():
    """Obtém instância do RecipeService."""
    return RecipeService()


# Rotas de Dashboard
@mash_bp.route('/dashboard/layout', methods=['GET'])
@login_required
def get_dashboard_layout():
    """Obtém layout do dashboard."""
    try:
        layout_id = request.args.get('layout_id')
        user_id = current_user.id if current_user.is_authenticated else None
        
        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        if layout_id:
            layout = dashboard_builder.load_layout(layout_id)
        else:
            layout = dashboard_builder.get_default_layout(user_id)
        
        # Se não encontrou layout, retornar layout vazio ao invés de erro
        if not layout:
            layout = {
                'id': None,
                'name': 'Novo Layout',
                'elements': [],
                'is_default': True
            }
        
        return jsonify(layout), 200
    except Exception as e:
        logger.error(f"Erro ao obter layout: {e}", exc_info=True)
        # Retornar layout vazio em caso de erro
        return jsonify({
            'id': None,
            'name': 'Novo Layout',
            'elements': [],
            'is_default': True
        }), 200


@mash_bp.route('/dashboard/layout', methods=['POST'])
@login_required
def save_dashboard_layout():
    """Salva layout do dashboard."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        user_id = current_user.id if current_user.is_authenticated else None
        
        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        # Garantir que temos elementos no formato correto
        elements = data.get('elements', [])
        if not isinstance(elements, list):
            elements = []
        
        layout_data = {
            'name': data.get('name', 'Novo Layout'),
            'elements': elements,
            'id': data.get('id')
        }
        
        logger.info(f"Salvando layout: {layout_data.get('name')}, elementos: {len(elements)}")
        
        layout_id = dashboard_builder.save_layout(
            layout_data,
            user_id=user_id,
            is_default=data.get('is_default', True)
        )
        
        if layout_id:
            logger.info(f"Layout salvo com sucesso: {layout_id}")
            return jsonify({'id': layout_id, 'message': 'Layout salvo'}), 200
        else:
            logger.error("Falha ao salvar layout")
            return jsonify({'error': 'Erro ao salvar layout'}), 500
    except Exception as e:
        logger.error(f"Erro ao salvar layout: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/devices', methods=['GET'])
@login_required
def get_dashboard_devices():
    """Lista dispositivos disponíveis. Retorna lista vazia se device_manager não está disponível."""
    try:
        device_integration = DeviceIntegrationService()
        
        filters = {}
        if request.args.get('device_type'):
            filters['device_type'] = request.args.get('device_type')
        if request.args.get('protocol'):
            filters['protocol'] = request.args.get('protocol')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active') == 'true'
        
        # DeviceIntegrationService retorna [] se device_manager não está disponível
        devices = device_integration.get_available_devices(filters)
        return jsonify(devices), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/components', methods=['GET'])
@login_required
def get_dashboard_components():
    """Lista componentes SVG disponíveis."""
    try:
        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        components = dashboard_builder.get_svg_components()
        return jsonify(components), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/layouts', methods=['GET'])
@login_required
def list_dashboard_layouts():
    """Lista todos os dashboards do usuário."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        
        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        layouts = dashboard_builder.list_user_layouts(user_id, limit=10)
        return jsonify(layouts), 200
    except Exception as e:
        logger.error(f"Erro ao listar layouts: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/layout/<layout_id>/set-default', methods=['POST'])
@login_required
def set_default_dashboard(layout_id):
    """Define um dashboard como padrão."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        
        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        success = dashboard_builder.set_default_layout(layout_id, user_id)
        if success:
            return jsonify({'message': 'Dashboard padrão definido'}), 200
        return jsonify({'error': 'Erro ao definir dashboard padrão'}), 500
    except Exception as e:
        logger.error(f"Erro ao definir dashboard padrão: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/layout/<layout_id>', methods=['DELETE'])
@login_required
def delete_dashboard_layout(layout_id):
    """Deleta um dashboard."""
    try:
        user_id = current_user.id if current_user.is_authenticated else None
        
        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        success = dashboard_builder.delete_layout(layout_id, user_id)
        if success:
            return jsonify({'message': 'Dashboard deletado'}), 200
        return jsonify({'error': 'Erro ao deletar dashboard'}), 500
    except Exception as e:
        logger.error(f"Erro ao deletar dashboard: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/layout/<layout_id>/element/<element_id>/position', methods=['PUT'])
@login_required
def update_element_position(layout_id, element_id):
    """Atualiza posição de um elemento no layout."""
    try:
        data = request.get_json()
        if not data or 'x' not in data or 'y' not in data:
            return jsonify({'error': 'Coordenadas x e y são obrigatórias'}), 400

        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500

        success = dashboard_builder.update_element_position(
            element_id, layout_id, data['x'], data['y']
        )
        if success:
            return jsonify({'message': 'Posição atualizada'}), 200
        return jsonify({'error': 'Elemento ou layout não encontrado'}), 404
    except Exception as e:
        logger.error(f"Erro ao atualizar posição: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/layout/<layout_id>/element/<element_id>/link-device', methods=['POST'])
@login_required
def link_element_to_device(layout_id, element_id):
    """Vincula um elemento SVG a um dispositivo."""
    try:
        data = request.get_json()
        if not data or 'device_id' not in data:
            return jsonify({'error': 'device_id é obrigatório'}), 400

        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500

        success = dashboard_builder.link_element_to_device(
            element_id, layout_id, data['device_id']
        )
        if success:
            return jsonify({'message': 'Dispositivo vinculado'}), 200
        return jsonify({'error': 'Elemento ou layout não encontrado'}), 404
    except Exception as e:
        logger.error(f"Erro ao vincular dispositivo: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/layout/<layout_id>/telemetry', methods=['GET'])
@login_required
def get_layout_telemetry(layout_id):
    """Obtém telemetria ao vivo dos dispositivos vinculados ao layout."""
    try:
        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500

        layout = dashboard_builder.load_layout(layout_id)
        if not layout:
            return jsonify({'error': 'Layout não encontrado'}), 404

        elements = layout.get('elements', [])
        device_integration = DeviceIntegrationService()

        telemetry = []
        for element in elements:
            device_id = element.get('device_id')
            if not device_id:
                telemetry.append({
                    'element_id': element.get('id'),
                    'device_id': None,
                    'status': 'unlinked'
                })
                continue

            try:
                device_status = device_integration.get_device_status(device_id)
                entry = {
                    'element_id': element.get('id'),
                    'device_id': device_id,
                }
                if device_status:
                    entry['status'] = device_status.get('status', 'unknown')
                    entry['actor_type'] = device_status.get('actor_type')
                    entry['name'] = device_status.get('name')
                    entry['value'] = device_status.get('value')
                else:
                    entry['status'] = 'offline'
                    entry['value'] = None
                telemetry.append(entry)
            except Exception as e:
                logger.warning(f"Falha ao obter status do device {device_id}: {e}")
                telemetry.append({
                    'element_id': element.get('id'),
                    'device_id': device_id,
                    'status': 'offline',
                    'value': None
                })

        return jsonify({'elements': telemetry}), 200
    except Exception as e:
        logger.error(f"Erro ao obter telemetria: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/status', methods=['GET'])
@login_required
def get_dashboard_status():
    """Status atual do dashboard."""
    try:
        BrewSession = get_brew_session()
        if not BrewSession:
            return jsonify({'error': 'Modelo não disponível'}), 500
        
        active_sessions = BrewSession.query.filter_by(status='running').count()
        paused_sessions = BrewSession.query.filter_by(status='paused').count()
        
        return jsonify({
            'active_sessions': active_sessions,
            'paused_sessions': paused_sessions,
            'total_sessions': active_sessions + paused_sessions
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== ROTAS DE WIDGET DATA ==============


@mash_bp.route('/dashboard/widget/<element_id>/data', methods=['GET'])
@login_required
def get_widget_data(element_id):
    """
    Retorna dados ao vivo de um widget específico do dashboard.

    Busca o layout que contém o elemento, localiza o elemento pelo ID,
    resolve o device_id vinculado e retorna o valor atual do sensor/atuador.
    """
    try:
        layout_id = request.args.get('layout_id')
        if not layout_id:
            return jsonify({'error': 'layout_id é obrigatório'}), 400

        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500

        layout = dashboard_builder.load_layout(layout_id)
        if not layout:
            return jsonify({'error': 'Layout não encontrado'}), 404

        elements = layout.get('elements', [])
        element = next((el for el in elements if el.get('id') == element_id), None)
        if not element:
            return jsonify({'error': 'Elemento não encontrado no layout'}), 404

        device_id = element.get('device_id')
        if not device_id:
            return jsonify({
                'element_id': element_id,
                'element_type': element.get('type'),
                'device_id': None,
                'status': 'unlinked',
                'value': None
            }), 200

        device_integration = DeviceIntegrationService()
        if not device_integration.is_available():
            return jsonify({
                'element_id': element_id,
                'device_id': device_id,
                'status': 'unavailable',
                'value': None
            }), 200

        # Obter status do dispositivo
        device_status = device_integration.get_device_status(device_id)
        if not device_status:
            return jsonify({
                'element_id': element_id,
                'device_id': device_id,
                'status': 'offline',
                'value': None
            }), 200

        # Para sensores, incluir também portas detalhadas
        ports = {}
        if device_status.get('actor_type') == 'sensor':
            ports = device_integration.get_all_ports(device_id)

        return jsonify({
            'element_id': element_id,
            'element_type': element.get('type'),
            'device_id': device_id,
            'actor_type': device_status.get('actor_type'),
            'name': device_status.get('name'),
            'status': device_status.get('status', 'online'),
            'value': device_status.get('value'),
            'ports': ports,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Erro ao obter dados do widget {element_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/dashboard/widgets/batch', methods=['GET'])
@login_required
def get_widgets_batch_data():
    """
    Retorna dados ao vivo de múltiplos widgets em uma única requisição.

    Query params:
        layout_id (string): ID do layout
        element_ids (string): IDs separados por vírgula

    Útil para atualização periódica (polling) do dashboard sem sobrecarregar
    o servidor com N requisições individuais.
    """
    try:
        layout_id = request.args.get('layout_id')
        element_ids_param = request.args.get('element_ids', '')

        if not layout_id or not element_ids_param:
            return jsonify({'error': 'layout_id e element_ids são obrigatórios'}), 400

        element_ids = [eid.strip() for eid in element_ids_param.split(',') if eid.strip()]
        if not element_ids:
            return jsonify({'error': 'Nenhum element_id válido fornecido'}), 400

        dashboard_builder = get_dashboard_builder()
        if not dashboard_builder:
            return jsonify({'error': 'Serviço não disponível'}), 500

        layout = dashboard_builder.load_layout(layout_id)
        if not layout:
            return jsonify({'error': 'Layout não encontrado'}), 404

        elements = layout.get('elements', [])
        device_integration = DeviceIntegrationService()
        results = {}

        for element_id in element_ids:
            element = next((el for el in elements if el.get('id') == element_id), None)
            if not element:
                results[element_id] = {'error': 'Elemento não encontrado no layout'}
                continue

            device_id = element.get('device_id')
            if not device_id:
                results[element_id] = {
                    'device_id': None,
                    'status': 'unlinked',
                    'value': None
                }
                continue

            if not device_integration.is_available():
                results[element_id] = {
                    'device_id': device_id,
                    'status': 'unavailable',
                    'value': None
                }
                continue

            try:
                device_status = device_integration.get_device_status(device_id)
                if not device_status:
                    results[element_id] = {
                        'device_id': device_id,
                        'status': 'offline',
                        'value': None
                    }
                else:
                    entry = {
                        'device_id': device_id,
                        'actor_type': device_status.get('actor_type'),
                        'name': device_status.get('name'),
                        'status': device_status.get('status', 'online'),
                        'value': device_status.get('value'),
                    }
                    # Incluir portas detalhadas para sensores
                    if device_status.get('actor_type') == 'sensor':
                        entry['ports'] = device_integration.get_all_ports(device_id)
                    results[element_id] = entry
            except Exception as e:
                logger.warning(f"Falha ao obter dados do device {device_id}: {e}")
                results[element_id] = {
                    'device_id': device_id,
                    'status': 'offline',
                    'value': None
                }

        return jsonify({
            'elements': results,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 200

    except Exception as e:
        logger.error(f"Erro ao obter dados batch dos widgets: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# Rotas de Sessões
@mash_bp.route('/sessions', methods=['GET'])
@login_required
def list_sessions():
    """Lista sessões."""
    try:
        BrewSession = get_brew_session()
        if not BrewSession:
            return jsonify({'error': 'Modelo não disponível'}), 500
        
        status = request.args.get('status')
        query = BrewSession.query
        
        if status:
            query = query.filter_by(status=status)
        
        sessions = query.order_by(BrewSession.created_at.desc()).limit(50).all()
        return jsonify([s.to_dict() for s in sessions]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions/<session_id>', methods=['GET'])
@login_required
def get_session(session_id):
    """Obtém sessão específica."""
    try:
        BrewSession = get_brew_session()
        if not BrewSession:
            return jsonify({'error': 'Modelo não disponível'}), 500
        
        session = BrewSession.query.get(session_id)
        if session:
            return jsonify(session.to_dict()), 200
        return jsonify({'error': 'Sessão não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions', methods=['POST'])
@login_required
def create_session():
    """Inicia nova sessão."""
    try:
        data = request.get_json()
        recipe_id = data.get('recipe_id')
        equipment_mapping = data.get('equipment_mapping', {})
        session_name = data.get('name')
        plant_id = data.get('plant_id')

        if not recipe_id:
            return jsonify({'error': 'recipe_id é obrigatório'}), 400

        process_control = get_process_control()
        if not process_control:
            return jsonify({'error': 'Serviço não disponível'}), 500

        session_id = process_control.start_session(
            recipe_id, equipment_mapping, session_name, plant_id
        )

        if session_id:
            return jsonify({'id': session_id, 'message': 'Sessão iniciada'}), 201
        return jsonify({'error': 'Erro ao iniciar sessão'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions/<session_id>/pause', methods=['POST'])
@login_required
def pause_session(session_id):
    """Pausa sessão."""
    try:
        process_control = get_process_control()
        if not process_control:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        if process_control.pause_session(session_id):
            return jsonify({'message': 'Sessão pausada'}), 200
        return jsonify({'error': 'Erro ao pausar sessão'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions/<session_id>/resume', methods=['POST'])
@login_required
def resume_session(session_id):
    """Retoma sessão."""
    try:
        process_control = get_process_control()
        if not process_control:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        if process_control.resume_session(session_id):
            return jsonify({'message': 'Sessão retomada'}), 200
        return jsonify({'error': 'Erro ao retomar sessão'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions/<session_id>/stop', methods=['POST'])
@login_required
def stop_session(session_id):
    """Para sessão."""
    try:
        process_control = get_process_control()
        if not process_control:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        if process_control.stop_session(session_id):
            return jsonify({'message': 'Sessão parada'}), 200
        return jsonify({'error': 'Erro ao parar sessão'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions/<session_id>/command', methods=['POST'])
@login_required
def send_session_command(session_id):
    """Envia comando manual para sessão."""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        command = data.get('command')
        payload = data.get('payload', {})
        
        if not device_id or not command:
            return jsonify({'error': 'device_id e command são obrigatórios'}), 400
        
        device_integration = DeviceIntegrationService()
        if not device_integration.is_available():
            return jsonify({'error': 'device_manager não disponível'}), 500
        
        result = device_integration.send_command(device_id, command, payload)
        
        if result:
            return jsonify({'message': 'Comando enviado'}), 200
        return jsonify({'error': 'Erro ao enviar comando'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions/<session_id>/logs', methods=['GET'])
@login_required
def get_session_logs(session_id):
    """Obtém logs da sessão."""
    try:
        BrewSession = get_brew_session()
        if not BrewSession:
            return jsonify({'error': 'Modelo não disponível'}), 500
        
        session = BrewSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        session_dict = session.to_dict()
        events = session_dict.get('session_data', {}).get('events', [])
        
        return jsonify({'events': events}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/sessions/<session_id>/telemetry', methods=['GET'])
@login_required
def get_session_telemetry(session_id):
    """Obtém telemetria da sessão (polling)."""
    try:
        BrewSession = get_brew_session()
        if not BrewSession:
            return jsonify({'error': 'Modelo não disponível'}), 500
        
        session = BrewSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        
        session_dict = session.to_dict()
        telemetry = session_dict.get('session_data', {}).get('telemetry', [])
        
        # Obter valores atuais dos dispositivos
        equipment_used = session_dict.get('equipment_used', [])
        device_integration = DeviceIntegrationService()
        
        current_values = {}
        if device_integration.is_available():
            for device_id in equipment_used:
                ports = device_integration.get_all_ports(device_id)
                current_values[device_id] = ports
        
        return jsonify({
            'telemetry': telemetry[-100:],  # Últimos 100 registros
            'current_values': current_values
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============== ROTAS DE PLANTS ==============

@mash_bp.route('/plants', methods=['GET'])
@login_required
def list_plants():
    """Lista todas as plants do usuário."""
    try:
        plant_service = get_plant_service()
        user_id = current_user.id if current_user.is_authenticated else None
        
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        plants = plant_service.list_plants(user_id=user_id, is_active=is_active)
        
        return jsonify(plants), 200
    except Exception as e:
        logger.error(f"Erro ao listar plants: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/plants', methods=['POST'])
@login_required
def create_plant():
    """Cria uma nova plant."""
    try:
        data = request.get_json()
        if not data or not data.get('name'):
            return jsonify({'error': 'Nome da plant é obrigatório'}), 400
        
        plant_service = get_plant_service()
        user_id = current_user.id if current_user.is_authenticated else None
        
        plant = plant_service.create_plant(
            name=data.get('name'),
            description=data.get('description', ''),
            device_roles=data.get('device_roles', {}),
            user_id=user_id
        )
        
        if not plant:
            return jsonify({'error': 'Erro ao criar plant'}), 500
        
        logger.info(f"Plant criada: {plant.get('id')} por usuário {user_id}")
        return jsonify(plant), 201
    except Exception as e:
        logger.error(f"Erro ao criar plant: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/plants/<plant_id>', methods=['GET'])
@login_required
def get_plant(plant_id):
    """Obtém detalhes de uma plant."""
    try:
        plant_service = get_plant_service()
        plant = plant_service.get_plant(plant_id)
        
        if not plant:
            return jsonify({'error': 'Plant não encontrada'}), 404
        
        return jsonify(plant), 200
    except Exception as e:
        logger.error(f"Erro ao obter plant: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/plants/<plant_id>', methods=['PUT'])
@login_required
def update_plant(plant_id):
    """Atualiza uma plant."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        plant_service = get_plant_service()
        
        # Verificar se plant existe
        existing = plant_service.get_plant(plant_id)
        if not existing:
            return jsonify({'error': 'Plant não encontrada'}), 404
        
        # Preparar dados de atualização
        update_data = {}
        if 'name' in data:
            update_data['name'] = data['name']
        if 'description' in data:
            update_data['description'] = data['description']
        if 'device_roles' in data:
            update_data['device_roles'] = data['device_roles']
        if 'is_active' in data:
            update_data['is_active'] = data['is_active']
        
        updated_plant = plant_service.update_plant(plant_id, **update_data)
        
        if not updated_plant:
            return jsonify({'error': 'Erro ao atualizar plant'}), 500
        
        logger.info(f"Plant atualizada: {plant_id}")
        return jsonify(updated_plant), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar plant: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/plants/<plant_id>', methods=['DELETE'])
@login_required
def delete_plant(plant_id):
    """Deleta uma plant."""
    try:
        plant_service = get_plant_service()
        
        # Verificar se plant existe
        existing = plant_service.get_plant(plant_id)
        if not existing:
            return jsonify({'error': 'Plant não encontrada'}), 404
        
        success = plant_service.delete_plant(plant_id)
        
        if not success:
            return jsonify({'error': 'Erro ao deletar plant'}), 500
        
        logger.info(f"Plant deletada: {plant_id}")
        return jsonify({'message': 'Plant deletada com sucesso'}), 200
    except Exception as e:
        logger.error(f"Erro ao deletar plant: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/plants/<plant_id>/roles', methods=['PUT'])
@login_required
def update_plant_roles(plant_id):
    """Atualiza os mapeamentos de dispositivos (roles) de uma plant."""
    try:
        data = request.get_json()
        if not data or 'device_roles' not in data:
            return jsonify({'error': 'device_roles é obrigatório'}), 400
        
        plant_service = get_plant_service()
        
        # Verificar se plant existe
        existing = plant_service.get_plant(plant_id)
        if not existing:
            return jsonify({'error': 'Plant não encontrada'}), 404
        
        updated_plant = plant_service.update_plant(plant_id, device_roles=data['device_roles'])
        
        if not updated_plant:
            return jsonify({'error': 'Erro ao atualizar roles'}), 500
        
        logger.info(f"Roles da plant atualizados: {plant_id}")
        return jsonify(updated_plant), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar roles: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/plants/<plant_id>/actors', methods=['GET'])
@login_required
def get_plant_actors(plant_id):
    """
    Retorna os dispositivos resolvidos de uma Plant com detalhes de status.

    Para cada role configurada na Plant, busca as informações do dispositivo
    via DeviceIntegrationService (portas, status, etc).
    """
    try:
        plant_service = get_plant_service()
        plant = plant_service.get_plant(plant_id)
        if not plant:
            return jsonify({'error': 'Plant não encontrada'}), 404

        device_roles = plant.get('device_roles', {}) or {}
        device_integration = DeviceIntegrationService()
        resolved = {}

        for role, device_id in device_roles.items():
            info = {'device_id': device_id, 'status': None, 'ports': {}}
            if device_integration.is_available():
                info['status'] = device_integration.get_device_status(device_id)
                info['ports'] = device_integration.get_all_ports(device_id)
            resolved[role] = info

        return jsonify({
            'plant_id': plant_id,
            'plant_name': plant.get('name'),
            'actors': resolved
        }), 200
    except Exception as e:
        logger.error(f"Erro ao obter actors da plant {plant_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ROTAS DE RECEITAS (Recipes)
# ============================================================================

@mash_bp.route('/recipes', methods=['GET'])
@login_required
def list_recipes():
    """Lista receitas do usuário."""
    try:
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        user_id = current_user.id if current_user.is_authenticated else None
        
        recipe_service = get_recipe_service()
        recipes = recipe_service.list_recipes(user_id=user_id, is_active=is_active)
        
        logger.info(f"Listadas {len(recipes)} receitas para usuário {user_id}")
        return jsonify(recipes), 200
    except Exception as e:
        logger.error(f"Erro ao listar receitas: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/recipes', methods=['POST'])
@login_required
def create_recipe():
    """Cria uma nova receita."""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Nome da receita é obrigatório'}), 400
        
        user_id = current_user.id if current_user.is_authenticated else None
        recipe_service = get_recipe_service()
        
        # Extrair dados do request
        recipe = recipe_service.create_recipe(
            name=data['name'],
            description=data.get('description', ''),
            style=data.get('style', ''),
            original_gravity=int(data.get('original_gravity', 50)),
            final_gravity=int(data.get('final_gravity', 10)),
            ibu=int(data.get('ibu', 0)),
            volume=int(data.get('volume', 20)),
            boil_time=int(data.get('boil_time', 60)),
            ingredients=data.get('ingredients', {}),
            mash_steps=data.get('mash_steps', []),
            boil_additions=data.get('boil_additions', []),
            plant_id=data.get('plant_id'),
            user_id=user_id
        )
        
        if not recipe:
            return jsonify({'error': 'Erro ao criar receita'}), 500
        
        logger.info(f"Receita criada: {recipe['id']} - {recipe['name']}")
        return jsonify(recipe), 201
    except Exception as e:
        logger.error(f"Erro ao criar receita: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/recipes/<recipe_id>', methods=['GET'])
@login_required
def get_recipe(recipe_id):
    """Obtém uma receita pelo ID."""
    try:
        recipe_service = get_recipe_service()
        recipe = recipe_service.get_recipe(recipe_id)
        
        if not recipe:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        return jsonify(recipe), 200
    except Exception as e:
        logger.error(f"Erro ao obter receita {recipe_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/recipes/<recipe_id>', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Atualiza uma receita."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        recipe_service = get_recipe_service()
        
        # Verificar se receita existe
        existing = recipe_service.get_recipe(recipe_id)
        if not existing:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        # Preparar dados para atualização
        update_data = {}
        simple_fields = ['name', 'description', 'style', 'original_gravity', 
                        'final_gravity', 'ibu', 'volume', 'boil_time', 'plant_id', 'is_active']
        complex_fields = ['ingredients', 'mash_steps', 'boil_additions']
        
        for field in simple_fields:
            if field in data:
                if field in ['original_gravity', 'final_gravity', 'ibu', 'volume', 'boil_time']:
                    update_data[field] = int(data[field])
                else:
                    update_data[field] = data[field]
        
        for field in complex_fields:
            if field in data:
                update_data[field] = data[field]
        
        updated_recipe = recipe_service.update_recipe(recipe_id, **update_data)
        
        if not updated_recipe:
            return jsonify({'error': 'Erro ao atualizar receita'}), 500
        
        logger.info(f"Receita atualizada: {recipe_id}")
        return jsonify(updated_recipe), 200
    except Exception as e:
        logger.error(f"Erro ao atualizar receita: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/recipes/<recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """Deleta uma receita."""
    try:
        recipe_service = get_recipe_service()
        
        # Verificar se receita existe
        existing = recipe_service.get_recipe(recipe_id)
        if not existing:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        success = recipe_service.delete_recipe(recipe_id)
        
        if not success:
            return jsonify({'error': 'Erro ao deletar receita'}), 500
        
        logger.info(f"Receita deletada: {recipe_id}")
        return jsonify({'message': 'Receita deletada com sucesso'}), 200
    except Exception as e:
        logger.error(f"Erro ao deletar receita: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/recipes/<recipe_id>/clone', methods=['POST'])
@login_required
def clone_recipe(recipe_id):
    """Clona uma receita com novo nome."""
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Nome da nova receita é obrigatório'}), 400
        
        user_id = current_user.id if current_user.is_authenticated else None
        recipe_service = get_recipe_service()
        
        cloned = recipe_service.clone_recipe(recipe_id, data['name'], user_id=user_id)
        
        if not cloned:
            return jsonify({'error': 'Erro ao clonar receita ou receita não encontrada'}), 500
        
        logger.info(f"Receita clonada: {recipe_id} -> {cloned['id']}")
        return jsonify(cloned), 201
    except Exception as e:
        logger.error(f"Erro ao clonar receita: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ROTAS DO DASHBOARD DE MOSTURA (Mash Session Dashboard)
# ============================================================================
# Estas rotas expõem o estado ao vivo de sessões de mostura gerenciadas
# pelo MashSessionService (com MashExecutor) para consumo do frontend.

@mash_bp.route('/mash-dashboard/start', methods=['POST'])
@login_required
def api_mash_dashboard_start():
    """Inicia uma nova sessão de mostura para o dashboard."""
    try:
        data = request.get_json()
        recipe_id = data.get('recipe_id')
        plant_id = data.get('plant_id')
        equipment_mapping = data.get('equipment_mapping', {})
        session_name = data.get('name')

        if not recipe_id:
            return jsonify({'error': 'recipe_id é obrigatório'}), 400

        # Se plant_id foi fornecido mas equipment_mapping vazio, resolver da planta
        if plant_id and not equipment_mapping:
            plant_svc = PlantService()
            plant = plant_svc.get_plant(plant_id)
            if plant:
                equipment_mapping = plant.get('device_roles', {})

        session_service = get_mash_session_service()
        user_id = current_user.id if current_user.is_authenticated else None

        session_id = session_service.start_session(
            recipe_id=recipe_id,
            plant_id=plant_id,
            session_name=session_name,
            equipment_mapping=equipment_mapping,
            user_id=user_id
        )

        if session_id:
            return jsonify({'session_id': session_id, 'message': 'Mostura iniciada'}), 201
        return jsonify({'error': 'Erro ao iniciar mostura'}), 500
    except Exception as e:
        logger.error(f"Erro ao iniciar mostura: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/mash-dashboard/<session_id>/status', methods=['GET'])
@login_required
def api_mash_dashboard_status(session_id):
    """Retorna o estado completo da sessão de mostura para o dashboard."""
    try:
        session_service = get_mash_session_service()
        status = session_service.get_session_status(session_id)
        if not status:
            return jsonify({'error': 'Sessão não encontrada'}), 404
        return jsonify(status), 200
    except Exception as e:
        logger.error(f"Erro ao obter status da mostura: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/mash-dashboard/<session_id>/control', methods=['POST'])
@login_required
def api_mash_dashboard_control(session_id):
    """
    Controla a sessão de mostura: pause, resume, stop, advance.

    Body: { "action": "pause" | "resume" | "stop" | "advance" }
    """
    try:
        data = request.get_json()
        action = data.get('action') if data else None

        if not action:
            return jsonify({'error': 'action é obrigatório (pause/resume/stop/advance)'}), 400

        session_service = get_mash_session_service()
        result = False

        if action == 'pause':
            result = session_service.pause_session(session_id)
        elif action == 'resume':
            result = session_service.resume_session(session_id)
        elif action == 'stop':
            result = session_service.stop_session(session_id)
        elif action == 'advance':
            result = session_service.advance_step(session_id)
        else:
            return jsonify({'error': f'Ação desconhecida: {action}'}), 400

        if result:
            return jsonify({'message': f'Sessão {action}ada'}), 200
        return jsonify({'error': 'Sessão não encontrada ou não disponível'}), 404
    except Exception as e:
        logger.error(f"Erro ao controlar sessão {session_id}: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/mash-dashboard/active', methods=['GET'])
@login_required
def api_mash_dashboard_active():
    """Lista todas as sessões de mostura ativas em memória."""
    try:
        session_service = get_mash_session_service()
        sessions = session_service.get_active_sessions()
        return jsonify({'sessions': sessions}), 200
    except Exception as e:
        logger.error(f"Erro ao listar sessões ativas: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/mash-dashboard/recent', methods=['GET'])
@login_required
def api_mash_dashboard_recent():
    """Lista sessões recentes do banco de dados."""
    try:
        session_service = get_mash_session_service()
        sessions = session_service.list_recent_sessions()
        return jsonify({'sessions': sessions}), 200
    except Exception as e:
        logger.error(f"Erro ao listar sessões recentes: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/mash-dashboard/recipes-with-steps', methods=['GET'])
@login_required
def api_mash_dashboard_recipes():
    """Lista receitas que possuem etapas de mostura, prontas para execução."""
    try:
        from plugins.plugin_mash_control.utils.model_loader import get_recipe
        RecipeModel = get_recipe()
        if not RecipeModel:
            return jsonify({'recipes': []}), 200

        recipes = RecipeModel.query.filter_by(is_active=True).all()
        result = []
        for r in recipes:
            mash_steps = []
            if r.mash_steps:
                try:
                    mash_steps = json.loads(r.mash_steps) if isinstance(r.mash_steps, str) else r.mash_steps
                except (json.JSONDecodeError, TypeError):
                    pass
            if mash_steps:
                result.append({
                    'id': r.id,
                    'name': r.name,
                    'style': r.style,
                    'step_count': len(mash_steps),
                    'volume': r.volume,
                    'original_gravity': r.original_gravity,
                    'ibu': r.ibu
                })

        return jsonify({'recipes': result}), 200
    except Exception as e:
        logger.error(f"Erro ao listar receitas para mostura: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@mash_bp.route('/mash-dashboard/plants', methods=['GET'])
@login_required
def api_mash_dashboard_plants():
    """Lista plantas disponíveis para seleção no dashboard de mostura."""
    try:
        plant_svc = PlantService()
        user_id = current_user.id if current_user.is_authenticated else None
        plants = plant_svc.list_plants(user_id=user_id)
        result = []
        for p in plants:
            device_roles = p.get('device_roles', {})
            result.append({
                'id': p.get('id'),
                'name': p.get('name'),
                'description': p.get('description'),
                'device_count': len(device_roles),
                'device_roles': device_roles
            })
        return jsonify({'plants': result}), 200
    except Exception as e:
        logger.error(f"Erro ao listar plantas: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

