# routes/brewfather_routes.py
from flask import Blueprint, request, jsonify, send_file
from flask_login import login_required
from model.brewfather import BrewFatherService, BrewFatherRecipe, BrewFatherBatch, BrewFatherInventory
from model.config import Configuracao
from db.database import db
from datetime import datetime, timedelta
import pandas as pd
import io
import openpyxl
from openpyxl.styles import PatternFill, Font


brewfather_bp = Blueprint('brewfather', __name__)

@brewfather_bp.route('/brewfather/status')
@login_required
def get_brewfather_status():
    """Obtém status da integração com BrewFather"""
    enabled = Configuracao.get_config('BREWFATHER_ENABLED')
    user_id = Configuracao.get_config('BREWFATHER_USER_ID')
    api_key = Configuracao.get_config('BREWFATHER_API_KEY')
    
    status = {
        'enabled': bool(enabled),
        'configured': bool(user_id and api_key),
        'sync_status': BrewFatherService.get_sync_status()
    }
    
    # Testar conexão se estiver configurado
    if status['configured']:
        api = BrewFatherService.get_api_client()
        status['connection_test'] = api.test_connection() if api else False
    
    return jsonify(status)

@brewfather_bp.route('/brewfather/sync/recipes', methods=['POST'])
@login_required
def sync_recipes():
    """Sincroniza receitas do BrewFather"""
    result = BrewFatherService.sync_recipes()
    return jsonify(result)

@brewfather_bp.route('/brewfather/sync/batches', methods=['POST'])
@login_required
def sync_batches():
    """Sincroniza lotes do BrewFather"""
    result = BrewFatherService.sync_batches()
    return jsonify(result)

@brewfather_bp.route('/brewfather/sync/inventory', methods=['POST'])
@login_required
def sync_inventory():
    """Sincroniza estoque do BrewFather"""
    result = BrewFatherService.sync_inventory()
    return jsonify(result)

@brewfather_bp.route('/brewfather/sync/all', methods=['POST'])
@login_required
def sync_all():
    """Sincroniza todos os dados do BrewFather"""
    results = {}
    
    print("Iniciando sincronização completa com BrewFather...")
    
    # Sincronizar receitas
    results['recipes'] = BrewFatherService.sync_recipes()
    
    # Sincronizar lotes
    results['batches'] = BrewFatherService.sync_batches()
    
    # Sincronizar estoque
    results['inventory'] = BrewFatherService.sync_inventory()
    
    print("Sincronização completa com BrewFather finalizada.")
    
    return jsonify(results)

@brewfather_bp.route('/brewfather/recipes')
@login_required
def get_recipes():
    """Obtém receitas sincronizadas"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    search = request.args.get('search', '')
    
    query = BrewFatherRecipe.query
    
    if search:
        query = query.filter(BrewFatherRecipe.name.ilike(f'%{search}%'))
    
    recipes = query.order_by(BrewFatherRecipe.name)\
        .paginate(page=page, per_page=per_page, error_out=False)
    print(recipes)
    return jsonify({
        'recipes': [{
            'id': recipe.id,
            'brewfather_id': recipe.brewfather_id,
            'name': recipe.name,
            'style': recipe.style,
            'abv': recipe.abv,
            'ibu': recipe.ibu,
            'color': recipe.color,
            'batch_size': recipe.batch_size,
            'efficiency': recipe.efficiency,
            'original_gravity': recipe.original_gravity,
            'final_gravity': recipe.final_gravity,
            'rating': recipe.rating,
            'brew_count': recipe.brew_count,
            'last_brewed': recipe.last_brewed.isoformat() if recipe.last_brewed else None,
            'synchronized_at': recipe.synchronized_at.isoformat() if recipe.synchronized_at else None
        } for recipe in recipes.items],
        'total': recipes.total,
        'pages': recipes.pages,
        'current_page': page
    })

@brewfather_bp.route('/brewfather/batches')
@login_required
def get_batches():
    """Obtém lotes sincronizados"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    status_filter = request.args.get('status', '')
    
    query = BrewFatherBatch.query
    
    if status_filter:
        query = query.filter(BrewFatherBatch.status == status_filter)
    
    batches = query.order_by(BrewFatherBatch.brew_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'batches': [{
            'id': batch.id,
            'brewfather_id': batch.brewfather_id,
            'recipe_name': batch.recipe_name,
            'batch_no': batch.batch_no,
            'status': batch.status,
            'brew_date': batch.brew_date.isoformat() if batch.brew_date else None,
            'estimated_og': batch.estimated_og,
            'measured_og': batch.measured_og,
            'estimated_abv': batch.estimated_abv,
            'measured_abv': batch.measured_abv,
            'batch_size': batch.batch_size,
            'rating': batch.rating,
            'synchronized_at': batch.synchronized_at.isoformat() if batch.synchronized_at else None
        } for batch in batches.items],
        'total': batches.total,
        'pages': batches.pages,
        'current_page': page
    })

@brewfather_bp.route('/brewfather/inventory')
@login_required
def get_inventory():
    """Obtém estoque sincronizado"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)
    type_filter = request.args.get('type', '')
    
    query = BrewFatherInventory.query
    
    if type_filter:
        query = query.filter(BrewFatherInventory.type == type_filter)
    
    inventory = query.order_by(BrewFatherInventory.name)\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'inventory': [{
            'id': item.id,
            'brewfather_id': item.brewfather_id,
            'name': item.name,
            'type': item.type,
            'category': item.category,
            'quantity': item.quantity,
            'unit': item.unit,
            'price': item.price,
            'supplier': item.supplier,
            'synchronized_at': item.synchronized_at.isoformat() if item.synchronized_at else None
        } for item in inventory.items],
        'total': inventory.total,
        'pages': inventory.pages,
        'current_page': page
    })

@brewfather_bp.route('/brewfather/recipe/<int:recipe_id>')
@login_required
def get_recipe_detail(recipe_id):
    """Obtém detalhes de uma receita"""
    recipe = BrewFatherRecipe.query.get_or_404(recipe_id)
    
    return jsonify({
        'recipe': {
            'id': recipe.id,
            'brewfather_id': recipe.brewfather_id,
            'name': recipe.name,
            'style': recipe.style,
            'abv': recipe.abv,
            'ibu': recipe.ibu,
            'color': recipe.color,
            'batch_size': recipe.batch_size,
            'efficiency': recipe.efficiency,
            'original_gravity': recipe.original_gravity,
            'final_gravity': recipe.final_gravity,
            'ingredients': recipe.ingredients,
            'notes': recipe.notes,
            'rating': recipe.rating,
            'brew_count': recipe.brew_count,
            'last_brewed': recipe.last_brewed.isoformat() if recipe.last_brewed else None,
            'created_date': recipe.created_date.isoformat() if recipe.created_date else None,
            'synchronized_at': recipe.synchronized_at.isoformat() if recipe.synchronized_at else None
        }
    })

@brewfather_bp.route('/brewfather/batch/<int:batch_id>')
@login_required
def get_batch_detail(batch_id):
    """Obtém detalhes de um lote"""
    batch = BrewFatherBatch.query.get_or_404(batch_id)
    
    return jsonify({
        'batch': {
            'id': batch.id,
            'brewfather_id': batch.brewfather_id,
            'recipe_id': batch.recipe_id,
            'recipe_name': batch.recipe_name,
            'batch_no': batch.batch_no,
            'status': batch.status,
            'brew_date': batch.brew_date.isoformat() if batch.brew_date else None,
            'estimated_og': batch.estimated_og,
            'measured_og': batch.measured_og,
            'estimated_fg': batch.estimated_fg,
            'measured_fg': batch.measured_fg,
            'estimated_abv': batch.estimated_abv,
            'measured_abv': batch.measured_abv,
            'estimated_ibu': batch.estimated_ibu,
            'estimated_color': batch.estimated_color,
            'batch_size': batch.batch_size,
            'efficiency': batch.efficiency,
            'notes': batch.notes,
            'rating': batch.rating,
            'raw_data': batch.raw_data,
            'synchronized_at': batch.synchronized_at.isoformat() if batch.synchronized_at else None
        }
    })

@brewfather_bp.route('/brewfather/stats', methods=['GET'])
@login_required
def get_brewfather_stats():
    """Obtém estatísticas dos dados sincronizados"""
    try:
        recipes_count = BrewFatherRecipe.query.count()
        batches_count = BrewFatherBatch.query.count()
        inventory_count = BrewFatherInventory.query.count()
        
        # Última sincronização
        from model.brewfather import BrewFatherSync
        last_syncs = BrewFatherService.get_sync_status()
        
        # Contagem por tipo de estoque
        inventory_by_type = {}
        inventory_types = db.session.query(
            BrewFatherInventory.type,
            db.func.count(BrewFatherInventory.id)
        ).group_by(BrewFatherInventory.type).all()
        
        for tipo, count in inventory_types:
            inventory_by_type[tipo] = count
        
        return jsonify({
            'recipes_count': recipes_count,
            'batches_count': batches_count,
            'inventory_count': inventory_count,
            'inventory_by_type': inventory_by_type,
            'last_syncs': last_syncs
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar estatísticas do BrewFather: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@brewfather_bp.route('/brewfather/cleanup', methods=['POST'])
@login_required
def cleanup_brewfather_data():
    """Limpa dados antigos do BrewFather"""
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import and_
        
        data = request.get_json()
        days_old = data.get('days_old', 30)
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        # Limpar receitas antigas
        recipes_deleted = BrewFatherRecipe.query.filter(
            BrewFatherRecipe.synchronized_at < cutoff_date
        ).delete()
        
        # Limpar lotes antigos
        batches_deleted = BrewFatherBatch.query.filter(
            BrewFatherBatch.synchronized_at < cutoff_date
        ).delete()
        
        # Limpar estoque antigo
        inventory_deleted = BrewFatherInventory.query.filter(
            BrewFatherInventory.synchronized_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'message': f'Dados antigos limpos com sucesso',
            'recipes_deleted': recipes_deleted,
            'batches_deleted': batches_deleted,
            'inventory_deleted': inventory_deleted,
            'cutoff_date': cutoff_date.isoformat()
        }), 200
        
    except Exception as e:
        print(f"Erro ao limpar dados do BrewFather: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@brewfather_bp.route('/brewfather/recipes/fetch', methods=['POST'])
@login_required
def fetch_recipes_from_brewfather():
    """Busca receitas diretamente da API do BrewFather"""
    try:
        api = BrewFatherService.get_api_client()
        if not api:
            return jsonify({'error': 'API não configurada'}), 400
        
        # Buscar lista de receitas
        recipes_list = api.get_recipes_list()
        
        # Para cada receita, buscar detalhes completos
        detailed_recipes = []
        for recipe_summary in recipes_list:
            recipe_id = recipe_summary.get('_id')
            if recipe_id:
                recipe_detail = api.get_recipe_detail(recipe_id)
                if recipe_detail:
                    detailed_recipes.append(recipe_detail)
        
        return jsonify({
            'count': len(detailed_recipes),
            'recipes': detailed_recipes
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar receitas do BrewFather: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@brewfather_bp.route('/brewfather/recipe/fetch/<string:brewfather_id>', methods=['GET'])
@login_required
def fetch_recipe_detail_from_brewfather(brewfather_id):
    """Busca detalhes de uma receita específica da API do BrewFather"""
    try:
        api = BrewFatherService.get_api_client()
        if not api:
            return jsonify({'error': 'API não configurada'}), 400
        
        recipe_detail = api.get_recipe_detail(brewfather_id)
        
        if not recipe_detail:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        return jsonify({
            'recipe': recipe_detail
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar detalhes da receita do BrewFather: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
    
    
@brewfather_bp.route('/brewfather/recipe/<int:recipe_id>/cadastrar-insumos', methods=['POST'])
@login_required
def cadastrar_insumos_receita(recipe_id):
    """Cadastra automaticamente os insumos de uma receita do BrewFather"""
    try:
        receita = BrewFatherRecipe.query.get_or_404(recipe_id)
        
        from model.ingredientes import cadastrar_insumos_brewfather_automatico
        resultado = cadastrar_insumos_brewfather_automatico(receita)
        
        return jsonify(resultado), 200
        
    except Exception as e:
        print(f"Erro ao cadastrar insumos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@brewfather_bp.route('/brewfather/recipes/<int:recipe_id>/ingredientes-faltantes')
@login_required
def get_ingredientes_faltantes(recipe_id):
    """Lista ingredientes da receita que ainda não estão cadastrados"""
    try:
        receita = BrewFatherRecipe.query.get_or_404(recipe_id)
        
        if not receita.ingredients:
            return jsonify({'ingredientes_faltantes': []})
        
        ingredientes_faltantes = {
            'maltes': [],
            'lupulos': [],
            'leveduras': []
        }
        
        from model.ingredientes import Malte, Lupulo, Levedura
        
        # Verificar maltes faltantes
        for fermentable in receita.ingredients.get('fermentables', []):
            nome = fermentable.get('name', '').strip()
            fabricante = fermentable.get('supplier', '').strip()
            
            if nome and not Malte.query.filter_by(nome=nome, fabricante=fabricante, ativo=True).first():
                ingredientes_faltantes['maltes'].append({
                    'nome': nome,
                    'fabricante': fabricante,
                    'cor': fermentable.get('color', 0),
                    'rendimento': fermentable.get('yield', 75)
                })
        
        # Verificar lúpulos faltantes
        for hop in receita.ingredients.get('hops', []):
            nome = hop.get('name', '').strip()
            fabricante = hop.get('supplier', '').strip()
            
            if nome and not Lupulo.query.filter_by(nome=nome, fabricante=fabricante, ativo=True).first():
                ingredientes_faltantes['lupulos'].append({
                    'nome': nome,
                    'fabricante': fabricante,
                    'alpha_acidos': hop.get('alpha', 0),
                    'formato': hop.get('form', '')
                })
        
        # Verificar leveduras faltantes
        for yeast in receita.ingredients.get('yeasts', []):
            nome = yeast.get('name', '').strip()
            fabricante = yeast.get('supplier', '').strip()
            
            if nome and not Levedura.query.filter_by(nome=nome, fabricante=fabricante, ativo=True).first():
                ingredientes_faltantes['leveduras'].append({
                    'nome': nome,
                    'fabricante': fabricante,
                    'tipo': yeast.get('type', ''),
                    'atenuacao': yeast.get('attenuation', 75)
                })
        
        return jsonify({
            'ingredientes_faltantes': ingredientes_faltantes,
            'total_faltantes': (
                len(ingredientes_faltantes['maltes']) +
                len(ingredientes_faltantes['lupulos']) +
                len(ingredientes_faltantes['leveduras'])
            )
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar ingredientes faltantes: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@brewfather_bp.route('/brewfather/sync/recipes-with-insumos', methods=['POST'])
@login_required
def sync_recipes_with_insumos():
    """Sincroniza receitas e cadastra automaticamente os insumos faltantes"""
    try:
        # Primeiro sincroniza as receitas
        sync_result = BrewFatherService.sync_recipes()
        
        if not sync_result.get('success'):
            return jsonify(sync_result)
        
        # Agora cadastra insumos para todas as receitas sincronizadas
        receitas = BrewFatherRecipe.query.all()
        total_insumos_cadastrados = {
            'maltes': 0,
            'lupulos': 0,
            'leveduras': 0
        }
        
        from model.ingredientes import cadastrar_insumos_brewfather_automatico
        
        for receita in receitas:
            resultado = cadastrar_insumos_brewfather_automatico(receita)
            if resultado.get('success'):
                ingredientes = resultado.get('ingredientes_cadastrados', {})
                total_insumos_cadastrados['maltes'] += len(ingredientes.get('maltes', []))
                total_insumos_cadastrados['lupulos'] += len(ingredientes.get('lupulos', []))
                total_insumos_cadastrados['leveduras'] += len(ingredientes.get('leveduras', []))
        
        return jsonify({
            'success': True,
            'sync_result': sync_result,
            'insumos_cadastrados': total_insumos_cadastrados,
            'message': f"Sincronização completa! {sync_result.get('count', 0)} receitas sincronizadas, "
                      f"{total_insumos_cadastrados['maltes']} maltes, "
                      f"{total_insumos_cadastrados['lupulos']} lúpulos, "
                      f"{total_insumos_cadastrados['leveduras']} leveduras cadastrados"
        }), 200
        
    except Exception as e:
        print(f"Erro na sincronização com insumos: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500    
    
    



@brewfather_bp.route('/brewfather/relatorio', methods=['GET'])
@login_required
def get_relatorio_brewfather():
    """Retorna dados para o relatório de lotes e receitas"""
    try:
        # Obter filtros
        lote_id = request.args.get('lote', '').strip()
        receita_id = request.args.get('receita', '').strip()
        status = request.args.get('status', '').strip()
        data_inicio = request.args.get('dataInicio', '').strip()
        data_fim = request.args.get('dataFim', '').strip()
        
        # Query base para lotes
        query = BrewFatherBatch.query
        
        # Aplicar filtros apenas se não estiverem vazios
        if lote_id:
            query = query.filter_by(brewfather_id=lote_id)
        if receita_id:
            query = query.filter_by(recipe_id=receita_id)
        if status:
            query = query.filter_by(status=status)
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                query = query.filter(BrewFatherBatch.brew_date >= data_inicio_dt)
            except ValueError:
                # Ignora data inválida
                pass
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query = query.filter(BrewFatherBatch.brew_date <= data_fim_dt)
            except ValueError:
                # Ignora data inválida
                pass
        
        # Ordenar por data mais recente
        lotes = query.order_by(BrewFatherBatch.brew_date.desc()).all()
        
        # Preparar dados para resposta
        dados_lotes = []
        for lote in lotes:
            # Buscar receita associada
            receita = BrewFatherRecipe.query.filter_by(brewfather_id=lote.recipe_id).first()
            
            dados_lotes.append({
                'brewfather_id': lote.brewfather_id,
                'recipe_id': lote.recipe_id,
                'recipe_name': lote.recipe_name,
                'batch_no': lote.batch_no,
                'status': lote.status,
                'brew_date': lote.brew_date.isoformat() if lote.brew_date else None,
                'estimated_og': lote.estimated_og,
                'measured_og': lote.measured_og,
                'estimated_fg': lote.estimated_fg,
                'measured_fg': lote.measured_fg,
                'estimated_abv': lote.estimated_abv,
                'measured_abv': lote.measured_abv,
                'estimated_ibu': lote.estimated_ibu,
                'measured_ibu': lote.measured_ibu,
                'estimated_color': lote.estimated_color,
                'measured_color': lote.measured_color,
                'batch_size': lote.batch_size,
                'efficiency': lote.efficiency,
                'rating': lote.rating,
                'notes': lote.notes,
                'style': receita.style if receita else None
            })
        
        # Calcular resumo
        resumo = calcular_resumo_lotes(lotes)
        
        return jsonify({
            'success': True,
            'dados': dados_lotes,
            'resumo': resumo,
            'filtros_aplicados': {
                'lote': lote_id,
                'receita': receita_id,
                'status': status,
                'data_inicio': data_inicio,
                'data_fim': data_fim
            }
        })
        
    except Exception as e:
        print(f"Erro no relatório: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@brewfather_bp.route('/brewfather/batches', methods=['GET'])
@login_required
def get_batches_for_filters():  # Mude o nome da função também
    """Retorna lista de lotes para filtros"""
    try:
        batches = BrewFatherBatch.query.order_by(BrewFatherBatch.brew_date.desc()).all()
        
        batches_data = []
        for batch in batches:
            batches_data.append({
                'brewfather_id': batch.brewfather_id,
                'recipe_name': batch.recipe_name,
                'batch_no': batch.batch_no,
                'status': batch.status,
                'brew_date': batch.brew_date.isoformat() if batch.brew_date else None
            })
        
        return jsonify({
            'success': True,
            'batches': batches_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



# Mude esta rota (linha ~470):
@brewfather_bp.route('/brewfather/recipes', methods=['GET'])
@login_required
def get_recipes_for_filters():  # Mude o nome da função também
    """Retorna lista de receitas para filtros"""
    try:
        recipes = BrewFatherRecipe.query.order_by(BrewFatherRecipe.name).all()
        
        recipes_data = []
        for recipe in recipes:
            recipes_data.append({
                'brewfather_id': recipe.brewfather_id,
                'name': recipe.name,
                'style': recipe.style,
                'abv': recipe.abv,
                'ibu': recipe.ibu
            })
        
        return jsonify({
            'success': True,
            'recipes': recipes_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    """Retorna lista de receitas para filtros"""
    try:
        recipes = BrewFatherRecipe.query.order_by(BrewFatherRecipe.name).all()
        
        recipes_data = []
        for recipe in recipes:
            recipes_data.append({
                'brewfather_id': recipe.brewfather_id,
                'name': recipe.name,
                'style': recipe.style,
                'abv': recipe.abv,
                'ibu': recipe.ibu
            })
        
        return jsonify({
            'success': True,
            'recipes': recipes_data
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def calcular_resumo_lotes(lotes):
    """Calcula resumo estatístico dos lotes"""
    if not lotes:
        return {
            'total_lotes': 0,
            'lotes_concluidos': 0,
            'abv_medio': 0,
            'ibu_medio': 0,
            'eficiencia_media': 0,
            'batchs_ativos': 0,
            'abv_estimado': 0,
            'ibu_estimado': 0
        }
    
    lotes_concluidos = [l for l in lotes if l.status == 'Completed']
    batchs_ativos = [l for l in lotes if l.status in ['Brewing', 'Fermenting', 'Conditioning']]
    
    # ABV médio (usar medido quando disponível)
    abv_valores = [l.measured_abv or l.estimated_abv for l in lotes if (l.measured_abv or l.estimated_abv) and (l.measured_abv > 0 or l.estimated_abv > 0)]
    abv_medio = round(sum(abv_valores) / len(abv_valores), 1) if abv_valores else 0
    
    # IBU médio
    ibu_valores = [l.measured_ibu or l.estimated_ibu for l in lotes if (l.measured_ibu or l.estimated_ibu) and (l.measured_ibu > 0 or l.estimated_ibu > 0)]
    ibu_medio = round(sum(ibu_valores) / len(ibu_valores), 0) if ibu_valores else 0
    
    # Eficiência média
    eficiencia_valores = [l.efficiency for l in lotes if l.efficiency and l.efficiency > 0]
    eficiencia_media = round(sum(eficiencia_valores) / len(eficiencia_valores), 1) if eficiencia_valores else 0
    
    # Valores estimados médios
    abv_estimado_valores = [l.estimated_abv for l in lotes if l.estimated_abv and l.estimated_abv > 0]
    abv_estimado = round(sum(abv_estimado_valores) / len(abv_estimado_valores), 1) if abv_estimado_valores else 0
    
    ibu_estimado_valores = [l.estimated_ibu for l in lotes if l.estimated_ibu and l.estimated_ibu > 0]
    ibu_estimado = round(sum(ibu_estimado_valores) / len(ibu_estimado_valores), 0) if ibu_estimado_valores else 0
    
    return {
        'total_lotes': len(lotes),
        'lotes_concluidos': len(lotes_concluidos),
        'abv_medio': abv_medio,
        'ibu_medio': ibu_medio,
        'eficiencia_media': eficiencia_media,
        'batchs_ativos': len(batchs_ativos),
        'abv_estimado': abv_estimado,
        'ibu_estimado': ibu_estimado
    }





@brewfather_bp.route('/brewfather/batch/<batch_id>', methods=['GET'])
@login_required
def get_batch_detalhes(batch_id):
    """Retorna detalhes completos de um lote"""
    try:
        batch = BrewFatherBatch.query.filter_by(brewfather_id=batch_id).first()
        if not batch:
            return jsonify({'success': False, 'error': 'Lote não encontrado'}), 404
        
        receita = None
        if batch.recipe_id:
            receita = BrewFatherRecipe.query.filter_by(brewfather_id=batch.recipe_id).first()
        
        return jsonify({
            'success': True,
            'batch': batch.to_dict() if hasattr(batch, 'to_dict') else {
                'brewfather_id': batch.brewfather_id,
                'recipe_id': batch.recipe_id,
                'recipe_name': batch.recipe_name,
                'batch_no': batch.batch_no,
                'status': batch.status,
                'brew_date': batch.brew_date.isoformat() if batch.brew_date else None,
                'estimated_og': batch.estimated_og,
                'measured_og': batch.measured_og,
                'estimated_fg': batch.estimated_fg,
                'measured_fg': batch.measured_fg,
                'estimated_abv': batch.estimated_abv,
                'measured_abv': batch.measured_abv,
                'estimated_ibu': batch.estimated_ibu,
                'measured_ibu': batch.measured_ibu,
                'estimated_color': batch.estimated_color,
                'measured_color': batch.measured_color,
                'batch_size': batch.batch_size,
                'efficiency': batch.efficiency,
                'rating': batch.rating,
                'notes': batch.notes
            },
            'receita': receita.to_dict() if receita and hasattr(receita, 'to_dict') else {
                'brewfather_id': receita.brewfather_id if receita else None,
                'name': receita.name if receita else None,
                'style': receita.style if receita else None,
                'abv': receita.abv if receita else None,
                'ibu': receita.ibu if receita else None,
                'color': receita.color if receita else None,
                'batch_size': receita.batch_size if receita else None,
                'efficiency': receita.efficiency if receita else None,
                'original_gravity': receita.original_gravity if receita else None,
                'final_gravity': receita.final_gravity if receita else None,
                'ingredients': receita.ingredients if receita else None,
                'notes': receita.notes if receita else None
            } if receita else None
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

#@brewfather_bp.route('/brewfather/exportar-relatorio', methods=['POST'])
#@login_required
#def exportar_relatorio_brewfather():
#    """Exporta relatório para Excel"""
#    try:
#        import pandas as pd
#        import io
#        
#        dados = request.json.get('dados', [])
#        if not dados:
#            return jsonify({'success': False, 'error': 'Nenhum dado para exportar'}), 400
#        
#        # Criar DataFrame
#        df = pd.DataFrame(dados)
#        
#        # Criar arquivo em memória
#        output = io.BytesIO()
#        with pd.ExcelWriter(output, engine='openpyxl') as writer:
#            df.to_excel(writer, sheet_name='Relatorio_Lotes', index=False)
#            
#            # Ajustar largura das colunas
#            worksheet = writer.sheets['Relatorio_Lotes']
#            for column in worksheet.columns:
#                max_length = 0
#                column_letter = column[0].column_letter
#                for cell in column:
#                    try:
#                        if len(str(cell.value)) > max_length:
#                            max_length = len(str(cell.value))
#                    except:
#                        pass
#                adjusted_width = min(max_length + 2, 30)
#                worksheet.column_dimensions[column_letter].width = adjusted_width
#        
#        output.seek(0)
#        
#        return send_file(
#            output,
#            as_attachment=True,
#            download_name=f'relatorio_brewfather_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
#            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
#        )
#        
#    except Exception as e:
#        return jsonify({'success': False, 'error': str(e)}), 500


@brewfather_bp.route('/brewfather/exportar-relatorio', methods=['POST'])
@login_required
def exportar_relatorio_brewfather():
    """Exporta relatório para Excel"""
    try:
        dados = request.json.get('dados', [])
        if not dados:
            return jsonify({'success': False, 'error': 'Nenhum dado para exportar'}), 400
        
        # Criar DataFrame
        df = pd.DataFrame(dados)
        
        # Remover colunas desnecessárias para o Excel
        colunas_para_remover = ['brewfather_id', 'recipe_id', 'notes']
        colunas_finais = [col for col in df.columns if col not in colunas_para_remover]
        df = df[colunas_finais]
        
        # Renomear colunas para português
        mapeamento_colunas = {
            'recipe_name': 'Receita',
            'batch_no': 'Número do Lote',
            'status': 'Status',
            'brew_date': 'Data da Brassagem',
            'estimated_og': 'OG Estimada',
            'measured_og': 'OG Medida',
            'estimated_fg': 'FG Estimada',
            'measured_fg': 'FG Medida',
            'estimated_abv': 'ABV Estimado (%)',
            'measured_abv': 'ABV Medido (%)',
            'estimated_ibu': 'IBU Estimado',
            'measured_ibu': 'IBU Medido',
            'estimated_color': 'Cor Estimada (EBC)',
            'measured_color': 'Cor Medida (EBC)',
            'batch_size': 'Tamanho do Lote (L)',
            'efficiency': 'Eficiência (%)',
            'rating': 'Avaliação',
            'style': 'Estilo'
        }
        
        df = df.rename(columns=mapeamento_colunas)
        
        # Formatar datas
        if 'Data da Brassagem' in df.columns:
            df['Data da Brassagem'] = pd.to_datetime(df['Data da Brassagem']).dt.strftime('%d/%m/%Y')
        
        # Criar arquivo em memória
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Relatório_Lotes', index=False)
            
            # Ajustar largura das colunas
            worksheet = writer.sheets['Relatório_Lotes']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 30)
                worksheet.column_dimensions[column_letter].width = adjusted_width
            
            # Adicionar formatação condicional para eficiência
            for row in range(2, len(df) + 2):
                cell_ref = f'P{row}'  # Coluna da eficiência
                worksheet.conditional_formatting.add(
                    cell_ref,
                    openpyxl.formatting.rule.ColorScaleRule(
                        start_type='num', start_value=50, start_color='FF0000',  # Vermelho para baixa eficiência
                        mid_type='num', mid_value=70, mid_color='FFFF00',       # Amarelo para média
                        end_type='num', end_value=90, end_color='00FF00'        # Verde para alta eficiência
                    )
                )
        
        output.seek(0)
        
        return send_file(
            output,
            as_attachment=True,
            download_name=f'relatorio_brewfather_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        print(f"Erro ao exportar relatório: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
    
    

def calcular_resumo_lotes(lotes):
    """Calcula resumo estatístico dos lotes"""
    if not lotes:
        return {
            'total_lotes': 0,
            'lotes_concluidos': 0,
            'abv_medio': 0,
            'ibu_medio': 0,
            'eficiencia_media': 0,
            'batchs_ativos': 0,
            'abv_estimado': 0,
            'ibu_estimado': 0
        }
    
    lotes_concluidos = [l for l in lotes if l.status == 'Completed']
    batchs_ativos = [l for l in lotes if l.status in ['Brewing', 'Fermenting', 'Conditioning']]
    
    # ABV médio (usar medido quando disponível)
    abv_total = sum(l.measured_abv or l.estimated_abv for l in lotes if l.measured_abv or l.estimated_abv)
    abv_count = sum(1 for l in lotes if l.measured_abv or l.estimated_abv)
    abv_medio = round(abv_total / abv_count, 1) if abv_count > 0 else 0
    # IBU médio
    ibu_total = sum(l.measured_ibu or l.estimated_ibu for l in lotes if l.measured_ibu or l.estimated_ibu)
    ibu_count = sum(1 for l in lotes if l.measured_ibu or l.estimated_ibu)
    ibu_medio = round(ibu_total / ibu_count, 0) if ibu_count > 0 else 0
    
    # Eficiência média
    eficiencia_total = sum(l.efficiency for l in lotes if l.efficiency)
    eficiencia_count = sum(1 for l in lotes if l.efficiency)
    eficiencia_media = round(eficiencia_total / eficiencia_count, 1) if eficiencia_count > 0 else 0
    
    # Valores estimados médios
    abv_estimado = round(sum(l.estimated_abv for l in lotes if l.estimated_abv) / len(lotes), 1)
    ibu_estimado = round(sum(l.estimated_ibu for l in lotes if l.estimated_ibu) / len(lotes), 0)
    
    return {
        'total_lotes': len(lotes),
        'lotes_concluidos': len(lotes_concluidos),
        'abv_medio': abv_medio,
        'ibu_medio': ibu_medio,
        'eficiencia_media': eficiencia_media,
        'batchs_ativos': len(batchs_ativos),
        'abv_estimado': abv_estimado,
        'ibu_estimado': ibu_estimado
    }