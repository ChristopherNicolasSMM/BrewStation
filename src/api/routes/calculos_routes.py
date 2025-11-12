# routes/calculos_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from model.brewfather import BrewFatherRecipe
from model.ingredientes import CalculoPreco
from utils.calculadora_brewfather import CalculadoraPrecosBrewFather
from db.database import db

calculos_bp = Blueprint('calculos', __name__)

@calculos_bp.route('/calcular', methods=['POST'])
@login_required
def calcular_preco():
    """Calcular preço para uma receita do BrewFather"""
    try:
        data = request.get_json()
        print("Received data for calculation:", data)
        
        receita_id = data.get('receita_id')
        if not receita_id:
            return jsonify({'error': 'ID da receita é obrigatório'}), 400
        
        # Buscar receita do BrewFather
        receita = BrewFatherRecipe.query.get(receita_id)
        if not receita:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        # Validar dados obrigatórios
        quantidade_ml = data.get('quantidade_ml')
        if not quantidade_ml:
            return jsonify({'error': 'Quantidade em ml é obrigatória'}), 400
        
        # Inicializar calculadora
        calculadora = CalculadoraPrecosBrewFather()
        
        # Calcular preço
        resultado = calculadora.calcular_receita_brewfather(
            receita=receita,
            quantidade_ml=int(quantidade_ml),
            custo_embalagem=float(data.get('custo_embalagem', 0)),
            custo_impressao=float(data.get('custo_impressao', 0)),
            custo_tampinha=float(data.get('custo_tampinha', 0)),
            percentual_lucro=float(data.get('percentual_lucro', 30)),
            margem_cartao=float(data.get('margem_cartao', 3.5)),
            percentual_sanitizacao=float(data.get('percentual_sanitizacao', 2.0)),
            percentual_impostos=float(data.get('percentual_impostos', 8.0))
        )
        
        # Salvar no banco de dados
        calculo_preco = CalculoPreco(
            receita_id=receita_id,
            nome_produto=data.get('nome_produto', receita.name),
            quantidade_ml=int(quantidade_ml),
            tipo_embalagem=data.get('tipo_embalagem', 'Garrafa'),
            valor_litro_base=resultado['valor_litro_base'],
            custo_embalagem=float(data.get('custo_embalagem', 0)),
            custo_impressao=float(data.get('custo_impressao', 0)),
            custo_tampinha=float(data.get('custo_tampinha', 0)),
            percentual_lucro=float(data.get('percentual_lucro', 30)),
            margem_cartao=float(data.get('margem_cartao', 3.5)),
            percentual_sanitizacao=float(data.get('percentual_sanitizacao', 2.0)),
            percentual_impostos=float(data.get('percentual_impostos', 8.0)),
            valor_total=resultado['resultado']['valor_total'],
            valor_venda_final=resultado['resultado']['valor_venda_final']
        )
        
        db.session.add(calculo_preco)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'resultado': resultado['resultado'],
            'calculo_id': calculo_preco.id,
            'detalhes_ingredientes': resultado['ingredientes'],
            'custo_ingredientes': resultado['resumo']['custo_total_ingredientes']
        }), 200
        
    except Exception as e:
        print(f"Erro no cálculo: {e}")
        db.session.rollback()
        return jsonify({'error': f'Erro no cálculo: {str(e)}'}), 500

@calculos_bp.route('/calculos', methods=['GET'])
@login_required
def get_calculos():
    """Obter histórico de cálculos"""
    try:
        calculos = CalculoPreco.query.order_by(CalculoPreco.data_calculo.desc()).limit(10).all()
        
        return jsonify([{
            'id': calc.id,
            'receita_id': calc.receita_id,
            'nome_produto': calc.nome_produto,
            'quantidade_ml': calc.quantidade_ml,
            'tipo_embalagem': calc.tipo_embalagem,
            'valor_venda_final': float(calc.valor_venda_final),
            'data_calculo': calc.data_calculo.isoformat() if calc.data_calculo else None
        } for calc in calculos]), 200
        
    except Exception as e:
        print(f"Erro ao buscar cálculos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@calculos_bp.route('/calculos/<int:calculo_id>', methods=['GET'])
@login_required
def get_calculo_detalhes(calculo_id):
    """Obter detalhes de um cálculo específico"""
    try:
        calculo = CalculoPreco.query.get_or_404(calculo_id)
        
        return jsonify({
            'calculo': {
                'id': calculo.id,
                'receita_id': calculo.receita_id,
                'nome_produto': calculo.nome_produto,
                'quantidade_ml': calculo.quantidade_ml,
                'tipo_embalagem': calculo.tipo_embalagem,
                'valor_litro_base': float(calculo.valor_litro_base),
                'custo_embalagem': float(calculo.custo_embalagem),
                'custo_impressao': float(calculo.custo_impressao),
                'custo_tampinha': float(calculo.custo_tampinha),
                'percentual_lucro': float(calculo.percentual_lucro),
                'margem_cartao': float(calculo.margem_cartao),
                'percentual_sanitizacao': float(calculo.percentual_sanitizacao),
                'percentual_impostos': float(calculo.percentual_impostos),
                'valor_total': float(calculo.valor_total),
                'valor_venda_final': float(calculo.valor_venda_final),
                'data_calculo': calculo.data_calculo.isoformat() if calculo.data_calculo else None
            }
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar cálculo: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500