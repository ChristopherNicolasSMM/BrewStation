"""
BrewStation - Sistema de Precificação de Cervejas
Arquivo principal da aplicação
"""

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente - caminho correto
load_dotenv('src/.env')

def create_app():
    """Factory function para criar a aplicação Flask"""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Configurações básicas
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['DEBUG'] = os.getenv('DEBUG', 'True').lower() == 'true'
    app.config['UPLOAD_FOLDER'] = os.getenv('UPLOAD_FOLDER', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16777216))
    
    # Configurar banco de dados PRIMEIRO
    from db.database import init_db
    init_db(app)
    
    # Configurar Login Manager DEPOIS do banco
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        from model.user import User
        return User.query.get(int(user_id))
    
    # Habilitar CORS
    CORS(app)
    
    # Registrar blueprints
    register_blueprints(app)
    
    # Context processor para notificações
    register_context_processors(app)
    
    # Inicialização dentro do app context
    initialize_app_data(app)
    
    return app

def register_blueprints(app):
    """Registra todos os blueprints da aplicação"""
    try:
        from api.routes import all_blueprints
        from controller.auth import auth_bp
        from controller.main import main_bp
        
        # Registrar blueprint principal
        app.register_blueprint(main_bp)
        
        # Registrar blueprints da API
        for bp in all_blueprints:
            app.register_blueprint(bp, url_prefix='/api')
            
        # Registrar blueprint de autenticação
        app.register_blueprint(auth_bp, url_prefix='/auth')
        
        print("✅ Blueprints registrados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao registrar blueprints: {e}")
        raise

def register_context_processors(app):
    """Registra context processors"""
    @app.context_processor
    def inject_notifications_count():
        from flask_login import current_user
        try:
            if current_user.is_authenticated:
                from model.notification import Notification
                unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
                return {'unread_notifications_count': unread}
        except Exception as e:
            # Log silencioso em produção
            if app.config['DEBUG']:
                print(f"Erro no context processor: {e}")
        return {'unread_notifications_count': 0}

def initialize_app_data(app):
    """Inicializa dados padrão da aplicação"""
    with app.app_context():
        from db.database import db
        from model.user import User
        from model.config import Configuracao
        
        try:
            # Criar admin user se não existir
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@brew-station.com',
                    is_admin=True,
                    is_active=True  # Importante para PostgreSQL
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("✅ Usuário admin criado: admin / admin123")
            else:
                print("✅ Usuário admin já existe")

            # Inicializar configurações padrão
            Configuracao.initialize_default_configs()
            print("✅ Configurações padrão inicializadas com sucesso")
            
            # Testar conexão com o banco
            from db.database import test_connection
            test_connection()
            
        except Exception as e:
            print(f"❌ Erro na inicialização: {e}")
            db.session.rollback()
            # Não levantar exceção para não quebrar a aplicação

# =================================================================
# ESTA É A CORREÇÃO PRINCIPAL PARA O VERCEL/GUNICORN:
# DEFINIR A VARIÁVEL 'app' no escopo global
# =================================================================
app = create_app()

if __name__ == '__main__':
    # Configurações do servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    
    print(f"🚀 Iniciando BrewStation em http://{host}:{port}")
    print(f"🔧 Modo debug: {debug}")
    
    app.run(host=host, port=port, debug=debug)