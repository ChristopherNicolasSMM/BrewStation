# routes/receitas_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from model.ingredientes import Receita, IngredienteReceita
from db.database import db

receitas_bp = Blueprint('receitas', __name__)

@receitas_bp.route('/receitas', methods=['GET'])
@login_required
def get_receitas():
    """Obter lista de receitas"""
    receitas = Receita.query.filter_by(ativo=True).all()
    return jsonify([receita.to_dict() for receita in receitas]), 200

@receitas_bp.route('/receitas', methods=['POST'])
@login_required
def create_receita():
    """Criar nova receita"""
    data = request.get_json()
    
    receita = Receita(
        nome=data['nome'],
        descricao=data.get('descricao', ''),
        volume_litros=data['volume_litros'],
        eficiencia=data.get('eficiencia', 75.0)
    )
    
    db.session.add(receita)
    db.session.commit()
    
    return jsonify({'message': 'Receita criada com sucesso', 'receita': receita.to_dict()}), 201

@receitas_bp.route('/receitas/<int:receita_id>', methods=['PUT'])
@login_required
def update_receita(receita_id):
    """Atualizar dados da receita"""
    receita = Receita.query.get_or_404(receita_id)
    data = request.get_json()
    for key in ['nome', 'descricao', 'volume_litros', 'eficiencia', 'ativo']:
        if key in data:
            setattr(receita, key, data[key])
    db.session.commit()
    return jsonify({'message': 'Receita atualizada com sucesso', 'receita': receita.to_dict()}), 200

@receitas_bp.route('/receitas/<int:receita_id>/ingredientes', methods=['POST'])
@login_required
def add_ingrediente_receita(receita_id):
    """Adicionar ingrediente à receita"""
    data = request.get_json()
    
    ingrediente = IngredienteReceita(
        receita_id=receita_id,
        tipo_ingrediente=data['tipo_ingrediente'],
        ingrediente_id=data['ingrediente_id'],
        quantidade=data['quantidade'],
        tempo_adicao=data.get('tempo_adicao'),
        observacoes=data.get('observacoes', '')
    )
    
    db.session.add(ingrediente)
    db.session.commit()
    
    return jsonify({'message': 'Ingrediente adicionado com sucesso', 'ingrediente': ingrediente.to_dict()}), 201

@receitas_bp.route('/receitas/<int:receita_id>/ingredientes', methods=['GET'])
@login_required
def list_ingredientes_receita(receita_id):
    """Listar ingredientes de uma receita"""
    itens = IngredienteReceita.query.filter_by(receita_id=receita_id).all()
    return jsonify([i.to_dict() for i in itens]), 200

@receitas_bp.route('/receitas/<int:receita_id>/ingredientes/<int:item_id>', methods=['PUT'])
@login_required
def update_ingrediente_receita(receita_id, item_id):
    """Atualizar ingrediente da receita"""
    item = IngredienteReceita.query.filter_by(id=item_id, receita_id=receita_id).first_or_404()
    data = request.get_json()
    for key in ['tipo_ingrediente', 'ingrediente_id', 'quantidade', 'tempo_adicao', 'observacoes']:
        if key in data:
            setattr(item, key, data[key])
    db.session.commit()
    return jsonify({'message': 'Ingrediente atualizado com sucesso', 'ingrediente': item.to_dict()}), 200

@receitas_bp.route('/receitas/<int:receita_id>/ingredientes/<int:item_id>', methods=['DELETE'])
@login_required
def delete_ingrediente_receita(receita_id, item_id):
    """Remover ingrediente da receita"""
    item = IngredienteReceita.query.filter_by(id=item_id, receita_id=receita_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Ingrediente removido com sucesso'}), 200