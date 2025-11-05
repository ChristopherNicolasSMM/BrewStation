#!/usr/bin/env python3
"""
Script de inicialização do PrecificaValirian
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

def create_directories():
    """Cria diretórios necessários"""
    directories = [
        'uploads',
        'static/img',
        'static/css',
        'static/js',
        'static/vendor',
        'src/logs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Diretório criado: {directory}")

def copy_niceadmin_assets():
    """Copia assets necessários do NiceAdmin"""
    if os.path.exists('NiceAdmin'):
        # Copiar arquivos CSS e JS principais
        assets_to_copy = [
            ('NiceAdmin/assets/css/style.css', 'static/css/style.css'),
            ('NiceAdmin/assets/js/main.js', 'static/js/main.js'),
            ('NiceAdmin/assets/img/logo.png', 'static/img/logo.png'),
            ('NiceAdmin/assets/img/favicon.png', 'static/img/favicon.png'),
            ('NiceAdmin/assets/img/apple-touch-icon.png', 'static/img/apple-touch-icon.png'),
            ('NiceAdmin/assets/img/profile-img.jpg', 'static/img/profile-img.jpg'),
        ]
        
        for src, dst in assets_to_copy:
            if os.path.exists(src):
                shutil.copy2(src, dst)
                print(f"✅ Asset copiado: {dst}")
        
        # Copiar vendor files
        vendor_dirs = ['bootstrap', 'bootstrap-icons', 'boxicons', 'quill', 'remixicon']
        for vendor_dir in vendor_dirs:
            src_dir = f'NiceAdmin/assets/vendor/{vendor_dir}'
            dst_dir = f'static/vendor/{vendor_dir}'
            if os.path.exists(src_dir):
                shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
                print(f"✅ Vendor copiado: {vendor_dir}")
    else:
        print("⚠️  Pasta NiceAdmin não encontrada. Assets não foram copiados.")

def install_dependencies():
    """Instala dependências do projeto"""
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✅ Dependências instaladas com sucesso")
    except subprocess.CalledProcessError:
        print("❌ Erro ao instalar dependências")
        sys.exit(1)

def create_admin_user():
    """Cria usuário administrador padrão"""
    print("✅ Usuário admin será criado automaticamente na primeira execução")

def main():
    """Função principal"""
    print("🍺 PrecificaValirian - Setup Inicial")
    print("=" * 50)
    
    # Verificações
    check_python_version()
    
    # Criar estrutura
    create_directories()
    copy_niceadmin_assets()
    
    # Instalar dependências
    print("\n📦 Instalando dependências...")
    install_dependencies()
    
    # Configurações finais
    create_admin_user()
    
    print("\n" + "=" * 50)
    print("🎉 Setup concluído com sucesso!")
    print("\nPara executar o sistema:")
    print("  python src/main.py")
    print("\nAcesse: http://localhost:5000")
    print("Usuário: admin")
    print("Senha: admin123")
    print("\n⚠️  IMPORTANTE: Altere a senha padrão em produção!")

if __name__ == '__main__':
    main()
