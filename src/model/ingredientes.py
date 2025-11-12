"""
Modelos de dados para o sistema de precificação de cervejas
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from datetime import datetime
from db.database import db

class Malte(db.Model):
    """Modelo para dados de malte"""
    __tablename__ = 'malte'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    fabricante = Column(String(100), nullable=False)
    cor_ebc = Column(Float, nullable=False)
    poder_diastatico = Column(Float, nullable=False)
    rendimento = Column(Float, nullable=False)
    preco_kg = Column(Float, nullable=False)
    tipo = Column(String(50), nullable=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Malte {self.nome} - {self.fabricante}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'fabricante': self.fabricante,
            'cor_ebc': self.cor_ebc,
            'poder_diastatico': self.poder_diastatico,
            'rendimento': self.rendimento,
            'preco_kg': self.preco_kg,
            'tipo': self.tipo,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Lupulo(db.Model):
    """Modelo para dados de lúpulo"""
    __tablename__ = 'lupulo'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    fabricante = Column(String(100), nullable=False)
    alpha_acidos = Column(Float, nullable=False)
    beta_acidos = Column(Float, nullable=False)
    formato = Column(String(50), nullable=False)
    origem = Column(String(100), nullable=False)
    preco_kg = Column(Float, nullable=False)
    aroma = Column(String(200), nullable=True)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Lupulo {self.nome} - {self.fabricante}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'fabricante': self.fabricante,
            'alpha_acidos': self.alpha_acidos,
            'beta_acidos': self.beta_acidos,
            'formato': self.formato,
            'origem': self.origem,
            'preco_kg': self.preco_kg,
            'aroma': self.aroma,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Levedura(db.Model):
    """Modelo para dados de levedura"""
    __tablename__ = 'levedura'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    fabricante = Column(String(100), nullable=False)
    formato = Column(String(50), nullable=False)
    atenuacao = Column(Float, nullable=False)
    temp_fermentacao = Column(Float, nullable=False)
    preco_unidade = Column(Float, nullable=False)
    floculacao = Column(String(50), nullable=False)
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Levedura {self.nome} - {self.fabricante}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'fabricante': self.fabricante,
            'formato': self.formato,
            'atenuacao': self.atenuacao,
            'temp_fermentacao': self.temp_fermentacao,
            'preco_unidade': self.preco_unidade,
            'floculacao': self.floculacao,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }

class Receita(db.Model):
    """Modelo para receitas de cerveja"""
    __tablename__ = 'receita'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(String(500), nullable=True)
    volume_litros = Column(Float, nullable=False)
    eficiencia = Column(Float, default=75.0)  # Eficiência padrão de 75%
    ativo = Column(Boolean, default=True)
    data_criacao = Column(DateTime, default=func.now())
    data_atualizacao = Column(DateTime, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f'<Receita {self.nome}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'volume_litros': self.volume_litros,
            'eficiencia': self.eficiencia,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None,
            'data_atualizacao': self.data_atualizacao.isoformat() if self.data_atualizacao else None
        }       

class IngredienteReceita(db.Model):
    """Modelo para ingredientes de uma receita"""
    __tablename__ = 'ingrediente_receita'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    receita_id = Column(Integer, nullable=False)
    tipo_ingrediente = Column(String(20), nullable=False)  # 'malte', 'lupulo', 'levedura'
    ingrediente_id = Column(Integer, nullable=False)
    quantidade = Column(Float, nullable=False)
    tempo_adicao = Column(Float, nullable=True)  # Para lúpulos (minutos)
    observacoes = Column(String(200), nullable=True)
    
    def __repr__(self):
        return f'<IngredienteReceita {self.tipo_ingrediente} - {self.quantidade}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'receita_id': self.receita_id,
            'tipo_ingrediente': self.tipo_ingrediente,
            'ingrediente_id': self.ingrediente_id,
            'quantidade': self.quantidade,
            'tempo_adicao': self.tempo_adicao,
            'observacoes': self.observacoes
        }

class CalculoPreco(db.Model):
    """Modelo para cálculos de preço"""
    __tablename__ = 'calculo_preco'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    receita_id = Column(Integer, nullable=False)
    nome_produto = Column(String(100), nullable=False)
    quantidade_ml = Column(Integer, nullable=False)
    tipo_embalagem = Column(String(50), nullable=False)
    valor_litro_base = Column(Float, nullable=False)
    custo_embalagem = Column(Float, nullable=False)
    custo_impressao = Column(Float, nullable=False)
    custo_tampinha = Column(Float, nullable=False)
    percentual_lucro = Column(Float, nullable=False)
    margem_cartao = Column(Float, nullable=False)
    percentual_sanitizacao = Column(Float, nullable=False)
    percentual_impostos = Column(Float, nullable=False)
    valor_total = Column(Float, nullable=False)
    valor_venda_final = Column(Float, nullable=False)
    data_calculo = Column(DateTime, default=func.now())
    
    def __repr__(self):
        return f'<CalculoPreco {self.nome_produto} - {self.valor_venda_final}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'receita_id': self.receita_id,
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



def cadastrar_ingrediente_automatico(tipo, dados):
    """
    Cadastra automaticamente maltes, lúpulos e leveduras se não existirem
    tipo: 'malte', 'lupulo', 'levedura'
    dados: dicionário com os dados do ingrediente
    """
    try:
        if tipo == 'malte':
            # Verificar se já existe pelo nome e fabricante
            existente = Malte.query.filter_by(
                nome=dados.get('nome', '').strip(),
                fabricante=dados.get('fabricante', '').strip(),
                ativo=True
            ).first()
            
            if not existente:
                malte = Malte(
                    nome=dados.get('nome', '').strip(),
                    fabricante=dados.get('fabricante', '').strip(),
                    cor_ebc=dados.get('cor_ebc', 0),
                    poder_diastatico=dados.get('poder_diastatico', 0),
                    rendimento=dados.get('rendimento', 75),
                    preco_kg=0.01,  # Preço mínimo para cadastro
                    tipo=dados.get('tipo', 'Base')
                )
                db.session.add(malte)
                db.session.flush()  # Para obter o ID
                print(f"✅ Malte cadastrado automaticamente: {malte.nome}")
                return malte.id
            return existente.id

        elif tipo == 'lupulo':
            # Verificar se já existe pelo nome e fabricante
            existente = Lupulo.query.filter_by(
                nome=dados.get('nome', '').strip(),
                fabricante=dados.get('fabricante', '').strip(),
                ativo=True
            ).first()
            
            if not existente:
                lupulo = Lupulo(
                    nome=dados.get('nome', '').strip(),
                    fabricante=dados.get('fabricante', '').strip(),
                    alpha_acidos=dados.get('alpha_acidos', 0),
                    beta_acidos=dados.get('beta_acidos', 0),
                    formato=dados.get('formato', 'Pellet'),
                    origem=dados.get('origem', ''),
                    preco_kg=0.01,  # Preço mínimo para cadastro
                    aroma=dados.get('aroma', '')
                )
                db.session.add(lupulo)
                db.session.flush()
                print(f"✅ Lúpulo cadastrado automaticamente: {lupulo.nome}")
                return lupulo.id
            return existente.id

        elif tipo == 'levedura':
            # Verificar se já existe pelo nome e fabricante
            existente = Levedura.query.filter_by(
                nome=dados.get('nome', '').strip(),
                fabricante=dados.get('fabricante', '').strip(),
                ativo=True
            ).first()
            
            if not existente:
                levedura = Levedura(
                    nome=dados.get('nome', '').strip(),
                    fabricante=dados.get('fabricante', '').strip(),
                    formato=dados.get('formato', 'Líquida'),
                    atenuacao=dados.get('atenuacao', 75),
                    temp_fermentacao=dados.get('temp_fermentacao', 20),
                    preco_unidade=0.01,  # Preço mínimo para cadastro
                    floculacao=dados.get('floculacao', 'Média')
                )
                db.session.add(levedura)
                db.session.flush()
                print(f"✅ Levedura cadastrada automaticamente: {levedura.nome}")
                return levedura.id
            return existente.id

        return None

    except Exception as e:
        print(f"❌ Erro ao cadastrar {tipo} automaticamente: {e}")
        db.session.rollback()
        return None