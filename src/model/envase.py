from db.database import db
from datetime import datetime
from sqlalchemy import Numeric

class TipoEmbalagem(db.Model):
    __tablename__ = 'tipos_embalagem'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    capacidade_ml = db.Column(db.Integer)  # Capacidade em ml
    cor = db.Column(db.String(50))
    material = db.Column(db.String(100))
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'capacidade_ml': self.capacidade_ml,
            'cor': self.cor,
            'material': self.material,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Embalagem(db.Model):
    __tablename__ = 'embalagens'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo_embalagem_id = db.Column(db.Integer, db.ForeignKey('tipos_embalagem.id'), nullable=False)
    fornecedor = db.Column(db.String(200))
    referencia = db.Column(db.String(100))
    link_referencia = db.Column(db.Text)
    lote_compra = db.Column(db.Integer, default=0)  # Quantidade no lote de compra
    frete = db.Column(Numeric(10, 2), default=0.0)  # Valor do frete
    valor_lote = db.Column(Numeric(10, 2), default=0.0)  # Valor total do lote
    valor_unidade = db.Column(Numeric(10, 4), default=0.0)  # Valor por unidade (calculado)
    estoque_atual = db.Column(db.Integer, default=0)
    estoque_minimo = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    tipo_embalagem = db.relationship('TipoEmbalagem', backref='embalagens')
    
    def calcular_valor_unidade(self):
        """Calcula o valor por unidade baseado no valor do lote + frete"""
        try:
            # Garantir que temos valores numéricos
            lote_compra = self.lote_compra or 0
            valor_lote = float(self.valor_lote or 0)
            frete = float(self.frete or 0)
            
            if lote_compra > 0:
                valor_total = valor_lote + frete
                self.valor_unidade = valor_total / lote_compra
            else:
                self.valor_unidade = 0.0
                
            return self.valor_unidade
        except (TypeError, ValueError) as e:
            print(f"Erro ao calcular valor unitário: {e}")
            self.valor_unidade = 0.0
            return 0.0
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo_embalagem_id': self.tipo_embalagem_id,
            'tipo_embalagem_nome': self.tipo_embalagem.nome if self.tipo_embalagem else None,
            'tipo_embalagem_capacidade': self.tipo_embalagem.capacidade_ml if self.tipo_embalagem else None,
            'fornecedor': self.fornecedor,
            'referencia': self.referencia,
            'link_referencia': self.link_referencia,
            'lote_compra': self.lote_compra,
            'frete': float(self.frete) if self.frete else 0,
            'valor_lote': float(self.valor_lote) if self.valor_lote else 0,
            'valor_unidade': float(self.valor_unidade) if self.valor_unidade else 0,
            'estoque_atual': self.estoque_atual,
            'estoque_minimo': self.estoque_minimo,
            'ativo': self.ativo,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Envase(db.Model):
    __tablename__ = 'envases'
    
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('brewfather_batches.id'))
    quantidade_litros = db.Column(Numeric(8, 2))  # Quantidade total em litros
    data_envase = db.Column(db.DateTime, default=datetime.utcnow)
    tipo_envase = db.Column(db.String(50))  # Completo, parcial, etc.
    observacoes = db.Column(db.Text)
    status = db.Column(db.String(20), default='planejado')  # planejado, em_andamento, concluido
    
    # Relacionamentos
    lote = db.relationship('BrewFatherBatch', backref='envases')
    itens_envase = db.relationship('ItemEnvase', backref='envase', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'lote_id': self.lote_id,
            'lote_nome': f"{self.lote.recipe_name} - Lote {self.lote.batch_no}" if self.lote else None,
            'quantidade_litros': float(self.quantidade_litros) if self.quantidade_litros else 0,
            'data_envase': self.data_envase.isoformat() if self.data_envase else None,
            'tipo_envase': self.tipo_envase,
            'observacoes': self.observacoes,
            'status': self.status,
            'itens_envase': [item.to_dict() for item in self.itens_envase],
            'created_at': self.created_at.isoformat() if hasattr(self, 'created_at') and self.created_at else None
        }

class ItemEnvase(db.Model):
    __tablename__ = 'itens_envase'
    
    id = db.Column(db.Integer, primary_key=True)
    envase_id = db.Column(db.Integer, db.ForeignKey('envases.id'), nullable=False)
    embalagem_id = db.Column(db.Integer, db.ForeignKey('embalagens.id'), nullable=False)
    quantidade = db.Column(db.Integer)  # Quantidade de unidades utilizadas
    capacidade_ml = db.Column(db.Integer)  # Capacidade da embalagem em ml
    
    # Relacionamentos
    embalagem = db.relationship('Embalagem', backref='itens_envase')
    
    def to_dict(self):
        return {
            'id': self.id,
            'envase_id': self.envase_id,
            'embalagem_id': self.embalagem_id,
            'embalagem_nome': self.embalagem.tipo_embalagem.nome if self.embalagem and self.embalagem.tipo_embalagem else None,
            'quantidade': self.quantidade,
            'capacidade_ml': self.capacidade_ml,
            'capacidade_litros': self.capacidade_ml / 1000 if self.capacidade_ml else 0,
            'total_litros': (self.quantidade * self.capacidade_ml) / 1000 if self.quantidade and self.capacidade_ml else 0
        }