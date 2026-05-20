from datetime import datetime

from db.database import db


class CalculoEnvase(db.Model):
    __tablename__ = 'calculo_envase'
    
    id = db.Column(db.Integer, primary_key=True)
    envase_id = db.Column(db.Integer, db.ForeignKey('envases.id'), nullable=True)
    nome_produto = db.Column(db.String(200), nullable=False)
    quantidade_ml = db.Column(db.Integer, nullable=False)
    tipo_embalagem = db.Column(db.String(50), nullable=False)
    valor_litro_base = db.Column(db.Float, nullable=False)
    custo_embalagem = db.Column(db.Float, default=0.0)
    custo_impressao = db.Column(db.Float, default=0.0)
    custo_tampinha = db.Column(db.Float, default=0.0)
    percentual_lucro = db.Column(db.Float, nullable=False)
    margem_cartao = db.Column(db.Float, nullable=False)
    percentual_sanitizacao = db.Column(db.Float, nullable=False)
    percentual_impostos = db.Column(db.Float, nullable=False)
    valor_total = db.Column(db.Float, nullable=False)
    valor_venda_final = db.Column(db.Float, nullable=False)
    data_calculo = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento opcional com envase
    envase = db.relationship('Envase', backref='calculos_envase')
    
    def to_dict(self):
        return {
            'id': self.id,
            'envase_id': self.envase_id,
            'nome_produto': self.nome_produto,
            'quantidade_ml': self.quantidade_ml,
            'tipo_embalagem': self.tipo_embalagem,
            'valor_litro_base': self.valor_litro_base,
            'custo_embalagem': self.custo_embalagem,
            'custo_impressao': self.custo_impressao,
            'custo_tampinha': self.custo_tampinha,
            'percentual_lucro': self.percentual_lucro,
            'margem_cartao': self.margem_cartao,
            'percentual_sanitizacao': self.percentual_sanitizacao,
            'percentual_impostos': self.percentual_impostos,
            'valor_total': self.valor_total,
            'valor_venda_final': self.valor_venda_final,
            'data_calculo': self.data_calculo.isoformat() if self.data_calculo else None
        }