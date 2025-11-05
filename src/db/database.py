# src/db/database.py
from flask_sqlalchemy import SQLAlchemy
import os
from pathlib import Path

db = SQLAlchemy()

def init_db(app):
    """Inicializa o banco de dados"""
    try:
        # Garantir que o diretório existe
        db_path = Path('instance')
        db_path.mkdir(exist_ok=True)
        
        # Configurar SQLite com caminho absoluto
        database_uri = f"sqlite:///{db_path.absolute()}/brewstation.db"
        app.config['SQLALCHEMY_DATABASE_URI'] = database_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        print(f"Database path: {database_uri}")
        
        # Inicializar db com app
        db.init_app(app)
        
        # Importar modelos DEPOIS de inicializar o db
        with app.app_context():
            # Importar todos os modelos para garantir registro
            import model.user
            import model.config
            import model.equipamento
            # Adicione outros modelos conforme necessário
            
            # Criar tabelas
            db.create_all()
            print("Tabelas criadas com sucesso!")
            
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        raise

def get_db():
    """Retorna a instância do banco de dados"""
    return db