from sqlalchemy import func, text
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from model.ingredientes import Malte, Lupulo, Levedura, Receita, IngredienteReceita, CalculoPreco
from model.dispositivos import Dispositivo, TipoDispositivo, ProtocoloComunicacao, StatusDispositivo, HistoricoDispositivo
from model.user import User
from model.config import Configuracao
from model.notification import Notification
from model.sessao_brasagem import SessaoBrasagem
from model.brewfather import BrewFatherService, BrewFatherRecipe, BrewFatherBatch, BrewFatherInventory
from db.database import db
from utils.calculadora import CalculadoraPrecos
import pandas as pd
import json
from pathlib import Path
import os
import smtplib
from email.mime.text import MIMEText # Opcional, para simular uma mensagem

api_bp = Blueprint('api', __name__)
 

# =========================================================================================
# ================================ ROTAS PARA CONFIGURAÇÕES ===============================
# =========================================================================================    
@api_bp.route('/configuracoes', methods=['GET'])
def get_configuracoes():
    """Retorna as configurações atuais do sistema"""
    try:
        from model.config import Configuracao
        configs = Configuracao.get_all_configs(include_sensitive=False)
        
        # Converter para formato simples (chave: valor) para compatibilidade com o frontend
        configs_simplificado = {}
        campos_configurados = {}  # Para indicar quais campos têm valores
        
        for chave, config_data in configs.items():
            configs_simplificado[chave] = config_data['valor']
            # Indicar se o campo tem valor configurado (útil para campos sensíveis)
            #OBS
            #Tirar o true e descomentar restante da linha para validar campos sensíveis
            campos_configurados[chave] = True #config_data['valor'] not in ['', None, '********']
        
        return jsonify({
            'configuracoes': configs_simplificado,
            'campos_configurados': campos_configurados
        })
        
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return jsonify({'error': str(e)}), 500    
    

@api_bp.route('/configuracoes', methods=['POST'])
def save_configuracoes():
    """Salva as configurações no banco de dados"""
    try:
        from model.config import Configuracao
        configs_data = request.get_json()
        
        for chave, valor in configs_data.items():
            # Buscar configuração existente para manter os metadados
            config_existente = Configuracao.query.filter_by(chave=chave).first()
            
            if config_existente:
                
                # Se for um campo sensível e o valor estiver vazio, não atualizar
                if ( config_existente.is_sensitive and valor == '' ) or valor == '••••••••':
                    continue  # Pular campos sensíveis vazios
                
                # Se é um checkbox, converter para string booleana
                if chave == 'BREWFATHER_ENABLED':
                    valor = 'True' if valor else 'False'
                if valor == 'True' or valor == True:
                    valor = True
                elif valor == 'False' or valor == False:
                    valor = False
                config_existente.set_value(valor)
            else:
                # Criar nova configuração com valores padrão
                nova_config = Configuracao(
                    chave=chave,
                    tipo='string',
                    categoria='sistema',
                    descricao=f'Configuração {chave}',
                    is_sensitive=chave in ['SECRET_KEY', 'BREWFATHER_API_KEY', 'MAIL_PASSWORD']
                )
                
                # Não criar configurações sensíveis com valor vazio
                if not (nova_config.is_sensitive and valor == ''):
                    nova_config.set_value(valor)
                    db.session.add(nova_config)
            
                print(f"Criando nova configuração {chave} com valor {valor}")
        db.session.commit()
        return jsonify({'success': True, 'message': 'Configurações salvas com sucesso'})
        
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/configuracoes/testar', methods=['POST'])
def testar_configuracoes():
    """Testa as configurações atuais"""
    try:
        from model.config import Configuracao
        
        # Testar conexão com banco de dados
        db.session.execute(text('SELECT * FROM configuracoes LIMIT 1'))
        db_status = 'connected'
        
        # Testar BrewFather API
        brewfather_status = 'disconnected'
        user_id = Configuracao.get_config('BREWFATHER_USER_ID')
        api_key = Configuracao.get_config('BREWFATHER_API_KEY')
        
        if user_id and api_key:
            try:
                import requests
                response = requests.get(
                    f'https://api.brewfather.app/v1/recipes',
                    auth=(user_id, api_key),
                    timeout=10
                )
                if response.status_code == 200:
                    brewfather_status = 'connected'
                else:
                    brewfather_status = 'error'
            except Exception as api_error:
                print(f"Erro BrewFather API: {api_error}")
                brewfather_status = 'error'
                
                
                
                
        # Testar configurações de email
        email_status = 'disconnected'
        mail_server = Configuracao.get_config('MAIL_SERVER')
        if mail_server:
            email_status = 'configured'  # Configurado mas não testado
        
        # Recuperar todas as configurações relevantes
        mail_port = int(Configuracao.get_config('MAIL_PORT'))
        mail_username = Configuracao.get_config('MAIL_USERNAME')
        mail_password = Configuracao.get_config('MAIL_PASSWORD')
        mail_use_tls = Configuracao.get_config('MAIL_USE_TLS') == True # Converta para booleano
        
        if mail_server and mail_port and mail_username and mail_password:
            print("Iniciando teste de email...")
            print(f"Servidor: {mail_server}, Porta: {mail_port}, Usuário: {mail_username}, TLS: {mail_use_tls}")
            print('******************************')
            try:
                # 1. Tentar conectar ao servidor e porta
                server = smtplib.SMTP(mail_server, int(mail_port), timeout=60)
                email_status = 'configured' # Pelo menos a conexão básica funcionou
                
                # 2. Iniciar TLS/SSL se necessário
                if mail_use_tls:
                    server.starttls()
                else:
                    print("TLS não está habilitado para o teste de email.")
                    server.verify(mail_username)
                
                # 3. Tentar login (o teste mais importante)
                server.login(mail_username, mail_password)
                
                # Se chegou até aqui, as credenciais e conexão estão CORRETAS
                email_status = 'connected'
                
                # 4. Fechar a conexão
                server.quit()
                
            except smtplib.SMTPAuthenticationError:
                email_status = 'auth_error' # Credenciais (usuário/senha) inválidas
                print("Erro de autenticação SMTP.")
            except smtplib.SMTPConnectError:
                email_status = 'connect_error' # Servidor/porta errado ou firewall
                print("Erro de conexão SMTP.")
            except Exception as e:
                email_status = 'error'
                print(f"Erro geral ao testar email: {e}")            
    
        return jsonify({
            'success': True,
            'database': db_status,
            'brewfather': brewfather_status,
            'email': email_status
        })
        
    except Exception as e:
        print(f"Erro teste configurações: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



@api_bp.route('/configuracoes/status', methods=['GET'])
def get_status():
    """Retorna o status atual das conexões"""
    try:
        if Configuracao.query.count() > 0:
            db_status = 'connected'
        else:
            db_status = 'disconnected'            
    except Exception as e:
        print(f"Erro DB: {e}")
        db_status = 'error'
    
    # Status BrewFather
    brewfather_status = 'disconnected'
    user_id = Configuracao.get_config('BREWFATHER_USER_ID')
    api_key = Configuracao.get_config('BREWFATHER_API_KEY')
    
    if user_id and api_key:
        brewfather_status = 'configured'
    
    # Status Email
    email_status = 'disconnected'
    if Configuracao.get_config('MAIL_SERVER'):
        email_status = 'configured'
    
    return jsonify({
        'database': db_status,
        'brewfather': brewfather_status,
        'email': email_status
    })



# =========================================================================================
# =================================== ROTAS PARA MALTES ===================================
# =========================================================================================

@api_bp.route('/maltes', methods=['GET'])
@login_required
def get_maltes():
    """Obter lista de maltes"""
    maltes = Malte.query.filter_by(ativo=True).all()
    return jsonify([malte.to_dict() for malte in maltes]), 200


@api_bp.route('/maltes/<int:malte_id>', methods=['GET'])
@login_required
def get_malte_id(malte_id):
    """Obter malte específico por ID"""
    try:
        malte = Malte.query.get(malte_id)
        if not malte:
            return jsonify({'error': 'Malte não encontrado'}), 404
            
        return jsonify(malte.to_dict()), 200  # ✅ Retorna apenas o objeto malte
        
    except Exception as e:
        print(f"Erro ao buscar malte {malte_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500


@api_bp.route('/maltes', methods=['POST'])
@login_required
def create_malte():
    """Criar novo malte"""
    data = request.get_json()
    
    malte = Malte(
        nome=data['nome'],
        fabricante=data['fabricante'],
        cor_ebc=data['cor_ebc'],
        poder_diastatico=data['poder_diastatico'],
        rendimento=data['rendimento'],
        preco_kg=data['preco_kg'],
        tipo=data['tipo']
    )
    
    db.session.add(malte)
    db.session.commit()
    
    return jsonify({'message': 'Malte criado com sucesso', 'malte': malte.to_dict()}), 201

@api_bp.route('/maltes/<int:malte_id>', methods=['PUT'])
@login_required
def update_malte(malte_id):
    """Atualizar malte"""
    malte = Malte.query.get_or_404(malte_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(malte, key):
            setattr(malte, key, value)
    
    db.session.commit()
    
    return jsonify({'message': 'Malte atualizado com sucesso', 'malte': malte.to_dict()}), 200

@api_bp.route('/maltes/<int:malte_id>', methods=['DELETE'])
@login_required
def delete_malte(malte_id):
    """Deletar malte (soft delete)"""
    malte = Malte.query.get_or_404(malte_id)
    malte.ativo = False
    db.session.commit()
    
    return jsonify({'message': 'Malte deletado com sucesso'}), 200



# =========================================================================================
# =================================== ROTAS PARA LÚPULOS ==================================
# =========================================================================================

@api_bp.route('/lupulos', methods=['GET'])
@login_required
def get_lupulos():
    """Obter lista de lúpulos"""
    lupulos = Lupulo.query.filter_by(ativo=True).all()
    return jsonify([lupulo.to_dict() for lupulo in lupulos]), 200


@api_bp.route('/lupulos/<int:lupulo_id>', methods=['GET'])
@login_required
def get_lupulo_id(lupulo_id):
    """Obter lupulo específico por ID"""
    try:
        lupulo = lupulo.query.get(lupulo_id)
        if not lupulo:
            return jsonify({'error': 'lupulo não encontrado'}), 404
            
        return jsonify(lupulo.to_dict()), 200  # ✅ Retorna apenas o objeto lupulo
        
    except Exception as e:
        print(f"Erro ao buscar lupulo {lupulo_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
    

@api_bp.route('/lupulos', methods=['POST'])
@login_required
def create_lupulo():
    """Criar novo lúpulo"""
    data = request.get_json()
    
    lupulo = Lupulo(
        nome=data['nome'],
        fabricante=data['fabricante'],
        alpha_acidos=data['alpha_acidos'],
        beta_acidos=data['beta_acidos'],
        formato=data['formato'],
        origem=data['origem'],
        preco_kg=data['preco_kg'],
        aroma=data.get('aroma', '')
    )
    
    db.session.add(lupulo)
    db.session.commit()
    
    return jsonify({'message': 'Lúpulo criado com sucesso', 'lupulo': lupulo.to_dict()}), 201

@api_bp.route('/lupulos/<int:lupulo_id>', methods=['PUT'])
@login_required
def update_lupulo(lupulo_id):
    """Atualizar lúpulo"""
    lupulo = Lupulo.query.get_or_404(lupulo_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(lupulo, key):
            setattr(lupulo, key, value)
    
    db.session.commit()
    
    return jsonify({'message': 'Lúpulo atualizado com sucesso', 'lupulo': lupulo.to_dict()}), 200

@api_bp.route('/lupulos/<int:lupulo_id>', methods=['DELETE'])
@login_required
def delete_lupulo(lupulo_id):
    """Deletar lúpulo (soft delete)"""
    lupulo = Lupulo.query.get_or_404(lupulo_id)
    lupulo.ativo = False
    db.session.commit()
    
    return jsonify({'message': 'Lúpulo deletado com sucesso'}), 200




# =========================================================================================
# =================================== ROTAS PARA LEVEDURAS ================================
# =========================================================================================

@api_bp.route('/leveduras', methods=['GET'])
@login_required
def get_leveduras():
    """Obter lista de leveduras"""
    leveduras = Levedura.query.filter_by(ativo=True).all()
    return jsonify([levedura.to_dict() for levedura in leveduras]), 200


@api_bp.route('/leveduras/<int:levedura_id>', methods=['GET'])
@login_required
def get_levedura_id(levedura_id):
    """Obter levedura específico por ID"""
    try:
        levedura = levedura.query.get(levedura_id)
        if not levedura:
            return jsonify({'error': 'levedura não encontrado'}), 404
            
        return jsonify(levedura.to_dict()), 200  # ✅ Retorna apenas o objeto levedura
        
    except Exception as e:
        print(f"Erro ao buscar levedura {levedura_id}: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500
    

@api_bp.route('/leveduras', methods=['POST'])
@login_required
def create_levedura():
    """Criar nova levedura"""
    data = request.get_json()
    
    levedura = Levedura(
        nome=data['nome'],
        fabricante=data['fabricante'],
        formato=data['formato'],
        atenuacao=data['atenuacao'],
        temp_fermentacao=data['temp_fermentacao'],
        preco_unidade=data['preco_unidade'],
        floculacao=data['floculacao']
    )
    
    db.session.add(levedura)
    db.session.commit()
    
    return jsonify({'message': 'Levedura criada com sucesso', 'levedura': levedura.to_dict()}), 201

@api_bp.route('/leveduras/<int:levedura_id>', methods=['PUT'])
@login_required
def update_levedura(levedura_id):
    """Atualizar levedura"""
    levedura = Levedura.query.get_or_404(levedura_id)
    data = request.get_json()
    
    for key, value in data.items():
        if hasattr(levedura, key):
            setattr(levedura, key, value)
    
    db.session.commit()
    
    return jsonify({'message': 'Levedura atualizada com sucesso', 'levedura': levedura.to_dict()}), 200

@api_bp.route('/leveduras/<int:levedura_id>', methods=['DELETE'])
@login_required
def delete_levedura(levedura_id):
    """Deletar levedura (soft delete)"""
    levedura = Levedura.query.get_or_404(levedura_id)
    levedura.ativo = False
    db.session.commit()
    
    return jsonify({'message': 'Levedura deletada com sucesso'}), 200











# =========================================================================================
# =================================== ROTAS PARA RECEITAS =================================
# =========================================================================================


@api_bp.route('/receitas', methods=['GET'])
@login_required
def get_receitas():
    """Obter lista de receitas"""
    receitas = Receita.query.filter_by(ativo=True).all()
    return jsonify([receita.to_dict() for receita in receitas]), 200

@api_bp.route('/receitas', methods=['POST'])
@login_required
def create_receita():
    """Criar nova receita"""
    data = request.get_json()
    
    receita = Receita(
        nome=data['nome'],
        descricao=data.get('descricao', ''),
        volume_litros=data['volume_litros'],
        eficiencia=data.get('eficiencia', 75.0)
    )
    
    db.session.add(receita)
    db.session.commit()
    
    return jsonify({'message': 'Receita criada com sucesso', 'receita': receita.to_dict()}), 201

@api_bp.route('/receitas/<int:receita_id>', methods=['PUT'])
@login_required
def update_receita(receita_id):
    """Atualizar dados da receita"""
    receita = Receita.query.get_or_404(receita_id)
    data = request.get_json()
    for key in ['nome', 'descricao', 'volume_litros', 'eficiencia', 'ativo']:
        if key in data:
            setattr(receita, key, data[key])
    db.session.commit()
    return jsonify({'message': 'Receita atualizada com sucesso', 'receita': receita.to_dict()}), 200

@api_bp.route('/receitas/<int:receita_id>/ingredientes', methods=['POST'])
@login_required
def add_ingrediente_receita(receita_id):
    """Adicionar ingrediente à receita"""
    data = request.get_json()
    
    ingrediente = IngredienteReceita(
        receita_id=receita_id,
        tipo_ingrediente=data['tipo_ingrediente'],
        ingrediente_id=data['ingrediente_id'],
        quantidade=data['quantidade'],
        tempo_adicao=data.get('tempo_adicao'),
        observacoes=data.get('observacoes', '')
    )
    
    db.session.add(ingrediente)
    db.session.commit()
    
    return jsonify({'message': 'Ingrediente adicionado com sucesso', 'ingrediente': ingrediente.to_dict()}), 201

@api_bp.route('/receitas/<int:receita_id>/ingredientes', methods=['GET'])
@login_required
def list_ingredientes_receita(receita_id):
    """Listar ingredientes de uma receita"""
    itens = IngredienteReceita.query.filter_by(receita_id=receita_id).all()
    return jsonify([i.to_dict() for i in itens]), 200

@api_bp.route('/receitas/<int:receita_id>/ingredientes/<int:item_id>', methods=['PUT'])
@login_required
def update_ingrediente_receita(receita_id, item_id):
    """Atualizar ingrediente da receita"""
    item = IngredienteReceita.query.filter_by(id=item_id, receita_id=receita_id).first_or_404()
    data = request.get_json()
    for key in ['tipo_ingrediente', 'ingrediente_id', 'quantidade', 'tempo_adicao', 'observacoes']:
        if key in data:
            setattr(item, key, data[key])
    db.session.commit()
    return jsonify({'message': 'Ingrediente atualizado com sucesso', 'ingrediente': item.to_dict()}), 200

@api_bp.route('/receitas/<int:receita_id>/ingredientes/<int:item_id>', methods=['DELETE'])
@login_required
def delete_ingrediente_receita(receita_id, item_id):
    """Remover ingrediente da receita"""
    item = IngredienteReceita.query.filter_by(id=item_id, receita_id=receita_id).first_or_404()
    db.session.delete(item)
    db.session.commit()
    return jsonify({'message': 'Ingrediente removido com sucesso'}), 200











# =========================================================================================
# =================================== ROTAS PARA CÁLCULOS =================================
# =========================================================================================


@api_bp.route('/calcular', methods=['POST'])
@login_required
def calcular_preco():
    """Calcular preço de uma receita"""
    data = request.get_json()
    
    calculadora = CalculadoraPrecos()
    
    # Obter receita e ingredientes
    receita = Receita.query.get(data['receita_id'])
    ingredientes = IngredienteReceita.query.filter_by(receita_id=data['receita_id']).all()
    
    # Obter dados dos ingredientes
    maltes = {malte.id: malte for malte in Malte.query.filter_by(ativo=True).all()}
    lupulos = {lupulo.id: lupulo for lupulo in Lupulo.query.filter_by(ativo=True).all()}
    leveduras = {levedura.id: levedura for levedura in Levedura.query.filter_by(ativo=True).all()}
    
    # Calcular preço
    resultado = calculadora.calcular_receita_completa(
        receita=receita,
        ingredientes=ingredientes,
        maltes=maltes,
        lupulos=lupulos,
        leveduras=leveduras,
        quantidade_ml=data['quantidade_ml'],
        custo_embalagem=data['custo_embalagem'],
        custo_impressao=data['custo_impressao'],
        custo_tampinha=data['custo_tampinha'],
        percentual_lucro=data['percentual_lucro'],
        margem_cartao=data['margem_cartao'],
        percentual_sanitizacao=data['percentual_sanitizacao'],
        percentual_impostos=data['percentual_impostos']
    )
    
    # Salvar cálculo no banco
    calculo = CalculoPreco(
        receita_id=data['receita_id'],
        nome_produto=data.get('nome_produto', receita.nome),
        quantidade_ml=data['quantidade_ml'],
        tipo_embalagem=data.get('tipo_embalagem', 'Garrafa'),
        valor_litro_base=resultado['valor_litro_base'],
        custo_embalagem=data['custo_embalagem'],
        custo_impressao=data['custo_impressao'],
        custo_tampinha=data['custo_tampinha'],
        percentual_lucro=data['percentual_lucro'],
        margem_cartao=data['margem_cartao'],
        percentual_sanitizacao=data['percentual_sanitizacao'],
        percentual_impostos=data['percentual_impostos'],
        valor_total=resultado['resultado']['valor_total'],
        valor_venda_final=resultado['resultado']['valor_venda_final']
    )
    
    db.session.add(calculo)
    db.session.commit()
    
    return jsonify({
        'message': 'Cálculo realizado com sucesso',
        'resultado': resultado,
        'calculo_id': calculo.id
    }), 200

@api_bp.route('/calculos', methods=['GET'])
@login_required
def get_calculos():
    """Obter lista de cálculos realizados"""
    calculos = CalculoPreco.query.order_by(CalculoPreco.data_calculo.desc()).all()
    return jsonify([calculo.to_dict() for calculo in calculos]), 200











# =========================================================================================
# =================================== ROTAS PARA UPLOAD ===================================
# =========================================================================================


@api_bp.route('/upload/maltes', methods=['POST'])
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

@api_bp.route('/upload/lupulos', methods=['POST'])
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

@api_bp.route('/upload/leveduras', methods=['POST'])
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









# =========================================================================================
# ================================= ROTAS PARA DISPOSITIVOS ===============================
# =========================================================================================


@api_bp.route('/dispositivos', methods=['GET'])
@login_required
def get_dispositivos():
    """Obter lista de dispositivos"""
    try:
        dispositivos = Dispositivo.query.all()
        return jsonify([dispositivo.to_dict() for dispositivo in dispositivos]), 200
    except Exception as e:
        print(f"Erro ao buscar dispositivos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/dispositivos/<int:dispositivo_id>', methods=['GET'])
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

@api_bp.route('/dispositivos', methods=['POST'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>', methods=['PUT'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>', methods=['DELETE'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>/status', methods=['POST'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>/calibrar', methods=['POST'])
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

@api_bp.route('/dispositivos/tipo/<tipo>', methods=['GET'])
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

@api_bp.route('/dispositivos/ativos', methods=['GET'])
@login_required
def get_dispositivos_ativos():
    """Obter dispositivos ativos"""
    try:
        dispositivos = Dispositivo.get_ativos()
        return jsonify([dispositivo.to_dict() for dispositivo in dispositivos]), 200
    except Exception as e:
        print(f"Erro ao buscar dispositivos ativos: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/dispositivos/protocolo/<protocolo>', methods=['GET'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>/historico', methods=['GET'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>/historico', methods=['POST'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>/historico/<int:historico_id>', methods=['DELETE'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>/config', methods=['GET'])
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

@api_bp.route('/dispositivos/<int:dispositivo_id>/config', methods=['POST'])
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

@api_bp.route('/dispositivos/enums', methods=['GET'])
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
















# =========================================================================================
# ================================= ROTAS PARA DISPOSITIVOS ===============================
# =========================================================================================


# routes.py - Adicione estas rotas
@api_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Obter notificações do usuário"""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        unread_only = request.args.get('unread_only', 'false').lower() == 'true'
        
        # Query base
        query = Notification.query.filter_by(user_id=current_user.id)
        
        # Filtrar apenas não lidas se solicitado
        if unread_only:
            query = query.filter_by(is_read=False)
        
        # Ordenar e paginar
        notifications = query.order_by(
            Notification.priority.desc(), 
            Notification.created_at.desc()
        ).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return jsonify({
            'notifications': [notification.to_dict() for notification in notifications.items],
            'total': notifications.total,
            'pages': notifications.pages,
            'current_page': page,
            'unread_count': Notification.query.filter_by(
                user_id=current_user.id, 
                is_read=False
            ).count()
        }), 200
        
    except Exception as e:
        print(f"Erro ao buscar notificações: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/notifications/<int:notification_id>/read', methods=['PUT'])
@login_required
def mark_notification_read(notification_id):
    """Marcar notificação como lida"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notificação não encontrada'}), 404
            
        notification.is_read = True
        db.session.commit()
        
        return jsonify({
            'message': 'Notificação marcada como lida',
            'notification': notification.to_dict()
        }), 200
        
    except Exception as e:
        print(f"Erro ao marcar notificação como lida: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/notifications/read-all', methods=['PUT'])
@login_required
def mark_all_notifications_read():
    """Marcar todas as notificações como lidas"""
    try:
        updated = Notification.query.filter_by(
            user_id=current_user.id, 
            is_read=False
        ).update({'is_read': True})
        
        db.session.commit()
        
        return jsonify({
            'message': f'{updated} notificações marcadas como lidas',
            'updated_count': updated
        }), 200
        
    except Exception as e:
        print(f"Erro ao marcar todas as notificações como lidas: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/notifications/<int:notification_id>', methods=['DELETE'])
@login_required
def delete_notification(notification_id):
    """Excluir notificação (mover para lixeira)"""
    try:
        notification = Notification.query.filter_by(
            id=notification_id, 
            user_id=current_user.id
        ).first()
        
        if not notification:
            return jsonify({'error': 'Notificação não encontrada'}), 404
        
        # Mover para lixeira
        trash_notification = NotificationTrash(
            original_notification_id=notification.id,
            user_id=notification.user_id,
            title=notification.title,
            message=notification.message,
            notification_type=notification.notification_type,
            is_read=notification.is_read,
            action_url=notification.action_url,
            action_params=notification.action_params,
            icon=notification.icon,
            priority=notification.priority,
            created_at=notification.created_at
        )
        
        db.session.add(trash_notification)
        db.session.delete(notification)
        db.session.commit()
        
        return jsonify({'message': 'Notificação excluída com sucesso'}), 200
        
    except Exception as e:
        print(f"Erro ao excluir notificação: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500

@api_bp.route('/notifications/create', methods=['POST'])
@login_required
def create_notification():
    """Criar nova notificação (útil para testes)"""
    try:
        data = request.get_json()
        
        notification = Notification(
            user_id=current_user.id,
            title=data.get('title'),
            message=data['message'],
            notification_type=data.get('notification_type', 'info'),
            action_url=data.get('action_url'),
            action_params=data.get('action_params'),
            icon=data.get('icon', 'bi-bell'),
            priority=data.get('priority', 0)
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Notificação criada com sucesso',
            'notification': notification.to_dict()
        }), 201
        
    except Exception as e:
        print(f"Erro ao criar notificação: {e}")
        db.session.rollback()
        return jsonify({'error': 'Erro interno do servidor'}), 500










# =========================================================================================
# ================================== ROTAS PARA BREWFATHER ================================
# =========================================================================================  



@api_bp.route('/brewfather/status')
def get_brewfather_status():
    """Obtém status da integração com BrewFather"""
    enabled = Configuracao.get_config('BREWFATHER_ENABLED')
    user_id = Configuracao.get_config('BREWFATHER_USER_ID')
    api_key = Configuracao.get_config('BREWFATHER_API_KEY')
    
    status = {
        'enabled': bool(enabled),
        'configured': bool(user_id and api_key),
        'sync_status': BrewFatherService.get_sync_status()
    }
    
    # Testar conexão se estiver configurado
    if status['configured']:
        api = BrewFatherService.get_api_client()
        status['connection_test'] = api.test_connection() if api else False
    
    return jsonify(status)

@api_bp.route('/brewfather/sync/recipes', methods=['POST'])
def sync_recipes():
    """Sincroniza receitas do BrewFather"""
    result = BrewFatherService.sync_recipes()
    return jsonify(result)

@api_bp.route('/brewfather/sync/batches', methods=['POST'])
def sync_batches():
    """Sincroniza lotes do BrewFather"""
    result = BrewFatherService.sync_batches()
    return jsonify(result)

@api_bp.route('/brewfather/sync/inventory', methods=['POST'])
def sync_inventory():
    """Sincroniza estoque do BrewFather"""
    result = BrewFatherService.sync_inventory()
    return jsonify(result)

@api_bp.route('/brewfather/sync/all', methods=['POST'])
def sync_all():
    """Sincroniza todos os dados do BrewFather"""
    results = {}
    
    print("Iniciando sincronização completa com BrewFather...")
    
    # Sincronizar receitas
    results['recipes'] = BrewFatherService.sync_recipes()
    
    # Sincronizar lotes
    results['batches'] = BrewFatherService.sync_batches()
    
    # Sincronizar estoque
    results['inventory'] = BrewFatherService.sync_inventory()
    
    print("Sincronização completa com BrewFather finalizada.")
    print(results)
    
    return jsonify(results)

@api_bp.route('/brewfather/recipes')
def get_recipes():
    """Obtém receitas sincronizadas"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    query = BrewFatherRecipe.query
    
    if search:
        query = query.filter(BrewFatherRecipe.name.ilike(f'%{search}%'))
    
    recipes = query.order_by(BrewFatherRecipe.name)\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'recipes': [{
            'id': recipe.id,
            'brewfather_id': recipe.brewfather_id,
            'name': recipe.name,
            'style': recipe.style,
            'abv': recipe.abv,
            'ibu': recipe.ibu,
            'color': recipe.color,
            'batch_size': recipe.batch_size,
            'efficiency': recipe.efficiency,
            'original_gravity': recipe.original_gravity,
            'final_gravity': recipe.final_gravity,
            'rating': recipe.rating,
            'brew_count': recipe.brew_count,
            'last_brewed': recipe.last_brewed.isoformat() if recipe.last_brewed else None,
            'synchronized_at': recipe.synchronized_at.isoformat() if recipe.synchronized_at else None
        } for recipe in recipes.items],
        'total': recipes.total,
        'pages': recipes.pages,
        'current_page': page
    })

@api_bp.route('/brewfather/batches')
def get_batches():
    """Obtém lotes sincronizados"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    status_filter = request.args.get('status', '')
    
    query = BrewFatherBatch.query
    
    if status_filter:
        query = query.filter(BrewFatherBatch.status == status_filter)
    
    batches = query.order_by(BrewFatherBatch.brew_date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'batches': [{
            'id': batch.id,
            'brewfather_id': batch.brewfather_id,
            'recipe_name': batch.recipe_name,
            'batch_no': batch.batch_no,
            'status': batch.status,
            'brew_date': batch.brew_date.isoformat() if batch.brew_date else None,
            'estimated_og': batch.estimated_og,
            'measured_og': batch.measured_og,
            'estimated_abv': batch.estimated_abv,
            'measured_abv': batch.measured_abv,
            'batch_size': batch.batch_size,
            'rating': batch.rating,
            'synchronized_at': batch.synchronized_at.isoformat() if batch.synchronized_at else None
        } for batch in batches.items],
        'total': batches.total,
        'pages': batches.pages,
        'current_page': page
    })

@api_bp.route('/brewfather/inventory')
def get_inventory():
    """Obtém estoque sincronizado"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    type_filter = request.args.get('type', '')
    
    query = BrewFatherInventory.query
    
    if type_filter:
        query = query.filter(BrewFatherInventory.type == type_filter)
    
    inventory = query.order_by(BrewFatherInventory.name)\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'inventory': [{
            'id': item.id,
            'brewfather_id': item.brewfather_id,
            'name': item.name,
            'type': item.type,
            'category': item.category,
            'quantity': item.quantity,
            'unit': item.unit,
            'price': item.price,
            'supplier': item.supplier,
            'synchronized_at': item.synchronized_at.isoformat() if item.synchronized_at else None
        } for item in inventory.items],
        'total': inventory.total,
        'pages': inventory.pages,
        'current_page': page
    })

@api_bp.route('/brewfather/recipe/<int:recipe_id>')
def get_recipe_detail(recipe_id):
    """Obtém detalhes de uma receita"""
    recipe = BrewFatherRecipe.query.get_or_404(recipe_id)
    
    return jsonify({
        'recipe': {
            'id': recipe.id,
            'brewfather_id': recipe.brewfather_id,
            'name': recipe.name,
            'style': recipe.style,
            'abv': recipe.abv,
            'ibu': recipe.ibu,
            'color': recipe.color,
            'batch_size': recipe.batch_size,
            'efficiency': recipe.efficiency,
            'original_gravity': recipe.original_gravity,
            'final_gravity': recipe.final_gravity,
            'ingredients': recipe.ingredients,
            'notes': recipe.notes,
            'rating': recipe.rating,
            'brew_count': recipe.brew_count,
            'last_brewed': recipe.last_brewed.isoformat() if recipe.last_brewed else None,
            'created_date': recipe.created_date.isoformat() if recipe.created_date else None,
            'synchronized_at': recipe.synchronized_at.isoformat() if recipe.synchronized_at else None
        }
    })

@api_bp.route('/brewfather/batch/<int:batch_id>')
def get_batch_detail(batch_id):
    """Obtém detalhes de um lote"""
    batch = BrewFatherBatch.query.get_or_404(batch_id)
    
    return jsonify({
        'batch': {
            'id': batch.id,
            'brewfather_id': batch.brewfather_id,
            'recipe_id': batch.recipe_id,
            'recipe_name': batch.recipe_name,
            'batch_no': batch.batch_no,
            'status': batch.status,
            'brew_date': batch.brew_date.isoformat() if batch.brew_date else None,
            'estimated_og': batch.estimated_og,
            'measured_og': batch.measured_og,
            'estimated_fg': batch.estimated_fg,
            'measured_fg': batch.measured_fg,
            'estimated_abv': batch.estimated_abv,
            'measured_abv': batch.measured_abv,
            'estimated_ibu': batch.estimated_ibu,
            'estimated_color': batch.estimated_color,
            'batch_size': batch.batch_size,
            'efficiency': batch.efficiency,
            'notes': batch.notes,
            'rating': batch.rating,
            'raw_data': batch.raw_data,
            'synchronized_at': batch.synchronized_at.isoformat() if batch.synchronized_at else None
        }
    })








# =========================================================================================
# ================================== ROTAS ================================
# =========================================================================================  



#
#@api_bp.route('/lupulos/<int:id>', methods=['GET'])
#@login_required
#def get_lupulo_by_id(id):
#    """Obter lúpulo específico por ID (para frontend)"""
#    try:
#        lupulo = Lupulo.query.get_or_404(id)
#        return jsonify(lupulo.to_dict())
#    except Exception as e:
#        return jsonify({'error': f'Erro ao buscar lúpulo: {str(e)}'}), 500
#
#@api_bp.route('/leveduras/<int:id>', methods=['GET'])
#@login_required
#def get_levedura_by_id(id):
#    """Obter levedura específica por ID (para frontend)"""
#    try:
#        levedura = Levedura.query.get_or_404(id)
#        return jsonify(levedura.to_dict())
#    except Exception as e:
#        return jsonify({'error': f'Erro ao buscar levedura: {str(e)}'}), 500