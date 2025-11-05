import json
from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime
from sqlalchemy.sql import func
from db.database import db

class Configuracao(db.Model):
    """Modelo para configurações do sistema"""
    __tablename__ = 'configuracoes'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    chave = Column(String(100), unique=True, nullable=False, index=True)
    valor = Column(Text, nullable=True)
    tipo = Column(String(20), nullable=False, default='string')  # string, number, boolean, json
    categoria = Column(String(50), nullable=False, default='sistema')  # sistema, brewfather, email, etc.
    descricao = Column(Text, nullable=True)
    is_sensitive = Column(Boolean, default=False)  # Para senhas e chaves API
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def get_value(self):
        """Retorna o valor convertido para o tipo correto"""
        if self.tipo == 'boolean':
            return self.valor.lower() == 'true' if self.valor else False
        elif self.tipo == 'number':
            try:
                return float(self.valor) if self.valor else 0
            except (ValueError, TypeError):
                return 0
        elif self.tipo == 'json':
            try:
                return json.loads(self.valor) if self.valor else {}
            except (json.JSONDecodeError, TypeError):
                return {}
        else:  # string
            return self.valor or ''
    
    def set_value(self, value):
        """Define o valor convertendo para string"""
        if self.tipo == 'boolean':
            self.valor = 'true' if value else 'false'
        elif self.tipo == 'json':
            self.valor = json.dumps(value) if value else '{}'
        else:
            self.valor = str(value) if value is not None else ''
    
    def to_dict(self, include_sensitive=False):
        """Converte para dicionário, ocultando valores sensíveis se necessário"""
        data = {
            'id': self.id,
            'chave': self.chave,
            'tipo': self.tipo,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'is_sensitive': self.is_sensitive,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_sensitive or not self.is_sensitive:
            data['valor'] = self.get_value()
        else:
            data['valor'] = '********'  # Ocultar valores sensíveis
        
        return data
    
    @classmethod
    def get_config(cls, chave, default=None):
        """Obtém uma configuração pelo nome"""
        config = cls.query.filter_by(chave=chave).first()
        if config:
            return config.get_value()
        return default
    
    @classmethod
    def set_config(cls, chave, valor, tipo='string', categoria='sistema', descricao=None, is_sensitive=False):
        """Define uma configuração"""
        config = cls.query.filter_by(chave=chave).first()
        if not config:
            config = cls(
                chave=chave,
                tipo=tipo,
                categoria=categoria,
                descricao=descricao,
                is_sensitive=is_sensitive
            )
            db.session.add(config)
        
        config.set_value(valor)
        db.session.commit()
        return config
    
    @classmethod
    def get_all_configs(cls, include_sensitive=False):
        """Obtém todas as configurações"""
        configs = cls.query.all()
        return {config.chave: config.to_dict(include_sensitive) for config in configs}
    
    @classmethod
    def initialize_default_configs(cls):
        """Inicializa as configurações padrão do sistema"""
        default_configs = [
            # Configurações do Sistema
            {
                'chave': 'SECRET_KEY',
                'valor': 'dev-secret-key-change-in-production',
                'tipo': 'string',
                'categoria': 'sistema',
                'descricao': 'Chave secreta para segurança da aplicação',
                'is_sensitive': True
            },
            {
                'chave': 'DEBUG',
                'valor': 'True',
                'tipo': 'boolean',
                'categoria': 'sistema',
                'descricao': 'Modo de desenvolvimento (ativar apenas em desenvolvimento)',
                'is_sensitive': False
            },
            {
                'chave': 'DATABASE_URL',
                'valor': 'sqlite:///precifica_valirian.db',
                'tipo': 'string',
                'categoria': 'sistema',
                'descricao': 'URL de conexão com o banco de dados',
                'is_sensitive': False
            },
            {
                'chave': 'UPLOAD_FOLDER',
                'valor': 'uploads',
                'tipo': 'string',
                'categoria': 'sistema',
                'descricao': 'Diretório para armazenar arquivos enviados',
                'is_sensitive': False
            },
            {
                'chave': 'MAX_CONTENT_LENGTH',
                'valor': '16777216',
                'tipo': 'number',
                'categoria': 'sistema',
                'descricao': 'Tamanho máximo permitido para upload de arquivos (16MB = 16777216 bytes)',
                'is_sensitive': False
            },
            
            # Configurações BrewFather
            {
                'chave': 'BREWFATHER_USER_ID',
                'valor': '',
                'tipo': 'string',
                'categoria': 'brewfather',
                'descricao': 'User ID do BrewFather para integração com a API',
                'is_sensitive': True
            },
            {
                'chave': 'BREWFATHER_API_KEY',
                'valor': '',
                'tipo': 'string',
                'categoria': 'brewfather',
                'descricao': 'Chave de API do BrewFather',
                'is_sensitive': True
            },
            {
                'chave': 'BREWFATHER_ENABLED',
                'valor': 'False',
                'tipo': 'boolean',
                'categoria': 'brewfather',
                'descricao': 'Habilitar integração automática com BrewFather',
                'is_sensitive': False
            },
            {
                'chave': 'BREWFATHER_SYNC_INTERVAL',
                'valor': '3600',
                'tipo': 'number',
                'categoria': 'brewfather',
                'descricao': 'Intervalo de sincronização com BrewFather em segundos',
                'is_sensitive': False
            },
            
            # Configurações de Email
            {
                'chave': 'MAIL_SERVER',
                'valor': '',
                'tipo': 'string',
                'categoria': 'email',
                'descricao': 'Servidor SMTP para envio de emails',
                'is_sensitive': False
            },
            {
                'chave': 'MAIL_PORT',
                'valor': '587',
                'tipo': 'number',
                'categoria': 'email',
                'descricao': 'Porta do servidor SMTP',
                'is_sensitive': False
            },
            {
                'chave': 'MAIL_USERNAME',
                'valor': '',
                'tipo': 'string',
                'categoria': 'email',
                'descricao': 'Usuário para autenticação no servidor SMTP',
                'is_sensitive': False
            },
            {
                'chave': 'MAIL_PASSWORD',
                'valor': '',
                'tipo': 'string',
                'categoria': 'email',
                'descricao': 'Senha para autenticação no servidor SMTP',
                'is_sensitive': True
            },
            {
                'chave': 'MAIL_USE_TLS',
                'valor': 'True',
                'tipo': 'boolean',
                'categoria': 'email',
                'descricao': 'Usar TLS para conexão segura com o servidor SMTP',
                'is_sensitive': False
            },
            {
                'chave': 'MAIL_DEFAULT_SENDER',
                'valor': '',
                'tipo': 'string',
                'categoria': 'email',
                'descricao': 'Email remetente padrão para notificações',
                'is_sensitive': False
            },
            
            # Configurações da Aplicação
            {
                'chave': 'APP_NAME',
                'valor': 'PrecificaValirian',
                'tipo': 'string',
                'categoria': 'aplicacao',
                'descricao': 'Nome da aplicação',
                'is_sensitive': False
            },
            {
                'chave': 'APP_VERSION',
                'valor': '1.0.0',
                'tipo': 'string',
                'categoria': 'aplicacao',
                'descricao': 'Versão da aplicação',
                'is_sensitive': False
            },
            {
                'chave': 'ITEMS_PER_PAGE',
                'valor': '10',
                'tipo': 'number',
                'categoria': 'aplicacao',
                'descricao': 'Número de itens por página nas listagens',
                'is_sensitive': False
            }
        ]
        
        for config_data in default_configs:
            existing_config = cls.query.filter_by(chave=config_data['chave']).first()
            if not existing_config:
                config = cls(
                    chave=config_data['chave'],
                    tipo=config_data['tipo'],
                    categoria=config_data['categoria'],
                    descricao=config_data['descricao'],
                    is_sensitive=config_data['is_sensitive']
                )
                config.set_value(config_data['valor'])
                db.session.add(config)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<Configuracao {self.chave}>'