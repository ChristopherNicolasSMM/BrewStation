"""
Rotas principais da aplicação web
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user, login_user, logout_user
from model.user import User
from db.database import db
import os
from werkzeug.utils import secure_filename
from model.notification import Notification, NotificationTrash

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Página inicial - redireciona para login ou dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('main.login'))

@main_bp.route('/login')
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('login.html')

@main_bp.route('/register')
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('register.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal"""
    return render_template('dashboard.html')

@main_bp.route('/config')
@login_required
def config():
    """Página de configurações"""
    return render_template('config.html')



#################################################################
# Página de maltes
#################################################################
@main_bp.route('/maltes')
@login_required
def maltes():
    """Página de maltes"""
    return render_template('maltes.html')

#################################################################
# Página de lupulos
#################################################################

@main_bp.route('/lupulos')
@login_required
def lupulos():
    """Página de lúpulos"""
    return render_template('lupulos.html')


#################################################################
# Página de leveduras
#################################################################
@main_bp.route('/leveduras')
@login_required
def leveduras():
    """Página de leveduras"""
    return render_template('leveduras.html')


#################################################################
# Página de dispositivos
#################################################################
@main_bp.route('/dispositivos')
@login_required
def dispositivos():
    """Página de dispositivos"""
    return render_template('dispositivos.html')





#################################################################
# Página de Notificações
#################################################################
@main_bp.route('/notifications')
@login_required
def notifications_page():
    """Página completa de notificações"""
    return render_template('notifications.html')




#################################################################
# Página de Notificações
#################################################################
@main_bp.route('/brewfather')
@login_required
def brewfather():
    """Página completa do Brewfather API"""
    return render_template('brewfather.html')



#################################################################
# Página de receitas e cálculos
#################################################################

@main_bp.route('/receitas')
@login_required
def receitas():
    """Página de receitas"""
    return render_template('receitas.html')

@main_bp.route('/calculos')
@login_required
def calculos():
    """Página de cálculos"""
    return render_template('calculos.html')

@main_bp.route('/upload')
@login_required
def upload():
    """Página de upload"""
    return render_template('upload.html')

@main_bp.route('/relatorio-precos')
@login_required
def relatorio_precos():
    """Relatório de preços"""
    return render_template('relatorio_precos.html')

@main_bp.route('/relatorio-ingredientes')
@login_required
def relatorio_ingredientes():
    """Relatório de ingredientes"""
    return render_template('relatorio_ingredientes.html')


#################################################################
## Página de perfil do usuário
#################################################################
@main_bp.route('/profile')
@login_required
def profile():
    """Página de perfil"""
    return render_template('profile.html')

@main_bp.route('/perfil')
@login_required
def perfil():
    """Página de perfil do usuário"""
    return render_template('perfil.html')

@main_bp.route('/api/atualizar_perfil', methods=['POST'])
@login_required
def atualizar_perfil():
    """Atualizar dados do perfil do usuário"""
    try:
        # Se veio via formulário (template), usar request.form/request.files
        if request.form:
            # Mapear campos do formulário para o modelo
            current_user.nome_completo = request.form.get('fullName') or current_user.nome_completo
            current_user.sobre = request.form.get('about') or current_user.sobre
            current_user.empresa = request.form.get('company') or current_user.empresa
            current_user.cargo = request.form.get('job') or current_user.cargo
            current_user.pais = request.form.get('country') or current_user.pais
            current_user.endereco = request.form.get('address') or current_user.endereco
            current_user.telefone = request.form.get('phone') or current_user.telefone
            current_user.twitter = request.form.get('twitter') or current_user.twitter
            current_user.facebook = request.form.get('facebook') or current_user.facebook
            current_user.instagram = request.form.get('instagram') or current_user.instagram
            current_user.linkedin = request.form.get('linkedin') or current_user.linkedin

            # Upload da imagem de perfil, se enviada
            if 'profileImage' in request.files:
                file = request.files['profileImage']
                if file and file.filename:
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    ext_ok = '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions
                    if not ext_ok:
                        flash('Tipo de arquivo não permitido. Use png, jpg, jpeg ou gif.', 'danger')
                    else:
                        filename = secure_filename(f"user_{current_user.id}_{file.filename}")
                        # Salvar dentro de static/uploads/profiles para servir via url_for('static', ...)
                        save_dir = os.path.join(current_app.static_folder, 'uploads', 'profiles')
                        os.makedirs(save_dir, exist_ok=True)
                        filepath = os.path.join(save_dir, filename)
                        file.save(filepath)
                        # Armazenar caminho relativo a partir de static/
                        current_user.foto_perfil = f"uploads/profiles/{filename}"

            db.session.commit()
            flash('Perfil atualizado com sucesso.', 'success')
            return redirect(url_for('main.profile'))

        # Caso contrário, assumir JSON (API)
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Nenhum dado enviado'}), 400

        current_user.nome_completo = data.get('nome_completo', current_user.nome_completo)
        current_user.empresa = data.get('empresa', current_user.empresa)
        current_user.cargo = data.get('cargo', current_user.cargo)
        current_user.pais = data.get('pais', current_user.pais)
        current_user.endereco = data.get('endereco', current_user.endereco)
        current_user.telefone = data.get('telefone', current_user.telefone)
        current_user.sobre = data.get('sobre', current_user.sobre)
        current_user.twitter = data.get('twitter', current_user.twitter)
        current_user.facebook = data.get('facebook', current_user.facebook)
        current_user.instagram = data.get('instagram', current_user.instagram)
        current_user.linkedin = data.get('linkedin', current_user.linkedin)

        db.session.commit()

        return jsonify({
            'message': 'Perfil atualizado com sucesso',
            'user': {
                'nome_completo': current_user.nome_completo,
                'email': current_user.email,
                'empresa': current_user.empresa,
                'cargo': current_user.cargo
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        if request.form:
            flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')
            return redirect(url_for('main.profile'))
        return jsonify({'error': f'Erro ao atualizar perfil: {str(e)}'}), 400

@main_bp.route('/api/atualizar_configuracoes', methods=['POST'])
@login_required
def atualizar_configuracoes():
    """Atualizar configurações do usuário"""
    try:
        if request.form:
            current_user.notificacao_alteracoes = bool(request.form.get('notificacao_alteracoes'))
            current_user.notificacao_novos_produtos = bool(request.form.get('notificacao_novos_produtos'))
            current_user.notificacao_ofertas = bool(request.form.get('notificacao_ofertas'))
            db.session.commit()
            flash('Configurações atualizadas com sucesso.', 'success')
            return redirect(url_for('main.profile'))

        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'Nenhum dado enviado'}), 400
        current_user.notificacao_alteracoes = data.get('notificacao_alteracoes', False)
        current_user.notificacao_novos_produtos = data.get('notificacao_novos_produtos', False)
        current_user.notificacao_ofertas = data.get('notificacao_ofertas', False)
        db.session.commit()
        return jsonify({
            'message': 'Configurações atualizadas com sucesso',
            'configuracoes': {
                'notificacao_alteracoes': current_user.notificacao_alteracoes,
                'notificacao_novos_produtos': current_user.notificacao_novos_produtos,
                'notificacao_ofertas': current_user.notificacao_ofertas
            }
        }), 200
    except Exception as e:
        db.session.rollback()
        if request.form:
            flash(f'Erro ao atualizar configurações: {str(e)}', 'danger')
            return redirect(url_for('main.profile'))
        return jsonify({'error': f'Erro ao atualizar configurações: {str(e)}'}), 400

@main_bp.route('/api/alterar_senha', methods=['POST'])
@login_required
def alterar_senha():
    """Alterar senha do usuário"""
    try:
        if request.form:
            senha_atual = request.form.get('currentPassword')
            nova_senha = request.form.get('newPassword')
            confirmar_senha = request.form.get('renewPassword')
        else:
            data = request.get_json(silent=True) or {}
            senha_atual = data.get('senha_atual')
            nova_senha = data.get('nova_senha')
            confirmar_senha = data.get('confirmar_senha')

        if not all([senha_atual, nova_senha, confirmar_senha]):
            if request.form:
                flash('Todos os campos são obrigatórios.', 'danger')
                return redirect(url_for('main.profile'))
            return jsonify({'error': 'Todos os campos são obrigatórios'}), 400

        if not current_user.verify_password(senha_atual):
            if request.form:
                flash('Senha atual incorreta.', 'danger')
                return redirect(url_for('main.profile'))
            return jsonify({'error': 'Senha atual incorreta'}), 400

        if nova_senha != confirmar_senha:
            if request.form:
                flash('As novas senhas não coincidem.', 'danger')
                return redirect(url_for('main.profile'))
            return jsonify({'error': 'As novas senhas não coincidem'}), 400

        if len(nova_senha) < 6:
            if request.form:
                flash('A senha deve ter pelo menos 6 caracteres.', 'danger')
                return redirect(url_for('main.profile'))
            return jsonify({'error': 'A senha deve ter pelo menos 6 caracteres'}), 400

        current_user.password = nova_senha
        db.session.commit()

        if request.form:
            flash('Senha alterada com sucesso.', 'success')
            return redirect(url_for('main.profile'))
        return jsonify({'message': 'Senha alterada com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        if request.form:
            flash(f'Erro ao alterar senha: {str(e)}', 'danger')
            return redirect(url_for('main.profile'))
        return jsonify({'error': f'Erro ao alterar senha: {str(e)}'}), 400

@main_bp.route('/api/upload_foto_perfil', methods=['POST'])
@login_required
def upload_foto_perfil():
    """Upload de foto de perfil"""
    return jsonify({'error': 'Funcionalidade de upload desativada. Use /api/atualizar_perfil com multipart/form-data.'}), 501
    #try:
    #    if 'foto' not in request.files:
    #        return jsonify({'error': 'Nenhuma imagem enviada'}), 400
    #    
    #    file = request.files['foto']
    #    if file.filename == '':
    #        return jsonify({'error': 'Nenhuma imagem selecionada'}), 400
    #    
    #    # Validar tipo de arquivo
    #    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    #    if not ('.' in file.filename and 
    #            file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
    #        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
    #    
    #    # Processar imagem (aqui você pode salvar no filesystem, S3, etc.)
    #    filename = secure_filename(f"user_{current_user.id}_{file.filename}")
    #    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', filename)
    #    
    #    # Criar diretório se não existir
    #    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    #    file.save(filepath)
    #    
    #    # Atualizar caminho da foto no usuário
    #    current_user.foto_perfil = filename
    #    db.session.commit()
    #    
    #    return jsonify({
    #        'message': 'Foto de perfil atualizada com sucesso',
    #        'foto_url': url_for('static', filename=f'uploads/profiles/{filename}')
    #    }), 200
    #    
    #except Exception as e:
    #    return jsonify({'error': f'Erro ao fazer upload da foto: {str(e)}'}), 400
    


#################################################################
## Handlers de erro personalizados
#################################################################
@main_bp.errorhandler(404)
def not_found(error):
    """Handler para páginas não encontradas"""
    return render_template('notFound.html'), 404

@main_bp.errorhandler(500)
def internal_error(error):
    """Handler para erros internos do servidor"""
    db.session.rollback()
    return render_template('notFound.html'), 500

# Rota explícita para a página notFound
@main_bp.route('/notFound')
def not_found_page():
    """Página personalizada para rotas não encontradas"""
    return render_template('notFound.html')


#################################################################
# API de Notificações
#################################################################

@main_bp.route('/api/notifications', methods=['GET', 'POST'])
@login_required
def notifications():
    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        message = data.get('message')
        if not message:
            return jsonify({'error': 'Mensagem é obrigatória'}), 400
        notif = Notification(user_id=current_user.id, message=message)
        db.session.add(notif)
        db.session.commit()
        return jsonify({'message': 'Notificação criada', 'notification': notif.to_dict()}), 201

    # GET listagem
    status = request.args.get('status')  # all|read|unread
    q = Notification.query.filter_by(user_id=current_user.id)
    if status == 'read':
        q = q.filter_by(is_read=True)
    elif status == 'unread':
        q = q.filter_by(is_read=False)
    q = q.order_by(Notification.created_at.desc())
    return jsonify({'notifications': [n.to_dict() for n in q.all()]}), 200


@main_bp.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id: int):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if not notif:
        return jsonify({'error': 'Notificação não encontrada'}), 404
    notif.is_read = True
    db.session.commit()
    return jsonify({'message': 'Notificação marcada como lida'}), 200


@main_bp.route('/api/notifications/<int:notif_id>/unread', methods=['POST'])
@login_required
def mark_notification_unread(notif_id: int):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if not notif:
        return jsonify({'error': 'Notificação não encontrada'}), 404
    notif.is_read = False
    db.session.commit()
    return jsonify({'message': 'Notificação marcada como não lida'}), 200


@main_bp.route('/api/notifications/<int:notif_id>/trash', methods=['POST'])
@login_required
def move_notification_to_trash(notif_id: int):
    notif = Notification.query.filter_by(id=notif_id, user_id=current_user.id).first()
    if not notif:
        return jsonify({'error': 'Notificação não encontrada'}), 404
    trashed = NotificationTrash(
        original_notification_id=notif.id,
        user_id=notif.user_id,
        message=notif.message,
        is_read=notif.is_read,
        created_at=notif.created_at,
    )
    db.session.add(trashed)
    db.session.delete(notif)
    db.session.commit()
    return jsonify({'message': 'Notificação movida para a lixeira', 'trash': trashed.to_dict()}), 200


@main_bp.route('/api/notifications/trash', methods=['GET'])
@login_required
def list_trash_notifications():
    q = NotificationTrash.query.filter_by(user_id=current_user.id).order_by(NotificationTrash.trashed_at.desc())
    return jsonify({'trash': [t.to_dict() for t in q.all()]}), 200


@main_bp.route('/api/notifications/trash/<int:trash_id>/restore', methods=['POST'])
@login_required
def restore_trash_notification(trash_id: int):
    t = NotificationTrash.query.filter_by(id=trash_id, user_id=current_user.id).first()
    if not t:
        return jsonify({'error': 'Item da lixeira não encontrado'}), 404
    notif = Notification(
        user_id=t.user_id,
        message=t.message,
        is_read=t.is_read,
        created_at=t.created_at,
    )
    db.session.add(notif)
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': 'Notificação restaurada', 'notification': notif.to_dict()}), 200


@main_bp.route('/api/notifications/trash/<int:trash_id>', methods=['DELETE'])
@login_required
def delete_trash_notification(trash_id: int):
    t = NotificationTrash.query.filter_by(id=trash_id, user_id=current_user.id).first()
    if not t:
        return jsonify({'error': 'Item da lixeira não encontrado'}), 404
    db.session.delete(t)
    db.session.commit()
    return jsonify({'message': 'Excluída definitivamente'}), 200


@main_bp.route('/api/notifications/count', methods=['GET'])
@login_required
def unread_notifications_count():
    count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    return jsonify({'unread': count}), 200