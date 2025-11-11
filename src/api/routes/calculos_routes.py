# routes/calculos_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from model.ingredientes import Receita, IngredienteReceita, Malte, Lupulo, Levedura, CalculoPreco
from utils.calculadora import CalculadoraPrecos
from db.database import db 
    

calculos_bp = Blueprint('calculos', __name__)

@calculos_bp.route('/calcular', methods=['POST'])
@login_required
def calcular_preco():
    """Calcular preço de uma receita"""
    data = request.get_json()
    
    calculadora = CalculadoraPrecos()
    
    # Obter receita e ingredientes
    receita = Receita.query.get(data['receita_id'])
    ingredientes = IngredienteReceita.query.filter_by(receita_id=data['receita_id']).all()
    
    # Obter dados dos ingredientes
    maltes = {malte.id: malte for malte in Malte.query.filter_by(ativo=True).all()}
    lupulos = {lupulo.id: lupulo for lupulo in Lupulo.query.filter_by(ativo=True).all()}
    leveduras = {levedura.id: levedura for levedura in Levedura.query.filter_by(ativo=True).all()}
    
    # Calcular preço
    resultado = calculadora.calcular_receita_completa(
        receita=receita,
        ingredientes=ingredientes,
        maltes=maltes,
        lupulos=lupulos,
        leveduras=leveduras,
        quantidade_ml=data['quantidade_ml'],
        custo_embalagem=data['custo_embalagem'],
        custo_impressao=data['custo_impressao'],
        custo_tampinha=data['custo_tampinha'],
        percentual_lucro=data['percentual_lucro'],
        margem_cartao=data['margem_cartao'],
        percentual_sanitizacao=data['percentual_sanitizacao'],
        percentual_impostos=data['percentual_impostos']
    )
    
    # Salvar cálculo no banco
    calculo = CalculoPreco(
        receita_id=data['receita_id'],
        nome_produto=data.get('nome_produto', receita.nome),
        quantidade_ml=data['quantidade_ml'],
        tipo_embalagem=data.get('tipo_embalagem', 'Garrafa'),
        valor_litro_base=resultado['valor_litro_base'],
        custo_embalagem=data['custo_embalagem'],
        custo_impressao=data['custo_impressao'],
        custo_tampinha=data['custo_tampinha'],
        percentual_lucro=data['percentual_lucro'],
        margem_cartao=data['margem_cartao'],
        percentual_sanitizacao=data['percentual_sanitizacao'],
        percentual_impostos=data['percentual_impostos'],
        valor_total=resultado['resultado']['valor_total'],
        valor_venda_final=resultado['resultado']['valor_venda_final']
    )
    
    db.session.add(calculo)
    db.session.commit()
    
    return jsonify({
        'message': 'Cálculo realizado com sucesso',
        'resultado': resultado,
        'calculo_id': calculo.id
    }), 200

@calculos_bp.route('/calculos', methods=['GET'])
@login_required
def get_calculos():
    """Obter lista de cálculos realizados"""
    calculos = CalculoPreco.query.order_by(CalculoPreco.data_calculo.desc()).all()
    return jsonify([calculo.to_dict() for calculo in calculos]), 200