"""
Modelos SQLAlchemy para o plugin Mash Control.

IMPORTANTE:
- O __tablename__ será automaticamente prefixado pelo sistema
- Prefixo atual: "mash_ctrl_" (definido em install.json)
- Use model_loader nas rotas API para garantir que o modelo prefixado seja usado
"""

import json
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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

