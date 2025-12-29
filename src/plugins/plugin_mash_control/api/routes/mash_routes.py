"""
Rotas API para controle de brassagem e sessões.
"""

import json
import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from pathlib import Path

from plugins.plugin_mash_control.services.device_integration import DeviceIntegrationService
from plugins.plugin_mash_control.services.process_control import ProcessControlService
from plugins.plugin_mash_control.services.dashboard_builder import DashboardBuilderService
from plugins.plugin_mash_control.utils.model_loader import get_brew_session, get_dashboard_layout

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
    """Lista dispositivos disponíveis."""
    try:
        device_integration = DeviceIntegrationService()
        if not device_integration.is_available():
            return jsonify({'error': 'device_manager não disponível'}), 500
        
        filters = {}
        if request.args.get('device_type'):
            filters['device_type'] = request.args.get('device_type')
        if request.args.get('protocol'):
            filters['protocol'] = request.args.get('protocol')
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active') == 'true'
        
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
        
        if not recipe_id:
            return jsonify({'error': 'recipe_id é obrigatório'}), 400
        
        process_control = get_process_control()
        if not process_control:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        session_id = process_control.start_session(recipe_id, equipment_mapping, session_name)
        
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

