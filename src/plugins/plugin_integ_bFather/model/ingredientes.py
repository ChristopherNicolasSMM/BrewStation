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
    fabricante = Column(String(100), nullable=True)
    alpha_acidos = Column(Float, nullable=True)
    beta_acidos = Column(Float, nullable=True)
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
                    preco_kg=0.00,  # Preço mínimo para cadastro
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
                    preco_kg=0.00,  # Preço mínimo para cadastro
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
                    preco_unidade=0.00,  # Preço mínimo para cadastro
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
    
    
def safe_float(value, default=0):
    """Converte valor para float de forma segura, tratando None"""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

def safe_string(value, default=''):
    """Converte valor para string de forma segura, tratando None"""
    if value is None:
        return default
    return str(value).strip() or default

def cadastrar_insumos_brewfather_automatico(receita_brewfather):
    """
    Cadastra automaticamente todos os insumos de uma receita do BrewFather
    que ainda não existem no sistema - Versão robusta
    """
    try:
        if not receita_brewfather or not receita_brewfather.ingredients:
            return {'success': False, 'error': 'Receita sem ingredientes'}
        
        ingredientes_cadastrados = {
            'maltes': [],
            'lupulos': [], 
            'leveduras': []
        }
        
        # Processar fermentáveis (maltes)
        for fermentable in receita_brewfather.ingredients.get('fermentables', []):
            nome = safe_string(fermentable.get('name'))
            fabricante = safe_string(fermentable.get('supplier'), 'Desconhecido')
            
            if not nome:
                continue
                
            # Verificar se já existe
            existente = Malte.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if not existente:
                # Determinar tipo baseado no nome
                tipo = determinar_tipo_malte(nome)
                
                malte = Malte(
                    nome=nome,
                    fabricante=fabricante,
                    cor_ebc=safe_float(fermentable.get('color')),
                    poder_diastatico=safe_float(fermentable.get('diastaticPower')),
                    rendimento=safe_float(fermentable.get('yield'), 75),
                    preco_kg=0.00,
                    tipo=tipo
                )
                db.session.add(malte)
                db.session.flush()
                ingredientes_cadastrados['maltes'].append({
                    'id': malte.id,
                    'nome': malte.nome,
                    'fabricante': malte.fabricante,
                    'tipo': malte.tipo
                })
                print(f"✅ Malte cadastrado: {malte.nome} - {malte.fabricante}")
        
        # Processar lúpulos
        for hop in receita_brewfather.ingredients.get('hops', []):
            nome = safe_string(hop.get('name'))
            fabricante = safe_string(hop.get('origin'), 'Não Aplicável')
            origem = safe_string(hop.get('origin'), 'Desconhecida')
            
            if not nome:
                continue
                
            # Verificar se já existe
            existente = Lupulo.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if not existente:
                # Determinar formato
                formato = determinar_formato_lupulo(hop.get('form', ''))
                
                lupulo = Lupulo(
                    nome=nome,
                    fabricante=fabricante,
                    alpha_acidos=safe_float(hop.get('alpha')),
                    beta_acidos=safe_float(hop.get('beta')),
                    formato=formato,
                    origem=origem,
                    preco_kg=0.00,
                    aroma=safe_string(hop.get('use'), 'Geral')
                )
                db.session.add(lupulo)
                db.session.flush()
                ingredientes_cadastrados['lupulos'].append({
                    'id': lupulo.id,
                    'nome': lupulo.nome,
                    'fabricante': lupulo.fabricante,
                    'formato': lupulo.formato
                })
                print(f"✅ Lúpulo cadastrado: {lupulo.nome} - {lupulo.fabricante}")
        
        # Processar leveduras
        for yeast in receita_brewfather.ingredients.get('yeasts', []):
            nome = safe_string(yeast.get('name'))
            fabricante = safe_string(yeast.get('laboratory'), 'Desconhecido')
            
            if not nome:
                continue
                
            # Verificar se já existe
            existente = Levedura.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if not existente:
                # Determinar formato
                formato = determinar_formato_levedura(yeast.get('type', ''))
                floculacao = determinar_floculacao_levedura(yeast.get('flocculation', ''))
                
                levedura = Levedura(
                    nome=nome,
                    fabricante=fabricante,
                    formato=formato,
                    atenuacao=safe_float(yeast.get('attenuation'), 75),
                    temp_fermentacao=determinar_temp_fermentacao(yeast.get('name', '')),
                    preco_unidade=0.00,
                    floculacao=floculacao
                )
                db.session.add(levedura)
                db.session.flush()
                ingredientes_cadastrados['leveduras'].append({
                    'id': levedura.id,
                    'nome': levedura.nome,
                    'fabricante': levedura.fabricante,
                    'formato': levedura.formato
                })
                print(f"✅ Levedura cadastrada: {levedura.nome} - {levedura.fabricante}")
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f"Cadastrados: {len(ingredientes_cadastrados['maltes'])} maltes, "
                      f"{len(ingredientes_cadastrados['lupulos'])} lúpulos, "
                      f"{len(ingredientes_cadastrados['leveduras'])} leveduras",
            'ingredientes_cadastrados': ingredientes_cadastrados
        }
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao cadastrar insumos automaticamente: {e}")
        return {'success': False, 'error': str(e)}


# Funções auxiliares para determinar valores padrão
def determinar_tipo_malte(nome):
    """Determina o tipo de malte baseado no nome"""
    
    
    #Sem frescura, só uma lógica simples
    return  nome.lower()
    nome_lower = nome.lower()
    
    if any(palavra in nome_lower for palavra in ['pilsen', 'pilsner', 'lager']):
        return 'Pilsen'
    elif any(palavra in nome_lower for palavra in ['pale', 'pale ale', '2-row']):
        return 'Pale Ale'
    elif any(palavra in nome_lower for palavra in ['munich', 'munique']):
        return 'Munich'
    elif any(palavra in nome_lower for palavra in ['caramelo', 'caramel', 'crystal']):
        return 'Caramelo'
    elif any(palavra in nome_lower for palavra in ['chocolate', 'choco']):
        return 'Chocolate'
    elif any(palavra in nome_lower for palavra in ['trigo', 'wheat']):
        return 'Trigo'
    elif any(palavra in nome_lower for palavra in ['cevada', 'barley']):
        return 'Cevada'
    else:
        return 'Base'

def determinar_formato_lupulo(formato_brewfather):
    """Converte formato do BrewFather para formato local"""
    formatos = {
        'pellet': 'Pellet',
        'leaf': 'Folha',
        'plug': 'Plug',
        'extract': 'Extrato'
    }
    return formatos.get(formato_brewfather.lower(), 'Pellet')

def determinar_formato_levedura(tipo_brewfather):
    """Converte tipo de levedura do BrewFather para formato local"""
    if tipo_brewfather and 'liquid' in tipo_brewfather.lower():
        return 'Líquida'
    else:
        return 'Seca'

def determinar_floculacao_levedura(floculacao_brewfather):
    """Converte floculação do BrewFather para formato local"""
    floculacoes = {
        'low': 'Baixa',
        'medium': 'Média',
        'high': 'Alta',
        'very high': 'Muito Alta'
    }
    return floculacoes.get(floculacao_brewfather.lower(), 'Média')

def determinar_temp_fermentacao(nome_levedura):
    """Determina temperatura de fermentação baseada no nome da levedura"""
    nome_lower = nome_levedura.lower()
    
    if any(palavra in nome_lower for palavra in ['lager', 'pilsner', 'california']):
        return 12.0  # Leveduras lager
    elif any(palavra in nome_lower for palavra in ['ale', 'english', 'belgian']):
        return 20.0  # Leveduras ale
    elif any(palavra in nome_lower for palavra in ['saison', 'belgian']):
        return 25.0  # Leveduras de alta temperatura
    else:
        return 18.0  # Padrão    