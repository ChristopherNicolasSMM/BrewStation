# routes/brewfather_routes.py
from flask import Blueprint, request, jsonify
from db.database import db
from model.brewfather import BrewFatherService, BrewFatherRecipe, BrewFatherBatch, BrewFatherInventory
from model.config import Configuracao

brewfather_bp = Blueprint('brewfather', __name__)

@brewfather_bp.route('/brewfather/status')
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
def sync_recipes():
    """Sincroniza receitas do BrewFather"""
    result = BrewFatherService.sync_recipes()
    return jsonify(result)

@brewfather_bp.route('/brewfather/sync/batches', methods=['POST'])
def sync_batches():
    """Sincroniza lotes do BrewFather"""
    result = BrewFatherService.sync_batches()
    return jsonify(result)

@brewfather_bp.route('/brewfather/sync/inventory', methods=['POST'])
def sync_inventory():
    """Sincroniza estoque do BrewFather"""
    result = BrewFatherService.sync_inventory()
    return jsonify(result)

@brewfather_bp.route('/brewfather/sync/all', methods=['POST'])
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
    print(results)
    
    return jsonify(results)

@brewfather_bp.route('/brewfather/recipes')
def get_recipes():
    """Obtém receitas sincronizadas"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = BrewFatherRecipe.query
    
    if search:
        query = query.filter(BrewFatherRecipe.name.ilike(f'%{search}%'))
    
    recipes = query.order_by(BrewFatherRecipe.name)\
        .paginate(page=page, per_page=per_page, error_out=False)
    
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
def get_batches():
    """Obtém lotes sincronizados"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
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
def get_inventory():
    """Obtém estoque sincronizado"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
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