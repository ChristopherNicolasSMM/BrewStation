# routes/ingredientes_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from model.ingredientes import Malte, Lupulo, Levedura
from db.database import db
    

ingredientes_bp = Blueprint('ingredientes', __name__)

# ================================ ROTAS PARA MALTES ===================================
@ingredientes_bp.route('/maltes', methods=['GET'])
@login_required
def get_maltes():
    """Obter lista de maltes"""
    maltes = Malte.query.filter_by(ativo=True).all()
    return jsonify([malte.to_dict() for malte in maltes]), 200

@ingredientes_bp.route('/maltes/<int:malte_id>', methods=['GET'])
@login_required
def get_malte_id(malte_id):
    """Obter malte específico por ID"""
    try:
        malte = Malte.query.get(malte_id)
        if not malte:
            return jsonify({'error': 'Malte não encontrado'}), 404
        return jsonify(malte.to_dict()), 200
    except Exception as e:
        print(f"Erro ao buscar malte {malte_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ingredientes_bp.route('/maltes', methods=['POST'])
@login_required
def create_malte():
    """Criar novo malte"""
    data = request.get_json()
    
    malte = Malte(
        nome=data['nome'],
        fabricante=data['fabricante'],
        cor_ebc=data['cor_ebc'],
        poder_diastatico=data['poder_diastatico'],
        rendimento=data['rendimento'],
        preco_kg=data['preco_kg'],
        tipo=data['tipo']
    )
    
    db.session.add(malte)
    db.session.commit()
    
    return jsonify({'message': 'Malte criado com sucesso', 'malte': malte.to_dict()}), 201

@ingredientes_bp.route('/maltes/<int:malte_id>', methods=['PUT'])
@login_required
def update_malte(malte_id):
    """Atualizar malte"""
    malte = Malte.query.get_or_404(malte_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(malte, key):
            setattr(malte, key, value)
    
    db.session.commit()
    
    return jsonify({'message': 'Malte atualizado com sucesso', 'malte': malte.to_dict()}), 200

@ingredientes_bp.route('/maltes/<int:malte_id>', methods=['DELETE'])
@login_required
def delete_malte(malte_id):
    """Deletar malte (soft delete)"""
    malte = Malte.query.get_or_404(malte_id)
    malte.ativo = False
    db.session.commit()
    
    return jsonify({'message': 'Malte deletado com sucesso'}), 200

# ================================ ROTAS PARA LÚPULOS ==================================
@ingredientes_bp.route('/lupulos', methods=['GET'])
@login_required
def get_lupulos():
    """Obter lista de lúpulos"""
    lupulos = Lupulo.query.filter_by(ativo=True).all()
    return jsonify([lupulo.to_dict() for lupulo in lupulos]), 200

@ingredientes_bp.route('/lupulos/<int:lupulo_id>', methods=['GET'])
@login_required
def get_lupulo_id(lupulo_id):
    """Obter lupulo específico por ID"""
    try:
        lupulo = Lupulo.query.get(lupulo_id)
        if not lupulo:
            return jsonify({'error': 'lupulo não encontrado'}), 404
        return jsonify(lupulo.to_dict()), 200
    except Exception as e:
        print(f"Erro ao buscar lupulo {lupulo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ingredientes_bp.route('/lupulos', methods=['POST'])
@login_required
def create_lupulo():
    """Criar novo lúpulo"""
    data = request.get_json()
    
    lupulo = Lupulo(
        nome=data['nome'],
        fabricante=data['fabricante'],
        alpha_acidos=data['alpha_acidos'],
        beta_acidos=data['beta_acidos'],
        formato=data['formato'],
        origem=data['origem'],
        preco_kg=data['preco_kg'],
        aroma=data.get('aroma', '')
    )
    
    db.session.add(lupulo)
    db.session.commit()
    
    return jsonify({'message': 'Lúpulo criado com sucesso', 'lupulo': lupulo.to_dict()}), 201

@ingredientes_bp.route('/lupulos/<int:lupulo_id>', methods=['PUT'])
@login_required
def update_lupulo(lupulo_id):
    """Atualizar lúpulo"""
    lupulo = Lupulo.query.get_or_404(lupulo_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(lupulo, key):
            setattr(lupulo, key, value)
    
    db.session.commit()
    
    return jsonify({'message': 'Lúpulo atualizado com sucesso', 'lupulo': lupulo.to_dict()}), 200

@ingredientes_bp.route('/lupulos/<int:lupulo_id>', methods=['DELETE'])
@login_required
def delete_lupulo(lupulo_id):
    """Deletar lúpulo (soft delete)"""
    lupulo = Lupulo.query.get_or_404(lupulo_id)
    lupulo.ativo = False
    db.session.commit()
    
    return jsonify({'message': 'Lúpulo deletado com sucesso'}), 200

# ================================ ROTAS PARA LEVEDURAS ================================
@ingredientes_bp.route('/leveduras', methods=['GET'])
@login_required
def get_leveduras():
    """Obter lista de leveduras"""
    leveduras = Levedura.query.filter_by(ativo=True).all()
    return jsonify([levedura.to_dict() for levedura in leveduras]), 200

@ingredientes_bp.route('/leveduras/<int:levedura_id>', methods=['GET'])
@login_required
def get_levedura_id(levedura_id):
    """Obter levedura específico por ID"""
    try:
        levedura = Levedura.query.get(levedura_id)
        if not levedura:
            return jsonify({'error': 'levedura não encontrado'}), 404
        return jsonify(levedura.to_dict()), 200
    except Exception as e:
        print(f"Erro ao buscar levedura {levedura_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@ingredientes_bp.route('/leveduras', methods=['POST'])
@login_required
def create_levedura():
    """Criar nova levedura"""
    data = request.get_json()
    
    levedura = Levedura(
        nome=data['nome'],
        fabricante=data['fabricante'],
        formato=data['formato'],
        atenuacao=data['atenuacao'],
        temp_fermentacao=data['temp_fermentacao'],
        preco_unidade=data['preco_unidade'],
        floculacao=data['floculacao']
    )
    
    db.session.add(levedura)
    db.session.commit()
    
    return jsonify({'message': 'Levedura criada com sucesso', 'levedura': levedura.to_dict()}), 201

@ingredientes_bp.route('/leveduras/<int:levedura_id>', methods=['PUT'])
@login_required
def update_levedura(levedura_id):
    """Atualizar levedura"""
    levedura = Levedura.query.get_or_404(levedura_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(levedura, key):
            setattr(levedura, key, value)
    
    db.session.commit()
    
    return jsonify({'message': 'Levedura atualizada com sucesso', 'levedura': levedura.to_dict()}), 200

@ingredientes_bp.route('/leveduras/<int:levedura_id>', methods=['DELETE'])
@login_required
def delete_levedura(levedura_id):
    """Deletar levedura (soft delete)"""
    levedura = Levedura.query.get_or_404(levedura_id)
    levedura.ativo = False
    db.session.commit()
    
    return jsonify({'message': 'Levedura deletada com sucesso'}), 200