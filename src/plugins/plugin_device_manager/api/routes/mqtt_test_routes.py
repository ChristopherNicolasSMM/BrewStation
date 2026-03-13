"""
Rotas API para testes do broker MQTT.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required
import json
import logging

logger = logging.getLogger(__name__)

mqtt_test_bp = Blueprint('plugin_device_manager_mqtt_test_api', __name__)


def get_mqtt_service():
    """Obtém instância do MQTTService."""
    from flask import current_app
    
    plugin_manager = current_app.plugin_manager
    plugin = plugin_manager.get_plugin('device_manager')
    if plugin and hasattr(plugin, '_mqtt_service'):
        return plugin._mqtt_service
    return None


@mqtt_test_bp.route('/mqtt/test/publish', methods=['POST'])
@login_required
def test_publish():
    """Publica mensagem de teste no broker MQTT."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'MQTTService não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        topic = data.get('topic')
        payload = data.get('payload')
        qos = data.get('qos', 1)
        retain = data.get('retain', False)
        
        if not topic or payload is None:
            return jsonify({'error': 'topic e payload são obrigatórios'}), 400
        
        # Converter payload para string se necessário
        if not isinstance(payload, str):
            payload = json.dumps(payload) if payload else ''
        
        # Publicar mensagem
        success = mqtt_service.publish(topic, payload, qos=qos, retain=retain)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Mensagem publicada com sucesso',
                'topic': topic,
                'payload': payload
            }), 200
        else:
            return jsonify({'error': 'Erro ao publicar mensagem'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao publicar mensagem de teste: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@mqtt_test_bp.route('/mqtt/test/subscribe', methods=['POST'])
@login_required
def test_subscribe():
    """Inscreve em tópico para teste."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'MQTTService não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        topic = data.get('topic')
        qos = data.get('qos', 1)
        
        if not topic:
            return jsonify({'error': 'topic é obrigatório'}), 400
        
        # Inscrever no tópico
        success = mqtt_service.subscribe(topic, callback=None, qos=qos)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Inscrito no tópico {topic}',
                'topic': topic,
                'qos': qos
            }), 200
        else:
            return jsonify({'error': 'Erro ao inscrever no tópico'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao inscrever no tópico: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@mqtt_test_bp.route('/mqtt/test/history', methods=['GET'])
@login_required
def test_history():
    """Retorna histórico de mensagens MQTT."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'MQTTService não disponível'}), 500
        
        # Parâmetros opcionais
        limit = request.args.get('limit', 100, type=int)
        topic = request.args.get('topic')  # Filtrar por tópico
        
        # Obter histórico
        history = mqtt_service.get_message_history(limit=limit)
        
        # Filtrar por tópico se especificado
        if topic:
            history = [msg for msg in history if topic in msg.get('topic', '')]
        
        return jsonify({
            'success': True,
            'messages': history,
            'total': len(history),
            'limit': limit
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@mqtt_test_bp.route('/mqtt/broker/status', methods=['GET'])
@login_required
def broker_status():
    """Status do broker MQTT."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({
                'success': True,
                'status': 'not_available',
                'message': 'MQTTService não disponível'
            }), 200
        
        # Obter status
        is_running = mqtt_service.is_running if hasattr(mqtt_service, 'is_running') else False
        subscriptions = mqtt_service.get_subscriptions() if hasattr(mqtt_service, 'get_subscriptions') else {}
        
        status_data = {
            'success': True,
            'status': 'running' if is_running else 'stopped',
            'is_running': is_running,
            'subscriptions_count': len(subscriptions),
            'subscriptions': list(subscriptions.keys()) if subscriptions else []
        }
        
        # Adicionar configuração se disponível
        if hasattr(mqtt_service, '_config') and mqtt_service._config:
            config = mqtt_service._config.copy()
            # Remover senha se existir
            if 'authentication' in config and 'password' in config['authentication']:
                config['authentication']['password'] = '***'
            status_data['config'] = config
        
        return jsonify(status_data), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter status do broker: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@mqtt_test_bp.route('/mqtt/test/unsubscribe', methods=['POST'])
@login_required
def test_unsubscribe():
    """Desinscreve de tópico."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'MQTTService não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        topic = data.get('topic')
        
        if not topic:
            return jsonify({'error': 'topic é obrigatório'}), 400
        
        # Desinscrever do tópico
        success = mqtt_service.unsubscribe(topic) if hasattr(mqtt_service, 'unsubscribe') else False
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Desinscrito do tópico {topic}',
                'topic': topic
            }), 200
        else:
            return jsonify({'error': 'Erro ao desinscrever do tópico'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao desinscrever do tópico: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500
