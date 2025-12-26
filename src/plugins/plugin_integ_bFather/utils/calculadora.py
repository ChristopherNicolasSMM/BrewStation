"""
Sistema de cálculo de preços para cervejas
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from model.ingredientes import Malte, Lupulo, Levedura, Receita, IngredienteReceita

@dataclass
class IngredienteCalculo:
    """Classe para ingredientes no cálculo"""
    nome: str
    quantidade: float
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

class CalculadoraPrecos:
    """Classe principal para cálculos de preços"""
    
    def __init__(self):
        self.eficiencia_padrao = 75.0  # Eficiência padrão de 75%
    
    def calcular_custo_ingredientes(self, receita: Receita, ingredientes: List[IngredienteReceita], 
                                  maltes: Dict[int, Malte], lupulos: Dict[int, Lupulo], 
                                  leveduras: Dict[int, Levedura]) -> List[IngredienteCalculo]:
        """Calcula o custo dos ingredientes de uma receita"""
        ingredientes_calculo = []
        
        for ingrediente in ingredientes:
            if ingrediente.tipo_ingrediente == 'malte':
                malte = maltes.get(ingrediente.ingrediente_id)
                if malte:
                    custo_total = (ingrediente.quantidade * malte.preco_kg) / 1000  # Converter kg para g
                    ingredientes_calculo.append(IngredienteCalculo(
                        nome=malte.nome,
                        quantidade=ingrediente.quantidade,
                        preco_unitario=malte.preco_kg,
                        custo_total=custo_total
                    ))
            
            elif ingrediente.tipo_ingrediente == 'lupulo':
                lupulo = lupulos.get(ingrediente.ingrediente_id)
                if lupulo:
                    custo_total = (ingrediente.quantidade * lupulo.preco_kg) / 1000  # Converter kg para g
                    ingredientes_calculo.append(IngredienteCalculo(
                        nome=lupulo.nome,
                        quantidade=ingrediente.quantidade,
                        preco_unitario=lupulo.preco_kg,
                        custo_total=custo_total
                    ))
            
            elif ingrediente.tipo_ingrediente == 'levedura':
                levedura = leveduras.get(ingrediente.ingrediente_id)
                if levedura:
                    custo_total = ingrediente.quantidade * levedura.preco_unidade
                    ingredientes_calculo.append(IngredienteCalculo(
                        nome=levedura.nome,
                        quantidade=ingrediente.quantidade,
                        preco_unitario=levedura.preco_unidade,
                        custo_total=custo_total
                    ))
        
        return ingredientes_calculo
    
    def calcular_preco_por_litro(self, ingredientes_calculo: List[IngredienteCalculo], 
                               receita: Receita) -> float:
        """Calcula o preço por litro baseado nos ingredientes"""
        custo_total_ingredientes = sum(ingrediente.custo_total for ingrediente in ingredientes_calculo)
        
        # Aplicar eficiência da receita
        eficiencia = receita.eficiencia / 100.0
        custo_por_litro = custo_total_ingredientes / (receita.volume_litros * eficiencia)
        
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
    
    def calcular_receita_completa(self, receita: Receita, ingredientes: List[IngredienteReceita],
                                maltes: Dict[int, Malte], lupulos: Dict[int, Lupulo],
                                leveduras: Dict[int, Levedura], quantidade_ml: int,
                                custo_embalagem: float, custo_impressao: float,
                                custo_tampinha: float, percentual_lucro: float,
                                margem_cartao: float, percentual_sanitizacao: float,
                                percentual_impostos: float) -> Dict:
        """Calcula o preço completo de uma receita"""
        
        # Calcular ingredientes
        ingredientes_calculo = self.calcular_custo_ingredientes(
            receita, ingredientes, maltes, lupulos, leveduras
        )
        
        # Calcular preço por litro
        valor_litro_base = self.calcular_preco_por_litro(ingredientes_calculo, receita)
        
        # Calcular preço final
        resultado = self.calcular_preco_final(
            valor_litro_base, quantidade_ml, custo_embalagem, custo_impressao,
            custo_tampinha, percentual_lucro, margem_cartao, percentual_sanitizacao,
            percentual_impostos
        )
        
        return {
            'receita': receita.to_dict(),
            'ingredientes': [ingrediente.__dict__ for ingrediente in ingredientes_calculo],
            'valor_litro_base': valor_litro_base,
            'resultado': resultado.__dict__,
            'resumo': {
                'custo_total_ingredientes': sum(ingrediente.custo_total for ingrediente in ingredientes_calculo),
                'valor_final': resultado.valor_venda_final,
                'margem_lucro': percentual_lucro,
                'quantidade_ml': quantidade_ml
            }
        }
