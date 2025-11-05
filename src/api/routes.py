from sqlalchemy import func, text
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from model.ingredientes import Malte, Lupulo, Levedura, Receita, IngredienteReceita, CalculoPreco
from model.user import User
from model.config import Configuracao
from db.database import db
from utils.calculadora import CalculadoraPrecos
import pandas as pd
import json
from pathlib import Path
import os
import smtplib
from email.mime.text import MIMEText # Opcional, para simular uma mensagem

api_bp = Blueprint('api', __name__)
 
    
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












# ========== ROTAS PARA MALTES ==========

@api_bp.route('/maltes', methods=['GET'])
@login_required
def get_maltes():
    """Obter lista de maltes"""
    maltes = Malte.query.filter_by(ativo=True).all()
    return jsonify([malte.to_dict() for malte in maltes]), 200

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

# ========== ROTAS PARA LÚPULOS ==========

@api_bp.route('/lupulos', methods=['GET'])
@login_required
def get_lupulos():
    """Obter lista de lúpulos"""
    lupulos = Lupulo.query.filter_by(ativo=True).all()
    return jsonify([lupulo.to_dict() for lupulo in lupulos]), 200

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

# ========== ROTAS PARA LEVEDURAS ==========

@api_bp.route('/leveduras', methods=['GET'])
@login_required
def get_leveduras():
    """Obter lista de leveduras"""
    leveduras = Levedura.query.filter_by(ativo=True).all()
    return jsonify([levedura.to_dict() for levedura in leveduras]), 200

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

# ========== ROTAS PARA RECEITAS ==========

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

# ========== ROTAS PARA CÁLCULOS ==========

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

# ========== ROTAS PARA UPLOAD ==========

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

# ========== ROTAS ADICIONAIS PARA FRONTEND ==========

@api_bp.route('/lupulos/<int:id>', methods=['GET'])
@login_required
def get_lupulo_by_id(id):
    """Obter lúpulo específico por ID (para frontend)"""
    try:
        lupulo = Lupulo.query.get_or_404(id)
        return jsonify(lupulo.to_dict())
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar lúpulo: {str(e)}'}), 500

@api_bp.route('/leveduras/<int:id>', methods=['GET'])
@login_required
def get_levedura_by_id(id):
    """Obter levedura específica por ID (para frontend)"""
    try:
        levedura = Levedura.query.get_or_404(id)
        return jsonify(levedura.to_dict())
    except Exception as e:
        return jsonify({'error': f'Erro ao buscar levedura: {str(e)}'}), 500