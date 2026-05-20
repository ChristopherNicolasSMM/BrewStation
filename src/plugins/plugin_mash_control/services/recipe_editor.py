"""
Serviço de edição e gerenciamento de receitas.

Gerencia criação, edição, validação e importação de receitas do BrewFather.
"""

import json
import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import current_app

from db.database import db
from plugins.plugin_mash_control.services.device_integration import \
    DeviceIntegrationService
from plugins.plugin_mash_control.utils.model_loader import get_mash_recipe

logger = logging.getLogger(__name__)


class RecipeEditorService:
    """
    Serviço para edição e gerenciamento de receitas.
    
    Gerencia criação, edição, validação, importação do BrewFather e
    exportação de receitas.
    """
    
    def __init__(self, plugin_path: Path):
        """
        Inicializa o serviço de edição de receitas.
        
        Args:
            plugin_path: Caminho do diretório do plugin
        """
        self.plugin_path = plugin_path
        self.recipes_path = plugin_path / "data" / "recipes"
        self.recipes_path.mkdir(parents=True, exist_ok=True)
        self.device_integration = DeviceIntegrationService()
    
    def create_recipe(self, recipe_data: Dict[str, Any]) -> Optional[str]:
        """
        Cria uma nova receita.
        
        Args:
            recipe_data: Dados da receita
            
        Returns:
            ID da receita criada ou None em caso de erro
        """
        try:
            MashRecipe = get_mash_recipe()
            if not MashRecipe:
                return None
            
            # Validar receita
            if not self.validate_recipe(recipe_data):
                logger.error("Receita inválida")
                return None
            
            recipe_id = recipe_data.get('id') or str(uuid.uuid4())
            
            recipe = MashRecipe(
                id=recipe_id,
                name=recipe_data.get('name', 'Nova Receita'),
                description=recipe_data.get('description', ''),
                recipe_data=json.dumps(recipe_data.get('recipe_data', {})),
                equipment_mapping=json.dumps(recipe_data.get('equipment_mapping', {})),
                brewfather_recipe_id=recipe_data.get('brewfather_recipe_id'),
                created_by=current_app.login_manager.current_user.id if hasattr(current_app, 'login_manager') else None,
                is_active=True
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            # Salvar também em JSON
            recipe_file = self.recipes_path / f"{recipe_id}.json"
            with open(recipe_file, 'w', encoding='utf-8') as f:
                json.dump(recipe_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Receita {recipe_id} criada")
            return recipe_id
        except Exception as e:
            logger.error(f"Erro ao criar receita: {e}", exc_info=True)
            db.session.rollback()
            return None
    
    def update_recipe(self, recipe_id: str, updates: Dict[str, Any]) -> bool:
        """
        Atualiza uma receita existente.
        
        Args:
            recipe_id: ID da receita
            updates: Dados a serem atualizados
            
        Returns:
            True se receita foi atualizada
        """
        try:
            MashRecipe = get_mash_recipe()
            if not MashRecipe:
                return False
            
            recipe = MashRecipe.query.get(recipe_id)
            if not recipe:
                return False
            
            # Atualizar campos
            if 'name' in updates:
                recipe.name = updates['name']
            if 'description' in updates:
                recipe.description = updates['description']
            if 'recipe_data' in updates:
                recipe.recipe_data = json.dumps(updates['recipe_data'])
            if 'equipment_mapping' in updates:
                recipe.equipment_mapping = json.dumps(updates['equipment_mapping'])
            if 'is_active' in updates:
                recipe.is_active = updates['is_active']
            
            db.session.commit()
            
            # Atualizar arquivo JSON
            recipe_file = self.recipes_path / f"{recipe_id}.json"
            if recipe_file.exists():
                recipe_dict = recipe.to_dict()
                recipe_dict.update(updates)
                with open(recipe_file, 'w', encoding='utf-8') as f:
                    json.dump(recipe_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Receita {recipe_id} atualizada")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar receita: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def delete_recipe(self, recipe_id: str) -> bool:
        """
        Remove uma receita.
        
        Args:
            recipe_id: ID da receita
            
        Returns:
            True se receita foi removida
        """
        try:
            MashRecipe = get_mash_recipe()
            if not MashRecipe:
                return False
            
            recipe = MashRecipe.query.get(recipe_id)
            if not recipe:
                return False
            
            db.session.delete(recipe)
            db.session.commit()
            
            # Remover arquivo JSON
            recipe_file = self.recipes_path / f"{recipe_id}.json"
            if recipe_file.exists():
                recipe_file.unlink()
            
            logger.info(f"Receita {recipe_id} removida")
            return True
        except Exception as e:
            logger.error(f"Erro ao remover receita: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém uma receita específica.
        
        Args:
            recipe_id: ID da receita
            
        Returns:
            Dados da receita ou None se não encontrada
        """
        try:
            MashRecipe = get_mash_recipe()
            if not MashRecipe:
                return None
            
            recipe = MashRecipe.query.get(recipe_id)
            if not recipe:
                return None
            
            return recipe.to_dict()
        except Exception as e:
            logger.error(f"Erro ao obter receita: {e}", exc_info=True)
            return None
    
    def list_recipes(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Lista receitas com filtros opcionais.
        
        Args:
            filters: Filtros (is_active, brewfather_recipe_id, created_by)
            
        Returns:
            Lista de receitas
        """
        try:
            MashRecipe = get_mash_recipe()
            if not MashRecipe:
                return []
            
            query = MashRecipe.query
            
            if filters:
                if 'is_active' in filters:
                    query = query.filter_by(is_active=filters['is_active'])
                if 'brewfather_recipe_id' in filters:
                    query = query.filter_by(brewfather_recipe_id=filters['brewfather_recipe_id'])
                if 'created_by' in filters:
                    query = query.filter_by(created_by=filters['created_by'])
            
            recipes = query.all()
            return [recipe.to_dict() for recipe in recipes]
        except Exception as e:
            logger.error(f"Erro ao listar receitas: {e}", exc_info=True)
            return []
    
    def import_from_brewfather(self, brewfather_recipe_id: str) -> Optional[str]:
        """
        Importa uma receita do BrewFather via plugin integ_bFather.
        
        Args:
            brewfather_recipe_id: ID da receita no BrewFather
            
        Returns:
            ID da receita importada ou None em caso de erro
        """
        try:
            # Verificar se plugin integ_bFather está disponível
            from flask import current_app
            plugin_manager = current_app.plugin_manager
            brewfather_plugin = plugin_manager.get_plugin('integ_bFather')
            
            if not brewfather_plugin or not brewfather_plugin.is_active:
                logger.error("Plugin integ_bFather não está disponível")
                return None
            
            # Obter receita do BrewFather via API
            from plugins.plugin_integ_bFather.utils.model_loader import \
                BrewFatherRecipe
            
            brewfather_recipe = BrewFatherRecipe.query.filter_by(brewfather_id=brewfather_recipe_id).first()
            if not brewfather_recipe:
                logger.error(f"Receita {brewfather_recipe_id} não encontrada no BrewFather")
                return None
            
            # Converter formato BrewFather para formato mash_control
            mash_recipe_data = self._convert_brewfather_to_mash(brewfather_recipe)
            
            # Criar receita
            mash_recipe_data['brewfather_recipe_id'] = brewfather_recipe_id
            recipe_id = self.create_recipe(mash_recipe_data)
            
            if recipe_id:
                logger.info(f"Receita {brewfather_recipe_id} importada do BrewFather como {recipe_id}")
            
            return recipe_id
        except Exception as e:
            logger.error(f"Erro ao importar receita do BrewFather: {e}", exc_info=True)
            return None
    
    def validate_recipe(self, recipe_data: Dict[str, Any]) -> bool:
        """
        Valida estrutura de uma receita.
        
        Args:
            recipe_data: Dados da receita
            
        Returns:
            True se receita é válida
        """
        try:
            # Validar campos obrigatórios
            if not recipe_data.get('name'):
                logger.error("Nome da receita é obrigatório")
                return False
            
            recipe_structure = recipe_data.get('recipe_data', {})
            if not isinstance(recipe_structure, dict):
                logger.error("recipe_data deve ser um dicionário")
                return False
            
            steps = recipe_structure.get('steps', [])
            if not isinstance(steps, list):
                logger.error("steps deve ser uma lista")
                return False
            
            # Validar cada etapa
            for step in steps:
                if not step.get('type'):
                    logger.error("Tipo da etapa é obrigatório")
                    return False
                if not step.get('name'):
                    logger.error("Nome da etapa é obrigatório")
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Erro ao validar receita: {e}", exc_info=True)
            return False
    
    def validate_equipment(self, recipe_data: Dict[str, Any], available_devices: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Valida se equipamento necessário está disponível.
        
        Args:
            recipe_data: Dados da receita
            available_devices: Lista de dispositivos disponíveis
            
        Returns:
            Dicionário com resultado da validação
        """
        try:
            recipe_data.get('equipment_mapping', {})
            recipe_structure = recipe_data.get('recipe_data', {})
            steps = recipe_structure.get('steps', [])
            
            required_devices = set()
            for step in steps:
                devices = step.get('devices', {})
                required_devices.update(devices.values())
            
            available_device_ids = {device.get('id') for device in available_devices}
            missing_devices = required_devices - available_device_ids
            
            return {
                'valid': len(missing_devices) == 0,
                'missing_devices': list(missing_devices),
                'required_devices': list(required_devices),
                'available_devices': list(available_device_ids)
            }
        except Exception as e:
            logger.error(f"Erro ao validar equipamento: {e}", exc_info=True)
            return {'valid': False, 'error': str(e)}
    
    def calculate_timeline(self, recipe_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Calcula timeline da receita.
        
        Args:
            recipe_data: Dados da receita
            
        Returns:
            Lista de eventos da timeline
        """
        try:
            recipe_structure = recipe_data.get('recipe_data', {})
            steps = recipe_structure.get('steps', [])
            
            timeline = []
            current_time = 0
            
            for step in steps:
                duration = step.get('duration', 0)
                timeline.append({
                    'step_name': step.get('name'),
                    'start_time': current_time,
                    'end_time': current_time + duration,
                    'duration': duration,
                    'target_temp': step.get('target_temp'),
                    'type': step.get('type')
                })
                current_time += duration
            
            return timeline
        except Exception as e:
            logger.error(f"Erro ao calcular timeline: {e}", exc_info=True)
            return []
    
    def export_recipe(self, recipe_id: str, format: str = 'json') -> Optional[str]:
        """
        Exporta receita em formato específico.
        
        Args:
            recipe_id: ID da receita
            format: Formato de exportação (json, xml, etc.)
            
        Returns:
            Caminho do arquivo exportado ou None em caso de erro
        """
        try:
            recipe = self.get_recipe(recipe_id)
            if not recipe:
                return None
            
            if format == 'json':
                export_file = self.recipes_path / f"{recipe_id}_export.json"
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(recipe, f, indent=2, ensure_ascii=False)
                return str(export_file)
            
            return None
        except Exception as e:
            logger.error(f"Erro ao exportar receita: {e}", exc_info=True)
            return None
    
    def _convert_brewfather_to_mash(self, brewfather_recipe) -> Dict[str, Any]:
        """
        Converte receita do BrewFather para formato mash_control.
        
        Args:
            brewfather_recipe: Objeto BrewFatherRecipe
            
        Returns:
            Dados da receita no formato mash_control
        """
        try:
            # Estrutura básica da receita
            recipe_data = {
                'id': str(uuid.uuid4()),
                'name': brewfather_recipe.name,
                'description': f"Receita importada do BrewFather: {brewfather_recipe.style or 'N/A'}",
                'version': '1.0',
                'brewfather_recipe_id': brewfather_recipe.brewfather_id,
                'recipe_data': {
                    'steps': []
                },
                'equipment_mapping': {}
            }
            
            # Converter etapas de mostura (mash steps)
            # Nota: BrewFather pode ter mash steps em formato diferente
            # Aqui fazemos uma conversão básica - em produção, ajustar conforme estrutura real
            
            # Exemplo de conversão (ajustar conforme estrutura real do BrewFather)
            if hasattr(brewfather_recipe, 'mash_steps') and brewfather_recipe.mash_steps:
                mash_steps = json.loads(brewfather_recipe.mash_steps) if isinstance(brewfather_recipe.mash_steps, str) else brewfather_recipe.mash_steps
                
                for step in mash_steps:
                    recipe_data['recipe_data']['steps'].append({
                        'type': 'mash',
                        'name': step.get('name', 'Mash Step'),
                        'target_temp': step.get('stepTemp', 0),
                        'duration': step.get('stepTime', 0),
                        'devices': {},
                        'actions': [
                            {'type': 'set_temperature', 'target': step.get('stepTemp', 0), 'tolerance': 1.0},
                            {'type': 'wait', 'duration': step.get('stepTime', 0)}
                        ]
                    })
            
            # Adicionar etapa de fervura (boil)
            if hasattr(brewfather_recipe, 'boil_time') and brewfather_recipe.boil_time:
                recipe_data['recipe_data']['steps'].append({
                    'type': 'boil',
                    'name': 'Fervura',
                    'target_temp': 100,  # Temperatura de fervura
                    'duration': brewfather_recipe.boil_time,
                    'devices': {},
                    'actions': [
                        {'type': 'set_temperature', 'target': 100, 'tolerance': 2.0},
                        {'type': 'wait', 'duration': brewfather_recipe.boil_time}
                    ]
                })
            
            return recipe_data
        except Exception as e:
            logger.error(f"Erro ao converter receita do BrewFather: {e}", exc_info=True)
            return {
                'id': str(uuid.uuid4()),
                'name': brewfather_recipe.name if hasattr(brewfather_recipe, 'name') else 'Receita Importada',
                'description': 'Erro na conversão',
                'recipe_data': {'steps': []},
                'equipment_mapping': {}
            }

