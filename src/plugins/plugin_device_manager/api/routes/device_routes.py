"""
Rotas API para gerenciamento de dispositivos IoT.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from pathlib import Path
import json
import logging

logger = logging.getLogger(__name__)

# Usar model_loader para garantir modelos prefixados
from plugins.plugin_device_manager.utils.model_loader import get_device_metadata

device_bp = Blueprint('plugin_device_manager_api', __name__)


def get_registry():
    """Obtém instância do DeviceRegistry."""
    from plugins.plugin_device_manager.utils.device_registry import DeviceRegistry
    from flask import current_app
    
    # Obter caminho do plugin
    plugin_manager = current_app.plugin_manager
    plugin = plugin_manager.get_plugin('device_manager')
    if plugin:
        return DeviceRegistry(plugin.plugin_path)
    return None


def get_mqtt_service():
    """Obtém instância do MQTTService."""
    from flask import current_app
    
    plugin_manager = current_app.plugin_manager
    plugin = plugin_manager.get_plugin('device_manager')
    if plugin and hasattr(plugin, '_mqtt_service'):
        return plugin._mqtt_service
    return None


@device_bp.route('/devices', methods=['GET'])
@login_required
def list_devices():
    """Lista todos os dispositivos."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        # Obter filtros da query string
        filters = {}
        device_type = request.args.get('type')
        protocol = request.args.get('protocol')
        
        if device_type:
            filters['type'] = device_type
        if protocol:
            filters['protocol'] = protocol
        
        devices = registry.list_devices(filters)
        
        # Adicionar estado de cada dispositivo
        for device in devices:
            device_id = device.get('device_id')
            state = registry.get_state(device_id)
            device['state'] = state
        
        return jsonify({
            'success': True,
            'devices': devices,
            'total': len(devices)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar dispositivos: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>', methods=['GET'])
@login_required
def get_device(device_id):
    """Obtém um dispositivo específico."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        device = registry.get_device(device_id)
        if not device:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        # Adicionar estado
        state = registry.get_state(device_id)
        device['state'] = state
        
        return jsonify({
            'success': True,
            'device': device
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter dispositivo {device_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices', methods=['POST'])
@login_required
def create_device():
    """Cria um novo dispositivo."""
    try:
        registry = get_registry()
        mqtt_service = get_mqtt_service()
        
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Registrar dispositivo
        device_id = registry.register_device(data)
        
        # Salvar metadados no banco
        DeviceMetadata = get_device_metadata()
        if DeviceMetadata:
            from db.database import db
            
            config_path = f"data/devices/configs/{device_id}.json"
            state_path = f"data/devices/states/{device_id}.json"
            
            port_config_json = json.dumps(data.get('ports', {}))
            
            device_metadata = DeviceMetadata(
                id=device_id,
                name=data.get('name', 'Dispositivo sem nome'),
                device_type=data.get('type', 'sensor'),
                protocol=data.get('protocol', 'mqtt'),
                config_path=config_path,
                state_path=state_path,
                is_active=True,
                port_config=port_config_json
            )
            
            db.session.add(device_metadata)
            db.session.commit()
        
        # Conectar dispositivo ao broker MQTT se disponível
        if mqtt_service and data.get('protocol') == 'mqtt':
            device_config = registry.get_device(device_id)
            mqtt_service.connect_device(device_config)
        
        return jsonify({
            'success': True,
            'device_id': device_id,
            'message': 'Dispositivo criado com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar dispositivo: {e}", exc_info=True)
        from db.database import db
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>', methods=['PUT'])
@login_required
def update_device(device_id):
    """Atualiza um dispositivo."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Atualizar configuração
        success = registry.update_device(device_id, data)
        
        if not success:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        # Atualizar metadados no banco
        DeviceMetadata = get_device_metadata()
        if DeviceMetadata:
            from db.database import db
            
            device_metadata = DeviceMetadata.query.get(device_id)
            if device_metadata:
                if 'name' in data:
                    device_metadata.name = data['name']
                if 'type' in data:
                    device_metadata.device_type = data['type']
                if 'protocol' in data:
                    device_metadata.protocol = data['protocol']
                if 'ports' in data:
                    device_metadata.port_config = json.dumps(data['ports'])
                
                db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Dispositivo atualizado com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar dispositivo {device_id}: {e}", exc_info=True)
        from db.database import db
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>', methods=['DELETE'])
@login_required
def delete_device(device_id):
    """Remove um dispositivo."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        # Remover do banco primeiro
        DeviceMetadata = get_device_metadata()
        if DeviceMetadata:
            from db.database import db
            
            device_metadata = DeviceMetadata.query.get(device_id)
            if device_metadata:
                db.session.delete(device_metadata)
                db.session.commit()
        
        # Remover arquivos JSON
        success = registry.delete_device(device_id)
        
        if not success:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Dispositivo removido com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao remover dispositivo {device_id}: {e}", exc_info=True)
        from db.database import db
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>/state', methods=['GET'])
@login_required
def get_device_state(device_id):
    """Obtém estado atual de um dispositivo."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        state = registry.get_state(device_id)
        if not state:
            return jsonify({'error': 'Estado não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'state': state
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter estado do dispositivo {device_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>/command', methods=['POST'])
@login_required
def send_command(device_id):
    """Envia comando para um dispositivo."""
    try:
        mqtt_service = get_mqtt_service()
        registry = get_registry()
        
        if not mqtt_service:
            return jsonify({'error': 'Serviço MQTT não disponível'}), 500
        
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        data = request.get_json()
        command = data.get('command')
        payload = data.get('payload', {})
        
        if not command:
            return jsonify({'error': 'Comando não fornecido'}), 400
        
        # Obter configuração do dispositivo
        device_config = registry.get_device(device_id)
        if not device_config:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        # Enviar comando via MQTT
        topics = device_config.get('topics', {})
        command_topic = topics.get('command')
        
        if not command_topic:
            return jsonify({'error': 'Tópico de comando não configurado'}), 400
        
        message = {
            'command': command,
            'payload': payload
        }
        
        success = mqtt_service.publish(command_topic, json.dumps(message), qos=1)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Comando enviado com sucesso'
            }), 200
        else:
            return jsonify({'error': 'Falha ao enviar comando'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao enviar comando para dispositivo {device_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>/ports', methods=['GET'])
@login_required
def get_device_ports(device_id):
    """Obtém configuração de portas de um dispositivo."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        device = registry.get_device(device_id)
        if not device:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        ports = device.get('ports', {})
        
        # Adicionar valores atuais das portas
        state = registry.get_state(device_id)
        if state:
            port_states = state.get('ports', {})
            for port_name, port_config in ports.items():
                if port_name in port_states:
                    port_config['current_value'] = port_states[port_name].get('value')
                    port_config['last_update'] = port_states[port_name].get('timestamp')
        
        return jsonify({
            'success': True,
            'ports': ports
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter portas do dispositivo {device_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>/ports', methods=['POST'])
@login_required
def configure_ports(device_id):
    """Configura portas de um dispositivo."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        data = request.get_json()
        ports = data.get('ports', {})
        
        if not ports:
            return jsonify({'error': 'Configuração de portas não fornecida'}), 400
        
        # Salvar configuração de portas
        success = registry.save_port_config(device_id, ports)
        
        # Atualizar metadados no banco
        DeviceMetadata = get_device_metadata()
        if DeviceMetadata:
            from db.database import db
            
            device_metadata = DeviceMetadata.query.get(device_id)
            if device_metadata:
                device_metadata.port_config = json.dumps(ports)
                db.session.commit()
        
        if not success:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        return jsonify({
            'success': True,
            'message': 'Configuração de portas salva com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao configurar portas do dispositivo {device_id}: {e}", exc_info=True)
        from db.database import db
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/status', methods=['GET'])
@login_required
def get_mqtt_status():
    """Obtém status do servidor MQTT."""
    try:
        mqtt_service = get_mqtt_service()
        
        if not mqtt_service:
            return jsonify({
                'success': True,
                'running': False,
                'message': 'Serviço MQTT não disponível'
            }), 200
        
        return jsonify({
            'success': True,
            'running': mqtt_service.is_running,
            'message': 'Servidor MQTT rodando' if mqtt_service.is_running else 'Servidor MQTT parado'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter status do MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/config', methods=['GET'])
@login_required
def get_mqtt_config():
    """Obtém configuração do broker MQTT."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        config_path = registry.data_path / "mqtt_broker.json"
        
        if not config_path.exists():
            return jsonify({'error': 'Configuração não encontrada'}), 404
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        return jsonify({
            'success': True,
            'config': config
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter configuração do MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/config', methods=['POST'])
@login_required
def update_mqtt_config():
    """Atualiza configuração do broker MQTT."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        config_path = registry.data_path / "mqtt_broker.json"
        
        # Salvar configuração
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Reiniciar servidor MQTT se estiver rodando
        mqtt_service = get_mqtt_service()
        if mqtt_service and mqtt_service.is_running:
            mqtt_service.stop_broker()
            mqtt_service.start_broker(str(config_path))
        
        return jsonify({
            'success': True,
            'message': 'Configuração do MQTT atualizada com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar configuração do MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/subscribe', methods=['POST'])
@login_required
def mqtt_subscribe():
    """Inscreve-se em um tópico MQTT para monitoramento."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'Serviço MQTT não disponível'}), 500
        
        data = request.get_json()
        topic = data.get('topic')
        qos = data.get('qos', 1)
        
        if not topic:
            return jsonify({'error': 'Tópico não fornecido'}), 400
        
        # Inscrever no tópico (callback será chamado automaticamente pelo MQTTService)
        success = mqtt_service.subscribe(topic, qos=qos)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Inscrito no tópico: {topic}'
            }), 200
        else:
            return jsonify({'error': 'Falha ao inscrever-se no tópico'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao inscrever-se no tópico MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/unsubscribe', methods=['POST'])
@login_required
def mqtt_unsubscribe():
    """Desinscreve-se de um tópico MQTT."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'Serviço MQTT não disponível'}), 500
        
        data = request.get_json()
        topic = data.get('topic')
        
        if not topic:
            return jsonify({'error': 'Tópico não fornecido'}), 400
        
        # Desinscrever
        success = mqtt_service.unsubscribe(topic)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Desinscrito do tópico: {topic}'
            }), 200
        else:
            return jsonify({'error': 'Falha ao desinscrever-se do tópico'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao desinscrever-se do tópico MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/publish', methods=['POST'])
@login_required
def mqtt_publish():
    """Publica uma mensagem MQTT de teste."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'Serviço MQTT não disponível'}), 500
        
        data = request.get_json()
        topic = data.get('topic')
        payload = data.get('payload', '')
        qos = data.get('qos', 1)
        retain = data.get('retain', False)
        
        if not topic:
            return jsonify({'error': 'Tópico não fornecido'}), 400
        
        # Publicar mensagem
        success = mqtt_service.publish(topic, payload, qos=qos, retain=retain)
        
        if success:
            logger.info(f"Mensagem publicada no tópico {topic}: {payload}")
            return jsonify({
                'success': True,
                'message': 'Mensagem publicada com sucesso'
            }), 200
        else:
            return jsonify({'error': 'Falha ao publicar mensagem'}), 500
        
    except Exception as e:
        logger.error(f"Erro ao publicar mensagem MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/subscriptions', methods=['GET'])
@login_required
def get_mqtt_subscriptions():
    """Obtém lista de tópicos inscritos."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'Serviço MQTT não disponível'}), 500
        
        subscriptions = mqtt_service.get_subscriptions()
        
        return jsonify({
            'success': True,
            'subscriptions': subscriptions
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter subscriptions MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/mqtt/messages', methods=['GET'])
@login_required
def get_mqtt_messages():
    """Obtém histórico de mensagens MQTT."""
    try:
        mqtt_service = get_mqtt_service()
        if not mqtt_service:
            return jsonify({'error': 'Serviço MQTT não disponível'}), 500
        
        limit = request.args.get('limit', 100, type=int)
        messages = mqtt_service.get_message_history(limit=limit)
        
        return jsonify({
            'success': True,
            'messages': messages,
            'total': len(messages)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter mensagens MQTT: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/<device_id>/ports/all', methods=['GET'])
@login_required
def get_all_device_ports(device_id):
    """Obtém todas as portas e seus valores de um dispositivo."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        device = registry.get_device(device_id)
        if not device:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        state = registry.get_state(device_id)
        ports_config = device.get('ports', {})
        ports_state = state.get('ports', {}) if state else {}
        
        # Combinar configuração e estado das portas
        all_ports = {}
        for port_name, port_config in ports_config.items():
            port_state = ports_state.get(port_name, {})
            all_ports[port_name] = {
                **port_config,
                'current_value': port_state.get('value'),
                'last_update': port_state.get('timestamp'),
                'status': 'active' if port_state.get('value') is not None else 'inactive'
            }
        
        return jsonify({
            'success': True,
            'ports': all_ports,
            'total': len(all_ports)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter portas do dispositivo {device_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@device_bp.route('/devices/by-port-type/<port_type>', methods=['GET'])
@login_required
def get_devices_by_port_type(port_type):
    """Lista dispositivos que possuem portas de um tipo específico."""
    try:
        registry = get_registry()
        if not registry:
            return jsonify({'error': 'Registry não disponível'}), 500
        
        devices = registry.list_devices()
        
        # Filtrar dispositivos que têm pelo menos uma porta do tipo especificado
        filtered_devices = []
        for device in devices:
            ports = device.get('ports', {})
            for port_name, port_config in ports.items():
                if port_config.get('type') == port_type:
                    filtered_devices.append(device)
                    break
        
        return jsonify({
            'success': True,
            'devices': filtered_devices,
            'total': len(filtered_devices),
            'port_type': port_type
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar dispositivos por tipo de porta: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500

