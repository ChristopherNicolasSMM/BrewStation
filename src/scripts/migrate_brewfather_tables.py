"""
Script para migrar dados das tabelas BrewFather sem prefixo para tabelas com prefixo.
"""

import sys
from pathlib import Path
import os

# Adicionar src ao path
script_dir = Path(__file__).parent
src_path = script_dir.parent
os.chdir(str(src_path))
sys.path.insert(0, str(src_path))

from db.database import db
from sqlalchemy import inspect, text
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/brewstation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def get_table_columns(table_name):
    """Obtém lista de colunas de uma tabela"""
    inspector = inspect(db.engine)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return columns

def migrate_table(old_name, new_name):
    """Migra dados de uma tabela antiga para uma nova"""
    try:
        inspector = inspect(db.engine)
        all_tables = inspector.get_table_names()
        
        if old_name not in all_tables:
            print(f"  ⚠️  Tabela {old_name} não existe, pulando...")
            return 0
        
        if new_name not in all_tables:
            print(f"  ⚠️  Tabela {new_name} não existe, criando estrutura primeiro...")
            print(f"     Execute 'flask recreate-plugin-tables' primeiro!")
            return 0
        
        # Obter colunas de ambas as tabelas
        old_columns = get_table_columns(old_name)
        new_columns = get_table_columns(new_name)
        
        # Encontrar colunas comuns
        common_columns = [col for col in old_columns if col in new_columns]
        
        if not common_columns:
            print(f"  ⚠️  Nenhuma coluna comum encontrada entre {old_name} e {new_name}")
            return 0
        
        # Verificar se já existem dados na nova tabela
        existing_count = db.session.execute(text(f"SELECT COUNT(*) FROM {new_name}")).scalar()
        if existing_count > 0:
            print(f"  ⚠️  Tabela {new_name} já possui {existing_count} registros")
            response = input(f"     Deseja continuar e adicionar mais registros? (s/N): ")
            if response.lower() != 's':
                return 0
        
        # Contar registros na tabela antiga
        old_count = db.session.execute(text(f"SELECT COUNT(*) FROM {old_name}")).scalar()
        
        if old_count == 0:
            print(f"  ℹ️  Tabela {old_name} está vazia, nada para migrar")
            return 0
        
        # Construir query de inserção
        columns_str = ', '.join(common_columns)
        placeholders = ', '.join([f':{col}' for col in common_columns])
        
        # Selecionar dados da tabela antiga
        select_query = text(f"SELECT {columns_str} FROM {old_name}")
        old_data = db.session.execute(select_query).fetchall()
        
        # Inserir na nova tabela
        insert_query = text(f"""
            INSERT INTO {new_name} ({columns_str})
            VALUES ({placeholders})
        """)
        
        migrated = 0
        for row in old_data:
            row_dict = {col: getattr(row, col) for col in common_columns}
            try:
                db.session.execute(insert_query, row_dict)
                migrated += 1
            except Exception as e:
                print(f"     ⚠️  Erro ao migrar registro: {e}")
                continue
        
        db.session.commit()
        print(f"  ✅ Migrados {migrated} de {old_count} registros de {old_name} para {new_name}")
        
        return migrated
        
    except Exception as e:
        print(f"  ❌ Erro ao migrar {old_name} -> {new_name}: {e}")
        db.session.rollback()
        return 0

with app.app_context():
    print("=" * 60)
    print("MIGRAÇÃO DE TABELAS BREWFATHER")
    print("=" * 60)
    
    migrations = {
        'brewfather_recipes': 'plugin_integ_bFather_brewfather_recipes',
        'brewfather_batches': 'plugin_integ_bFather_brewfather_batches',
        'brewfather_inventory': 'plugin_integ_bFather_brewfather_inventory',
        'brewfather_sync': 'plugin_integ_bFather_brewfather_sync'
    }
    
    total_migrated = 0
    
    for old_name, new_name in migrations.items():
        print(f"\nMigrando {old_name} -> {new_name}...")
        count = migrate_table(old_name, new_name)
        total_migrated += count
    
    print("\n" + "=" * 60)
    print(f"✅ Migração concluída! Total de registros migrados: {total_migrated}")
    print("=" * 60)
    
    if total_migrated > 0:
        print("\n⚠️  IMPORTANTE: Após verificar que os dados foram migrados corretamente,")
        print("   você pode remover as tabelas antigas manualmente se desejar.")

