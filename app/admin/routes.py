from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from app import db
from app.admin import admin
from app.admin.forms import UserForm, ProfesorForm, AsignaturaForm, ClaseForm
from app.models.user import User
from app.models.profesor import Profesor
from app.models.asignatura import Asignatura, AsignaturaProfesor
from app.models.clase import Clase
from app.admin.utils import admin_required, save_picture

# Dashboard
@admin.route('/')
@login_required
@admin_required
def dashboard():
    users_count = User.query.count()
    profesores_count = Profesor.query.count()
    asignaturas_count = Asignatura.query.count()
    clases_count = Clase.query.count()
    
    return render_template('admin/dashboard.html', 
                           title='Panel de Administración',
                           users_count=users_count,
                           profesores_count=profesores_count,
                           asignaturas_count=asignaturas_count,
                           clases_count=clases_count)

# Gestión de Usuarios
@admin.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10)
    return render_template('admin/users.html', title='Gestión de Usuarios', users=users)

@admin.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    form = UserForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            nombre=form.nombre.data,
            apellido=form.apellido.data,
            rol=form.rol.data,
            activo=form.activo.data
        )
        # Contraseña temporal
        user.set_password('temporal123')
        
        db.session.add(user)
        db.session.commit()
        
        flash(f'Usuario {form.username.data} creado con éxito. Contraseña temporal: temporal123', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/user_form.html', title='Añadir Usuario', form=form)

@admin.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(original_username=user.username, original_email=user.email)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.nombre = form.nombre.data
        user.apellido = form.apellido.data
        user.rol = form.rol.data
        user.activo = form.activo.data
        
        db.session.commit()
        flash('Usuario actualizado con éxito', 'success')
        return redirect(url_for('admin.users'))
    
    if request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.nombre.data = user.nombre
        form.apellido.data = user.apellido
        form.rol.data = user.rol
        form.activo.data = user.activo
    
    return render_template('admin/user_form.html', title='Editar Usuario', form=form, user=user)

@admin.route('/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado con éxito', 'success')
    return redirect(url_for('admin.users'))

# Gestión de Profesores
@admin.route('/profesores')
@login_required
@admin_required
def profesores():
    page = request.args.get('page', 1, type=int)
    profesores = Profesor.query.join(User).filter(User.activo == True).paginate(page=page, per_page=10)
    return render_template('admin/profesores.html', title='Gestión de Profesores', profesores=profesores)

@admin.route('/profesores/add/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def add_profesor(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.profesor:
        flash('Este usuario ya tiene un perfil de profesor', 'warning')
        return redirect(url_for('admin.profesores'))
    
    form = ProfesorForm()
    
    if form.validate_on_submit():
        foto_file = None
        if form.foto.data:
            foto_file = save_picture(form.foto.data, 'profesores')
        
        profesor = Profesor(
            usuario_id=user.id,
            especialidad=form.especialidad.data,
            bio=form.bio.data,
            max_horas_diarias=form.max_horas_diarias.data,
            foto=foto_file
        )
        
        db.session.add(profesor)
        db.session.commit()
        
        flash('Perfil de profesor creado con éxito', 'success')
        return redirect(url_for('admin.profesores'))
    
    return render_template('admin/profesor_form.html', title='Añadir Profesor', form=form, user=user)

@admin.route('/profesores/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profesor(id):
    profesor = Profesor.query.get_or_404(id)
    form = ProfesorForm()
    
    if form.validate_on_submit():
        if form.foto.data:
            foto_file = save_picture(form.foto.data, 'profesores')
            profesor.foto = foto_file
        
        profesor.especialidad = form.especialidad.data
        profesor.bio = form.bio.data
        profesor.max_horas_diarias = form.max_horas_diarias.data
        
        db.session.commit()
        flash('Perfil de profesor actualizado con éxito', 'success')
        return redirect(url_for('admin.profesores'))
    
    if request.method == 'GET':
        form.especialidad.data = profesor.especialidad
        form.bio.data = profesor.bio
        form.max_horas_diarias.data = profesor.max_horas_diarias
    
    return render_template('admin/profesor_form.html', 
                           title='Editar Profesor', 
                           form=form, 
                           profesor=profesor, 
                           user=profesor.usuario)

# Gestión de Asignaturas
@admin.route('/asignaturas')
@login_required
@admin_required
def asignaturas():
    page = request.args.get('page', 1, type=int)
    asignaturas = Asignatura.query.paginate(page=page, per_page=10)
    return render_template('admin/asignaturas.html', title='Gestión de Asignaturas', asignaturas=asignaturas)

@admin.route('/asignaturas/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_asignatura():
    form = AsignaturaForm()
    
    if form.validate_on_submit():
        asignatura = Asignatura(
            nombre=form.nombre.data,
            codigo=form.codigo.data,
            horas_semanales=form.horas_semanales.data,
            bloques_continuos=form.bloques_continuos.data,
            color=form.color.data,
            icono=form.icono.data,
            activa=form.activa.data
        )
        
        db.session.add(asignatura)
        db.session.commit()
        
        flash(f'Asignatura {form.nombre.data} creada con éxito', 'success')
        return redirect(url_for('admin.asignaturas'))
    
    return render_template('admin/asignatura_form.html', title='Añadir Asignatura', form=form)

@admin.route('/asignaturas/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_asignatura(id):
    asignatura = Asignatura.query.get_or_404(id)
    form = AsignaturaForm(original_nombre=asignatura.nombre, original_codigo=asignatura.codigo)
    
    if form.validate_on_submit():
        asignatura.nombre = form.nombre.data
        asignatura.codigo = form.codigo.data
        asignatura.horas_semanales = form.horas_semanales.data
        asignatura.bloques_continuos = form.bloques_continuos.data
        asignatura.color = form.color.data
        asignatura.icono = form.icono.data
        asignatura.activa = form.activa.data
        
        db.session.commit()
        flash('Asignatura actualizada con éxito', 'success')
        return redirect(url_for('admin.asignaturas'))
    
    if request.method == 'GET':
        form.nombre.data = asignatura.nombre
        form.codigo.data = asignatura.codigo
        form.horas_semanales.data = asignatura.horas_semanales
        form.bloques_continuos.data = asignatura.bloques_continuos
        form.color.data = asignatura.color
        form.icono.data = asignatura.icono
        form.activa.data = asignatura.activa
    
    return render_template('admin/asignatura_form.html', title='Editar Asignatura', form=form, asignatura=asignatura)

# Gestión de Clases
@admin.route('/clases')
@login_required
@admin_required
def clases():
    clases = Clase.query.all()
    return render_template('admin/clases.html', title='Gestión de Clases', clases=clases)

@admin.route('/clases/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_clase():
    form = ClaseForm()
    
    if form.validate_on_submit():
        clase = Clase(
            nombre=form.nombre.data,
            descripcion=form.descripcion.data,
            nivel=form.nivel.data,
            curso=form.curso.data,
            color=form.color.data,
            activa=form.activa.data
        )
        
        db.session.add(clase)
        db.session.commit()
        
        flash(f'Clase {form.nombre.data} creada con éxito', 'success')
        return redirect(url_for('admin.clases'))
    
    return render_template('admin/clase_form.html', title='Añadir Clase', form=form)

@admin.route('/clases/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_clase(id):
    clase = Clase.query.get_or_404(id)
    form = ClaseForm()
    
    if form.validate_on_submit():
        clase.nombre = form.nombre.data
        clase.descripcion = form.descripcion.data
        clase.nivel = form.nivel.data
        clase.curso = form.curso.data
        clase.color = form.color.data
        clase.activa = form.activa.data
        
        db.session.commit()
        flash('Clase actualizada con éxito', 'success')
        return redirect(url_for('admin.clases'))
    
    if request.method == 'GET':
        form.nombre.data = clase.nombre
        form.descripcion.data = clase.descripcion
        form.nivel.data = clase.nivel
        form.curso.data = clase.curso
        form.color.data = clase.color
        form.activa.data = clase.activa
    
    return render_template('admin/clase_form.html', title='Editar Clase', form=form, clase=clase) 