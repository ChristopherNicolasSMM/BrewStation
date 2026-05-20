# test_sqlalchemy_connection.py
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv('src/.env')

def test_sqlalchemy_connection():
    """Teste de conexão usando SQLAlchemy"""
    
    # String de conexão
    user = 'neondb_owner'
    password = 'npg_OgaVoGv46drL'
    host = 'ep-divine-hall-a4j3irz1-pooler.us-east-1.aws.neon.tech'
    port = '5432'
    database = 'neondb'

    encoded_password = quote_plus(password)
    conn_str = f'postgresql://{user}:{encoded_password}@{host}:{port}/{database}?sslmode=require'
    
    print("🔗 Testando conexão com SQLAlchemy...")
    print(f"String: {conn_str.split('@')[0]}@***")
    
    try:
        # Criar engine
        engine = create_engine(conn_str, echo=False)
        
        # Testar conexão
        with engine.connect() as conn:
            # Teste 1: Versão do PostgreSQL
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ PostgreSQL: {version.split(',')[0]}")
            
            # Teste 2: Database atual
            result = conn.execute(text("SELECT current_database()"))
            db_name = result.scalar()
            print(f"✅ Database: {db_name}")
            
            # Teste 3: Listar tabelas
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            tables = [row[0] for row in result]
            print(f"✅ Tabelas encontradas: {len(tables)}")
            for table in tables[:5]:  # Mostrar apenas as 5 primeiras
                print(f"   - {table}")
            if len(tables) > 5:
                print(f"   ... e mais {len(tables) - 5} tabelas")
                
        return True
        
    except Exception as e:
        print(f"❌ Erro no SQLAlchemy: {e}")
        return False

if __name__ == '__main__':
    test_sqlalchemy_connection()