# /var/www/christophernsmm_pythonanywhere_com_wsgi.py

import sys
import os

# Configuração do ambiente
project_home = '/home/ChristopherNSMM/BrewStation'
src_path = os.path.join(project_home, 'src')
venv_path = os.path.join(project_home, 'venv')

print("=== Iniciando WSGI ===")
print(f"Project: {project_home}")
print(f"Source: {src_path}")

# Adiciona paths ao sys.path
sys.path.insert(0, project_home)
sys.path.insert(0, src_path)

# Configura o ambiente virtual
if os.path.exists(venv_path):
    python_version = f'python{sys.version_info.major}.{sys.version_info.minor}'
    site_packages = os.path.join(venv_path, 'lib', python_version, 'site-packages')
    
    if os.path.exists(site_packages):
        sys.path.insert(0, site_packages)
        print(f"✅ Venv: {site_packages}")
    else:
        # Fallback
        import glob
        site_packages_glob = os.path.join(venv_path, 'lib', 'python*', 'site-packages')
        possible_paths = glob.glob(site_packages_glob)
        if possible_paths:
            sys.path.insert(0, possible_paths[0])
            print(f"✅ Venv (fallback): {possible_paths[0]}")
        else:
            print("⚠️  Venv não configurado")

print(f"Python path: {sys.path}")

# Importa a aplicação
try:
    from main import create_app
    application = create_app()
    print("✅ Aplicação Flask iniciada!")
    
except Exception as e:
    print(f"❌ Erro: {e}")
    # Fallback CORRIGIDO
    from flask import Flask
    application = Flask(__name__)
    
    # Salva o erro em uma variável global do módulo
    error_message = str(e)
    
    @application.route('/')
    def error():
        return f"Erro na aplicação: {error_message}", 500

print("=== WSGI Configurado ===")