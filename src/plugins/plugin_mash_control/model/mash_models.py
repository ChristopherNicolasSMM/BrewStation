"""
Modelos SQLAlchemy para o plugin Mash Control.

IMPORTANTE:
- O __tablename__ será automaticamente prefixado pelo sistema
- Prefixo atual: "mash_ctrl_" (definido em install.json)
- Use model_loader nas rotas API para garantir que o modelo prefixado seja usado
"""

import json

from sqlalchemy import (Boolean, Column, DateTime, ForeignKey, Integer, String,
                        Text)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from db.database import db


class MashRecipe(db.Model):
    """
    Modelo para armazenar perfis de brassagem reutilizáveis.
    
    Receitas completas são armazenadas em JSON no campo recipe_data.
    Metadados e relações são armazenados no banco de dados.
    """
    __tablename__ = 'mash_recipe'  # Será prefixado para "mash_ctrl_mash_recipe"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    recipe_data = Column(Text)  # JSON string com estrutura completa da receita
    equipment_mapping = Column(Text)  # JSON string com mapeamento dispositivo → função
    brewfather_recipe_id = Column(String(100), nullable=True)  # ID da receita no BrewFather
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos
    sessions = relationship('BrewSession', backref='recipe', lazy='dynamic')
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        recipe_data_dict = None
        equipment_mapping_dict = None
        
        try:
            if self.recipe_data:
                recipe_data_dict = json.loads(self.recipe_data)
        except (json.JSONDecodeError, TypeError):
            recipe_data_dict = {}
        
        try:
            if self.equipment_mapping:
                equipment_mapping_dict = json.loads(self.equipment_mapping)
        except (json.JSONDecodeError, TypeError):
            equipment_mapping_dict = {}
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'recipe_data': recipe_data_dict,
            'equipment_mapping': equipment_mapping_dict,
            'brewfather_recipe_id': self.brewfather_recipe_id,
            'created_by': self.created_by,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MashRecipe(id={self.id}, name="{self.name}")>'


class BrewSession(db.Model):
    """
    Modelo para registrar execuções de receitas.
    
    Logs detalhados e telemetria são armazenados em JSON no campo session_data.
    Metadados e status são armazenados no banco de dados.
    """
    __tablename__ = 'brew_session'  # Será prefixado para "mash_ctrl_brew_session"
    
    id = Column(String(36), primary_key=True)
    recipe_id = Column(String(36), ForeignKey('mash_recipe.id'), nullable=False)  # Prefixo será aplicado automaticamente
    plant_id = Column(String(36), ForeignKey('plant.id'), nullable=True)  # Plant usada (opcional, compatibilidade retroativa)
    name = Column(String(100), nullable=False)
    status = Column(String(20), default='pending')  # pending/running/paused/completed/error
    current_step = Column(Integer, default=0)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    session_data = Column(Text)  # JSON string com logs, telemetria, eventos
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    equipment_used = Column(Text)  # JSON string com lista de dispositivos usados
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        session_data_dict = None
        equipment_used_list = None
        
        try:
            if self.session_data:
                session_data_dict = json.loads(self.session_data)
        except (json.JSONDecodeError, TypeError):
            session_data_dict = {}
        
        try:
            if self.equipment_used:
                equipment_used_list = json.loads(self.equipment_used)
        except (json.JSONDecodeError, TypeError):
            equipment_used_list = []
        
        return {
            'id': self.id,
            'recipe_id': self.recipe_id,
            'plant_id': self.plant_id,
            'name': self.name,
            'status': self.status,
            'current_step': self.current_step,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'session_data': session_data_dict,
            'user_id': self.user_id,
            'equipment_used': equipment_used_list,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<BrewSession(id={self.id}, name="{self.name}", status="{self.status}")>'


class DashboardLayout(db.Model):
    """
    Modelo para salvar configurações visuais do dashboard.
    
    Layouts completos são armazenados em JSON no campo layout_data.
    Metadados são armazenados no banco de dados.
    """
    __tablename__ = 'dashboard_layout'  # Será prefixado para "mash_ctrl_dashboard_layout"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    layout_data = Column(Text)  # JSON string com posicionamento SVG, dispositivos vinculados
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        layout_data_dict = None
        
        try:
            if self.layout_data:
                layout_data_dict = json.loads(self.layout_data)
        except (json.JSONDecodeError, TypeError):
            layout_data_dict = {}
        
        return {
            'id': self.id,
            'name': self.name,
            'user_id': self.user_id,
            'layout_data': layout_data_dict,
            'is_default': self.is_default,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DashboardLayout(id={self.id}, name="{self.name}", is_default={self.is_default})>'


class Plant(db.Model):
    """
    Modelo para configurações de equipamentos de brassagem.
    
    Cada Plant representa um sistema físico com sensores e atuadores
    mapeados para funções lógicas (temperatura, vazão, etc).
    
    Configurações de dispositivos são armazenadas em JSON no campo device_roles.
    """
    __tablename__ = 'plant'  # Será prefixado para "mash_ctrl_plant"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    device_roles = Column(Text)  # JSON string com mapeamento {role: device_id, ...}
    # Exemplo: {"temperature_sensor": "dev_001", "heater": "dev_002", "pump": "dev_003"}
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        device_roles_dict = None
        
        try:
            if self.device_roles:
                device_roles_dict = json.loads(self.device_roles)
        except (json.JSONDecodeError, TypeError):
            device_roles_dict = {}
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'device_roles': device_roles_dict,
            'user_id': self.user_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Plant(id={self.id}, name="{self.name}", is_active={self.is_active})>'


class Recipe(db.Model):
    """
    Modelo para receitas de cerveja.
    
    Armazena informações completas sobre receitas de cerveja incluindo
    ingredientes, etapas de infusão e parâmetros de brassagem.
    
    - ingredients: JSON com {grains: [...], hops: [...], yeast: {...}, misc: [...]}
    - mash_steps: JSON com [{name, temperature, duration}, ...]
    - boil_additions: JSON com [{ingredient, time, type}, ...]
    """
    __tablename__ = 'recipe'  # Será prefixado para "mash_ctrl_recipe"
    
    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    style = Column(String(50), nullable=True)  # IPA, Stout, Pilsner, etc
    original_gravity = Column(Integer, default=0)  # em pontos (ex: 50 = 1.050)
    final_gravity = Column(Integer, default=0)    # em pontos (ex: 10 = 1.010)
    ibu = Column(Integer, default=0)  # International Bitterness Units
    volume = Column(Integer, default=20)  # litros
    ingredients = Column(Text)  # JSON com grains, hops, yeast, misc
    mash_steps = Column(Text)  # JSON com etapas de infusão [{name, temp_c, duration_min}, ...]
    boil_additions = Column(Text)  # JSON com adições no bolo [{name, time_min}, ...]
    boil_time = Column(Integer, default=60)  # minutos
    plant_id = Column(String(36), ForeignKey('plant.id'), nullable=True)  # Plant específica
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Converte o modelo para dicionário."""
        ingredients_dict = {}
        mash_steps_list = []
        boil_additions_list = []
        
        try:
            if self.ingredients:
                ingredients_dict = json.loads(self.ingredients)
        except (json.JSONDecodeError, TypeError):
            ingredients_dict = {'grains': [], 'hops': [], 'yeast': {}, 'misc': []}
        
        try:
            if self.mash_steps:
                mash_steps_list = json.loads(self.mash_steps)
        except (json.JSONDecodeError, TypeError):
            mash_steps_list = []
        
        try:
            if self.boil_additions:
                boil_additions_list = json.loads(self.boil_additions)
        except (json.JSONDecodeError, TypeError):
            boil_additions_list = []
        
        # Calcular ABV: (OG - FG) * 131.25
        # OG e FG estão em pontos, converter para densidade (1.050 = 50)
        og = 1.0 + (self.original_gravity / 1000.0)
        fg = 1.0 + (self.final_gravity / 1000.0)
        abv = max(0, (og - fg) * 131.25)
        
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'style': self.style,
            'original_gravity': self.original_gravity,
            'final_gravity': self.final_gravity,
            'ibu': self.ibu,
            'abv': round(abv, 2),
            'volume': self.volume,
            'ingredients': ingredients_dict,
            'mash_steps': mash_steps_list,
            'boil_additions': boil_additions_list,
            'boil_time': self.boil_time,
            'plant_id': self.plant_id,
            'user_id': self.user_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Recipe(id={self.id}, name="{self.name}", style="{self.style}")>'

