"""
Modelo de dados para plugins.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from db.database import db


class Plugin(db.Model):
    """Modelo para plugins instalados"""
    __tablename__ = 'plugins'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    author = Column(String(200), nullable=True)
    is_active = Column(Boolean, default=False)
    is_installed = Column(Boolean, default=False)
    install_date = Column(DateTime, default=func.now())
    config_json = Column(JSON, nullable=True)  # Configuração do plugin
    dependencies = Column(JSON, nullable=True)  # Lista de dependências
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Plugin {self.name} v{self.version}>'
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'is_active': self.is_active,
            'is_installed': self.is_installed,
            'install_date': self.install_date.isoformat() if self.install_date else None,
            'config_json': self.config_json,
            'dependencies': self.dependencies,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

