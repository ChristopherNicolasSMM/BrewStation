#!/usr/bin/env python3
"""
Script de inicialização do ambiente para o sistema BrewStation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_version():
    """Verifica se a versão do Python é compatível"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ é necessário")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detectado")

def create_virtualenv():
    """Cria e ativa a virtual environment"""
    venv_name = "vEnvStation"
    venv_path = Path(venv_name)
    
    if venv_path.exists():
        print(f"✅ Virtual environment '{venv_name}' já existe")
        return venv_name
    
    try:
        print(f"🐍 Criando virtual environment '{venv_name}'...")
        subprocess.check_call([sys.executable, '-m', 'venv', venv_name])
        print(f"✅ Virtual environment '{venv_name}' criada com sucesso")
        return venv_name
    except subprocess.CalledProcessError:
        print(f"❌ Erro ao criar virtual environment '{venv_name}'")
        sys.exit(1)

def get_venv_python(venv_name):
    """Retorna o caminho para o Python da virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join(venv_name, 'Scripts', 'python.exe')
    else:  # Linux/Mac
        return os.path.join(venv_name, 'bin', 'python')

def get_venv_pip(venv_name):
    """Retorna o caminho para o pip da virtual environment"""
    if os.name == 'nt':  # Windows
        return os.path.join(venv_name, 'Scripts', 'pip.exe')
    else:  # Linux/Mac
        return os.path.join(venv_name, 'bin', 'pip')

def install_dependencies(venv_name):
    """Instala dependências do projeto na virtual environment"""
    try:
        pip_executable = get_venv_pip(venv_name)
        
        # Atualizar pip primeiro
        print("📦 Atualizando pip...")
        subprocess.check_call([pip_executable, 'install', '--upgrade', 'pip'])
        
        # Instalar dependências
        print("📦 Instalando dependências do projeto...")
        subprocess.check_call([pip_executable, 'install', '-r', 'requirements.txt'])
        print("✅ Dependências instaladas com sucesso")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar dependências: {e}")
        sys.exit(1)

def create_activation_script(venv_name):
    """Cria script de ativação para facilitar o uso"""
    if os.name == 'nt':  # Windows
        script_content = f'''@echo off
                             echo Ativando virtual environment {venv_name}...
                             call {venv_name}\\Scripts\\activate.bat
                             echo Virtual environment ativada!
                             python src/main.py
                             '''
        script_name = "ativar_venv.bat"
    else:  # Linux/Mac
        script_content = f'''#!/bin/bash
echo "🐍 Ativando virtual environment {venv_name}..."
source {venv_name}/bin/activate
echo "✅ Virtual environment ativada!"
python src/main.py
'''
        script_name = "ativar_venv.sh"
        # Dar permissão de execução no Linux
        Path(script_name).chmod(0o755)
    
    with open(script_name, 'w', encoding='utf-8') as f:
        f.write(script_content)
    
    print(f"✅ Script de ativação '{script_name}' criado")

def check_requirements_file():
    """Verifica se o arquivo requirements.txt existe"""
    if not Path('requirements.txt').exists():
        print("❌ Arquivo requirements.txt não encontrado")
        print("📋 Criando requirements.txt básico...")
        
        basic_requirements = """Flask==2.3.3
                                Flask-Login==0.6.3
                                Flask-SQLAlchemy==3.0.5
                                Flask-CORS==4.0.0
                                SQLAlchemy==2.0.23
                                Werkzeug==2.3.7
                                requests==2.31.0
                                python-dotenv==1.0.0
                                """
        
        with open('requirements.txt', 'w', encoding='utf-8') as f:
            f.write(basic_requirements)
        print("✅ requirements.txt básico criado")

def create_admin_user():
    """Cria usuário administrador padrão"""
    print("✅ Usuário admin será criado automaticamente na primeira execução")

def show_usage_instructions(venv_name):
    """Mostra instruções de uso"""
    print("\n" + "=" * 50)
    print("🎉 Setup concluído com sucesso!")
    
    if os.name == 'nt':  # Windows
        print(f"\nPara ativar a virtual environment:")
        print(f"  {venv_name}\\Scripts\\activate")
        print(f"\nOu use o script criado:")
        print(f"  ativar_venv.bat")
    else:  # Linux/Mac
        print(f"\nPara ativar a virtual environment:")
        print(f"  source {venv_name}/bin/activate")
        print(f"\nOu use o script criado:")
        print(f"  ./ativar_venv.sh")
    
    print(f"\nPara executar o sistema:")
    print("  python src/main.py")
    print("\nAcesse: http://localhost:5000")
    print("Usuário: admin")
    print("Senha: admin123")
    print("\n⚠️  IMPORTANTE: Altere a senha padrão em produção!")

def main():
    """Função principal"""
    print("🍺 PrecificaValirian - Setup Inicial")
    print("=" * 50)
    
    # Verificações iniciais
    check_python_version()
    check_requirements_file()
    
    # Criar virtual environment
    print("\n🐍 Configurando ambiente virtual...")
    venv_name = create_virtualenv()
    
    # Instalar dependências na venv
    print("\n📦 Instalando dependências...")
    install_dependencies(venv_name)
    
    # Criar script de ativação
    print("\n📝 Criando script de ativação...")
    create_activation_script(venv_name)
    
    # Configurações finais
    create_admin_user()
    
    # Mostrar instruções
    show_usage_instructions(venv_name)

if __name__ == '__main__':
    main()