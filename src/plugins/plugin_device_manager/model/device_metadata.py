"""
Modelo de metadados de dispositivos IoT.

Este modelo armazena apenas metadados no banco de dados.
Configurações detalhadas e estados são armazenados em arquivos JSON.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func
from db.database import db


class DeviceMetadata(db.Model):
    """
    Metadados de dispositivos IoT.
    
    Armazena apenas informações básicas no banco de dados.
    Configurações detalhadas e estados são salvos em arquivos JSON
    dentro de data/devices/configs/ e data/devices/states/.
    """
    __tablename__ = 'device_metadata'  # Será prefixado automaticamente para dvmanage_device_metadata
    
    id = Column(String(36), primary_key=True)  # UUID ou ID único do dispositivo
    name = Column(String(100), nullable=False)
    device_type = Column(String(50))  # sensor, actuator, gateway
    protocol = Column(String(20))  # mqtt, http, websocket
    config_path = Column(String(500))  # Caminho relativo para JSON de configuração
    state_path = Column(String(500))  # Caminho relativo para JSON de estado
    is_active = Column(Boolean, default=True)
    port_config = Column(Text)  # JSON string com configuração de portas (GPIO, entradas, saídas)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """
        Converte o modelo para dicionário.
        
        Útil para retornar dados em APIs JSON.
        """
        import json
        
        port_config_dict = None
        if self.port_config:
            try:
                port_config_dict = json.loads(self.port_config)
            except (json.JSONDecodeError, TypeError):
                port_config_dict = {}
        
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'protocol': self.protocol,
            'config_path': self.config_path,
            'state_path': self.state_path,
            'is_active': self.is_active,
            'port_config': port_config_dict,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<DeviceMetadata(id={self.id}, name="{self.name}", type={self.device_type})>'

