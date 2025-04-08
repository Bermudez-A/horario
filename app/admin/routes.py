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

@admin.route('/users/toggle_status/<int:id>')
@login_required
@admin_required
def toggle_user_status(id):
    user = User.query.get_or_404(id)
    
    if user.id == current_user.id:
        flash('No puedes cambiar el estado de tu propio usuario', 'danger')
        return redirect(url_for('admin.users'))
    
    user.activo = not user.activo
    db.session.commit()
    
    estado = "activado" if user.activo else "desactivado"
    flash(f'Usuario {user.username} {estado} con éxito', 'success')
    
    return redirect(url_for('admin.users'))

# Gestión de Profesores
@admin.route('/profesores')
@login_required
@admin_required
def profesores():
    page = request.args.get('page', 1, type=int)
    profesores = Profesor.query.join(User).filter(User.activo == True).paginate(page=page, per_page=10)
    return render_template('admin/profesores.html', title='Gestión de Profesores', profesores=profesores)

@admin.route('/profesores/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_profesor():
    # Verificar si hay asignaturas disponibles
    asignaturas_disponibles = Asignatura.query.filter_by(activa=True).all()
    
    if not asignaturas_disponibles:
        flash('No hay asignaturas disponibles. Primero debe crear alguna asignatura.', 'warning')
        return render_template('admin/profesor_form.html', 
                               title='Añadir Profesor', 
                               no_asignaturas=True, 
                               asignaturas_url=url_for('admin.add_asignatura'))
    
    form = ProfesorForm()
    # Agregar las asignaturas disponibles al campo select
    form.asignatura_id.choices = [(a.id, f"{a.nombre} ({a.codigo})") for a in asignaturas_disponibles]
    
    # Cargar usuarios no administradores y sin perfil de profesor para el selector
    usuarios_disponibles = User.query.filter(
        User.rol != 'admin',  # No permitir administradores
        ~User.id.in_(db.session.query(Profesor.usuario_id))  # Solo usuarios sin perfil de profesor
    ).all()
    
    form.usuario_id.choices = [(u.id, f"{u.nombre} {u.apellido} ({u.username})") for u in usuarios_disponibles]
    
    if form.validate_on_submit():
        usuario_id = None
        
        if form.usuario_tipo.data == 'existente':
            # Usar un usuario existente
            usuario_id = form.usuario_id.data
            usuario = User.query.get(usuario_id)
            
            if not usuario:
                flash('El usuario seleccionado no existe.', 'danger')
                return redirect(url_for('admin.add_profesor'))
                
            if usuario.rol == 'admin':
                flash('No se puede asignar un perfil de profesor a un administrador.', 'danger')
                return redirect(url_for('admin.add_profesor'))
                
            # Cambiar el rol del usuario a profesor si no lo es
            if usuario.rol != 'profesor':
                usuario.rol = 'profesor'
                db.session.commit()
                
        else:  # form.usuario_tipo.data == 'nuevo'
            # Crear un usuario automáticamente para este profesor
            username = f"{form.nombre.data.lower()}.{form.apellido.data.lower()}".replace(" ", "")
            email = f"{username}@docente.com"
            
            # Asegurarse de que el username sea único
            base_username = username
            count = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{count}"
                count += 1
            
            # Crear el usuario
            user = User(
                username=username,
                email=email,
                nombre=form.nombre.data,
                apellido=form.apellido.data,
                rol='profesor'
            )
            user.activo = True
            user.set_password('profesor123')  # Contraseña por defecto
            
            db.session.add(user)
            db.session.flush()  # Para obtener el ID del usuario
            
            usuario_id = user.id
            usuario = user
        
        # Crear el perfil de profesor
        foto_file = None
        if form.foto.data:
            foto_file = save_picture(form.foto.data, 'profesores')
        
        profesor = Profesor(
            usuario_id=usuario_id,
            especialidad=Asignatura.query.get(form.asignatura_id.data).nombre,
            bio=form.bio.data,
            max_horas_diarias=form.max_horas_diarias.data,
            foto=foto_file
        )
        
        db.session.add(profesor)
        db.session.flush()
        
        # Crear la relación entre profesor y asignatura
        asignatura_profesor = AsignaturaProfesor(
            asignatura_id=form.asignatura_id.data,
            profesor_id=profesor.id
        )
        
        db.session.add(asignatura_profesor)
        db.session.commit()
        
        mensaje = 'Profesor creado con éxito'
        if form.usuario_tipo.data == 'nuevo':
            mensaje += f". Usuario: {username}, Contraseña: profesor123"
            
        flash(mensaje, 'success')
        return redirect(url_for('admin.profesores'))
    
    return render_template('admin/profesor_form.html', title='Añadir Profesor', form=form)

@admin.route('/profesores/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profesor(id):
    profesor = Profesor.query.get_or_404(id)
    form = ProfesorForm()
    
    # Obtener asignaturas disponibles para el select
    asignaturas_disponibles = Asignatura.query.filter_by(activa=True).all()
    form.asignatura_id.choices = [(a.id, f"{a.nombre} ({a.codigo})") for a in asignaturas_disponibles]
    
    if form.validate_on_submit():
        # Actualizar datos del usuario vinculado
        profesor.usuario.nombre = form.nombre.data
        profesor.usuario.apellido = form.apellido.data
        
        if form.foto.data:
            foto_file = save_picture(form.foto.data, 'profesores')
            profesor.foto = foto_file
        
        # Actualizar especialidad
        asignatura = Asignatura.query.get(form.asignatura_id.data)
        profesor.especialidad = asignatura.nombre
        profesor.bio = form.bio.data
        profesor.max_horas_diarias = form.max_horas_diarias.data
        
        # Actualizar la relación con asignaturas
        # Primero, eliminar todas las relaciones actuales
        AsignaturaProfesor.query.filter_by(profesor_id=profesor.id).delete()
        
        # Luego, crear la nueva relación
        asignatura_profesor = AsignaturaProfesor(
            asignatura_id=form.asignatura_id.data,
            profesor_id=profesor.id
        )
        db.session.add(asignatura_profesor)
        
        db.session.commit()
        flash('Perfil de profesor actualizado con éxito', 'success')
        return redirect(url_for('admin.profesores'))
    
    if request.method == 'GET':
        form.nombre.data = profesor.usuario.nombre
        form.apellido.data = profesor.usuario.apellido
        form.bio.data = profesor.bio
        form.max_horas_diarias.data = profesor.max_horas_diarias
        
        # Seleccionar la asignatura actual (si existe)
        asignatura_actual = AsignaturaProfesor.query.filter_by(profesor_id=profesor.id).first()
        if asignatura_actual:
            form.asignatura_id.data = asignatura_actual.asignatura_id
    
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

@admin.route('/asignaturas/delete/<int:id>')
@login_required
@admin_required
def delete_asignatura(id):
    asignatura = Asignatura.query.get_or_404(id)
    
    # Verificar si la asignatura está en uso en horarios
    if asignatura.horarios:
        flash(f'No se puede eliminar la asignatura {asignatura.nombre} porque está asignada a horarios.', 'danger')
        return redirect(url_for('admin.asignaturas'))
    
    # Primero eliminar todas las relaciones con profesores
    AsignaturaProfesor.query.filter_by(asignatura_id=asignatura.id).delete()
    
    # Luego eliminar la asignatura
    db.session.delete(asignatura)
    db.session.commit()
    
    flash(f'Asignatura {asignatura.nombre} eliminada con éxito', 'success')
    return redirect(url_for('admin.asignaturas'))

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

# Ruta para gestionar la disponibilidad de un profesor
@admin.route('/profesores/disponibilidad/<int:profesor_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def disponibilidad_profesor(profesor_id):
    profesor = Profesor.query.get_or_404(profesor_id)
    
    # Obtener la disponibilidad actual del profesor
    disponibilidad = {
        'lunes': [0] * 24,
        'martes': [0] * 24,
        'miercoles': [0] * 24,
        'jueves': [0] * 24,
        'viernes': [0] * 24,
        'sabado': [0] * 24,
        'domingo': [0] * 24
    }
    
    # Cargar disponibilidad existente en DB
    for disp in profesor.disponibilidad:
        disponibilidad[disp.dia][disp.hora] = disp.disponible
    
    if request.method == 'POST':
        # Actualizar disponibilidad desde el formulario
        from app.models.disponibilidad import Disponibilidad
        
        # Eliminar registros existentes
        for disp in profesor.disponibilidad:
            db.session.delete(disp)
        
        # Crear nuevos registros según el formulario
        for dia in disponibilidad.keys():
            for hora in range(24):
                estado = request.form.get(f'{dia}_{hora}', '0')
                if estado == '1':  # Solo guardar las horas disponibles
                    nueva_disp = Disponibilidad(
                        profesor_id=profesor.id,
                        dia=dia,
                        hora=hora,
                        disponible=1
                    )
                    db.session.add(nueva_disp)
        
        db.session.commit()
        flash('Disponibilidad actualizada correctamente', 'success')
        return redirect(url_for('admin.profesores'))
    
    dias_semana = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado', 'domingo']
    horas = list(range(24))
    
    return render_template('admin/disponibilidad_profesor.html', 
                           title=f'Disponibilidad de {profesor.get_nombre_completo()}',
                           profesor=profesor,
                           disponibilidad=disponibilidad,
                           dias_semana=dias_semana,
                           horas=horas)

# Ruta para cambiar el estado del profesor (activo/inactivo)
@admin.route('/profesores/toggle_status/<int:id>')
@login_required
@admin_required
def toggle_profesor_status(id):
    profesor = Profesor.query.get_or_404(id)
    usuario = profesor.usuario
    
    usuario.activo = not usuario.activo
    db.session.commit()
    
    estado = "activado" if usuario.activo else "desactivado"
    flash(f'Profesor {profesor.get_nombre_completo()} {estado} correctamente', 'success')
    
    return redirect(url_for('admin.profesores'))

# Ruta para eliminar un profesor
@admin.route('/profesores/delete/<int:id>')
@login_required
@admin_required
def delete_profesor(id):
    profesor = Profesor.query.get_or_404(id)
    usuario = profesor.usuario
    
    # Eliminar profesor (las relaciones se eliminarán en cascada)
    db.session.delete(profesor)
    # Eliminar usuario asociado
    db.session.delete(usuario)
    
    db.session.commit()
    flash('Profesor eliminado correctamente', 'success')
    
    return redirect(url_for('admin.profesores')) 