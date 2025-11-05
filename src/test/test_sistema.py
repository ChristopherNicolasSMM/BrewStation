"""
Testes básicos para o sistema PrecificaValirian
"""

import unittest
import sys
import os

# Adicionar o diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.model.ingredientes import Malte, Lupulo, Levedura, Receita
from src.utils.calculadora import CalculadoraPrecos, IngredienteCalculo, ResultadoCalculo

class TestIngredientes(unittest.TestCase):
    """Testes para os modelos de ingredientes"""
    
    def test_malte_creation(self):
        """Testa criação de malte"""
        malte = Malte(
            nome="Pilsner",
            fabricante="Weyermann",
            cor_ebc=3.5,
            poder_diastatico=120,
            rendimento=82,
            preco_kg=8.50,
            tipo="Base"
        )
        
        self.assertEqual(malte.nome, "Pilsner")
        self.assertEqual(malte.fabricante, "Weyermann")
        self.assertEqual(malte.cor_ebc, 3.5)
        self.assertEqual(malte.preco_kg, 8.50)
        self.assertTrue(malte.ativo)
    
    def test_lupulo_creation(self):
        """Testa criação de lúpulo"""
        lupulo = Lupulo(
            nome="Saaz",
            fabricante="Zatec",
            alpha_acidos=3.5,
            beta_acidos=4.0,
            formato="Pellet",
            origem="República Tcheca",
            preco_kg=45.00,
            aroma="Floral, especiado"
        )
        
        self.assertEqual(lupulo.nome, "Saaz")
        self.assertEqual(lupulo.alpha_acidos, 3.5)
        self.assertEqual(lupulo.preco_kg, 45.00)
        self.assertTrue(lupulo.ativo)
    
    def test_levedura_creation(self):
        """Testa criação de levedura"""
        levedura = Levedura(
            nome="Safale US-05",
            fabricante="Fermentis",
            formato="Seca",
            atenuacao=78,
            temp_fermentacao=18,
            preco_unidade=8.50,
            floculacao="Baixa"
        )
        
        self.assertEqual(levedura.nome, "Safale US-05")
        self.assertEqual(levedura.atenuacao, 78)
        self.assertEqual(levedura.preco_unidade, 8.50)
        self.assertTrue(levedura.ativo)

class TestCalculadora(unittest.TestCase):
    """Testes para a calculadora de preços"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.calculadora = CalculadoraPrecos()
        
        # Criar ingredientes de teste
        self.malte = Malte(
            nome="Pilsner",
            fabricante="Weyermann",
            cor_ebc=3.5,
            poder_diastatico=120,
            rendimento=82,
            preco_kg=8.50,
            tipo="Base"
        )
        
        self.lupulo = Lupulo(
            nome="Saaz",
            fabricante="Zatec",
            alpha_acidos=3.5,
            beta_acidos=4.0,
            formato="Pellet",
            origem="República Tcheca",
            preco_kg=45.00,
            aroma="Floral, especiado"
        )
        
        self.levedura = Levedura(
            nome="Safale US-05",
            fabricante="Fermentis",
            formato="Seca",
            atenuacao=78,
            temp_fermentacao=18,
            preco_unidade=8.50,
            floculacao="Baixa"
        )
        
        self.receita = Receita(
            nome="Teste",
            descricao="Receita de teste",
            volume_litros=20,
            eficiencia=75
        )
    
    def test_calculo_preco_final(self):
        """Testa cálculo de preço final"""
        resultado = self.calculadora.calcular_preco_final(
            valor_litro_base=8.00,
            quantidade_ml=500,
            custo_embalagem=2.50,
            custo_impressao=1.00,
            custo_tampinha=0.10,
            percentual_lucro=100.0,
            margem_cartao=20.0,
            percentual_sanitizacao=5.0,
            percentual_impostos=18.0
        )
        
        # Verificar se o resultado é uma instância de ResultadoCalculo
        self.assertIsInstance(resultado, ResultadoCalculo)
        
        # Verificar se os valores são positivos
        self.assertGreater(resultado.valor_venda_final, 0)
        self.assertGreater(resultado.valor_total, 0)
        self.assertGreater(resultado.subtotal, 0)
    
    def test_calculo_ingredientes(self):
        """Testa cálculo de custo de ingredientes"""
        from src.model.ingredientes import IngredienteReceita
        
        ingredientes = [
            IngredienteReceita(
                receita_id=1,
                tipo_ingrediente="malte",
                ingrediente_id=1,
                quantidade=4000  # 4kg
            )
        ]
        
        maltes = {1: self.malte}
        lupulos = {}
        leveduras = {}
        
        ingredientes_calculo = self.calculadora.calcular_custo_ingredientes(
            self.receita, ingredientes, maltes, lupulos, leveduras
        )
        
        self.assertEqual(len(ingredientes_calculo), 1)
        self.assertEqual(ingredientes_calculo[0].nome, "Pilsner")
        self.assertGreater(ingredientes_calculo[0].custo_total, 0)

class TestModelos(unittest.TestCase):
    """Testes para métodos dos modelos"""
    
    def test_malte_to_dict(self):
        """Testa conversão de malte para dicionário"""
        malte = Malte(
            nome="Pilsner",
            fabricante="Weyermann",
            cor_ebc=3.5,
            poder_diastatico=120,
            rendimento=82,
            preco_kg=8.50,
            tipo="Base"
        )
        
        malte_dict = malte.to_dict()
        
        self.assertIsInstance(malte_dict, dict)
        self.assertEqual(malte_dict['nome'], "Pilsner")
        self.assertEqual(malte_dict['fabricante'], "Weyermann")
        self.assertEqual(malte_dict['preco_kg'], 8.50)
        self.assertTrue(malte_dict['ativo'])

def run_tests():
    """Executa todos os testes"""
    print("🧪 Executando testes do PrecificaValirian...")
    print("=" * 50)
    
    # Criar suite de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adicionar testes
    suite.addTests(loader.loadTestsFromTestCase(TestIngredientes))
    suite.addTests(loader.loadTestsFromTestCase(TestCalculadora))
    suite.addTests(loader.loadTestsFromTestCase(TestModelos))
    
    # Executar testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resultado
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ Todos os testes passaram!")
    else:
        print(f"❌ {len(result.failures)} falhas, {len(result.errors)} erros")
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
