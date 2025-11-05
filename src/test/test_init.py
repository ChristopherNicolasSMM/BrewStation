#!/usr/bin/env python3
"""
Script simples para testar a inicialização do sistema
"""

import sys
import os

# Adicionar o diretório src ao path
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

def test_imports():
    """Testa se todos os imports estão funcionando"""
    try:
        print("🔍 Testando imports...")
        
        # Testar imports básicos
        from db.database import db
        print("✅ Database importado")
        
        from model.user import User
        print("✅ User model importado")
        
        from model.ingredientes import Malte, Lupulo, Levedura, Receita, IngredienteReceita, CalculoPreco
        print("✅ Modelos de ingredientes importados")
        
        from utils.calculadora import CalculadoraPrecos
        print("✅ Calculadora importada")
        
        from api.routes import api_bp
        print("✅ API routes importadas")
        
        from controller.auth import auth_bp
        print("✅ Auth controller importado")
        
        from controller.main import main_bp
        print("✅ Main controller importado")
        
        print("\n🎉 Todos os imports funcionaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no import: {e}")
        return False

def test_app_creation():
    """Testa a criação da aplicação"""
    try:
        print("\n🚀 Testando criação da aplicação...")
        
        from main import create_app
        app = create_app()
        
        print("✅ Aplicação criada com sucesso!")
        print(f"✅ Configuração: {app.config['SQLALCHEMY_DATABASE_URI']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na criação da aplicação: {e}")
        return False

def main():
    """Função principal"""
    print("🍺 PrecificaValirian - Teste de Inicialização")
    print("=" * 50)
    
    # Testar imports
    if not test_imports():
        print("\n❌ Falha nos imports. Verifique os arquivos.")
        return False
    
    # Testar criação da aplicação
    if not test_app_creation():
        print("\n❌ Falha na criação da aplicação.")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Sistema pronto para uso!")
    print("\nPara executar:")
    print("  python src/main.py")
    print("\nAcesse: http://localhost:5000")
    print("Usuário: admin")
    print("Senha: admin123")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
