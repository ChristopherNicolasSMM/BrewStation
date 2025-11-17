from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from model.envase import TipoEmbalagem, Embalagem, Envase, ItemEnvase
from model.brewfather import BrewFatherBatch
from db.database import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

envase_bp = Blueprint('envase', __name__)

# ===== TIPOS DE EMBALAGEM =====
@envase_bp.route('/envase/tipos-embalagem')
@login_required
def get_tipos_embalagem():
    """Lista todos os tipos de embalagem"""
    try:
        tipos = TipoEmbalagem.query.filter_by(ativo=True).order_by(TipoEmbalagem.nome).all()
        return jsonify({
            'success': True,
            'tipos': [tipo.to_dict() for tipo in tipos]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar tipos de embalagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@envase_bp.route('/envase/tipos-embalagem', methods=['POST'])
@login_required
def criar_tipo_embalagem():
    """Cria um novo tipo de embalagem"""
    try:
        data = request.get_json()
        
        tipo = TipoEmbalagem(
            nome=data['nome'],
            descricao=data.get('descricao'),
            capacidade_ml=data.get('capacidade_ml'),
            cor=data.get('cor'),
            material=data.get('material')
        )
        
        db.session.add(tipo)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'tipo': tipo.to_dict(),
            'message': 'Tipo de embalagem criado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar tipo de embalagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@envase_bp.route('/envase/tipos-embalagem/<int:tipo_id>', methods=['PUT'])
@login_required
def atualizar_tipo_embalagem(tipo_id):
    """Atualiza um tipo de embalagem"""
    try:
        tipo = TipoEmbalagem.query.get_or_404(tipo_id)
        data = request.get_json()
        
        tipo.nome = data.get('nome', tipo.nome)
        tipo.descricao = data.get('descricao', tipo.descricao)
        tipo.capacidade_ml = data.get('capacidade_ml', tipo.capacidade_ml)
        tipo.cor = data.get('cor', tipo.cor)
        tipo.material = data.get('material', tipo.material)
        tipo.ativo = data.get('ativo', tipo.ativo)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'tipo': tipo.to_dict(),
            'message': 'Tipo de embalagem atualizado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar tipo de embalagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== EMBALAGENS =====
@envase_bp.route('/envase/embalagens')
@login_required
def get_embalagens():
    """Lista todas as embalagens"""
    try:
        embalagens = Embalagem.query.join(TipoEmbalagem).filter(Embalagem.ativo == True).order_by(TipoEmbalagem.nome).all()
        return jsonify({
            'success': True,
            'embalagens': [emb.to_dict() for emb in embalagens]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar embalagens: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@envase_bp.route('/envase/embalagens', methods=['POST'])
@login_required
def criar_embalagem():
    """Cria uma nova embalagem"""
    try:
        data = request.get_json()
               
        # Converter valores numéricos
        tipo_embalagem_id = int(data['tipo_embalagem_id']) if data.get('tipo_embalagem_id') else None
        lote_compra = int(data.get('lote_compra', 0)) if data.get('lote_compra') else 0
        frete = float(data.get('frete', 0)) if data.get('frete') else 0.0
        valor_lote = float(data.get('valor_lote', 0)) if data.get('valor_lote') else 0.0
        estoque_atual = int(data.get('estoque_atual', 0)) if data.get('estoque_atual') else 0
        estoque_minimo = int(data.get('estoque_minimo', 0)) if data.get('estoque_minimo') else 0
        
        embalagem = Embalagem(
            tipo_embalagem_id=tipo_embalagem_id,
            fornecedor=data.get('fornecedor', '').strip(),
            referencia=data.get('referencia', '').strip(),
            link_referencia=data.get('link_referencia', '').strip(),
            lote_compra=lote_compra,
            frete=frete,
            valor_lote=valor_lote,
            estoque_atual=estoque_atual,
            estoque_minimo=estoque_minimo,
            ativo=data.get('ativo', True)
        )
        
        # Calcular valor unitário
        embalagem.calcular_valor_unidade()
        
        db.session.add(embalagem)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'embalagem': embalagem.to_dict(),
            'message': 'Embalagem criada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar embalagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    

@envase_bp.route('/envase/embalagens/<int:embalagem_id>', methods=['PUT'])
@login_required
def atualizar_embalagem(embalagem_id):
    """Atualiza uma embalagem"""
    try:
        embalagem = Embalagem.query.get_or_404(embalagem_id)
        data = request.get_json()
        
        # Converter valores numéricos
        tipo_embalagem_id = int(data.get('tipo_embalagem_id', embalagem.tipo_embalagem_id)) if data.get('tipo_embalagem_id') else embalagem.tipo_embalagem_id
        lote_compra = int(data.get('lote_compra', embalagem.lote_compra)) if data.get('lote_compra') else embalagem.lote_compra
        frete = float(data.get('frete', embalagem.frete)) if data.get('frete') else embalagem.frete
        valor_lote = float(data.get('valor_lote', embalagem.valor_lote)) if data.get('valor_lote') else embalagem.valor_lote
        estoque_atual = int(data.get('estoque_atual', embalagem.estoque_atual)) if data.get('estoque_atual') else embalagem.estoque_atual
        estoque_minimo = int(data.get('estoque_minimo', embalagem.estoque_minimo)) if data.get('estoque_minimo') else embalagem.estoque_minimo
        
        embalagem.tipo_embalagem_id = tipo_embalagem_id
        embalagem.fornecedor = data.get('fornecedor', embalagem.fornecedor)
        embalagem.referencia = data.get('referencia', embalagem.referencia)
        embalagem.link_referencia = data.get('link_referencia', embalagem.link_referencia)
        embalagem.lote_compra = lote_compra
        embalagem.frete = frete
        embalagem.valor_lote = valor_lote
        embalagem.estoque_atual = estoque_atual
        embalagem.estoque_minimo = estoque_minimo
        embalagem.ativo = data.get('ativo', embalagem.ativo)
        
        # Recalcular valor unitário
        embalagem.calcular_valor_unidade()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'embalagem': embalagem.to_dict(),
            'message': 'Embalagem atualizada com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar embalagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500    
    
    

# ===== ENVASES =====
@envase_bp.route('/envase/envases')
@login_required
def get_envases():
    """Lista todos os envases"""
    try:
        envases = Envase.query.order_by(Envase.data_envase.desc()).all()
        return jsonify({
            'success': True,
            'envases': [envase.to_dict() for envase in envases]
        })
    except Exception as e:
        logger.error(f"Erro ao buscar envases: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@envase_bp.route('/envase/envases', methods=['POST'])
@login_required
def criar_envase():
    """Cria um novo envase"""
    try:
        data = request.get_json()
        
        # Converter valores numéricos
        lote_id = int(data.get('lote_id')) if data.get('lote_id') else None
        quantidade_litros = float(data.get('quantidade_litros', 0)) if data.get('quantidade_litros') else 0.0
        
        envase = Envase(
            lote_id=lote_id,
            quantidade_litros=quantidade_litros,
            data_envase=datetime.fromisoformat(data['data_envase']) if data.get('data_envase') else datetime.utcnow(),
            tipo_envase=data.get('tipo_envase'),
            observacoes=data.get('observacoes'),
            status=data.get('status', 'planejado')
        )
        
        db.session.add(envase)
        db.session.commit()
        
        # Adicionar itens do envase se fornecidos
        if 'itens_envase' in data:
            for item_data in data['itens_envase']:
                embalagem_id = int(item_data.get('embalagem_id')) if item_data.get('embalagem_id') else None
                quantidade = int(item_data.get('quantidade', 0)) if item_data.get('quantidade') else 0
                capacidade_ml = int(item_data.get('capacidade_ml', 0)) if item_data.get('capacidade_ml') else 0
                
                item = ItemEnvase(
                    envase_id=envase.id,
                    embalagem_id=embalagem_id,
                    quantidade=quantidade,
                    capacidade_ml=capacidade_ml
                )
                db.session.add(item)
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'envase': envase.to_dict(),
            'message': 'Envase criado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar envase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
    

@envase_bp.route('/envase/envases/<int:envase_id>', methods=['PUT'])
@login_required
def atualizar_envase(envase_id):
    """Atualiza um envase"""
    try:
        envase = Envase.query.get_or_404(envase_id)
        data = request.get_json()
        
        envase.lote_id = data.get('lote_id', envase.lote_id)
        envase.quantidade_litros = data.get('quantidade_litros', envase.quantidade_litros)
        envase.data_envase = datetime.fromisoformat(data['data_envase']) if data.get('data_envase') else envase.data_envase
        envase.tipo_envase = data.get('tipo_envase', envase.tipo_envase)
        envase.observacoes = data.get('observacoes', envase.observacoes)
        envase.status = data.get('status', envase.status)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'envase': envase.to_dict(),
            'message': 'Envase atualizado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar envase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ===== DADOS PARA FORMULÁRIOS =====
@envase_bp.route('/envase/dados-formulario')
@login_required
def get_dados_formulario():
    """Retorna dados necessários para os formulários"""
    try:
        lotes = BrewFatherBatch.query.filter(BrewFatherBatch.status.in_(['Completed', 'Conditioning'])).order_by(BrewFatherBatch.brew_date.desc()).all()
        tipos_embalagem = TipoEmbalagem.query.filter_by(ativo=True).order_by(TipoEmbalagem.nome).all()
        embalagens = Embalagem.query.filter_by(ativo=True).join(TipoEmbalagem).order_by(TipoEmbalagem.nome).all()
        return jsonify({
            'success': True,
            'lotes': [{
                'id': lote.batch_no,
                'nome': f"{lote.recipe_name} - Lote {lote.batch_no}"
                #'batch_size': lote.batch_size
            } for lote in lotes],
            'tipos_embalagem': [tipo.to_dict() for tipo in tipos_embalagem],
            'embalagens': [emb.to_dict() for emb in embalagens]
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar dados do formulário: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
    
    
@envase_bp.route('/envase/embalagens/<int:embalagem_id>', methods=['DELETE'])
@login_required
def excluir_embalagem(embalagem_id):
    """Exclui uma embalagem (desativa)"""
    try:
        embalagem = Embalagem.query.get_or_404(embalagem_id)
        embalagem.ativo = False
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Embalagem excluída com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir embalagem: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500    

# ===== PÁGINA PRINCIPAL =====
@envase_bp.route('/envase')
@login_required
def pagina_envase():
    """Página principal do módulo de envase"""
    return render_template('envase.html')