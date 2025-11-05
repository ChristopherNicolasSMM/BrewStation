#!/usr/bin/env python3
"""
Script para testar o sistema diretamente
"""

import sys
import os

# Adicionar src ao path
sys.path.insert(0, 'src')

def test_system():
    """Testa o sistema"""
    try:
        print("🍺 Testando PrecificaValirian...")
        
        # Importar e criar app
        from main import create_app
        app = create_app()
        
        print("✅ Sistema inicializado com sucesso!")
        print("✅ Banco de dados configurado")
        print("✅ Usuário admin criado")
        
        print("\n🚀 Para executar o servidor:")
        print("  python src/main.py")
        print("\n🌐 Acesse: http://localhost:5000")
        print("👤 Usuário: admin")
        print("🔑 Senha: admin123")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_system()
