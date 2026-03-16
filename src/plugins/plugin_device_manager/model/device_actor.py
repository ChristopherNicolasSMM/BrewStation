"""
Modelo de atores de dispositivos IoT.

Atores associam portas de devices a funções e permitem integração
com outros plugins do sistema.

NOTA sobre ForeignKeys:
  O BrewStation aplica o prefixo de tabela ("dvmanage_") externamente,
  após a definição da classe. Os ForeignKeys devem referenciar os nomes
  SEM prefixo — o sistema resolve o nome real em runtime.

NOTA sobre relationships:
  Os relacionamentos ORM estão desabilitados intencionalmente.
  Habilitá-los força a configuração do mapper no import, o que quebra
  a inicialização antes que o BrewStation aplique os prefixos de tabela.
  Use model_loader + queries manuais para acessar device/function.
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
    __tablename__ = 'device_actor'  # Prefixado automaticamente para dvmanage_device_actor

    id = Column(String(36), primary_key=True)  # UUID
    device_id = Column(
        String(36),
        ForeignKey('device_metadata.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )
    port_name = Column(String(50), nullable=False)   # GPIO1, ADC0, etc.
    function_id = Column(
        Integer,
        ForeignKey('device_function.id', ondelete='RESTRICT'),
        nullable=False,
        index=True
    )
    actor_type = Column(String(20), nullable=False)  # sensor, actuator, rule_trigger
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # Configuração específica do ator (JSON)
    config_json = Column(Text)

    # Relacionamentos com outros plugins
    plugin_name = Column(String(100), index=True)
    plugin_entity_id = Column(String(100), index=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relacionamentos ORM DESABILITADOS — ver nota no topo do arquivo.
    # Habilitar relationship() força configuração do mapper no import,
    # o que quebra o boot antes que o BrewStation aplique os prefixos.
    # device = relationship('DeviceMetadata', backref='actors')
    # function = relationship('DeviceFunction', backref='actors')

    def get_config(self) -> dict:
        """
        Retorna configuração do ator como dicionário.

        Returns:
            Dicionário com configuração ou {} se vazio
        """
        if not self.config_json:
            return {}
        try:
            return json.loads(self.config_json)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_config(self, config_dict: dict):
        """
        Define configuração do ator a partir de dicionário.

        Args:
            config_dict: Dicionário com configuração
        """
        if config_dict:
            self.config_json = json.dumps(config_dict, ensure_ascii=False)
        else:
            self.config_json = None

    def to_dict(self, include_relationships: bool = False) -> dict:
        """
        Converte o modelo para dicionário.

        Args:
            include_relationships: Reservado para futura implementação via
                                   queries manuais (não usa ORM relationship).

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
            # Carrega device e function via query manual para evitar
            # dependência de relationship() ORM (ver nota no topo).
            try:
                from plugins.plugin_device_manager.utils.model_loader import (
                    get_device_metadata,
                    get_device_function,
                )
                DeviceMetadata = get_device_metadata()
                DeviceFunction = get_device_function()

                if DeviceMetadata:
                    device = DeviceMetadata.query.get(self.device_id)
                    if device:
                        result['device'] = device.to_dict()

                if DeviceFunction:
                    function = DeviceFunction.query.get(self.function_id)
                    if function:
                        result['function'] = function.to_dict()
            except Exception:
                pass  # Modelos podem não estar disponíveis no contexto atual

        return result

    def __repr__(self):
        return (
            f'<DeviceActor(id={self.id}, name="{self.name}", '
            f'type={self.actor_type}, device_id={self.device_id})>'
        )
