import sys
from pathlib import Path

# Adicionar src ao path para imports
src_path = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from plugins.plugin_integ_bFather.utils.model_loader import (
    TipoEmbalagem, Embalagem, Envase, ItemEnvase, BrewFatherBatch
)
from plugins.plugin_integ_bFather.utils.calculadora_brewfather import CalculadoraPrecosBrewFather
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
    
    
@envase_bp.route('/envase/envases/<int:envase_id>')
@login_required
def get_envase(envase_id):
    """Busca um envase específico pelo ID"""
    try:
        envase = Envase.query.get(envase_id)
        
        if not envase:
            return jsonify({
                'success': False, 
                'error': 'Envase não encontrado'
            }), 404
        
        return jsonify({
            'success': True,
            'envase': envase.to_dict()
        })
    except Exception as e:
        logger.error(f"Erro ao buscar envase {envase_id}: {e}")
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
            'message': 'Envase atualizado com sucesso!'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar envase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
    
@envase_bp.route('/envase/envases/<int:envase_id>', methods=['DELETE'])
@login_required
def delete_envase(envase_id):
    """Exclui um envase específico pelo ID com validações"""
    try:
        envase = Envase.query.get(envase_id)
        
        if not envase:
            return jsonify({
                'success': False, 
                'error': 'Envase não encontrado'
            }), 404
        
        # Verificar se o usuário tem permissão para excluir este envase
        # (se você tiver controle de ownership)
        # if envase.user_id != current_user.id:
        #     return jsonify({
        #         'success': False,
        #         'error': 'Você não tem permissão para excluir este envase'
        #     }), 403
        
        # Verificar se o envase já foi concluído (impedir exclusão)
        if envase.status == 'concluido':
            return jsonify({
                'success': False,
                'error': 'Não é possível excluir um envase concluído'
            }), 400
        
        # Registrar dados do envase antes de excluir (para auditoria)
        envase_data = {
            'id': envase.id,
            'lote_id': envase.lote_id,
            'quantidade_litros': envase.quantidade_litros,
            'data_envase': envase.data_envase.isoformat() if envase.data_envase else None,
            'status': envase.status
        }
        
        db.session.delete(envase)
        db.session.commit()
        
        logger.info(f"Envase excluído: {envase_data}")
        
        return jsonify({
            'success': True,
            'message': 'Envase excluído com sucesso',
            'envase_excluido': envase_data  # Opcional: retornar dados do excluído
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao excluir envase {envase_id}: {e}")
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
    
    
@envase_bp.route('/envase/para-calculo')
@login_required
def get_envases_para_calculo():
    """Retorna envases para uso na calculadora"""
    try:
        envases = Envase.query.filter_by(status='concluido').order_by(Envase.data_envase.desc()).all()
        
        envases_calculo = []
        for envase in envases:
            # Calcular custo médio por litro baseado nos itens do envase
            custo_total = 0.0
            quantidade_total_ml = 0
            
            for item in envase.itens_envase:
                if item.embalagem and item.embalagem.valor_unidade:
                    # Converter para float para evitar problemas com Decimal
                    valor_unidade = float(item.embalagem.valor_unidade)
                    custo_total += item.quantidade * valor_unidade
                    quantidade_total_ml += item.quantidade * item.capacidade_ml
            
            # Converter para litros e calcular custo por litro
            if quantidade_total_ml > 0:
                quantidade_litros = float(quantidade_total_ml) / 1000.0
            else:
                quantidade_litros = float(envase.quantidade_litros) if envase.quantidade_litros else 0.0
            
            if quantidade_litros > 0:
                custo_por_litro = float(custo_total) / float(quantidade_litros)
            else:
                custo_por_litro = 0.0
            
            # Obter nome do lote
            lote_nome = "Não vinculado"
            if envase.lote:
                lote_nome = envase.lote.recipe_name or f"Lote {envase.lote.batch_no}"
            
            envases_calculo.append({
                'id': envase.id,
                'nome': f"{lote_nome} - {quantidade_litros:.1f}L",
                'quantidade_total_litros': quantidade_litros,
                'custo_por_litro': custo_por_litro,
                'data_envase': envase.data_envase.isoformat() if envase.data_envase else None,
                'lote_nome': lote_nome
            })
        
        return jsonify({
            'success': True,
            'envases': envases_calculo
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar envases para cálculo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



from model.calculo_envase import CalculoEnvase  # Adicionar import

@envase_bp.route('/calcular_envase', methods=['POST'])
@login_required
def calcular_envase():
    """Calcular preço baseado em envase (quantidade total e custo por litro)"""
    try:
        data = request.get_json()
        print("Received data for envase calculation:", data)
        
        # Se envase_id for fornecido, buscar dados do envase
        envase_id = data.get('envase_id')
        if envase_id:
            envase = Envase.query.get(envase_id)
            if envase:
                # Usar dados do envase cadastrado
                quantidade_total_litros = float(envase.quantidade_litros) if envase.quantidade_litros else 0.0
                
                # Calcular custo por litro baseado nos itens do envase
                custo_total = 0.0
                quantidade_total_ml = 0
                
                for item in envase.itens_envase:
                    if item.embalagem and item.embalagem.valor_unidade is not None:
                        try:
                            valor_unidade = float(item.embalagem.valor_unidade)
                            custo_total += item.quantidade * valor_unidade
                            quantidade_total_ml += item.quantidade * (item.capacidade_ml or 0)
                        except (TypeError, ValueError):
                            continue
                
                # Se temos dados de ml, usar para cálculo mais preciso
                if quantidade_total_ml > 0:
                    quantidade_litros = float(quantidade_total_ml) / 1000.0
                    custo_por_litro = float(custo_total) / float(quantidade_litros) if quantidade_litros > 0 else 0.0
                else:
                    # Usar dados diretos do envase
                    quantidade_litros = quantidade_total_litros
                    custo_por_litro = 8.5  # Valor padrão se não conseguir calcular
            else:
                return jsonify({'error': 'Envase não encontrado'}), 404
        else:
            # Usar dados manuais do formulário
            quantidade_total_litros = float(data.get('quantidade_total_litros', 0))
            custo_por_litro = float(data.get('custo_por_litro', 0))
        
        quantidade_ml = int(data.get('quantidade_ml', 0))
        
        if not quantidade_total_litros or not custo_por_litro or not quantidade_ml:
            return jsonify({'error': 'Quantidade total, custo por litro e quantidade em ml são obrigatórios'}), 400
        
        # Inicializar calculadora
        calculadora = CalculadoraPrecosBrewFather()
        
        # Calcular custo base para a quantidade total
        custo_total_ingredientes = quantidade_total_litros * custo_por_litro
        
        # Calcular preço final
        resultado = calculadora.calcular_preco_final(
            valor_litro_base=float(custo_por_litro),
            quantidade_ml=int(quantidade_ml),
            custo_embalagem=float(data.get('custo_embalagem', 0)),
            custo_impressao=float(data.get('custo_impressao', 0)),
            custo_tampinha=float(data.get('custo_tampinha', 0)),
            percentual_lucro=float(data.get('percentual_lucro', 30)),
            margem_cartao=float(data.get('margem_cartao', 3.5)),
            percentual_sanitizacao=float(data.get('percentual_sanitizacao', 2.0)),
            percentual_impostos=float(data.get('percentual_impostos', 8.0))
        )
        
        # Calcular total arrecadado
        unidades_produzidas = (quantidade_total_litros * 1000) / quantidade_ml
        total_arrecadado = unidades_produzidas * resultado.valor_venda_final
        
        # Salvar no banco de dados usando o novo modelo
        calculo_envase = CalculoEnvase(
            envase_id=envase_id,
            nome_produto=data.get('nome_produto', 'Cálculo por Envase'),
            quantidade_ml=int(quantidade_ml),
            tipo_embalagem=data.get('tipo_embalagem', 'Garrafa'),
            valor_litro_base=float(custo_por_litro),
            custo_embalagem=float(data.get('custo_embalagem', 0)),
            custo_impressao=float(data.get('custo_impressao', 0)),
            custo_tampinha=float(data.get('custo_tampinha', 0)),
            percentual_lucro=float(data.get('percentual_lucro', 30)),
            margem_cartao=float(data.get('margem_cartao', 3.5)),
            percentual_sanitizacao=float(data.get('percentual_sanitizacao', 2.0)),
            percentual_impostos=float(data.get('percentual_impostos', 8.0)),
            valor_total=float(resultado.valor_total),
            valor_venda_final=float(resultado.valor_venda_final)
        )
        
        db.session.add(calculo_envase)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'resultado': {
                'valor_venda_final': float(resultado.valor_venda_final),
                'valor_total': float(resultado.valor_total),
                'custo_ingredientes': float(resultado.custo_ingredientes),
                'custo_embalagem': float(resultado.custo_embalagem),
                'custo_impressao': float(resultado.custo_impressao),
                'custo_tampinha': float(resultado.custo_tampinha),
                'subtotal': float(resultado.subtotal),
                'valor_lucro': float(resultado.valor_lucro),
                'margem_cartao': float(resultado.margem_cartao),
                'valor_sanitizacao': float(resultado.valor_sanitizacao),
                'valor_impostos': float(resultado.valor_impostos)
            },
            'envase': {
                'quantidade_total_litros': float(quantidade_total_litros),
                'custo_por_litro': float(custo_por_litro),
                'custo_total_ingredientes': float(custo_total_ingredientes),
                'unidades_produzidas': float(unidades_produzidas),
                'total_arrecadado': float(total_arrecadado),
                'lucro_total': float(total_arrecadado - (custo_total_ingredientes + 
                    (unidades_produzidas * (resultado.custo_embalagem + resultado.custo_impressao + resultado.custo_tampinha))))
            },
            'calculo_id': calculo_envase.id
        }), 200
        
    except Exception as e:
        print(f"Erro no cálculo de envase: {e}")
        db.session.rollback()
        return jsonify({'error': f'Erro no cálculo: {str(e)}'}), 500
    
    
@envase_bp.route('/calculo_envase/historico')
@login_required
def get_historico_calculos_envase():
    """Obter histórico de cálculos de envase"""
    try:
        calculos = CalculoEnvase.query.order_by(CalculoEnvase.data_calculo.desc()).limit(10).all()
        
        return jsonify({
            'success': True,
            'calculos': [calculo.to_dict() for calculo in calculos]
        }), 200
        
    except Exception as e:
        logger.error(f"Erro ao buscar histórico de cálculos de envase: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500    
    
# ===== PÁGINA PRINCIPAL =====
@envase_bp.route('/envase')
@login_required
def pagina_envase():
    """Página principal do módulo de envase"""
    return render_template('envase.html')