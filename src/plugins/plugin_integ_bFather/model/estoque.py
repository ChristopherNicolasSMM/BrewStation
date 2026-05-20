from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric
from sqlalchemy.ext.hybrid import hybrid_property

from db.database import db


class MovimentacaoEstoque(db.Model):
    __tablename__ = 'movimentacoes_estoque'
    
    id = db.Column(db.Integer, primary_key=True)
    ingrediente_id = db.Column(db.Integer, nullable=False)  # ID do ingrediente (pode ser de malte, lupulo ou levedura)
    tipo_ingrediente = db.Column(db.String(20), nullable=False)  # 'malte', 'lupulo', 'levedura'
    tipo_movimentacao = db.Column(db.String(20), nullable=False)  # entrada, saida, ajuste
    quantidade = db.Column(Numeric(10, 3), nullable=False)  # Quantidade em kg ou unidades
    unidade_medida = db.Column(db.String(10), nullable=False)  # kg, g, L, ml, un
    custo_unitario = db.Column(Numeric(10, 4))  # Custo por unidade de medida
    custo_total = db.Column(Numeric(10, 2))  # Custo total da movimentação
    lote_fornecedor = db.Column(db.String(100))  # Lote do fornecedor
    data_validade = db.Column(db.Date)
    data_movimentacao = db.Column(db.DateTime, default=datetime.utcnow)
    observacoes = db.Column(db.Text)
    usuario_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relacionamento com usuário (usando string para evitar importação circular)
    # O modelo User está em model.user e será resolvido pelo SQLAlchemy
    # IMPORTANTE: O modelo User deve estar importado antes de registrar este modelo
    usuario = db.relationship('User', lazy='joined', foreign_keys=[usuario_id])
    
    def calcular_custo_total(self):
        if self.custo_unitario and self.quantidade:
            self.custo_total = self.custo_unitario * self.quantidade
        return self.custo_total
    
    def to_dict(self):
        pass
        
        # Buscar informações do ingrediente
        ingrediente_info = self.buscar_ingrediente_info()
        
        return {
            'id': self.id,
            'ingrediente_id': self.ingrediente_id,
            'ingrediente_nome': ingrediente_info.get('nome', 'Desconhecido'),
            'ingrediente_tipo': self.tipo_ingrediente,
            'tipo_movimentacao': self.tipo_movimentacao,
            'quantidade': float(self.quantidade) if self.quantidade else 0,
            'unidade_medida': self.unidade_medida,
            'custo_unitario': float(self.custo_unitario) if self.custo_unitario else 0,
            'custo_total': float(self.custo_total) if self.custo_total else 0,
            'lote_fornecedor': self.lote_fornecedor,
            'data_validade': self.data_validade.isoformat() if self.data_validade else None,
            'data_movimentacao': self.data_movimentacao.isoformat() if self.data_movimentacao else None,
            'observacoes': self.observacoes,
            'usuario_nome': self.usuario.username if self.usuario else 'Sistema'
        }
    
    def buscar_ingrediente_info(self):
        """Busca informações do ingrediente baseado no tipo e ID"""
        from model.ingredientes import Levedura, Lupulo, Malte
        
        try:
            if self.tipo_ingrediente == 'malte':
                ingrediente = Malte.query.get(self.ingrediente_id)
                if ingrediente:
                    return {
                        'nome': ingrediente.nome,
                        'fabricante': ingrediente.fabricante,
                        'tipo': ingrediente.tipo
                    }
            elif self.tipo_ingrediente == 'lupulo':
                ingrediente = Lupulo.query.get(self.ingrediente_id)
                if ingrediente:
                    return {
                        'nome': ingrediente.nome,
                        'fabricante': ingrediente.fabricante,
                        'formato': ingrediente.formato
                    }
            elif self.tipo_ingrediente == 'levedura':
                ingrediente = Levedura.query.get(self.ingrediente_id)
                if ingrediente:
                    return {
                        'nome': ingrediente.nome,
                        'fabricante': ingrediente.fabricante,
                        'formato': ingrediente.formato
                    }
        except Exception as e:
            print(f"Erro ao buscar informações do ingrediente: {e}")
        
        return {'nome': 'Desconhecido', 'fabricante': 'Desconhecido'}

class EstoqueIngrediente(db.Model):
    __tablename__ = 'estoque_ingredientes'
    
    id = db.Column(db.Integer, primary_key=True)
    ingrediente_id = db.Column(db.Integer, nullable=False)
    tipo_ingrediente = db.Column(db.String(20), nullable=False)  # 'malte', 'lupulo', 'levedura'
    quantidade_atual = db.Column(Numeric(10, 3), default=0)
    unidade_medida = db.Column(db.String(10), nullable=False)
    estoque_minimo = db.Column(Numeric(10, 3), default=0)
    estoque_maximo = db.Column(Numeric(10, 3))
    custo_medio = db.Column(Numeric(10, 4), default=0)
    valor_total_estoque = db.Column(Numeric(10, 2), default=0)
    ultima_atualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    @hybrid_property
    def status_estoque(self):
        quantidade = self.quantidade_atual or 0
        minimo = self.estoque_minimo or 0
        if quantidade <= 0:
            return 'esgotado'
        elif quantidade <= minimo:
            return 'critico'
        elif quantidade <= (minimo * 1.5):
            return 'baixo'
        else:
            return 'ok'
    
    def atualizar_estoque(self, movimentacao):
        """Atualiza o estoque baseado em uma movimentação"""
        if self.quantidade_atual is None:
            self.quantidade_atual = Decimal('0')
        if self.custo_medio is None:
            self.custo_medio = Decimal('0')
        if self.valor_total_estoque is None:
            self.valor_total_estoque = Decimal('0')

        if movimentacao.tipo_movimentacao == 'entrada':
            self.quantidade_atual += movimentacao.quantidade
            # Atualizar custo médio
            if movimentacao.custo_total and movimentacao.custo_total > 0 and self.quantidade_atual > 0:
                valor_total_anterior = self.custo_medio * (self.quantidade_atual - movimentacao.quantidade)
                self.custo_medio = (valor_total_anterior + movimentacao.custo_total) / self.quantidade_atual
                
        elif movimentacao.tipo_movimentacao == 'saida':
            self.quantidade_atual -= movimentacao.quantidade
            
        self.valor_total_estoque = self.custo_medio * self.quantidade_atual
        self.ultima_atualizacao = datetime.utcnow()
    
    def to_dict(self):
        pass
        
        # Buscar informações do ingrediente
        ingrediente_info = self.buscar_ingrediente_info()
        
        return {
            'id': self.id,
            'ingrediente_id': self.ingrediente_id,
            'ingrediente_nome': ingrediente_info.get('nome', 'Desconhecido'),
            'ingrediente_tipo': self.tipo_ingrediente,
            'quantidade_atual': float(self.quantidade_atual) if self.quantidade_atual else 0,
            'unidade_medida': self.unidade_medida,
            'estoque_minimo': float(self.estoque_minimo) if self.estoque_minimo else 0,
            'estoque_maximo': float(self.estoque_maximo) if self.estoque_maximo else None,
            'custo_medio': float(self.custo_medio) if self.custo_medio else 0,
            'valor_total_estoque': float(self.valor_total_estoque) if self.valor_total_estoque else 0,
            'status_estoque': self.status_estoque,
            'ultima_atualizacao': self.ultima_atualizacao.isoformat() if self.ultima_atualizacao else None,
            'fabricante': ingrediente_info.get('fabricante', 'Desconhecido'),
            'detalhes': ingrediente_info.get('detalhes', {})
        }
    
    def buscar_ingrediente_info(self):
        """Busca informações do ingrediente baseado no tipo e ID"""
        from model.ingredientes import Levedura, Lupulo, Malte
        
        try:
            if self.tipo_ingrediente == 'malte':
                ingrediente = Malte.query.get(self.ingrediente_id)
                if ingrediente:
                    return {
                        'nome': ingrediente.nome,
                        'fabricante': ingrediente.fabricante,
                        'detalhes': {
                            'tipo': ingrediente.tipo,
                            'cor_ebc': ingrediente.cor_ebc,
                            'rendimento': ingrediente.rendimento
                        }
                    }
            elif self.tipo_ingrediente == 'lupulo':
                ingrediente = Lupulo.query.get(self.ingrediente_id)
                if ingrediente:
                    return {
                        'nome': ingrediente.nome,
                        'fabricante': ingrediente.fabricante,
                        'detalhes': {
                            'alpha_acidos': ingrediente.alpha_acidos,
                            'formato': ingrediente.formato,
                            'origem': ingrediente.origem
                        }
                    }
            elif self.tipo_ingrediente == 'levedura':
                ingrediente = Levedura.query.get(self.ingrediente_id)
                if ingrediente:
                    return {
                        'nome': ingrediente.nome,
                        'fabricante': ingrediente.fabricante,
                        'detalhes': {
                            'formato': ingrediente.formato,
                            'atenuacao': ingrediente.atenuacao,
                            'floculacao': ingrediente.floculacao
                        }
                    }
        except Exception as e:
            print(f"Erro ao buscar informações do ingrediente: {e}")
        
        return {'nome': 'Desconhecido', 'fabricante': 'Desconhecido', 'detalhes': {}}

class CustoProducao(db.Model):
    __tablename__ = 'custos_producao'
    
    id = db.Column(db.Integer, primary_key=True)
    lote_id = db.Column(db.Integer, db.ForeignKey('brewfather_batches.id'))
    custo_ingredientes = db.Column(Numeric(10, 2), default=0)
    custo_embalagens = db.Column(Numeric(10, 2), default=0)
    custo_operacional = db.Column(Numeric(10, 2), default=0)  # Energia, água, gás, etc.
    custo_mao_obra = db.Column(Numeric(10, 2), default=0)
    custo_depreciacao = db.Column(Numeric(10, 2), default=0)  # Equipamentos
    custo_total = db.Column(Numeric(10, 2), default=0)
    preco_venda_sugerido = db.Column(Numeric(10, 2))
    margem_lucro = db.Column(Numeric(5, 2))  # Percentual
    quantidade_produzida = db.Column(Numeric(8, 2))  # Litros
    custo_por_litro = db.Column(Numeric(8, 4))
    data_calculo = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    lote = db.relationship('BrewFatherBatch', backref='custo_producao')
    
    def calcular_custos(self):
        """Calcula todos os custos automaticamente"""
        self.custo_total = (self.custo_ingredientes + self.custo_embalagens + 
                           self.custo_operacional + self.custo_mao_obra + self.custo_depreciacao)
        
        if self.quantidade_produzida and self.quantidade_produzida > 0:
            self.custo_por_litro = self.custo_total / self.quantidade_produzida
            
        if self.margem_lucro:
            self.preco_venda_sugerido = self.custo_total * (1 + (self.margem_lucro / 100))
    
    def to_dict(self):
        return {
            'id': self.id,
            'lote_id': self.lote_id,
            'lote_nome': f"{self.lote.recipe_name} - Lote {self.lote.batch_no}" if self.lote else None,
            'custo_ingredientes': float(self.custo_ingredientes) if self.custo_ingredientes else 0,
            'custo_embalagens': float(self.custo_embalagens) if self.custo_embalagens else 0,
            'custo_operacional': float(self.custo_operacional) if self.custo_operacional else 0,
            'custo_mao_obra': float(self.custo_mao_obra) if self.custo_mao_obra else 0,
            'custo_depreciacao': float(self.custo_depreciacao) if self.custo_depreciacao else 0,
            'custo_total': float(self.custo_total) if self.custo_total else 0,
            'preco_venda_sugerido': float(self.preco_venda_sugerido) if self.preco_venda_sugerido else 0,
            'margem_lucro': float(self.margem_lucro) if self.margem_lucro else 0,
            'quantidade_produzida': float(self.quantidade_produzida) if self.quantidade_produzida else 0,
            'custo_por_litro': float(self.custo_por_litro) if self.custo_por_litro else 0,
            'data_calculo': self.data_calculo.isoformat() if self.data_calculo else None
        }