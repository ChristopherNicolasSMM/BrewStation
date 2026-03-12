"""
Serviço para gerenciar configurações de equipamentos (Plants).

Uma Plant representa um conjunto físico de sensores e atuadores
mapeados para funções lógicas (temperatura, vazão, etc).
"""

import json
import logging
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from db.database import db
from plugins.plugin_mash_control.utils.model_loader import get_plant

logger = logging.getLogger(__name__)


class PlantService:
    """Serviço para gerenciar Plants (equipamentos de brassagem)."""
    
    def __init__(self):
        """Inicializa o serviço."""
        pass
    
    def create_plant(self, name: str, description: str = "", device_roles: Optional[Dict[str, str]] = None, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Cria uma nova Plant.
        
        Args:
            name: Nome da planta
            description: Descrição opcional
            device_roles: Mapeamento {role_name: device_id} (ex: {temperature_sensor: dev_001})
            user_id: ID do usuário proprietário
            
        Returns:
            Dicionário com dados da plant criada, ou None em caso de erro
        """
        try:
            Plant = get_plant()
            if not Plant:
                logger.error("Modelo Plant não está disponível")
                return None
            
            plant_id = str(uuid.uuid4())
            
            # Converter device_roles para JSON
            device_roles_json = json.dumps(device_roles or {})
            
            plant = Plant(
                id=plant_id,
                name=name,
                description=description,
                device_roles=device_roles_json,
                user_id=user_id,
                is_active=True
            )
            
            db.session.add(plant)
            db.session.commit()
            
            logger.info(f"Plant criada: {plant_id} ({name})")
            return plant.to_dict()
        except Exception as e:
            logger.error(f"Erro ao criar plant: {e}", exc_info=True)
            db.session.rollback()
            return None
    
    def get_plant(self, plant_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém uma plant pelo ID.
        
        Args:
            plant_id: ID da plant
            
        Returns:
            Dicionário com dados da plant, ou None se não encontrada
        """
        try:
            Plant = get_plant()
            if not Plant:
                return None
            
            plant = db.session.query(Plant).filter_by(id=plant_id).first()
            if plant:
                return plant.to_dict()
            return None
        except Exception as e:
            logger.error(f"Erro ao obter plant: {e}", exc_info=True)
            return None
    
    def list_plants(self, user_id: Optional[int] = None, is_active: bool = True) -> List[Dict[str, Any]]:
        """
        Lista todas as plants.
        
        Args:
            user_id: Filtrar por usuário (opcional)
            is_active: Incluir apenas plantas ativas
            
        Returns:
            Lista de plantas
        """
        try:
            Plant = get_plant()
            if not Plant:
                return []
            
            query = db.session.query(Plant)
            
            if user_id:
                query = query.filter_by(user_id=user_id)
            
            if is_active:
                query = query.filter_by(is_active=True)
            
            plants = query.all()
            return [plant.to_dict() for plant in plants]
        except Exception as e:
            logger.error(f"Erro ao listar plants: {e}", exc_info=True)
            return []
    
    def update_plant(self, plant_id: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Atualiza uma plant.
        
        Args:
            plant_id: ID da plant
            name: Nome (opcional)
            description: Descrição (opcional)
            device_roles: Mapeamento dispositivos (opcional)
            is_active: Ativar/desativar (opcional)
            
        Returns:
            Dicionário com dados atualizados, ou None em caso de erro
        """
        try:
            Plant = get_plant()
            if not Plant:
                return None
            
            plant = db.session.query(Plant).filter_by(id=plant_id).first()
            if not plant:
                logger.warning(f"Plant não encontrada: {plant_id}")
                return None
            
            # Atualizar campos
            if 'name' in kwargs:
                plant.name = kwargs['name']
            
            if 'description' in kwargs:
                plant.description = kwargs['description']
            
            if 'device_roles' in kwargs:
                device_roles = kwargs['device_roles']
                plant.device_roles = json.dumps(device_roles) if isinstance(device_roles, dict) else device_roles
            
            if 'is_active' in kwargs:
                plant.is_active = kwargs['is_active']
            
            # Atualizar timestamp
            plant.updated_at = datetime.now()
            
            db.session.commit()
            logger.info(f"Plant atualizada: {plant_id}")
            return plant.to_dict()
        except Exception as e:
            logger.error(f"Erro ao atualizar plant: {e}", exc_info=True)
            db.session.rollback()
            return None
    
    def delete_plant(self, plant_id: str) -> bool:
        """
        Deleta uma plant.
        
        Args:
            plant_id: ID da plant
            
        Returns:
            True se deletada, False caso contrário
        """
        try:
            Plant = get_plant()
            if not Plant:
                return False
            
            plant = db.session.query(Plant).filter_by(id=plant_id).first()
            if not plant:
                logger.warning(f"Plant não encontrada: {plant_id}")
                return False
            
            db.session.delete(plant)
            db.session.commit()
            logger.info(f"Plant deletada: {plant_id}")
            return True
        except Exception as e:
            logger.error(f"Erro ao deletar plant: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def assign_role(self, plant_id: str, role: str, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Atribui um dispositivo a uma função lógica na plant.
        
        Args:
            plant_id: ID da plant
            role: Nome da função (ex: 'temperature_sensor', 'heater')
            device_id: ID do dispositivo
            
        Returns:
            Dicionário com device_roles atualizado, ou None em caso de erro
        """
        try:
            plant_dict = self.get_plant(plant_id)
            if not plant_dict:
                logger.warning(f"Plant não encontrada: {plant_id}")
                return None
            
            device_roles = plant_dict.get('device_roles', {})
            device_roles[role] = device_id
            
            return self.update_plant(plant_id, device_roles=device_roles)
        except Exception as e:
            logger.error(f"Erro ao atribuir role: {e}", exc_info=True)
            return None
    
    def resolve_device(self, plant_id: str, role: str) -> Optional[str]:
        """
        Resolve qual dispositivo está atribuído a uma função.
        
        Args:
            plant_id: ID da plant
            role: Nome da função
            
        Returns:
            ID do dispositivo, ou None se não atribuído
        """
        try:
            plant_dict = self.get_plant(plant_id)
            if not plant_dict:
                return None
            
            device_roles = plant_dict.get('device_roles', {})
            return device_roles.get(role)
        except Exception as e:
            logger.error(f"Erro ao resolver dispositivo: {e}", exc_info=True)
            return None