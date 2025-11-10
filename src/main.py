"""
BrewStation - Sistema de Precificação de Cervejas
Arquivo principal da aplicação
"""

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
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
    
    # Registrar blueprints - IMPORTAR DENTRO DO CONTEXTO
    with app.app_context():
        #from api.routes import api_bp        
        from api.routes import all_blueprints
        from controller.auth import auth_bp
        from controller.main import main_bp
        
        app.register_blueprint(main_bp)
        # Registrar todos os blueprints
        for bp in all_blueprints:
            app.register_blueprint(bp, url_prefix='/api')
        #app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(auth_bp, url_prefix='/auth')        
    
    # Context processor
    @app.context_processor
    def inject_notifications_count():
        from flask_login import current_user
        try:
            if current_user.is_authenticated:
                from model.notification import Notification
                unread = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
                return {'unread_notifications_count': unread}
        except Exception:
            pass
        return {'unread_notifications_count': 0}
    
    # Inicialização dentro do app context
    with app.app_context():
        from db.database import db
        from model.user import User
        from model.config import Configuracao
        
        try:
            # Criar admin user
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@brew-station.com',
                    is_admin=True
                )
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                print("Usuário admin criado: admin / admin123")

            # Inicializar configurações
            Configuracao.initialize_default_configs()
            print("Configurações padrão inicializadas com sucesso")
            
        except Exception as e:
            print(f"Erro na inicialização: {e}")
            db.session.rollback()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)