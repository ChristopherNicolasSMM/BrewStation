# routes/config_routes.py
from flask import Blueprint, request, jsonify
from model.config import Configuracao
from sqlalchemy import text
import smtplib
import requests
from db.database import db

config_bp = Blueprint('config', __name__)

@config_bp.route('/configuracoes', methods=['GET'])
def get_configuracoes():
    """Retorna as configurações atuais do sistema"""
    try:
        configs = Configuracao.get_all_configs(include_sensitive=False)
        
        # Converter para formato simples (chave: valor) para compatibilidade com o frontend
        configs_simplificado = {}
        campos_configurados = {}  # Para indicar quais campos têm valores
        
        for chave, config_data in configs.items():
            configs_simplificado[chave] = config_data['valor']
            # Indicar se o campo tem valor configurado (útil para campos sensíveis)
            campos_configurados[chave] = True #config_data['valor'] not in ['', None, '********']
        
        return jsonify({
            'configuracoes': configs_simplificado,
            'campos_configurados': campos_configurados
        })
        
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return jsonify({'error': str(e)}), 500    

@config_bp.route('/configuracoes', methods=['POST'])
def save_configuracoes():
    """Salva as configurações no banco de dados"""
    try:
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

@config_bp.route('/configuracoes/testar', methods=['POST'])
def testar_configuracoes():
    """Testa as configurações atuais"""
    try:
        # Testar conexão com banco de dados
        db.session.execute(text('SELECT * FROM configuracoes LIMIT 1'))
        db_status = 'connected'
        
        # Testar BrewFather API
        brewfather_status = 'disconnected'
        user_id = Configuracao.get_config('BREWFATHER_USER_ID')
        api_key = Configuracao.get_config('BREWFATHER_API_KEY')
        
        if user_id and api_key:
            try:
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
        mail_use_tls = Configuracao.get_config('MAIL_USE_TLS') == True
        
        if mail_server and mail_port and mail_username and mail_password:
            print("Iniciando teste de email...")
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
                email_status = 'auth_error'
                print("Erro de autenticação SMTP.")
            except smtplib.SMTPConnectError:
                email_status = 'connect_error'
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

@config_bp.route('/configuracoes/status', methods=['GET'])
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