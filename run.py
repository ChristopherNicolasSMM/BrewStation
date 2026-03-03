#!/usr/bin/env python
"""
Script de execução do BrewStation.
Permite iniciar a aplicação a partir da raiz do projeto.
"""

import sys
import os
import argparse
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from flask import Flask
    from core.plugin_manager import PluginManager

# Adicionar src ao path para imports funcionarem
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(project_root))

# Mudar para o diretório src para garantir que os caminhos relativos funcionem
# Mas manter referência ao diretório original para .env
original_cwd = os.getcwd()
os.chdir(src_path)

# Ajustar variável de ambiente para o .env estar no lugar certo
# O main.py carrega de Path("src") / ".env", mas estamos em src/, então precisa ser relativo
env_path = project_root / "src" / ".env"
if env_path.exists():
    os.environ["ENV_FILE"] = str(env_path)



def start():
    """Inicia o servidor Flask."""
    print("🚀 Iniciando BrewStation...")
    print(f"📁 Diretório de trabalho: {os.getcwd()}")
    print("-" * 60)

    # Importar e executar main.py
    try:
        import main

        # Verificar se o app foi criado
        if not hasattr(main, "app"):
            print("❌ Erro: Aplicação Flask não foi criada corretamente.")
            sys.exit(1)

        app = main.app

        # Obter configurações de host, porta e debug
        host = os.getenv("HOST", "0.0.0.0")
        port = int(os.getenv("PORT", 5000))
        debug = os.getenv("DEBUG", "True").lower() == "true"

        # HTTPS opcional (default: true se DEBUG)
        https_enabled = os.getenv("HTTPS", "true" if debug else "false").lower() == "true"
        scheme = "https" if https_enabled else "http"

        print(f"🌐 Servidor iniciando em {scheme}://{host}:{port}")
        print(f"🔧 Debug: {debug}")
        print(f"🔒 HTTPS: {https_enabled}")
        print(f"📝 Logs: logs/application.log")


        run_kwargs = dict(
            host=host,
            port=port,
            debug=debug,
            use_reloader=False,  # evita problemas de caminho ao rodar via run.py
        )

        cert_file = Path(os.getenv("SSL_CERT_FILE", project_root / "cert.pem")).resolve()
        key_file  = Path(os.getenv("SSL_KEY_FILE", project_root / "key.pem")).resolve()

        if https_enabled:
            if not cert_file.exists():
                raise FileNotFoundError(f"Certificado não encontrado: {cert_file}")
            if not key_file.exists():
                raise FileNotFoundError(f"Chave privada não encontrada: {key_file}")

            run_kwargs["ssl_context"] = (str(cert_file), str(key_file))
            print(f"🔒 Incluido certificados para o SSL em BrewStation: {cert_file} / {key_file}")
        
        print("-" * 60)
        print("✅ BrewStation rodando! Pressione Ctrl+C para parar.")
        print("-" * 60)
        app.run(**run_kwargs)

    except KeyboardInterrupt:
        print("\n\n🛑 Servidor interrompido pelo usuário.")
        # se você usa original_cwd, garanta que ele existe no escopo
        # os.chdir(original_cwd)
        sys.exit(0)

    except Exception as e:
        print(f"❌ Erro ao iniciar o servidor: {e}")
        import traceback
        traceback.print_exc()
        # os.chdir(original_cwd)
        sys.exit(1)


def show_help():
    """Mostra ajuda sobre os comandos disponíveis."""
    print("""
🍺 BrewStation - Script de Execução

Uso:
    python run.py <comando> [opções]

Comandos disponíveis:
    start       Inicia o servidor Flask
    plugin      Gerencia plugins (criar, instalar, ativar, desativar)
    help        Mostra esta mensagem de ajuda

Exemplos:
    python run.py start
    python run.py plugin -h
    python run.py help

Variáveis de ambiente:
    HOST        Host do servidor (padrão: 0.0.0.0)
    PORT        Porta do servidor (padrão: 5000)
    DEBUG       Modo debug (padrão: True)
    FLASK_ENV   Ambiente (DEV/PRD)

Para mais informações, consulte a documentação em docs/
    """)


def handle_plugin_command():
    """Gerencia comandos de plugin."""
    # Importar módulos necessários primeiro
    from flask import Flask
    from utils.plugin_generator import PluginGenerator
    from core.plugin_manager import PluginManager
    
    parser = argparse.ArgumentParser(
        prog='python run.py plugin',
        description='Gerencia plugins do BrewStation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Documentação:
    Para mais informações sobre plugins, consulte:
    - docs/PLUGIN_SYSTEM.md
    - docs/PLUGIN_DEVELOPMENT.md
    - docs/PLUGIN_MENU_CONFIG.md

Exemplos:
    # Criar plugin interativo
    python run.py plugin -c
    
    # Criar plugin direto
    python run.py plugin -c meu_plugin "Meu Plugin"
    
    # Instalar plugin
    python run.py plugin -i meu_plugin
    
    # Ativar plugin
    python run.py plugin -a meu_plugin
    
    # Desativar plugin
    python run.py plugin -d meu_plugin
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-c', '--create', nargs='*', metavar=('NOME', 'MENU'),
                      help='Cria um novo plugin template. Use sem argumentos para modo interativo.')
    group.add_argument('-i', '--install', metavar='NOME',
                      help='Instala um plugin da pasta plugins/')
    group.add_argument('-a', '--activate', metavar='NOME',
                      help='Ativa um plugin instalado')
    group.add_argument('-d', '--deactivate', metavar='NOME',
                      help='Desativa um plugin ativo')
    
    args = parser.parse_args(sys.argv[2:])
    
    # Criar app Flask temporário para comandos
    app = Flask(__name__)
    
    # Configurar banco de dados (mesma lógica do dev_database.py)
    current_dir = Path.cwd()
    if current_dir.name == 'src':
        # Já estamos em src/, usar caminho relativo
        db_path = Path('instance')
    else:
        # Estamos na raiz, usar caminho com src/
        db_path = Path('src/instance')
    
    # Criar diretório se não existir
    db_path.mkdir(parents=True, exist_ok=True)
    
    # Configurar SQLite com caminho absoluto
    database_uri = f"sqlite:///{db_path.absolute()}/brewstation.db"
    app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    plugins_dir = Path("plugins")
    plugins_config = Path("plugins/plugins.json")
    
    if args.create is not None:
        # Criar plugin
        if len(args.create) == 0:
            # Modo interativo
            create_plugin_interactive(plugins_dir)
        elif len(args.create) == 2:
            # Modo direto
            plugin_name, menu_label = args.create
            generator = PluginGenerator(plugins_dir)
            generator.create_plugin_template(
                plugin_name=plugin_name,
                menu_label=menu_label,
                description=f"Plugin {menu_label}",
                author="BrewStation User",
                version="1.0.0"
            )
        else:
            print("❌ Erro: Use 'python run.py plugin -c [nome] [menu]' ou 'python run.py plugin -c' para modo interativo")
            sys.exit(1)
    
    elif args.install:
        # Instalar plugin
        install_plugin(app, plugins_dir, plugins_config, args.install)
    
    elif args.activate:
        # Ativar plugin
        activate_plugin(app, plugins_dir, plugins_config, args.activate)
    
    elif args.deactivate:
        # Desativar plugin
        deactivate_plugin(app, plugins_dir, plugins_config, args.deactivate)


def create_plugin_interactive(plugins_dir: Path):
    """Cria plugin em modo interativo."""
    from utils.plugin_generator import PluginGenerator
    
    print("\n🔧 Criar Novo Plugin")
    print("-" * 60)
    
    # Nome do plugin
    plugin_name = input("Nome do plugin (diretório, ex: meu_plugin): ").strip()
    if not plugin_name:
        print("❌ Erro: Nome do plugin é obrigatório")
        sys.exit(1)
    
    # Nome no menu
    menu_label = input("Nome exibido no menu (ex: Meu Plugin): ").strip()
    if not menu_label:
        menu_label = plugin_name.replace('_', ' ').title()
        print(f"⚠️  Usando '{menu_label}' como nome do menu")
    
    # Descrição
    description = input("Descrição do plugin (opcional): ").strip()
    if not description:
        description = f"Plugin {menu_label}"
    
    # Autor
    author = input("Autor (opcional): ").strip()
    if not author:
        author = "BrewStation User"
    
    # Versão
    version = input("Versão (padrão: 1.0.0): ").strip()
    if not version:
        version = "1.0.0"
    
    print("\n📦 Criando plugin...")
    generator = PluginGenerator(plugins_dir)
    generator.create_plugin_template(
        plugin_name=plugin_name,
        menu_label=menu_label,
        description=description,
        author=author,
        version=version
    )


def install_plugin(app: Any, plugins_dir: Path, plugins_config: Path, plugin_name: str):
    """Instala um plugin."""
    try:
        from flask import Flask
        from core.plugin_manager import PluginManager
        
        with app.app_context():
            from db.database import db
            # Inicializar db se ainda não foi inicializado
            if not hasattr(db, 'get_app') or db.get_app() is None:
                db.init_app(app)
            
            manager = PluginManager(app, plugins_dir, plugins_config)
            
            # Buscar plugin pelo nome do diretório ou pelo name do install.json
            plugin = manager.get_plugin(plugin_name)
            
            if not plugin:
                print(f"❌ Erro: Plugin '{plugin_name}' não encontrado")
                print(f"💡 Verifique se o plugin existe em {plugins_dir / plugin_name}")
                print(f"💡 Plugins disponíveis: {', '.join(manager.plugins.keys())}")
                sys.exit(1)
            
            # Obter o nome do diretório do plugin
            plugin_dir_name = None
            for p_name, p_instance in manager.plugins.items():
                if p_instance is plugin:
                    plugin_dir_name = p_name
                    break
            
            if not plugin_dir_name:
                print(f"❌ Erro: Não foi possível determinar o nome do diretório do plugin")
                sys.exit(1)
            
            if plugin.is_installed:
                print(f"ℹ️  Plugin '{plugin_dir_name}' já está instalado")
            else:
                print(f"📦 Instalando plugin '{plugin_dir_name}'...")
                if manager.install_plugin(plugin_dir_name):
                    print(f"✅ Plugin '{plugin_dir_name}' instalado com sucesso!")
                else:
                    print(f"❌ Erro ao instalar plugin '{plugin_dir_name}'")
                    sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def activate_plugin(app: Any, plugins_dir: Path, plugins_config: Path, plugin_name: str):
    """Ativa um plugin."""
    try:
        from flask import Flask
        from core.plugin_manager import PluginManager
        
        with app.app_context():
            from db.database import db
            # Inicializar db se ainda não foi inicializado
            if not hasattr(db, 'get_app') or db.get_app() is None:
                db.init_app(app)
            
            manager = PluginManager(app, plugins_dir, plugins_config)
            plugin = manager.get_plugin(plugin_name)
            
            if not plugin:
                print(f"❌ Erro: Plugin '{plugin_name}' não encontrado")
                print(f"💡 Plugins disponíveis: {', '.join(manager.plugins.keys())}")
                sys.exit(1)
            
            # Obter o nome do diretório do plugin
            plugin_dir_name = None
            for p_name, p_instance in manager.plugins.items():
                if p_instance is plugin:
                    plugin_dir_name = p_name
                    break
            
            if not plugin_dir_name:
                print(f"❌ Erro: Não foi possível determinar o nome do diretório do plugin")
                sys.exit(1)
            
            if not plugin.is_installed:
                print(f"❌ Erro: Plugin '{plugin_dir_name}' não está instalado")
                print(f"💡 Instale primeiro com: python run.py plugin -i {plugin_dir_name}")
                sys.exit(1)
            
            if plugin.is_active:
                print(f"ℹ️  Plugin '{plugin_dir_name}' já está ativo")
            else:
                print(f"🟢 Ativando plugin '{plugin_dir_name}'...")
                if manager.activate_plugin(plugin_dir_name):
                    print(f"✅ Plugin '{plugin_dir_name}' ativado com sucesso!")
                else:
                    print(f"❌ Erro ao ativar plugin '{plugin_dir_name}'")
                    sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def deactivate_plugin(app: Any, plugins_dir: Path, plugins_config: Path, plugin_name: str):
    """Desativa um plugin."""
    try:
        from flask import Flask
        from core.plugin_manager import PluginManager
        
        with app.app_context():
            from db.database import db
            # Inicializar db se ainda não foi inicializado
            if not hasattr(db, 'get_app') or db.get_app() is None:
                db.init_app(app)
            
            manager = PluginManager(app, plugins_dir, plugins_config)
            plugin = manager.get_plugin(plugin_name)
            
            if not plugin:
                print(f"❌ Erro: Plugin '{plugin_name}' não encontrado")
                print(f"💡 Plugins disponíveis: {', '.join(manager.plugins.keys())}")
                sys.exit(1)
            
            # Obter o nome do diretório do plugin
            plugin_dir_name = None
            for p_name, p_instance in manager.plugins.items():
                if p_instance is plugin:
                    plugin_dir_name = p_name
                    break
            
            if not plugin_dir_name:
                print(f"❌ Erro: Não foi possível determinar o nome do diretório do plugin")
                sys.exit(1)
            
            if not plugin.is_active:
                print(f"ℹ️  Plugin '{plugin_dir_name}' já está desativado")
            else:
                print(f"🔴 Desativando plugin '{plugin_dir_name}'...")
                if manager.deactivate_plugin(plugin_dir_name):
                    print(f"✅ Plugin '{plugin_dir_name}' desativado com sucesso!")
                else:
                    print(f"❌ Erro ao desativar plugin '{plugin_dir_name}'")
                    sys.exit(1)
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Função principal do script."""
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        start()
    elif command == "plugin":
        handle_plugin_command()
    elif command == "help" or command == "--help" or command == "-h":
        show_help()
    else:
        print(f"❌ Comando desconhecido: {command}")
        print("\nUse 'python run.py help' para ver os comandos disponíveis.")
        sys.exit(1)


if __name__ == "__main__":
    main()

