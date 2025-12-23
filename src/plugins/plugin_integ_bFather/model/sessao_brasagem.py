# model/sessao_brasagem.py
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from db.database import db

class SessaoBrasagem(db.Model):
    """Modelo para sessões de brassagem"""
    __tablename__ = 'sessoes_brasagem'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    receita_id = Column(Integer, ForeignKey('receita.id'), nullable=True)
    status = Column(String(20), default='planejada')  # planejada, em_andamento, finalizada, cancelada
    data_inicio = Column(DateTime, nullable=True)
    data_fim = Column(DateTime, nullable=True)
    temperatura_alvo = Column(Float, nullable=True)
    gravidade_original = Column(Float, nullable=True)
    gravidade_final = Column(Float, nullable=True)
    observacoes = Column(Text, nullable=True)
    
    # Metadados
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relacionamentos
    # dispositivos = relationship("Dispositivo", back_populates="sessao_brasagem")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'receita_id': self.receita_id,
            'status': self.status,
            'data_inicio': self.data_inicio.isoformat() if self.data_inicio else None,
            'data_fim': self.data_fim.isoformat() if self.data_fim else None,
            'temperatura_alvo': self.temperatura_alvo,
            'gravidade_original': self.gravidade_original,
            'gravidade_final': self.gravidade_final,
            'observacoes': self.observacoes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by
        }
    
    def __repr__(self):
        return f'<SessaoBrasagem {self.nome}>'