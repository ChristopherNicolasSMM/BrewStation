# routes/receitas_routes.py (adaptado)
from flask import Blueprint, request, jsonify
from flask_login import login_required
from model.brewfather import BrewFatherRecipe, BrewFatherBatch, BrewFatherService
from model.ingredientes import cadastrar_ingrediente_automatico
from model.ingredientes import IngredienteReceita, CalculoPreco, Malte, Lupulo, Levedura
from db.database import db

receitas_bp = Blueprint('receitas', __name__)

# ================================ ROTAS PARA RECEITAS (BREWFATHER) ================================

@receitas_bp.route('/receitas', methods=['GET'])
@login_required
def get_receitas():
    """Obter lista de receitas do BrewFather"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    query = BrewFatherRecipe.query.filter_by(is_active=True)
    
    if search:
        query = query.filter(BrewFatherRecipe.name.ilike(f'%{search}%'))
    
    receitas = query.order_by(BrewFatherRecipe.name)\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'receitas': [{
            'id': receita.id,
            'brewfather_id': receita.brewfather_id,
            'nome': receita.name,
            'estilo': receita.style,
            'abv': receita.abv,
            'ibu': receita.ibu,
            'cor': receita.color,
            'volume_litros': receita.batch_size,
            'eficiencia': receita.efficiency,
            'og': receita.original_gravity,
            'fg': receita.final_gravity,
            'avaliacao': receita.rating,
            'contagem_brassagens': receita.brew_count,
            'ultima_brassagem': receita.last_brewed.isoformat() if receita.last_brewed else None,
            'sincronizado_em': receita.synchronized_at.isoformat() if receita.synchronized_at else None
        } for receita in receitas.items],
        'total': receitas.total,
        'paginas': receitas.pages,
        'pagina_atual': page
    }), 200

@receitas_bp.route('/receitas/<int:receita_id>', methods=['GET'])
@login_required
def get_receita_id(receita_id):
    """Obter receita específica do BrewFather"""
    try:
        
        print(receita_id)
        receita = BrewFatherRecipe.query.get(receita_id)
        print(receita)
        if not receita:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        # Processar ingredientes e cadastrar automaticamente se necessário
        ingredientes_processados = processar_ingredientes_receita(receita)
        
        return jsonify({
            'receita': {
                'id': receita.id,
                'brewfather_id': receita.brewfather_id,
                'nome': receita.name,
                'estilo': receita.style,
                'abv': receita.abv,
                'ibu': receita.ibu,
                'cor': receita.color,
                'volume_litros': receita.batch_size,
                'eficiencia': receita.efficiency,
                'og': receita.original_gravity,
                'fg': receita.final_gravity,
                'ingredientes': receita.ingredients,
                'ingredientes_processados': ingredientes_processados,
                'notas': receita.notes,
                'avaliacao': receita.rating,
                'contagem_brassagens': receita.brew_count,
                'ultima_brassagem': receita.last_brewed.isoformat() if receita.last_brewed else None,
                'data_criacao': receita.created_date.isoformat() if receita.created_date else None,
                'sincronizado_em': receita.synchronized_at.isoformat() if receita.synchronized_at else None
            }
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar receita {receita_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

def processar_ingredientes_receita(receita):
    """
    Processa ingredientes de uma receita do BrewFather e cadastra automaticamente
    Retorna os ingredientes com IDs do sistema local
    """
    if not receita.ingredients:
        return []
    
    ingredientes_processados = []
    
    # Processar maltes/fermentáveis
    for fermentable in receita.ingredients.get('fermentables', []):
        ingrediente_id = cadastrar_ingrediente_automatico('malte', {
            'nome': fermentable.get('name', ''),
            'fabricante': fermentable.get('supplier', ''),
            'cor_ebc': fermentable.get('color', 0),
            'poder_diastatico': 0,  # BrewFather não fornece
            'rendimento': fermentable.get('yield', 75),
            'tipo': fermentable.get('type', 'Base')
        })
        
        if ingrediente_id:
            ingredientes_processados.append({
                'tipo': 'malte',
                'ingrediente_id': ingrediente_id,
                'nome': fermentable.get('name', ''),
                'quantidade': fermentable.get('amount', 0),
                'unidade': 'kg'
            })
    
    # Processar lúpulos
    for hop in receita.ingredients.get('hops', []):
        ingrediente_id = cadastrar_ingrediente_automatico('lupulo', {
            'nome': hop.get('name', ''),
            'fabricante': hop.get('supplier', ''),
            'alpha_acidos': hop.get('alpha', 0),
            'beta_acidos': hop.get('beta', 0),
            'formato': hop.get('form', 'Pellet'),
            'origem': hop.get('origin', ''),
            'aroma': hop.get('use', '')  # bittering, aroma, dry hop
        })
        
        if ingrediente_id:
            ingredientes_processados.append({
                'tipo': 'lupulo',
                'ingrediente_id': ingrediente_id,
                'nome': hop.get('name', ''),
                'quantidade': hop.get('amount', 0),
                'unidade': 'g',
                'tempo_adicao': hop.get('time', 0),
                'uso': hop.get('use', '')
            })
    
    # Processar leveduras
    for yeast in receita.ingredients.get('yeasts', []):
        ingrediente_id = cadastrar_ingrediente_automatico('levedura', {
            'nome': yeast.get('name', ''),
            'fabricante': yeast.get('supplier', ''),
            'formato': 'Líquida' if yeast.get('type', '').lower() == 'liquid' else 'Seca',
            'atenuacao': yeast.get('attenuation', 75),
            'temp_fermentacao': 20,  # BrewFather não fornece diretamente
            'floculacao': 'Média'
        })
        
        if ingrediente_id:
            ingredientes_processados.append({
                'tipo': 'levedura',
                'ingrediente_id': ingrediente_id,
                'nome': yeast.get('name', ''),
                'quantidade': yeast.get('amount', 0),
                'unidade': 'unidade'
            })
    
    return ingredientes_processados

# ================================ ROTAS PARA SESSÕES DE BRASSAGEM (BATCHES) ================================

@receitas_bp.route('/sessoes-brassagem', methods=['GET'])
@login_required
def get_sessoes_brassagem():
    """Obter lista de sessões de brassagem (batches) do BrewFather"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_filter = request.args.get('status', '')
    
    query = BrewFatherBatch.query
    
    if status_filter:
        query = query.filter(BrewFatherBatch.status == status_filter)
    
    batches = query.order_by(BrewFatherBatch.brew_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'sessoes_brassagem': [{
            'id': batch.id,
            'brewfather_id': batch.brewfather_id,
            'nome_receita': batch.recipe_name,
            'numero_lote': batch.batch_no,
            'status': batch.status,
            'data_brassagem': batch.brew_date.isoformat() if batch.brew_date else None,
            'og_estimada': batch.estimated_og,
            'og_medida': batch.measured_og,
            'abv_estimada': batch.estimated_abv,
            'abv_medida': batch.measured_abv,
            'volume_litros': batch.batch_size,
            'avaliacao': batch.rating,
            'sincronizado_em': batch.synchronized_at.isoformat() if batch.synchronized_at else None
        } for batch in batches.items],
        'total': batches.total,
        'paginas': batches.pages,
        'pagina_atual': page
    }), 200

@receitas_bp.route('/sessoes-brassagem/<int:batch_id>', methods=['GET'])
@login_required
def get_sessao_brassagem_id(batch_id):
    """Obter sessão de brassagem específica"""
    try:
        batch = BrewFatherBatch.query.get(batch_id)
        if not batch:
            return jsonify({'error': 'Sessão de brassagem não encontrada'}), 404
        
        return jsonify({
            'sessao_brassagem': {
                'id': batch.id,
                'brewfather_id': batch.brewfather_id,
                'recipe_id': batch.recipe_id,
                'nome_receita': batch.recipe_name,
                'numero_lote': batch.batch_no,
                'status': batch.status,
                'data_brassagem': batch.brew_date.isoformat() if batch.brew_date else None,
                'og_estimada': batch.estimated_og,
                'og_medida': batch.measured_og,
                'fg_estimada': batch.estimated_fg,
                'fg_medida': batch.measured_fg,
                'abv_estimada': batch.estimated_abv,
                'abv_medida': batch.measured_abv,
                'ibu_estimada': batch.estimated_ibu,
                'cor_estimada': batch.estimated_color,
                'volume_litros': batch.batch_size,
                'eficiencia': batch.efficiency,
                'notas': batch.notes,
                'avaliacao': batch.rating,
                'sincronizado_em': batch.synchronized_at.isoformat() if batch.synchronized_at else None
            }
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar sessão de brassagem {batch_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ================================ ROTAS PARA CÁLCULOS DE PREÇO ================================

@receitas_bp.route('/receitas/<int:receita_id>/calcular-preco', methods=['POST'])
@login_required
def calcular_preco_receita(receita_id):
    """Calcular preço para uma receita do BrewFather"""
    try:
        receita = BrewFatherRecipe.query.get(receita_id)
        if not receita:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        data = request.get_json()
        
        # Processar ingredientes para obter custos
        ingredientes_processados = processar_ingredientes_receita(receita)
        custo_ingredientes = calcular_custo_ingredientes(ingredientes_processados)
        
        # Calcular custo por litro (base)
        volume_litros = receita.batch_size
        custo_litro_base = custo_ingredientes / volume_litros if volume_litros > 0 else 0
        
        # Aplicar margens e custos adicionais
        calculo = calcular_preco_final(custo_litro_base, data)
        
        # Salvar cálculo
        calculo_preco = CalculoPreco(
            receita_id=receita_id,
            nome_produto=receita.name,
            quantidade_ml=data.get('quantidade_ml', 500),
            tipo_embalagem=data.get('tipo_embalagem', 'Garrafa'),
            valor_litro_base=custo_litro_base,
            custo_embalagem=data.get('custo_embalagem', 0),
            custo_impressao=data.get('custo_impressao', 0),
            custo_tampinha=data.get('custo_tampinha', 0),
            percentual_lucro=data.get('percentual_lucro', 30),
            margem_cartao=data.get('margem_cartao', 3),
            percentual_sanitizacao=data.get('percentual_sanitizacao', 5),
            percentual_impostos=data.get('percentual_impostos', 17),
            valor_total=calculo['custo_total'],
            valor_venda_final=calculo['preco_venda']
        )
        
        db.session.add(calculo_preco)
        db.session.commit()
        
        return jsonify({
            'calculo': calculo_preco.to_dict(),
            'detalhes_ingredientes': ingredientes_processados,
            'custo_ingredientes': custo_ingredientes
        }), 200
        
    except Exception as e:
        print(f"Erro ao calcular preço para receita {receita_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

def calcular_custo_ingredientes(ingredientes_processados):
    """Calcula custo total dos ingredientes"""
    custo_total = 0
    
    for ingrediente in ingredientes_processados:
        if ingrediente['tipo'] == 'malte':
            malte = Malte.query.get(ingrediente['ingrediente_id'])
            if malte:
                custo_total += ingrediente['quantidade'] * malte.preco_kg
        
        elif ingrediente['tipo'] == 'lupulo':
            lupulo = Lupulo.query.get(ingrediente['ingrediente_id'])
            if lupulo:
                # Converter gramas para kg
                custo_total += (ingrediente['quantidade'] / 1000) * lupulo.preco_kg
        
        elif ingrediente['tipo'] == 'levedura':
            levedura = Levedura.query.get(ingrediente['ingrediente_id'])
            if levedura:
                custo_total += ingrediente['quantidade'] * levedura.preco_unidade
    
    return custo_total

def calcular_preco_final(custo_litro_base, parametros):
    """Calcula preço final com todas as margens"""
    quantidade_ml = parametros.get('quantidade_ml', 500)
    custo_embalagem = parametros.get('custo_embalagem', 0)
    custo_impressao = parametros.get('custo_impressao', 0)
    custo_tampinha = parametros.get('custo_tampinha', 0)
    percentual_lucro = parametros.get('percentual_lucro', 30) / 100
    margem_cartao = parametros.get('margem_cartao', 3) / 100
    percentual_sanitizacao = parametros.get('percentual_sanitizacao', 5) / 100
    percentual_impostos = parametros.get('percentual_impostos', 17) / 100
    
    # Custo do produto
    custo_produto = (quantidade_ml / 1000) * custo_litro_base
    
    # Custos diretos
    custos_diretos = custo_embalagem + custo_impressao + custo_tampinha
    
    # Custo total
    custo_total = custo_produto + custos_diretos
    
    # Adicionar sanitização
    custo_com_sanitizacao = custo_total * (1 + percentual_sanitizacao)
    
    # Adicionar lucro
    preco_com_lucro = custo_com_sanitizacao * (1 + percentual_lucro)
    
    # Adicionar impostos
    preco_com_impostos = preco_com_lucro * (1 + percentual_impostos)
    
    # Adicionar margem do cartão
    preco_venda_final = preco_com_impostos * (1 + margem_cartao)
    
    return {
        'custo_produto': custo_produto,
        'custos_diretos': custos_diretos,
        'custo_total': custo_total,
        'custo_com_sanitizacao': custo_com_sanitizacao,
        'preco_com_lucro': preco_com_lucro,
        'preco_com_impostos': preco_com_impostos,
        'preco_venda': preco_venda_final
    }