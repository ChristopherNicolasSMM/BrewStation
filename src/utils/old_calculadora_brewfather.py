# src/utils/calculadora_brewfather.py
"""
Sistema de cálculo de preços para cervejas com BrewFather
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from model.ingredientes import Malte, Lupulo, Levedura
from model.brewfather import BrewFatherRecipe

@dataclass
class IngredienteCalculo:
    """Classe para ingredientes no cálculo"""
    tipo: str
    nome: str
    quantidade: float
    unidade: str
    preco_unitario: float
    custo_total: float

@dataclass
class ResultadoCalculo:
    """Resultado do cálculo de preços"""
    custo_ingredientes: float
    custo_total_litro: float
    custo_embalagem: float
    custo_impressao: float
    custo_tampinha: float
    subtotal: float
    valor_lucro: float
    margem_cartao: float
    valor_sanitizacao: float
    valor_total: float
    valor_impostos: float
    valor_venda_final: float

class CalculadoraPrecosBrewFather:
    """Classe principal para cálculos de preços com BrewFather"""
    
    def __init__(self):
        self.eficiencia_padrao = 75.0  # Eficiência padrão de 75%
    
    def calcular_custo_ingredientes_brewfather(self, receita: BrewFatherRecipe) -> List[IngredienteCalculo]:
        """Calcula o custo dos ingredientes de uma receita do BrewFather"""
        ingredientes_calculo = []
        
        if not receita.ingredients:
            return ingredientes_calculo
        
        # Processar fermentáveis (maltes)
        for fermentable in receita.ingredients.get('fermentables', []):
            nome = fermentable.get('name', '')
            quantidade = fermentable.get('amount', 0)  # em kg
            preco_kg = self._obter_preco_malte(nome, fermentable.get('supplier', ''))
            custo_total = quantidade * preco_kg
            
            ingredientes_calculo.append(IngredienteCalculo(
                tipo='malte',
                nome=nome,
                quantidade=quantidade,
                unidade='kg',
                preco_unitario=preco_kg,
                custo_total=custo_total
            ))
        
        # Processar lúpulos
        for hop in receita.ingredients.get('hops', []):
            nome = hop.get('name', '')
            quantidade = hop.get('amount', 0)  # em kg
            preco_kg = self._obter_preco_lupulo(nome, hop.get('supplier', ''))
            custo_total = quantidade * preco_kg
            
            ingredientes_calculo.append(IngredienteCalculo(
                tipo='lupulo',
                nome=nome,
                quantidade=quantidade * 1000,  # converter para gramas
                unidade='g',
                preco_unitario=preco_kg,
                custo_total=custo_total
            ))
        
        # Processar leveduras
        for yeast in receita.ingredients.get('yeasts', []):
            nome = yeast.get('name', '')
            quantidade = yeast.get('amount', 1)  # normalmente 1 unidade
            preco_unidade = self._obter_preco_levedura(nome, yeast.get('supplier', ''))
            custo_total = quantidade * preco_unidade
            
            ingredientes_calculo.append(IngredienteCalculo(
                tipo='levedura',
                nome=nome,
                quantidade=quantidade,
                unidade='unidade',
                preco_unitario=preco_unidade,
                custo_total=custo_total
            ))
        
        return ingredientes_calculo
    
    def _obter_preco_malte(self, nome: str, fabricante: str) -> float:
        """Obtém preço do malte do banco de dados ou usa padrão"""
        try:
            # Buscar no banco de dados primeiro
            malte = Malte.query.filter_by(
                nome=nome, 
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if malte and malte.preco_kg > 0:
                return malte.preco_kg
        except:
            pass
        
        # Preços padrão por tipo de malte (em R$/kg)
        precos_padrao = {
            'pilsen': 8.50,
            'pale': 9.00,
            'munich': 10.00,
            'caramelo': 12.00,
            'chocolate': 15.00,
            'cevada': 7.50,
            'trigo': 9.50
        }
        
        nome_lower = nome.lower()
        for tipo, preco in precos_padrao.items():
            if tipo in nome_lower:
                return preco
        
        return 9.00  # Preço médio padrão
    
    def _obter_preco_lupulo(self, nome: str, fabricante: str) -> float:
        """Obtém preço do lúpulo do banco de dados ou usa padrão"""
        try:
            # Buscar no banco de dados primeiro
            lupulo = Lupulo.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if lupulo and lupulo.preco_kg > 0:
                return lupulo.preco_kg
        except:
            pass
        
        # Preços padrão por tipo de lúpulo (em R$/kg)
        precos_padrao = {
            'cascade': 120.00,
            'citra': 180.00,
            'mosaic': 200.00,
            'amarillo': 150.00,
            'centennial': 130.00,
            'saaz': 110.00,
            'hallertau': 100.00
        }
        
        nome_lower = nome.lower()
        for tipo, preco in precos_padrao.items():
            if tipo in nome_lower:
                return preco
        
        return 140.00  # Preço médio padrão
    
    def _obter_preco_levedura(self, nome: str, fabricante: str) -> float:
        """Obtém preço da levedura do banco de dados ou usa padrão"""
        try:
            # Buscar no banco de dados primeiro
            levedura = Levedura.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if levedura and levedura.preco_unidade > 0:
                return levedura.preco_unidade
        except:
            pass
        
        # Preços padrão (em R$/unidade)
        return 25.00  # Preço médio padrão
    
    def calcular_preco_por_litro(self, ingredientes_calculo: List[IngredienteCalculo], 
                               receita: BrewFatherRecipe) -> float:
        """Calcula o preço por litro baseado nos ingredientes"""
        custo_total_ingredientes = sum(ingrediente.custo_total for ingrediente in ingredientes_calculo)
        
        # Usar eficiência da receita do BrewFather ou padrão
        eficiencia = (receita.efficiency or self.eficiencia_padrao) / 100.0
        volume_litros = receita.batch_size or 20.0  # Volume padrão de 20L
        
        if volume_litros > 0 and eficiencia > 0:
            custo_por_litro = custo_total_ingredientes / (volume_litros * eficiencia)
        else:
            custo_por_litro = custo_total_ingredientes / 20.0  # Fallback para 20L
            
        return custo_por_litro
    
    def calcular_preco_final(self, valor_litro_base: float, quantidade_ml: int,
                           custo_embalagem: float, custo_impressao: float, 
                           custo_tampinha: float, percentual_lucro: float,
                           margem_cartao: float, percentual_sanitizacao: float,
                           percentual_impostos: float) -> ResultadoCalculo:
        """Calcula o preço final do produto"""
        
        # Calcular custo base por quantidade
        custo_base = (valor_litro_base * quantidade_ml) / 1000
        
        # Subtotal (custo base + embalagem + impressão + tampinha)
        subtotal = custo_base + custo_embalagem + custo_impressao + custo_tampinha
        
        # Calcular lucro
        valor_lucro = subtotal * (percentual_lucro / 100.0)
        
        # Calcular margem do cartão
        margem_cartao_valor = subtotal * (margem_cartao / 100.0)
        
        # Calcular sanitização
        valor_sanitizacao = subtotal * (percentual_sanitizacao / 100.0)
        
        # Valor total antes dos impostos
        valor_total = subtotal + valor_lucro + margem_cartao_valor + valor_sanitizacao
        
        # Calcular impostos
        valor_impostos = valor_total * (percentual_impostos / 100.0)
        
        # Valor final de venda
        valor_venda_final = valor_total + valor_impostos
        
        return ResultadoCalculo(
            custo_ingredientes=custo_base,
            custo_total_litro=valor_litro_base,
            custo_embalagem=custo_embalagem,
            custo_impressao=custo_impressao,
            custo_tampinha=custo_tampinha,
            subtotal=subtotal,
            valor_lucro=valor_lucro,
            margem_cartao=margem_cartao_valor,
            valor_sanitizacao=valor_sanitizacao,
            valor_total=valor_total,
            valor_impostos=valor_impostos,
            valor_venda_final=valor_venda_final
        )
    
    def calcular_receita_brewfather(self, receita: BrewFatherRecipe, quantidade_ml: int,
                                  custo_embalagem: float, custo_impressao: float,
                                  custo_tampinha: float, percentual_lucro: float,
                                  margem_cartao: float, percentual_sanitizacao: float,
                                  percentual_impostos: float) -> Dict:
        """Calcula o preço completo de uma receita do BrewFather"""
        
        if not receita:
            raise ValueError("Receita não pode ser None")
        
        # Calcular ingredientes
        ingredientes_calculo = self.calcular_custo_ingredientes_brewfather(receita)
        
        # Calcular preço por litro
        valor_litro_base = self.calcular_preco_por_litro(ingredientes_calculo, receita)
        
        # Calcular preço final
        resultado = self.calcular_preco_final(
            valor_litro_base, quantidade_ml, custo_embalagem, custo_impressao,
            custo_tampinha, percentual_lucro, margem_cartao, percentual_sanitizacao,
            percentual_impostos
        )
        
        return {
            'receita': {
                'id': receita.id,
                'nome': receita.name,
                'estilo': receita.style,
                'volume_litros': receita.batch_size,
                'eficiencia': receita.efficiency,
                'abv': receita.abv,
                'ibu': receita.ibu
            },
            'ingredientes': [{
                'tipo': ing.tipo,
                'nome': ing.nome,
                'quantidade': ing.quantidade,
                'unidade': ing.unidade,
                'preco_unitario': ing.preco_unitario,
                'custo_total': ing.custo_total
            } for ing in ingredientes_calculo],
            'valor_litro_base': valor_litro_base,
            'resultado': {
                'custo_ingredientes': resultado.custo_ingredientes,
                'custo_total_litro': resultado.custo_total_litro,
                'custo_embalagem': resultado.custo_embalagem,
                'custo_impressao': resultado.custo_impressao,
                'custo_tampinha': resultado.custo_tampinha,
                'subtotal': resultado.subtotal,
                'valor_lucro': resultado.valor_lucro,
                'margem_cartao': resultado.margem_cartao,
                'valor_sanitizacao': resultado.valor_sanitizacao,
                'valor_total': resultado.valor_total,
                'valor_impostos': resultado.valor_impostos,
                'valor_venda_final': resultado.valor_venda_final
            },
            'resumo': {
                'custo_total_ingredientes': sum(ing.custo_total for ing in ingredientes_calculo),
                'valor_final': resultado.valor_venda_final,
                'margem_lucro': percentual_lucro,
                'quantidade_ml': quantidade_ml
            }
        }