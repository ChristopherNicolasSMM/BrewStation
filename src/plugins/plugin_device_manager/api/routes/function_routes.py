"""
Rotas API para gerenciamento de funções de dispositivos.
"""

import logging

from flask import Blueprint, jsonify, request
from flask_login import login_required

from db.database import db

logger = logging.getLogger(__name__)

# Usar model_loader para garantir modelos prefixados
from plugins.plugin_device_manager.utils.model_loader import \
    get_device_function

function_bp = Blueprint('plugin_device_manager_function_api', __name__)


@function_bp.route('/functions', methods=['GET'])
@login_required
def list_functions():
    """Lista todas as funções (pré-definidas + customizadas)."""
    try:
        DeviceFunction = get_device_function()
        if not DeviceFunction:
            return jsonify({'error': 'Modelo DeviceFunction não disponível'}), 500
        
        # Filtros opcionais
        category = request.args.get('category')
        is_predefined = request.args.get('is_predefined')
        search = request.args.get('search')
        
        query = DeviceFunction.query
        
        if category:
            query = query.filter(DeviceFunction.category == category)
        
        if is_predefined is not None:
            is_predefined_bool = is_predefined.lower() == 'true'
            query = query.filter(DeviceFunction.is_predefined == is_predefined_bool)
        
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                (DeviceFunction.name.ilike(search_term)) |
                (DeviceFunction.display_name.ilike(search_term)) |
                (DeviceFunction.description.ilike(search_term))
            )
        
        functions = query.order_by(DeviceFunction.is_predefined.desc(), DeviceFunction.display_name).all()
        
        return jsonify({
            'success': True,
            'functions': [f.to_dict() for f in functions],
            'total': len(functions)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar funções: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@function_bp.route('/functions/predefined', methods=['GET'])
@login_required
def list_predefined():
    """Lista apenas funções pré-definidas."""
    try:
        DeviceFunction = get_device_function()
        if not DeviceFunction:
            return jsonify({'error': 'Modelo DeviceFunction não disponível'}), 500
        
        functions = DeviceFunction.query.filter_by(is_predefined=True).order_by(DeviceFunction.display_name).all()
        
        return jsonify({
            'success': True,
            'functions': [f.to_dict() for f in functions],
            'total': len(functions)
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao listar funções pré-definidas: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@function_bp.route('/functions/<int:function_id>', methods=['GET'])
@login_required
def get_function(function_id):
    """Obtém uma função específica."""
    try:
        DeviceFunction = get_device_function()
        if not DeviceFunction:
            return jsonify({'error': 'Modelo DeviceFunction não disponível'}), 500
        
        function = DeviceFunction.query.get(function_id)
        if not function:
            return jsonify({'error': 'Função não encontrada'}), 404
        
        return jsonify({
            'success': True,
            'function': function.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao obter função {function_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@function_bp.route('/functions', methods=['POST'])
@login_required
def create_function():
    """Cria nova função customizada."""
    try:
        DeviceFunction = get_device_function()
        if not DeviceFunction:
            return jsonify({'error': 'Modelo DeviceFunction não disponível'}), 500
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Validar campos obrigatórios
        required_fields = ['name', 'display_name', 'category', 'data_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório faltando: {field}'}), 400
        
        # Verificar se nome já existe
        existing = DeviceFunction.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'error': f'Função com nome "{data["name"]}" já existe'}), 400
        
        # Criar função (sempre customizada via API)
        function = DeviceFunction(
            name=data['name'],
            display_name=data['display_name'],
            description=data.get('description'),
            category=data['category'],
            unit=data.get('unit'),
            data_type=data['data_type'],
            min_value=data.get('min_value'),
            max_value=data.get('max_value'),
            is_predefined=False,  # Funções criadas via API são sempre customizadas
            icon=data.get('icon', 'bi bi-circle')
        )
        
        db.session.add(function)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'function': function.to_dict(),
            'message': 'Função criada com sucesso'
        }), 201
        
    except Exception as e:
        logger.error(f"Erro ao criar função: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@function_bp.route('/functions/<int:function_id>', methods=['PUT'])
@login_required
def update_function(function_id):
    """Atualiza função (apenas customizadas)."""
    try:
        DeviceFunction = get_device_function()
        if not DeviceFunction:
            return jsonify({'error': 'Modelo DeviceFunction não disponível'}), 500
        
        function = DeviceFunction.query.get(function_id)
        if not function:
            return jsonify({'error': 'Função não encontrada'}), 404
        
        # Não permitir editar funções pré-definidas
        if function.is_predefined:
            return jsonify({'error': 'Não é possível editar funções pré-definidas'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Dados não fornecidos'}), 400
        
        # Atualizar campos permitidos
        updatable_fields = ['display_name', 'description', 'category', 'unit', 
                          'data_type', 'min_value', 'max_value', 'icon']
        
        for field in updatable_fields:
            if field in data:
                setattr(function, field, data[field])
        
        # Não permitir alterar nome (único)
        # Não permitir alterar is_predefined
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'function': function.to_dict(),
            'message': 'Função atualizada com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao atualizar função {function_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@function_bp.route('/functions/<int:function_id>', methods=['DELETE'])
@login_required
def delete_function(function_id):
    """Remove função (apenas customizadas)."""
    try:
        DeviceFunction = get_device_function()
        if not DeviceFunction:
            return jsonify({'error': 'Modelo DeviceFunction não disponível'}), 500
        
        function = DeviceFunction.query.get(function_id)
        if not function:
            return jsonify({'error': 'Função não encontrada'}), 404
        
        # Não permitir deletar funções pré-definidas
        if function.is_predefined:
            return jsonify({'error': 'Não é possível deletar funções pré-definidas'}), 403
        
        # Verificar se função está sendo usada por atores
        from plugins.plugin_device_manager.utils.model_loader import \
            get_device_actor
        DeviceActor = get_device_actor()
        if DeviceActor:
            actors_count = DeviceActor.query.filter_by(function_id=function_id).count()
            if actors_count > 0:
                return jsonify({
                    'error': f'Não é possível deletar função que está sendo usada por {actors_count} ator(es)'
                }), 400
        
        db.session.delete(function)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Função removida com sucesso'
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao deletar função {function_id}: {e}", exc_info=True)
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
