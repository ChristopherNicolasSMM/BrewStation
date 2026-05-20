"""
Script para diagnosticar e migrar tabelas do BrewFather.
Verifica quais tabelas existem e migra dados se necessário.
"""

import os
import sys
from pathlib import Path

# Adicionar src ao path
script_dir = Path(__file__).parent
src_path = script_dir.parent
os.chdir(str(src_path))
sys.path.insert(0, str(src_path))

from flask import Flask
from sqlalchemy import inspect, text

from db.database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///instance/brewstation.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    inspector = inspect(db.engine)
    all_tables = inspector.get_table_names()
    
    print("=" * 60)
    print("DIAGNÓSTICO DE TABELAS BREWFATHER")
    print("=" * 60)
    
    # Encontrar todas as tabelas relacionadas ao BrewFather
    brewfather_tables = [t for t in all_tables if 'brewfather' in t.lower()]
    
    print(f"\nTabelas encontradas relacionadas ao BrewFather:")
    for table in brewfather_tables:
        count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
        print(f"  - {table}: {count} registros")
    
    # Verificar tabelas esperadas
    expected_tables = {
        'brewfather_recipes': 'plugin_integ_bFather_brewfather_recipes',
        'brewfather_batches': 'plugin_integ_bFather_brewfather_batches',
        'brewfather_inventory': 'plugin_integ_bFather_brewfather_inventory',
        'brewfather_sync': 'plugin_integ_bFather_brewfather_sync'
    }
    
    print(f"\nVerificando migração necessária:")
    migration_needed = False
    
    for old_name, new_name in expected_tables.items():
        old_exists = old_name in all_tables
        new_exists = new_name in all_tables
        
        if old_exists and not new_exists:
            old_count = db.session.execute(text(f"SELECT COUNT(*) FROM {old_name}")).scalar()
            print(f"  ⚠️  {old_name} existe ({old_count} registros) mas {new_name} não existe")
            print(f"     → Migração necessária!")
            migration_needed = True
        elif old_exists and new_exists:
            old_count = db.session.execute(text(f"SELECT COUNT(*) FROM {old_name}")).scalar()
            new_count = db.session.execute(text(f"SELECT COUNT(*) FROM {new_name}")).scalar()
            print(f"  ⚠️  Ambas existem: {old_name} ({old_count}) e {new_name} ({new_count})")
            print(f"     → Verificar duplicação!")
        elif not old_exists and new_exists:
            new_count = db.session.execute(text(f"SELECT COUNT(*) FROM {new_name}")).scalar()
            print(f"  ✅ {new_name} existe ({new_count} registros) - OK")
        else:
            print(f"  ℹ️  Nenhuma tabela encontrada para {old_name}")
    
    print("\n" + "=" * 60)
    
    if migration_needed:
        print("\n⚠️  MIGRAÇÃO NECESSÁRIA DETECTADA")
        print("Execute o script de migração: migrate_brewfather_tables.py")
    else:
        print("\n✅ Todas as tabelas estão corretas!")

