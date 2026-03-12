"""
Serviço para gerenciar Receitas de Cerveja.

Uma Receita contém informações completas sobre ingredientes,
etapas de infusão e parâmetros de brassagem.
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from db.database import db
from plugins.plugin_mash_control.utils.model_loader import get_recipe

logger = logging.getLogger(__name__)


class RecipeService:
    """Serviço para gerenciar Recipes (receitas de cerveja)."""
    
    def __init__(self):
        """Inicializa o serviço."""
        pass
    
    def create_recipe(self, name: str, description: str = "", style: str = "", 
                     original_gravity: int = 50, final_gravity: int = 10,
                     ibu: int = 0, volume: int = 20, boil_time: int = 60,
                     ingredients: Optional[Dict] = None,
                     mash_steps: Optional[List[Dict]] = None,
                     boil_additions: Optional[List[Dict]] = None,
                     plant_id: Optional[str] = None, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Cria uma nova Receita.
        
        Args:
            name: Nome da receita
            description: Descrição opcional
            style: Estilo de cerveja (IPA, Stout, Pilsner, etc)
            original_gravity: OG em pontos (50 = 1.050)
            final_gravity: FG em pontos (10 = 1.010)
            ibu: International Bitterness Units
            volume: Volume a produzir (litros)
            boil_time: Tempo de fervura (minutos)
            ingredients: Dict com {grains: [], hops: [], yeast: {}, misc: []}
            mash_steps: Lista de dicts com {name, temperature, duration}
            boil_additions: Lista de dicts com {ingredient, time, type}
            plant_id: ID da plant específica
            user_id: ID do usuário proprietário
            
        Returns:
            Dicionário com dados da receita criada, ou None em caso de erro
        """
        try:
            Recipe = get_recipe()
            if not Recipe:
                logger.error("Modelo Recipe não está disponível")
                return None
            
            recipe_id = str(uuid.uuid4())
            
            # Converter estruturas complexas para JSON
            ingredients_json = json.dumps(ingredients or {
                'grains': [],
                'hops': [],
                'yeast': {},
                'misc': []
            })
            mash_steps_json = json.dumps(mash_steps or [])
            boil_additions_json = json.dumps(boil_additions or [])
            
            recipe = Recipe(
                id=recipe_id,
                name=name.strip(),
                description=description,
                style=style,
                original_gravity=original_gravity,
                final_gravity=final_gravity,
                ibu=ibu,
                volume=volume,
                boil_time=boil_time,
                ingredients=ingredients_json,
                mash_steps=mash_steps_json,
                boil_additions=boil_additions_json,
                plant_id=plant_id,
                user_id=user_id,
                is_active=True
            )
            
            db.session.add(recipe)
            db.session.commit()
            
            logger.info(f"Receita criada: {recipe_id} - {name}")
            return recipe.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao criar receita: {str(e)}")
            return None
    
    def get_recipe(self, recipe_id: str) -> Optional[Dict[str, Any]]:
        """Obtém uma receita pelo ID."""
        try:
            Recipe = get_recipe()
            if not Recipe:
                return None
            
            recipe = db.session.query(Recipe).filter(Recipe.id == recipe_id).first()
            if recipe:
                return recipe.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Erro ao obter receita {recipe_id}: {str(e)}")
            return None
    
    def list_recipes(self, user_id: Optional[int] = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """
        Lista receitas com filtros opcionais.
        
        Args:
            user_id: Filtrar por usuário (opcional)
            is_active: Filtrar por status ativo (padrão: True)
            
        Returns:
            Lista de dicionários com receitas
        """
        try:
            Recipe = get_recipe()
            if not Recipe:
                return []
            
            query = db.session.query(Recipe)
            
            if user_id:
                query = query.filter(Recipe.user_id == user_id)
            
            query = query.filter(Recipe.is_active == is_active)
            query = query.order_by(Recipe.created_at.desc())
            
            recipes = query.all()
            return [recipe.to_dict() for recipe in recipes]
            
        except Exception as e:
            logger.error(f"Erro ao listar receitas: {str(e)}")
            return []
    
    def update_recipe(self, recipe_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Atualiza uma receita existente.
        
        Args:
            recipe_id: ID da receita
            **kwargs: Campos a atualizar (name, description, original_gravity, etc)
            
        Returns:
            Dicionário atualizado ou None em caso de erro
        """
        try:
            Recipe = get_recipe()
            if not Recipe:
                return None
            
            recipe = db.session.query(Recipe).filter(Recipe.id == recipe_id).first()
            if not recipe:
                logger.warning(f"Receita não encontrada: {recipe_id}")
                return None
            
            # Mapear campos complexos para JSON
            complex_fields = ['ingredients', 'mash_steps', 'boil_additions']
            
            for key, value in kwargs.items():
                if key in complex_fields and isinstance(value, (dict, list)):
                    # Converter para JSON string
                    setattr(recipe, key, json.dumps(value))
                elif hasattr(recipe, key):
                    setattr(recipe, key, value)
            
            recipe.updated_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Receita atualizada: {recipe_id}")
            return recipe.to_dict()
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar receita {recipe_id}: {str(e)}")
            return None
    
    def delete_recipe(self, recipe_id: str, hard_delete: bool = False) -> bool:
        """
        Deleta uma receita (soft ou hard delete).
        
        Args:
            recipe_id: ID da receita
            hard_delete: Se True, deleta permanentemente. Se False, apenas marca como inativa.
            
        Returns:
            True se sucesso, False se erro
        """
        try:
            Recipe = get_recipe()
            if not Recipe:
                return False
            
            recipe = db.session.query(Recipe).filter(Recipe.id == recipe_id).first()
            if not recipe:
                logger.warning(f"Receita não encontrada para deletar: {recipe_id}")
                return False
            
            if hard_delete:
                db.session.delete(recipe)
            else:
                recipe.is_active = False
                recipe.updated_at = datetime.utcnow()
            
            db.session.commit()
            logger.info(f"Receita deletada: {recipe_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao deletar receita {recipe_id}: {str(e)}")
            return False
    
    def calculate_abv(self, original_gravity: int, final_gravity: int) -> float:
        """
        Calcula o ABV (Alcohol By Volume).
        
        ABV = (OG - FG) * 131.25
        Os valores devem estar em pontos (ex: 50 = 1.050)
        
        Args:
            original_gravity: OG em pontos
            final_gravity: FG em pontos
            
        Returns:
            ABV calculado
        """
        og = 1.0 + (original_gravity / 1000.0)
        fg = 1.0 + (final_gravity / 1000.0)
        return max(0, (og - fg) * 131.25)
    
    def update_mash_steps(self, recipe_id: str, mash_steps: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Atualiza apenas os mash steps de uma receita.
        
        Args:
            recipe_id: ID da receita
            mash_steps: Lista de steps [{name, temperature, duration}, ...]
            
        Returns:
            Receita atualizada ou None
        """
        return self.update_recipe(recipe_id, mash_steps=mash_steps)
    
    def update_ingredients(self, recipe_id: str, ingredients: Dict) -> Optional[Dict[str, Any]]:
        """
        Atualiza apenas os ingredientes de uma receita.
        
        Args:
            recipe_id: ID da receita
            ingredients: Dict com {grains, hops, yeast, misc}
            
        Returns:
            Receita atualizada ou None
        """
        return self.update_recipe(recipe_id, ingredients=ingredients)
    
    def clone_recipe(self, recipe_id: str, new_name: str, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Clona uma receita existente com novo nome.
        
        Args:
            recipe_id: ID da receita para clonar
            new_name: Nome da nova receita
            user_id: ID do novo proprietário (opcional)
            
        Returns:
            Nova receita ou None em caso de erro
        """
        try:
            original = self.get_recipe(recipe_id)
            if not original:
                logger.warning(f"Receita original não encontrada: {recipe_id}")
                return None
            
            # Preparar dados para nova receita
            new_recipe_data = {
                'name': new_name,
                'description': original['description'],
                'style': original['style'],
                'original_gravity': original['original_gravity'],
                'final_gravity': original['final_gravity'],
                'ibu': original['ibu'],
                'volume': original['volume'],
                'boil_time': original['boil_time'],
                'ingredients': original['ingredients'],
                'mash_steps': original['mash_steps'],
                'boil_additions': original['boil_additions'],
                'plant_id': original['plant_id'],
                'user_id': user_id or original['user_id']
            }
            
            cloned = self.create_recipe(**new_recipe_data)
            if cloned:
                logger.info(f"Receita clonada: {recipe_id} -> {cloned['id']}")
            return cloned
            
        except Exception as e:
            logger.error(f"Erro ao clonar receita {recipe_id}: {str(e)}")
            return None
