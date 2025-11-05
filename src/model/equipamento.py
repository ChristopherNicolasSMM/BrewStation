import json
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, Float, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from db.database import db

# Mover os Enums para um arquivo separado ou definir aqui
# Mas garantir que não causem import circular

class TipoDispositivo(PyEnum):
    """Tipos de dispositivos suportados pelo sistema"""
    CONTROLADOR_TEMPERATURA = "controlador_temperatura"
    ISPINDEL = "ispindel"
    CONTROLADOR_BRASAGEM = "controlador_brasagem"
    SENSOR_TEMPERATURA = "sensor_temperatura"
    VALVULA = "valvula"
    AQUECEDOR = "aquecedor"
    BOMBA = "bomba"
    OUTRO = "outro"

class ProtocoloComunicacao(PyEnum):
    """Protocolos de comunicação suportados"""
    MQTT = "mqtt"
    HTTP = "http"
    WEBSOCKET = "websocket"
    SERIAL = "serial"
    BLUETOOTH = "bluetooth"
    TCP = "tcp"
    UDP = "udp"

class StatusDispositivo(PyEnum):
    """Status possíveis do dispositivo"""
    ATIVO = "ativo"
    INATIVO = "inativo"
    CONECTADO = "conectado"
    DESCONECTADO = "desconectado"
    ERROR = "error"
    CALIBRACAO = "calibracao"
    MANUTENCAO = "manutencao"

class Dispositivo(db.Model):
    """Modelo para gerenciar dispositivos do sistema BrewStation"""
    __tablename__ = 'dispositivos'
    
    # Identificação básica
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False, index=True)
    descricao = Column(Text, nullable=True)
    tipo = Column(Enum(TipoDispositivo), nullable=False, index=True)
    fabricante = Column(String(100), nullable=True)
    modelo = Column(String(100), nullable=True)
    versao_firmware = Column(String(50), nullable=True)
    
    # Configuração de comunicação
    protocolo = Column(Enum(ProtocoloComunicacao), nullable=False, default=ProtocoloComunicacao.MQTT)
    endereco = Column(String(255), nullable=False)  # IP, URL, MAC, etc.
    porta = Column(Integer, nullable=True)
    topico_mqtt = Column(String(255), nullable=True)  # Para dispositivos MQTT
    
    # Credenciais e autenticação
    usuario = Column(String(100), nullable=True)
    senha = Column(String(100), nullable=True)
    token_acesso = Column(String(255), nullable=True)
    
    # Configurações específicas do dispositivo
    configuracao = Column(JSON, nullable=True)  # Configurações específicas em JSON
    parametros_calibracao = Column(JSON, nullable=True)  # Parâmetros de calibração
    
    # Status e controle
    status = Column(Enum(StatusDispositivo), nullable=False, default=StatusDispositivo.INATIVO)
    ultima_comunicacao = Column(DateTime, nullable=True)
    ultimo_valor_recebido = Column(JSON, nullable=True)  # Últimos dados recebidos
    intervalo_atualizacao = Column(Integer, default=30)  # Segundos entre atualizações
    
    # Metadados
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_by = Column(String(100), nullable=True)
    
    # Relacionamentos
    sessao_brasagem_id = Column(Integer, ForeignKey('sessoes_brasagem.id'), nullable=True)
    #sessao_brasagem = relationship("SessaoBrasagem", back_populates="dispositivos")
    
    def to_dict(self, include_sensitive=False):
        """Converte para dicionário"""
        data = {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'tipo': self.tipo.value,
            'fabricante': self.fabricante,
            'modelo': self.modelo,
            'versao_firmware': self.versao_firmware,
            'protocolo': self.protocolo.value,
            'endereco': self.endereco,
            'porta': self.porta,
            'topico_mqtt': self.topico_mqtt,
            'configuracao': self.configuracao or {},
            'parametros_calibracao': self.parametros_calibracao or {},
            'status': self.status.value,
            'ultima_comunicacao': self.ultima_comunicacao.isoformat() if self.ultima_comunicacao else None,
            'ultimo_valor_recebido': self.ultimo_valor_recebido or {},
            'intervalo_atualizacao': self.intervalo_atualizacao,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'sessao_brasagem_id': self.sessao_brasagem_id
        }
        
        if include_sensitive:
            data.update({
                'usuario': self.usuario,
                'senha': self.senha,
                'token_acesso': self.token_acesso
            })
        else:
            # Ocultar informações sensíveis
            if self.usuario:
                data['usuario'] = '********'
            if self.senha:
                data['senha'] = '********'
            if self.token_acesso:
                data['token_acesso'] = '********'
        
        return data
    
    def atualizar_status(self, novo_status, dados_recebidos=None):
        """Atualiza o status do dispositivo e registra comunicação"""
        self.status = novo_status
        self.ultima_comunicacao = func.now()
        
        if dados_recebidos:
            self.ultimo_valor_recebido = dados_recebidos
        
        db.session.commit()
    
    def get_config_value(self, chave, default=None):
        """Obtém um valor específico da configuração"""
        return self.configuracao.get(chave, default) if self.configuracao else default
    
    def set_config_value(self, chave, valor):
        """Define um valor específico na configuração"""
        if not self.configuracao:
            self.configuracao = {}
        self.configuracao[chave] = valor
        db.session.commit()
    
    def calibrar(self, parametros_calibracao):
        """Aplica parâmetros de calibração ao dispositivo"""
        self.parametros_calibracao = parametros_calibracao
        self.status = StatusDispositivo.CALIBRACAO
        db.session.commit()
    
    @classmethod
    def get_por_tipo(cls, tipo):
        """Obtém dispositivos por tipo"""
        return cls.query.filter_by(tipo=tipo).all()
    
    @classmethod
    def get_ativos(cls):
        """Obtém todos os dispositivos ativos"""
        return cls.query.filter(
            cls.status.in_([StatusDispositivo.ATIVO, StatusDispositivo.CONECTADO])
        ).all()
    
    @classmethod
    def get_por_protocolo(cls, protocolo):
        """Obtém dispositivos por protocolo de comunicação"""
        return cls.query.filter_by(protocolo=protocolo).all()
    
    @classmethod
    def get_por_sessao(cls, sessao_id):
        """Obtém dispositivos associados a uma sessão de brassagem"""
        return cls.query.filter_by(sessao_brasagem_id=sessao_id).all()
    
    def __repr__(self):
        return f'<Dispositivo {self.nome} ({self.tipo.value})>'


class HistoricoDispositivo(db.Model):
    """Modelo para histórico de dados dos dispositivos"""
    __tablename__ = 'historico_dispositivos'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    dispositivo_id = Column(Integer, ForeignKey('dispositivos.id'), nullable=False, index=True)
    
    # Dados recebidos
    dados = Column(JSON, nullable=False)
    temperatura = Column(Float, nullable=True)  # Campo comum para temperatura
    gravidade = Column(Float, nullable=True)    # Campo comum para gravidade (iSpindel)
    pressao = Column(Float, nullable=True)      # Campo comum para pressão
    unidade = Column(String(20), nullable=True) # Unidade de medida
    
    # Metadados
    timestamp = Column(DateTime, default=func.now(), index=True)
    qualidade_sinal = Column(Float, nullable=True)  # Qualidade do sinal (RSSI, etc.)
    bateria = Column(Float, nullable=True)          # Nível da bateria
    
    # Relacionamentos
    dispositivo = relationship("Dispositivo", backref="historico")
    
    def to_dict(self):
        """Converte para dicionário"""
        return {
            'id': self.id,
            'dispositivo_id': self.dispositivo_id,
            'dados': self.dados,
            'temperatura': self.temperatura,
            'gravidade': self.gravidade,
            'pressao': self.pressao,
            'unidade': self.unidade,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'qualidade_sinal': self.qualidade_sinal,
            'bateria': self.bateria
        }
    
    @classmethod
    def get_ultimas_leituras(cls, dispositivo_id, limite=100):
        """Obtém as últimas leituras de um dispositivo"""
        return cls.query.filter_by(dispositivo_id=dispositivo_id)\
                      .order_by(cls.timestamp.desc())\
                      .limit(limite)\
                      .all()
    
    @classmethod
    def get_leituras_por_periodo(cls, dispositivo_id, inicio, fim):
        """Obtém leituras de um dispositivo em um período específico"""
        return cls.query.filter(
            cls.dispositivo_id == dispositivo_id,
            cls.timestamp >= inicio,
            cls.timestamp <= fim
        ).order_by(cls.timestamp.asc()).all()


# Configurações padrão para dispositivos (adicionar ao Configuracao.initialize_default_configs)
DISPOSITIVO_DEFAULT_CONFIGS = [
    {
        'chave': 'MQTT_BROKER_URL',
        'valor': 'localhost',
        'tipo': 'string',
        'categoria': 'dispositivos',
        'descricao': 'URL do broker MQTT para comunicação com dispositivos',
        'is_sensitive': False
    },
    {
        'chave': 'MQTT_BROKER_PORT',
        'valor': '1883',
        'tipo': 'number',
        'categoria': 'dispositivos',
        'descricao': 'Porta do broker MQTT',
        'is_sensitive': False
    },
    {
        'chave': 'MQTT_USERNAME',
        'valor': '',
        'tipo': 'string',
        'categoria': 'dispositivos',
        'descricao': 'Usuário para autenticação no broker MQTT',
        'is_sensitive': True
    },
    {
        'chave': 'MQTT_PASSWORD',
        'valor': '',
        'tipo': 'string',
        'categoria': 'dispositivos',
        'descricao': 'Senha para autenticação no broker MQTT',
        'is_sensitive': True
    },
    {
        'chave': 'DISPOSITIVO_TIMEOUT',
        'valor': '30',
        'tipo': 'number',
        'categoria': 'dispositivos',
        'descricao': 'Tempo máximo de espera para comunicação com dispositivos (segundos)',
        'is_sensitive': False
    },
    {
        'chave': 'DISPOSITIVO_RETRY_ATTEMPTS',
        'valor': '3',
        'tipo': 'number',
        'categoria': 'dispositivos',
        'descricao': 'Número máximo de tentativas de comunicação',
        'is_sensitive': False
    }
]