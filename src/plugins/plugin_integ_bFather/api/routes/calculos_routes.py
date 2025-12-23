# routes/calculos_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
from model.brewfather import BrewFatherRecipe
from model.ingredientes import CalculoPreco
from model.calculo_envase import CalculoEnvase 
from model.envase import Envase
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
   
    
@calculos_bp.route('/calcular_envase', methods=['POST'])
@login_required
def calcular_envase():
    """Calcular preço baseado em envase (quantidade total e custo por litro)"""
    try:
        data = request.get_json()
        print("Received data for envase calculation:", data)
        
        # Se envase_id for fornecido, buscar dados do envase
        envase_id = data.get('envase_id')
        if envase_id:
            envase = Envase.query.get(envase_id)
            if envase:
                # Usar dados do envase cadastrado - converter para float
                quantidade_total_litros = float(envase.quantidade_litros) if envase.quantidade_litros else 0.0
                
                # Calcular custo por litro baseado nos itens do envase
                custo_total = 0.0
                quantidade_total_ml = 0.0
                
                for item in envase.itens_envase:
                    if item.embalagem and item.embalagem.valor_unidade is not None:
                        try:
                            # Converter tudo para float
                            valor_unidade = float(item.embalagem.valor_unidade)
                            quantidade_item = float(item.quantidade)
                            capacidade_ml = float(item.capacidade_ml) if item.capacidade_ml else 0.0
                            
                            custo_total += quantidade_item * valor_unidade
                            quantidade_total_ml += quantidade_item * capacidade_ml
                        except (TypeError, ValueError) as conv_error:
                            print(f"Erro na conversão de valores do item: {conv_error}")
                            continue
                
                # Se temos dados de ml, usar para cálculo mais preciso
                if quantidade_total_ml > 0:
                    quantidade_litros = float(quantidade_total_ml) / 1000.0
                    custo_por_litro = float(custo_total) / float(quantidade_litros) if quantidade_litros > 0 else 0.0
                else:
                    # Usar dados diretos do envase
                    quantidade_litros = quantidade_total_litros
                    custo_por_litro = 5.0  # Usar valor do formulário ou padrão
            else:
                return jsonify({'error': 'Envase não encontrado'}), 404
        else:
            # Usar dados manuais do formulário - converter para float
            quantidade_total_litros = float(data.get('quantidade_total_litros', 0))
            custo_por_litro = float(data.get('custo_por_litro', 0))
        
        quantidade_ml = int(data.get('quantidade_ml', 0))
        
        if not quantidade_total_litros or not custo_por_litro or not quantidade_ml:
            return jsonify({'error': 'Quantidade total, custo por litro e quantidade em ml são obrigatórios'}), 400
        
        # Converter todos os parâmetros para float
        custo_embalagem = float(data.get('custo_embalagem', 0))
        custo_impressao = float(data.get('custo_impressao', 0))
        custo_tampinha = float(data.get('custo_tampinha', 0))
        percentual_lucro = float(data.get('percentual_lucro', 30))
        margem_cartao = float(data.get('margem_cartao', 3.5))
        percentual_sanitizacao = float(data.get('percentual_sanitizacao', 2.0))
        percentual_impostos = float(data.get('percentual_impostos', 8.0))
        
        # Inicializar calculadora
        calculadora = CalculadoraPrecosBrewFather()
        
        # Calcular custo base para a quantidade total
        custo_total_ingredientes = quantidade_total_litros * custo_por_litro
        
        # Calcular preço final - garantir que todos os parâmetros são float
        resultado = calculadora.calcular_preco_final(
            valor_litro_base=float(custo_por_litro),
            quantidade_ml=int(quantidade_ml),
            custo_embalagem=float(custo_embalagem),
            custo_impressao=float(custo_impressao),
            custo_tampinha=float(custo_tampinha),
            percentual_lucro=float(percentual_lucro),
            margem_cartao=float(margem_cartao),
            percentual_sanitizacao=float(percentual_sanitizacao),
            percentual_impostos=float(percentual_impostos)
        )
        
        # Calcular total arrecadado - garantir conversão para float
        unidades_produzidas = (quantidade_total_litros * 1000.0) / float(quantidade_ml)
        total_arrecadado = float(unidades_produzidas) * float(resultado.valor_venda_final)
        
        # Calcular custos totais de embalagem
        custo_total_embalagens = float(unidades_produzidas) * (
            float(resultado.custo_embalagem) + 
            float(resultado.custo_impressao) + 
            float(resultado.custo_tampinha)
        )
        
        lucro_total = float(total_arrecadado) - (float(custo_total_ingredientes) + float(custo_total_embalagens))
        
        # Salvar no banco de dados usando o novo modelo
        calculo_envase = CalculoEnvase(
            envase_id=envase_id,
            nome_produto=data.get('nome_produto', 'Cálculo por Envase'),
            quantidade_ml=int(quantidade_ml),
            tipo_embalagem=data.get('tipo_embalagem', 'Garrafa'),
            valor_litro_base=float(custo_por_litro),
            custo_embalagem=float(custo_embalagem),
            custo_impressao=float(custo_impressao),
            custo_tampinha=float(custo_tampinha),
            percentual_lucro=float(percentual_lucro),
            margem_cartao=float(margem_cartao),
            percentual_sanitizacao=float(percentual_sanitizacao),
            percentual_impostos=float(percentual_impostos),
            valor_total=float(resultado.valor_total),
            valor_venda_final=float(resultado.valor_venda_final)
        )
        
        db.session.add(calculo_envase)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'resultado': {
                'valor_venda_final': float(resultado.valor_venda_final),
                'valor_total': float(resultado.valor_total),
                'custo_ingredientes': float(resultado.custo_ingredientes),
                'custo_embalagem': float(resultado.custo_embalagem),
                'custo_impressao': float(resultado.custo_impressao),
                'custo_tampinha': float(resultado.custo_tampinha),
                'subtotal': float(resultado.subtotal),
                'valor_lucro': float(resultado.valor_lucro),
                'margem_cartao': float(resultado.margem_cartao),
                'valor_sanitizacao': float(resultado.valor_sanitizacao),
                'valor_impostos': float(resultado.valor_impostos)
            },
            'envase': {
                'quantidade_total_litros': float(quantidade_total_litros),
                'custo_por_litro': float(custo_por_litro),
                'custo_total_ingredientes': float(custo_total_ingredientes),
                'unidades_produzidas': float(unidades_produzidas),
                'total_arrecadado': float(total_arrecadado),
                'custo_total_embalagens': float(custo_total_embalagens),
                'lucro_total': float(lucro_total)
            },
            'calculo_id': calculo_envase.id
        }), 200
        
    except Exception as e:
        print(f"Erro no cálculo de envase: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        db.session.rollback()
        return jsonify({'error': f'Erro no cálculo: {str(e)}'}), 500