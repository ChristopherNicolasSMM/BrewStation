# src/utils/calculadora_brewfather.py
"""
Sistema de cálculo de preços para cervejas com BrewFather
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from model.ingredientes import Malte, Lupulo, Levedura
from model.config import Configuracao
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
            custo_total = quantidade * ( preco_kg / 1000 )  # converter para g
            print(f"Lúpulo: {nome}, Quantidade: {quantidade}, Preço Kg: {preco_kg}")
            
            ingredientes_calculo.append(IngredienteCalculo(
                tipo='lupulo',
                nome=nome,
                quantidade=quantidade,
                unidade='g',
                preco_unitario=preco_kg,
                custo_total=custo_total
            ))
        
        # Processar leveduras
        for yeast in receita.ingredients.get('yeasts', []):
            nome = yeast.get('name', '')
            quantidade = yeast.get('amount', 1)  # normalmente 1 unidade
            preco_unidade = self._obter_preco_levedura(nome, yeast.get('supplier', ''))
            print(f"Levedura: {nome}, Quantidade: {quantidade}, Preço Unidade: {preco_unidade}")
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
        """Obtém preço do malte do banco de dados"""
        try:
            # Primeiro, tentar buscar por nome exato e fabricante
            malte = Malte.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if malte and malte.preco_kg > 0:
                return malte.preco_kg
            
            # Se não encontrou, buscar apenas por nome (ignorando fabricante)
            malte = Malte.query.filter_by(
                nome=nome,
                ativo=True
            ).first()
            
            if malte and malte.preco_kg > 0:
                return malte.preco_kg
            
            # Se ainda não encontrou, buscar por similaridade no nome
            maltes_similares = Malte.query.filter(
                Malte.nome.ilike(f'%{nome}%'),
                Malte.ativo == True
            ).all()
            
            if maltes_similares:
                # Retornar o preço do primeiro malte similar encontrado
                for malte_similar in maltes_similares:
                    if malte_similar.preco_kg > 0:
                        return malte_similar.preco_kg
            
        except Exception as e:
            print(f"Erro ao buscar preço do malte {nome}: {e}")
            
        # Buscar preço padrão das configurações
        preco_padrao = Configuracao.get_config('DEFAULT_MALTE_VALUE')
        if preco_padrao:
            try:
                return float(preco_padrao)
            except (ValueError, TypeError):
                pass            
        
        ## Preços padrão como fallback (em R$/kg)       
        return 25.00  # Preço médio padrão
    
    def _obter_preco_lupulo(self, nome: str, fabricante: str) -> float:
        """Obtém preço do lúpulo do banco de dados"""
        try:
            # Primeiro, tentar buscar por nome exato e fabricante
            lupulo = Lupulo.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if lupulo and lupulo.preco_kg > 0:
                return lupulo.preco_kg
            
            # Se não encontrou, buscar apenas por nome (ignorando fabricante)
            lupulo = Lupulo.query.filter_by(
                nome=nome,
                ativo=True
            ).first()
            
            if lupulo and lupulo.preco_kg > 0:
                return lupulo.preco_kg
            
            # Buscar por similaridade no nome
            lupulos_similares = Lupulo.query.filter(
                Lupulo.nome.ilike(f'%{nome}%'),
                Lupulo.ativo == True
            ).all()
            
            if lupulos_similares:
                for lupulo_similar in lupulos_similares:
                    if lupulo_similar.preco_kg > 0:
                        return lupulo_similar.preco_kg
                            
        except Exception as e:
            print(f"Erro ao buscar preço do lúpulo {nome}: {e}")
        
        
        # Buscar preço padrão das configurações
        preco_padrao = Configuracao.get_config('DEFAULT_HOPS_VALUE')
        if preco_padrao:
            try:
                return float(preco_padrao)
            except (ValueError, TypeError):
                pass        
        
        ## Preços padrão como fallback (em R$/kg)        
        return 400.00  # Preço médio padrão
    
    def _obter_preco_levedura(self, nome: str, fabricante: str) -> float:
        """Obtém preço da levedura do banco de dados"""
        try:
            # Primeiro, tentar buscar por nome exato e fabricante
            levedura = Levedura.query.filter_by(
                nome=nome,
                fabricante=fabricante,
                ativo=True
            ).first()
            
            if levedura and levedura.preco_unidade > 0:
                return levedura.preco_unidade
            
            # Se não encontrou, buscar apenas por nome (ignorando fabricante)
            levedura = Levedura.query.filter_by(
                nome=nome,
                ativo=True
            ).first()
            
            if levedura and levedura.preco_unidade > 0:
                return levedura.preco_unidade
            
            # Buscar por similaridade no nome
            leveduras_similares = Levedura.query.filter(
                Levedura.nome.ilike(f'%{nome}%'),
                Levedura.ativo == True
            ).all()
            
            if leveduras_similares:
                for levedura_similar in leveduras_similares:
                    if levedura_similar.preco_unidade > 0:
                        return levedura_similar.preco_unidade
            
        except Exception as e:
            print(f"Erro ao buscar preço da levedura {nome}: {e}")
        
        
        # Buscar preço padrão das configurações
        preco_padrao = Configuracao.get_config('DEFAULT_YEAST_VALUE')
        if preco_padrao:
            try:
                return float(preco_padrao)
            except (ValueError, TypeError):
                pass        
        
        # Preço padrão como fallback (em R$/unidade)
        return 30.00
    
    
    
    def calcular_preco_por_litro(self, ingredientes_calculo: List[IngredienteCalculo], 
                               receita: BrewFatherRecipe) -> float:
        """Calcula o preço por litro baseado nos ingredientes"""
        custo_total_ingredientes = sum(ingrediente.custo_total for ingrediente in ingredientes_calculo)
        
        # Usar eficiência da receita do BrewFather ou padrão
        #eficiencia = (receita.efficiency or self.eficiencia_padrao) / 100.0
        volume_litros = receita.batch_size or 20.0  # Volume padrão de 20L
        
        #if volume_litros > 0 and eficiencia > 0:
        if volume_litros > 0:
            custo_por_litro = custo_total_ingredientes / volume_litros
        else:
            custo_por_litro = custo_total_ingredientes / 20.0  # Fallback para 20L
            
        return custo_por_litro
    
    
    
    
    def calcular_preco_final(self, valor_litro_base: float, quantidade_ml: int,
                           custo_embalagem: float, custo_impressao: float, 
                           custo_tampinha: float, percentual_lucro: float,
                           margem_cartao: float, percentual_sanitizacao: float,
                           percentual_impostos: float) -> ResultadoCalculo:
        """Calcula o preço final do produto"""
        
        #print(2 * "\n")
        #print(94 * "-")
        #print("----------------------------------- Cálculo de Preço Final -----------------------------------")
        #print(94 * "-")
        
    
        # Calcular custo base por quantidade
        custo_base = (valor_litro_base * quantidade_ml) / 1000
        #print(f"Valor Litro Base: R$ {valor_litro_base:.2f}")
        #print(f"Quantidade (ml): {quantidade_ml} ml")     
        #print(f"Custo Base (Ingredientes): R$ {custo_base:.2f}")
        #print("\n")
        
    
        # Subtotal (custo base + embalagem + impressão + t
        subtotal = custo_base + custo_embalagem + custo_impressao + custo_tampinha
        #print(f"Custo Embalagem: R$ {custo_embalagem:.2f}")
        #print(f"Custo Impressão: R$ {custo_impressao:.2f}")
        #print(f"Custo Tampinha: R$ {custo_tampinha:.2f}")
        #print(f"Subtotal (antes de lucro e impostos): R$ {subtotal:.2f}")   
        #print("\n")
        
        
        # Calcular lucro
        valor_lucro = subtotal * (percentual_lucro / 100.0)
        #print(f"Percentual de Lucro: {percentual_lucro}%")
        #print(f"Valor do Lucro: R$ {valor_lucro:.2f}")
        #print("\n")
        
        
        # Calcular margem do cartão
        margem_cartao_valor = subtotal * (margem_cartao / 100.0)
        #print(f"Margem do Cartão: {margem_cartao}%")
        #print(f"Valor da Margem do Cartão: R$ {margem_cartao_valor:.2f}")
        #print("\n")
        
        # Calcular sanitização
        valor_sanitizacao = subtotal * (percentual_sanitizacao / 100.0)
        #print(f"Percentual de Sanitização: {percentual_sanitizacao}%")
        #print(f"Valor da Sanitização: R$ {valor_sanitizacao:.2f}")
        #print("\n")
        
        
        # Valor total antes dos impostos
        valor_total = subtotal + valor_lucro + margem_cartao_valor + valor_sanitizacao
        #print(f"Valor Total (antes de impostos): R$ {valor_total:.2f}")
        #print("\n")
        
        
        # Calcular impostos
        valor_impostos = valor_total * (percentual_impostos / 100.0)
        #print(f"Percentual de Impostos: {percentual_impostos}%")
        #print(f"Valor dos Impostos: R$ {valor_impostos:.2f}")
        #print("\n")
        
        
        # Valor final de venda
        valor_venda_final = valor_total + valor_impostos
        #print(f"Valor Final de Venda: R$ {valor_venda_final:.2f}")
        #print(94 * "-")
        
        
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