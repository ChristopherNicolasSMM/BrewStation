# src/db/database.py
from flask_sqlalchemy import SQLAlchemy
import os
from pathlib import Path
from sqlalchemy import text

db = SQLAlchemy()

def init_db(app):
    """Inicializa o banco de dados"""
    try:
        # Garantir que o diretório existe
        db_path = Path('src/instance')
        db_path.mkdir(exist_ok=True)
        
        # Configurar SQLite com caminho absoluto
        database_uri = f"sqlite:///{db_path.absolute()}/brewstation.db"
        print(database_uri)
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
            import model.ingredientes            
            import model.sessao_brasagem
            import model.dispositivos
            import model.notification   
            import model.brewfather
                       
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

def test_connection():
    """Testa a conexão com o banco de dados"""
    from flask import current_app
    try:
        with current_app.app_context():
            # A correção é aqui: usa text() para encapsular a string SQL
            db.session.execute(text('SELECT 1'))
            # A chamada db.session.commit() é necessária se uma transação for aberta,
            # mas SELECT 1 geralmente não a abre e é apenas para verificação de conexão.
            # No entanto, em alguns casos, chamar commit ou fechar a sessão pode ser mais seguro.
            db.session.commit()
            
            print("✅ Conexão com o banco de dados estabelecida com sucesso!")
            return True
    except Exception as e:
        # Revertendo a sessão em caso de erro para liberar recursos.
        db.session.rollback()
        print(f"❌ Erro na conexão com o banco: {e}")
        return False