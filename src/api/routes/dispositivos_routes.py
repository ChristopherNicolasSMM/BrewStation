# routes/dispositivos_routes.py
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from model.dispositivos import Dispositivo, TipoDispositivo, ProtocoloComunicacao, StatusDispositivo, HistoricoDispositivo
from db.database import db
    

dispositivos_bp = Blueprint('dispositivos', __name__)

@dispositivos_bp.route('/dispositivos', methods=['GET'])
@login_required
def get_dispositivos():
    """Obter lista de dispositivos"""
    try:
        dispositivos = Dispositivo.query.all()
        return jsonify([dispositivo.to_dict() for dispositivo in dispositivos]), 200
    except Exception as e:
        print(f"Erro ao buscar dispositivos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>', methods=['GET'])
@login_required
def get_dispositivo(dispositivo_id):
    """Obter dispositivo específico por ID"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        return jsonify(dispositivo.to_dict()), 200
        
    except Exception as e:
        print(f"Erro ao buscar dispositivo {dispositivo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos', methods=['POST'])
@login_required
def create_dispositivo():
    """Criar novo dispositivo"""
    try:
        data = request.get_json()
        
        # Validar campos obrigatórios
        required_fields = ['nome', 'tipo', 'protocolo', 'endereco']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'Campo obrigatório faltando: {field}'}), 400
        
        # Criar dispositivo
        dispositivo = Dispositivo(
            nome=data['nome'],
            descricao=data.get('descricao'),
            tipo=TipoDispositivo(data['tipo']),
            fabricante=data.get('fabricante'),
            modelo=data.get('modelo'),
            versao_firmware=data.get('versao_firmware'),
            protocolo=ProtocoloComunicacao(data['protocolo']),
            endereco=data['endereco'],
            porta=data.get('porta'),
            topico_mqtt=data.get('topico_mqtt'),
            usuario=data.get('usuario'),
            senha=data.get('senha'),
            token_acesso=data.get('token_acesso'),
            configuracao=data.get('configuracao'),
            parametros_calibracao=data.get('parametros_calibracao'),
            status=StatusDispositivo(data.get('status', 'inativo')),
            intervalo_atualizacao=data.get('intervalo_atualizacao', 30),
            created_by=current_user.username
        )
        
        db.session.add(dispositivo)
        db.session.commit()
        
        return jsonify({
            'message': 'Dispositivo criado com sucesso', 
            'dispositivo': dispositivo.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'error': f'Valor inválido para enum: {str(e)}'}), 400
    except Exception as e:
        print(f"Erro ao criar dispositivo: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>', methods=['PUT'])
@login_required
def update_dispositivo(dispositivo_id):
    """Atualizar dispositivo"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        data = request.get_json()
        
        # Campos que podem ser atualizados
        updateable_fields = [
            'nome', 'descricao', 'fabricante', 'modelo', 'versao_firmware',
            'endereco', 'porta', 'topico_mqtt', 'usuario', 'senha', 'token_acesso',
            'configuracao', 'parametros_calibracao', 'intervalo_atualizacao'
        ]
        
        for field in updateable_fields:
            if field in data:
                setattr(dispositivo, field, data[field])
        
        # Campos enum que precisam de conversão
        if 'tipo' in data:
            dispositivo.tipo = TipoDispositivo(data['tipo'])
        if 'protocolo' in data:
            dispositivo.protocolo = ProtocoloComunicacao(data['protocolo'])
        if 'status' in data:
            dispositivo.status = StatusDispositivo(data['status'])
        
        dispositivo.updated_at = func.now()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Dispositivo atualizado com sucesso', 
            'dispositivo': dispositivo.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Valor inválido para enum: {str(e)}'}), 400
    except Exception as e:
        print(f"Erro ao atualizar dispositivo {dispositivo_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>', methods=['DELETE'])
@login_required
def delete_dispositivo(dispositivo_id):
    """Deletar dispositivo"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        # Deletar histórico associado primeiro
        HistoricoDispositivo.query.filter_by(dispositivo_id=dispositivo_id).delete()
        
        db.session.delete(dispositivo)
        db.session.commit()
        
        return jsonify({'message': 'Dispositivo deletado com sucesso'}), 200
        
    except Exception as e:
        print(f"Erro ao deletar dispositivo {dispositivo_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>/status', methods=['POST'])
@login_required
def atualizar_status_dispositivo(dispositivo_id):
    """Atualizar status do dispositivo"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        data = request.get_json()
        
        if 'status' not in data:
            return jsonify({'error': 'Campo status é obrigatório'}), 400
            
        novo_status = StatusDispositivo(data['status'])
        dados_recebidos = data.get('dados_recebidos')
        
        dispositivo.atualizar_status(novo_status, dados_recebidos)
        
        return jsonify({
            'message': 'Status atualizado com sucesso',
            'dispositivo': dispositivo.to_dict()
        }), 200
        
    except ValueError as e:
        return jsonify({'error': f'Status inválido: {str(e)}'}), 400
    except Exception as e:
        print(f"Erro ao atualizar status do dispositivo {dispositivo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>/calibrar', methods=['POST'])
@login_required
def calibrar_dispositivo(dispositivo_id):
    """Calibrar dispositivo"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        data = request.get_json()
        
        if 'parametros_calibracao' not in data:
            return jsonify({'error': 'Parâmetros de calibração são obrigatórios'}), 400
            
        parametros_calibracao = data['parametros_calibracao']
        dispositivo.calibrar(parametros_calibracao)
        
        return jsonify({
            'message': 'Dispositivo calibrado com sucesso',
            'dispositivo': dispositivo.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Erro ao calibrar dispositivo {dispositivo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/tipo/<tipo>', methods=['GET'])
@login_required
def get_dispositivos_por_tipo(tipo):
    """Obter dispositivos por tipo"""
    try:
        tipo_enum = TipoDispositivo(tipo)
        dispositivos = Dispositivo.get_por_tipo(tipo_enum)
        return jsonify([dispositivo.to_dict() for dispositivo in dispositivos]), 200
        
    except ValueError as e:
        return jsonify({'error': f'Tipo de dispositivo inválido: {tipo}'}), 400
    except Exception as e:
        print(f"Erro ao buscar dispositivos por tipo {tipo}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/ativos', methods=['GET'])
@login_required
def get_dispositivos_ativos():
    """Obter dispositivos ativos"""
    try:
        dispositivos = Dispositivo.get_ativos()
        return jsonify([dispositivo.to_dict() for dispositivo in dispositivos]), 200
    except Exception as e:
        print(f"Erro ao buscar dispositivos ativos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/protocolo/<protocolo>', methods=['GET'])
@login_required
def get_dispositivos_por_protocolo(protocolo):
    """Obter dispositivos por protocolo"""
    try:
        protocolo_enum = ProtocoloComunicacao(protocolo)
        dispositivos = Dispositivo.get_por_protocolo(protocolo_enum)
        return jsonify([dispositivo.to_dict() for dispositivo in dispositivos]), 200
        
    except ValueError as e:
        return jsonify({'error': f'Protocolo inválido: {protocolo}'}), 400
    except Exception as e:
        print(f"Erro ao buscar dispositivos por protocolo {protocolo}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ========== ROTAS PARA HISTÓRICO DE DISPOSITIVOS ==========

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>/historico', methods=['GET'])
@login_required
def get_historico_dispositivo(dispositivo_id):
    """Obter histórico de um dispositivo"""
    try:
        # Verificar se dispositivo existe
        dispositivo = Dispositivo.query.get(dispositivo_id)
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
        
        # Parâmetros de paginação/filtro
        limite = request.args.get('limite', 100, type=int)
        inicio = request.args.get('inicio')
        fim = request.args.get('fim')
        
        if inicio and fim:
            # Buscar por período
            from datetime import datetime
            inicio_dt = datetime.fromisoformat(inicio.replace('Z', '+00:00'))
            fim_dt = datetime.fromisoformat(fim.replace('Z', '+00:00'))
            
            historico = HistoricoDispositivo.get_leituras_por_periodo(
                dispositivo_id, inicio_dt, fim_dt
            )
        else:
            # Buscar últimas leituras
            historico = HistoricoDispositivo.get_ultimas_leituras(dispositivo_id, limite)
        
        return jsonify([registro.to_dict() for registro in historico]), 200
        
    except Exception as e:
        print(f"Erro ao buscar histórico do dispositivo {dispositivo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>/historico', methods=['POST'])
@login_required
def adicionar_historico_dispositivo(dispositivo_id):
    """Adicionar registro ao histórico do dispositivo"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        data = request.get_json()
        
        if 'dados' not in data:
            return jsonify({'error': 'Campo dados é obrigatório'}), 400
        
        # Criar registro de histórico
        historico = HistoricoDispositivo(
            dispositivo_id=dispositivo_id,
            dados=data['dados'],
            temperatura=data.get('temperatura'),
            gravidade=data.get('gravidade'),
            pressao=data.get('pressao'),
            unidade=data.get('unidade'),
            qualidade_sinal=data.get('qualidade_sinal'),
            bateria=data.get('bateria')
        )
        
        db.session.add(historico)
        
        # Atualizar último valor recebido no dispositivo
        dispositivo.ultimo_valor_recebido = data['dados']
        dispositivo.ultima_comunicacao = func.now()
        
        db.session.commit()
        
        return jsonify({
            'message': 'Histórico adicionado com sucesso',
            'historico': historico.to_dict()
        }), 201
        
    except Exception as e:
        print(f"Erro ao adicionar histórico do dispositivo {dispositivo_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>/historico/<int:historico_id>', methods=['DELETE'])
@login_required
def delete_historico_dispositivo(dispositivo_id, historico_id):
    """Deletar registro do histórico"""
    try:
        historico = HistoricoDispositivo.query.filter_by(
            id=historico_id, 
            dispositivo_id=dispositivo_id
        ).first()
        
        if not historico:
            return jsonify({'error': 'Registro de histórico não encontrado'}), 404
            
        db.session.delete(historico)
        db.session.commit()
        
        return jsonify({'message': 'Registro de histórico deletado com sucesso'}), 200
        
    except Exception as e:
        print(f"Erro ao deletar histórico {historico_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ========== ROTAS PARA CONFIGURAÇÃO DE DISPOSITIVOS ==========

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>/config', methods=['GET'])
@login_required
def get_config_dispositivo(dispositivo_id):
    """Obter configuração específica do dispositivo"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        chave = request.args.get('chave')
        
        if chave:
            # Buscar valor específico
            valor = dispositivo.get_config_value(chave)
            return jsonify({'chave': chave, 'valor': valor}), 200
        else:
            # Retornar toda a configuração
            return jsonify(dispositivo.configuracao or {}), 200
            
    except Exception as e:
        print(f"Erro ao buscar configuração do dispositivo {dispositivo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@dispositivos_bp.route('/dispositivos/<int:dispositivo_id>/config', methods=['POST'])
@login_required
def set_config_dispositivo(dispositivo_id):
    """Definir configuração do dispositivo"""
    try:
        dispositivo = Dispositivo.query.get(dispositivo_id)
        
        if not dispositivo:
            return jsonify({'error': 'Dispositivo não encontrado'}), 404
            
        data = request.get_json()
        
        if 'chave' not in data or 'valor' not in data:
            return jsonify({'error': 'Campos chave e valor são obrigatórios'}), 400
            
        dispositivo.set_config_value(data['chave'], data['valor'])
        
        return jsonify({
            'message': 'Configuração atualizada com sucesso',
            'configuracao': dispositivo.configuracao
        }), 200
        
    except Exception as e:
        print(f"Erro ao definir configuração do dispositivo {dispositivo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

# ========== ROTA PARA ENUMS (Útil para frontend) ==========

@dispositivos_bp.route('/dispositivos/enums', methods=['GET'])
@login_required
def get_enums_dispositivos():
    """Obter valores dos enums para frontend"""
    try:
        return jsonify({
            'tipos_dispositivo': [tipo.value for tipo in TipoDispositivo],
            'protocolos_comunicacao': [protocolo.value for protocolo in ProtocoloComunicacao],
            'status_dispositivo': [status.value for status in StatusDispositivo]
        }), 200
    except Exception as e:
        print(f"Erro ao buscar enums: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500