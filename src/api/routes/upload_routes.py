# routes/upload_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required
import pandas as pd
from model.ingredientes import Malte, Lupulo, Levedura
from db.database import db

upload_bp = Blueprint('upload', __name__)

@upload_bp.route('/upload/maltes', methods=['POST'])
@login_required
def upload_maltes():
    """Upload de planilha de maltes"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    try:
        # Ler arquivo Excel
        df = pd.read_excel(file)
        
        # Validar colunas
        required_columns = ['Nome', 'Fabricante', 'Cor_EBC', 'Poder_Diastatico', 'Rendimento', 'Preco_Kg', 'Tipo']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': f'Colunas obrigatórias: {required_columns}'}), 400
        
        # Processar dados
        maltes_criados = 0
        for _, row in df.iterrows():
            malte = Malte(
                nome=row['Nome'],
                fabricante=row['Fabricante'],
                cor_ebc=float(row['Cor_EBC']),
                poder_diastatico=float(row['Poder_Diastatico']),
                rendimento=float(row['Rendimento']),
                preco_kg=float(row['Preco_Kg']),
                tipo=row['Tipo']
            )
            db.session.add(malte)
            maltes_criados += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{maltes_criados} maltes importados com sucesso',
            'quantidade': maltes_criados
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 400

@upload_bp.route('/upload/lupulos', methods=['POST'])
@login_required
def upload_lupulos():
    """Upload de planilha de lúpulos"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    try:
        # Ler arquivo Excel
        df = pd.read_excel(file)
        
        # Validar colunas
        required_columns = ['Nome', 'Fabricante', 'Alpha_Acidos', 'Beta_Acidos', 'Formato', 'Origem', 'Preco_Kg', 'Aroma']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': f'Colunas obrigatórias: {required_columns}'}), 400
        
        # Processar dados
        lupulos_criados = 0
        for _, row in df.iterrows():
            lupulo = Lupulo(
                nome=row['Nome'],
                fabricante=row['Fabricante'],
                alpha_acidos=float(row['Alpha_Acidos']),
                beta_acidos=float(row['Beta_Acidos']),
                formato=row['Formato'],
                origem=row['Origem'],
                preco_kg=float(row['Preco_Kg']),
                aroma=row['Aroma']
            )
            db.session.add(lupulo)
            lupulos_criados += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{lupulos_criados} lúpulos importados com sucesso',
            'quantidade': lupulos_criados
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 400

@upload_bp.route('/upload/leveduras', methods=['POST'])
@login_required
def upload_leveduras():
    """Upload de planilha de leveduras"""
    if 'file' not in request.files:
        return jsonify({'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
    
    try:
        # Ler arquivo Excel
        df = pd.read_excel(file)
        
        # Validar colunas
        required_columns = ['Nome', 'Fabricante', 'Formato', 'Atenuacao', 'Temp_Fermentacao', 'Preco_Unidade', 'Floculacao']
        if not all(col in df.columns for col in required_columns):
            return jsonify({'error': f'Colunas obrigatórias: {required_columns}'}), 400
        
        # Processar dados
        leveduras_criadas = 0
        for _, row in df.iterrows():
            levedura = Levedura(
                nome=row['Nome'],
                fabricante=row['Fabricante'],
                formato=row['Formato'],
                atenuacao=float(row['Atenuacao']),
                temp_fermentacao=float(row['Temp_Fermentacao']),
                preco_unidade=float(row['Preco_Unidade']),
                floculacao=row['Floculacao']
            )
            db.session.add(levedura)
            leveduras_criadas += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'{leveduras_criadas} leveduras importadas com sucesso',
            'quantidade': leveduras_criadas
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'Erro ao processar arquivo: {str(e)}'}), 400
    