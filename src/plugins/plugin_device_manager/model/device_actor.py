"""
Modelo de atores de dispositivos IoT.

Atores associam portas de devices a funções e permitem integração
com outros plugins do sistema.
"""

import json
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import db


class DeviceActor(db.Model):
    """
    Atores de dispositivos IoT.
    
    Um ator associa uma porta de um device a uma função específica,
    permitindo que outros plugins usem essa associação para controle
    e leitura de sensores/atuadores.
    """
    __tablename__ = 'device_actor'  # Será prefixado automaticamente para dvmanage_device_actor
    
    id = Column(String(36), primary_key=True)  # UUID
    device_id = Column(String(36), ForeignKey('device_metadata.id', ondelete='CASCADE'), nullable=False, index=True)
    port_name = Column(String(50), nullable=False)  # GPIO1, ADC0, etc.
    function_id = Column(Integer, ForeignKey('device_function.id', ondelete='RESTRICT'), nullable=False, index=True)
    actor_type = Column(String(20), nullable=False)  # sensor, actuator, rule_trigger
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Configuração específica do ator (JSON)
    config_json = Column(Text)  # JSON com configurações específicas (ex: tópico MQTT, mapeamento de valores, etc.)
    
    # Relacionamentos com outros plugins
    plugin_name = Column(String(100), index=True)  # Plugin que usa este ator (ex: plugin_mash_control)
    plugin_entity_id = Column(String(100), index=True)  # ID da entidade no plugin (ex: recipe_id, process_id)
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relacionamentos (serão definidos após prefixação)
    # device = relationship('DeviceMetadata', backref='actors')
    # function = relationship('DeviceFunction', backref='actors')
    
    def get_config(self):
        """
        Retorna configuração do ator como dicionário.
        
        Returns:
            Dicionário com configuração ou None se vazio
        """
        if not self.config_json:
            return {}
        
        try:
            return json.loads(self.config_json)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_config(self, config_dict):
        """
        Define configuração do ator a partir de dicionário.
        
        Args:
            config_dict: Dicionário com configuração
        """
        if config_dict:
            self.config_json = json.dumps(config_dict, ensure_ascii=False)
        else:
            self.config_json = None
    
    def to_dict(self, include_relationships=False):
        """
        Converte o modelo para dicionário.
        
        Args:
            include_relationships: Se True, inclui dados de relacionamentos
            
        Returns:
            Dicionário com dados do ator
        """
        result = {
            'id': self.id,
            'device_id': self.device_id,
            'port_name': self.port_name,
            'function_id': self.function_id,
            'actor_type': self.actor_type,
            'name': self.name,
            'description': self.description,
            'config': self.get_config(),
            'plugin_name': self.plugin_name,
            'plugin_entity_id': self.plugin_entity_id,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_relationships:
            # Adicionar dados de relacionamentos se disponíveis
            try:
                if hasattr(self, 'device') and self.device:
                    result['device'] = self.device.to_dict()
                if hasattr(self, 'function') and self.function:
                    result['function'] = self.function.to_dict()
            except Exception:
                pass  # Relacionamentos podem não estar carregados
        
        return result
    
    def __repr__(self):
        return f'<DeviceActor(id={self.id}, name="{self.name}", type={self.actor_type}, device_id={self.device_id})>'
