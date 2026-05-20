"""
Modelo de exemplo para o plugin mash_control.

Este é um modelo de exemplo. Você pode removê-lo ou usá-lo como base
para criar seus próprios modelos.

IMPORTANTE:
- O __tablename__ será automaticamente prefixado pelo sistema
- Se table_prefix for null no install.json, a tabela será criada como "plugin_mash_control_exemplo"
- Use model_loader nas rotas API para garantir que o modelo prefixado seja usado
"""

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.sql import func

from db.database import db


class MashControlExemplo(db.Model):
    """
    Modelo de exemplo.
    
    Este modelo demonstra como criar modelos SQLAlchemy em plugins.
    O nome da tabela será prefixado automaticamente.
    """
    __tablename__ = 'exemplo'  # Será prefixado automaticamente para "plugin_mash_control_exemplo"
    
    id = Column(Integer, primary_key=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(255))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """
        Converte o modelo para dicionário.
        
        Útil para retornar dados em APIs JSON.
        """
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<MashControlExemplo(id={self.id}, nome="{self.nome}")>'
