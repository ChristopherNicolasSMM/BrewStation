"""
Modelo de funções de dispositivos IoT.

Define funções que podem ser atribuídas a portas de devices.
Funções podem ser pré-definidas (do sistema) ou customizadas pelo usuário.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float
from sqlalchemy.sql import func
from db.database import db


class DeviceFunction(db.Model):
    """
    Funções de dispositivos IoT.
    
    Define funções que podem ser associadas a portas de devices.
    Funções pré-definidas são criadas automaticamente na instalação.
    Funções customizadas podem ser criadas pelo usuário.
    """
    __tablename__ = 'device_function'  # Será prefixado automaticamente para dvmanage_device_function
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)  # sensor, actuator, hybrid
    unit = Column(String(20))  # °C, %, V, bar, etc.
    data_type = Column(String(20), nullable=False, default='float')  # float, int, bool, string
    min_value = Column(Float)
    max_value = Column(Float)
    is_predefined = Column(Boolean, default=False, nullable=False)  # True para funções do sistema
    icon = Column(String(50))  # Bootstrap icon class
    created_at = Column(DateTime, default=func.now())
    
    def to_dict(self):
        """
        Converte o modelo para dicionário.
        
        Útil para retornar dados em APIs JSON.
        """
        return {
            'id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'description': self.description,
            'category': self.category,
            'unit': self.unit,
            'data_type': self.data_type,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'is_predefined': self.is_predefined,
            'icon': self.icon,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<DeviceFunction(id={self.id}, name="{self.name}", category={self.category})>'
