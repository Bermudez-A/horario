from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from datetime import datetime
from app import db
from app.auth import auth
from app.auth.forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm
from app.models.user import User

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Usuario o contraseña incorrectos', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.activo:
            flash('Esta cuenta ha sido desactivada. Contacte al administrador.', 'warning')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        user.ultima_conexion = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('index')
        
        flash(f'¡Bienvenido/a {user.nombre}!', 'success')
        return redirect(next_page)
    
    return render_template('auth/login.html', title='Iniciar Sesión', form=form)

@auth.route('/logout')
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))

@auth.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    if not current_user.rol == 'admin':
        flash('No tienes permisos para registrar usuarios', 'danger')
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            rol=form.rol.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuario {user.username} registrado correctamente', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('auth/register.html', title='Registrar Usuario', form=form)

@auth.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            # Aquí iría la lógica para enviar el correo con el token de restablecimiento
            # Por simplicidad, solo mostramos un mensaje de éxito
            flash('Se han enviado instrucciones para restablecer la contraseña a tu email.', 'info')
        else:
            flash('No se encontró ninguna cuenta con ese email.', 'warning')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', title='Restablecer Contraseña', form=form)

@auth.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Aquí iría la lógica para verificar el token
    # Por simplicidad, asumimos que el token es válido y mostramos el formulario
    
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        # user = User.verify_reset_password_token(token)
        # if not user:
        #     flash('El enlace de restablecimiento no es válido o ha caducado.', 'danger')
        #     return redirect(url_for('index'))
        
        # user.set_password(form.password.data)
        # db.session.commit()
        
        flash('Tu contraseña ha sido restablecida.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', title='Restablecer Contraseña', form=form) 