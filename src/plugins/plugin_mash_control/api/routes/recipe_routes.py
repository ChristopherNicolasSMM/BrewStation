"""
Rotas API para gerenciamento de receitas.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required

from plugins.plugin_mash_control.services.device_integration import \
    DeviceIntegrationService
from plugins.plugin_mash_control.services.recipe_editor import \
    RecipeEditorService

recipe_bp = Blueprint('plugin_mash_control_recipe_api', __name__)


def get_recipe_editor():
    """Obtém instância do RecipeEditorService."""
    try:
        from flask import current_app
        if hasattr(current_app, 'plugin_manager'):
            plugin_manager = current_app.plugin_manager
            # Tentar buscar pelo nome do diretório primeiro
            plugin = plugin_manager.get_plugin('plugin_mash_control')
            if not plugin:
                # Tentar pelo nome do plugin
                plugin = plugin_manager.get_plugin('mash_control')
            if plugin:
                return RecipeEditorService(plugin.plugin_path)
        # Fallback: usar caminho padrão
        from pathlib import Path
        plugin_path = Path(__file__).parent.parent.parent
        return RecipeEditorService(plugin_path)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao obter RecipeEditorService: {e}")
        return None


# Rotas de Receitas
@recipe_bp.route('/recipes', methods=['GET'])
@login_required
def list_recipes():
    """Lista receitas."""
    try:
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        filters = {}
        if request.args.get('is_active'):
            filters['is_active'] = request.args.get('is_active') == 'true'
        if request.args.get('brewfather_recipe_id'):
            filters['brewfather_recipe_id'] = request.args.get('brewfather_recipe_id')
        
        recipes = recipe_editor.list_recipes(filters)
        return jsonify(recipes), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes/<recipe_id>', methods=['GET'])
@login_required
def get_recipe(recipe_id):
    """Obtém receita específica."""
    try:
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        recipe = recipe_editor.get_recipe(recipe_id)
        if recipe:
            return jsonify(recipe), 200
        return jsonify({'error': 'Receita não encontrada'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes', methods=['POST'])
@login_required
def create_recipe():
    """Cria nova receita."""
    try:
        data = request.get_json()
        
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        recipe_id = recipe_editor.create_recipe(data)
        
        if recipe_id:
            return jsonify({'id': recipe_id, 'message': 'Receita criada'}), 201
        return jsonify({'error': 'Erro ao criar receita'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes/<recipe_id>', methods=['PUT'])
@login_required
def update_recipe(recipe_id):
    """Atualiza receita."""
    try:
        data = request.get_json()
        
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        if recipe_editor.update_recipe(recipe_id, data):
            return jsonify({'message': 'Receita atualizada'}), 200
        return jsonify({'error': 'Erro ao atualizar receita'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes/<recipe_id>', methods=['DELETE'])
@login_required
def delete_recipe(recipe_id):
    """Remove receita."""
    try:
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        if recipe_editor.delete_recipe(recipe_id):
            return jsonify({'message': 'Receita removida'}), 200
        return jsonify({'error': 'Erro ao remover receita'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes/import/brewfather', methods=['POST'])
@login_required
def import_from_brewfather():
    """Importa receita do BrewFather."""
    try:
        data = request.get_json()
        brewfather_recipe_id = data.get('brewfather_recipe_id')
        
        if not brewfather_recipe_id:
            return jsonify({'error': 'brewfather_recipe_id é obrigatório'}), 400
        
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        recipe_id = recipe_editor.import_from_brewfather(brewfather_recipe_id)
        
        if recipe_id:
            return jsonify({'id': recipe_id, 'message': 'Receita importada do BrewFather'}), 201
        return jsonify({'error': 'Erro ao importar receita'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes/brewfather/list', methods=['GET'])
@login_required
def list_brewfather_recipes():
    """Lista receitas disponíveis no BrewFather."""
    try:
        # Verificar se plugin integ_bFather está disponível
        from flask import current_app
        plugin_manager = current_app.plugin_manager
        brewfather_plugin = plugin_manager.get_plugin('integ_bFather')
        
        if not brewfather_plugin or not brewfather_plugin.is_active:
            return jsonify({'error': 'Plugin integ_bFather não está disponível'}), 500
        
        # Obter receitas do BrewFather
        from plugins.plugin_integ_bFather.utils.model_loader import \
            BrewFatherRecipe
        
        recipes = BrewFatherRecipe.query.filter_by(is_active=True).order_by(BrewFatherRecipe.name).all()
        
        recipes_data = [{
            'brewfather_id': r.brewfather_id,
            'name': r.name,
            'style': r.style,
            'abv': r.abv,
            'ibu': r.ibu
        } for r in recipes]
        
        return jsonify(recipes_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes/<recipe_id>/validate', methods=['POST'])
@login_required
def validate_recipe(recipe_id):
    """Valida receita."""
    try:
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        recipe = recipe_editor.get_recipe(recipe_id)
        if not recipe:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        # Validar estrutura
        is_valid = recipe_editor.validate_recipe(recipe)
        
        # Validar equipamento
        device_integration = DeviceIntegrationService()
        available_devices = device_integration.get_available_devices() if device_integration.is_available() else []
        
        equipment_validation = recipe_editor.validate_equipment(recipe, available_devices)
        
        return jsonify({
            'valid': is_valid and equipment_validation.get('valid', False),
            'structure_valid': is_valid,
            'equipment_validation': equipment_validation
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@recipe_bp.route('/recipes/<recipe_id>/timeline', methods=['GET'])
@login_required
def get_recipe_timeline(recipe_id):
    """Calcula timeline da receita."""
    try:
        recipe_editor = get_recipe_editor()
        if not recipe_editor:
            return jsonify({'error': 'Serviço não disponível'}), 500
        
        recipe = recipe_editor.get_recipe(recipe_id)
        if not recipe:
            return jsonify({'error': 'Receita não encontrada'}), 404
        
        timeline = recipe_editor.calculate_timeline(recipe)
        return jsonify(timeline), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

