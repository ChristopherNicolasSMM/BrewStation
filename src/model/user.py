"""
Sistema de autenticação
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from db.database import db

class User(UserMixin, db.Model):
    """Modelo de usuário para autenticação"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    # Campos de perfil
    nome = Column(String(120))
    nome_completo = Column(String(255))
    empresa = Column(String(255))
    cargo = Column(String(255))
    pais = Column(String(120))
    endereco = Column(String(255))
    telefone = Column(String(50))
    sobre = Column(Text)
    twitter = Column(String(255))
    facebook = Column(String(255))
    instagram = Column(String(255))
    linkedin = Column(String(255))
    foto_perfil = Column(String(255))  # caminho relativo em static
    # Configurações de notificação
    notificacao_alteracoes = Column(Boolean, default=False)
    notificacao_novos_produtos = Column(Boolean, default=False)
    notificacao_ofertas = Column(Boolean, default=False)
    
    def set_password(self, password):
        """Define a senha do usuário"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)

    # Propriedades auxiliares compatíveis com rotas existentes
    @property
    def password(self):
        raise AttributeError("password is write-only")

    @password.setter
    def password(self, password: str):
        self.set_password(password)

    def verify_password(self, password: str) -> bool:
        return self.check_password(password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'nome': self.nome,
            'nome_completo': self.nome_completo,
            'empresa': self.empresa,
            'cargo': self.cargo,
            'pais': self.pais,
            'endereco': self.endereco,
            'telefone': self.telefone,
            'sobre': self.sobre,
            'twitter': self.twitter,
            'facebook': self.facebook,
            'instagram': self.instagram,
            'linkedin': self.linkedin,
            'foto_perfil': self.foto_perfil,
            'notificacao_alteracoes': self.notificacao_alteracoes,
            'notificacao_novos_produtos': self.notificacao_novos_produtos,
            'notificacao_ofertas': self.notificacao_ofertas,
        }
    
    def __repr__(self):
        return f'<User {self.username}>'
