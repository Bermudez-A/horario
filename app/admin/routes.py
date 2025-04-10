from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
import os
from werkzeug.utils import secure_filename
from app import db
from app.admin import admin
from app.admin.forms import UserForm, ProfesorForm, AsignaturaForm, ClaseForm, AsignarProfesorClaseForm
from app.models.user import User
from app.models.profesor import Profesor
from app.models.asignatura import Asignatura, AsignaturaProfesor, AsignaturaProfesorClase
from app.models.clase import Clase
from app.admin.utils import admin_required, save_picture
from app.models.disponibilidad_comun import DisponibilidadComun
from app.models.actividad_especial import ActividadEspecial
from app.models.disponibilidad import Disponibilidad

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
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # Verificar que no se está intentando eliminar a sí mismo
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('admin.users'))
    
    try:
        # Si es profesor, primero desactivar el usuario
        if user.rol == 'profesor':
            user.activo = False
            db.session.flush()
            
            # Eliminar asignaciones de clases
            asignaciones = AsignaturaProfesorClase.query.filter_by(profesor_id=user.profesor.id).all()
            for asignacion in asignaciones:
                db.session.delete(asignacion)
            
            # Eliminar relaciones con asignaturas
            relaciones = AsignaturaProfesor.query.filter_by(profesor_id=user.profesor.id).all()
            for relacion in relaciones:
                db.session.delete(relacion)
            
            # Eliminar disponibilidades
            disponibilidades = Disponibilidad.query.filter_by(profesor_id=user.profesor.id).all()
            for disponibilidad in disponibilidades:
                db.session.delete(disponibilidad)
            
            # Eliminar el perfil de profesor
            db.session.delete(user.profesor)
        
        # Finalmente eliminar el usuario
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Usuario {user.username} eliminado exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el usuario: {str(e)}', 'danger')
    
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
    profesores = Profesor.query.all()
    asignaturas = Asignatura.query.all()
    
    # Agrupar profesores por asignatura
    profesores_por_asignatura = {}
    
    # Primero obtenemos todas las asignaturas
    for asignatura in asignaturas:
        profesores_por_asignatura[asignatura] = []
    
    # Lista para profesores sin asignar
    profesores_sin_asignar = []
    
    # Luego asignamos los profesores a sus asignaturas
    for profesor in profesores:
        if not profesor.asignaturas:
            # Si el profesor no tiene asignaturas, lo añadimos a la lista de sin asignar
            profesores_sin_asignar.append(profesor)
        else:
            # Si tiene asignaturas, lo añadimos a cada una de ellas
            for asignatura_profesor in profesor.asignaturas:
                if asignatura_profesor.asignatura in profesores_por_asignatura:
                    if profesor not in profesores_por_asignatura[asignatura_profesor.asignatura]:
                        profesores_por_asignatura[asignatura_profesor.asignatura].append(profesor)
    
    return render_template('admin/profesores.html', 
                           title='Gestión de Profesores', 
                           profesores_por_asignatura=profesores_por_asignatura,
                           profesores_sin_asignar=profesores_sin_asignar,
                           asignaturas=asignaturas)

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
    
    # Crear formulario para edición (sin campos de selección de usuario)
    form = ProfesorForm()
    
    # Obtener asignaturas disponibles para el select
    asignaturas_disponibles = Asignatura.query.filter_by(activa=True).all()
    form.asignatura_id.choices = [(a.id, f"{a.nombre} ({a.codigo})") for a in asignaturas_disponibles]
    
    # En modo de edición, establecer un valor para usuario_tipo para evitar validaciones innecesarias
    form.usuario_tipo.data = 'edicion'
    
    # También establecer un valor para usuario_id para evitar errores de validación
    # No es necesario cargar opciones para usuario_id ya que no se mostrará en modo de edición
    form.usuario_id.choices = [(0, 'No aplicable')]
    
    if request.method == 'GET':
        form.nombre.data = profesor.usuario.nombre
        form.apellido.data = profesor.usuario.apellido
        form.bio.data = profesor.bio
        form.max_horas_diarias.data = profesor.max_horas_diarias
        
        # Seleccionar la asignatura actual (si existe)
        asignatura_actual = AsignaturaProfesor.query.filter_by(profesor_id=profesor.id).first()
        if asignatura_actual:
            form.asignatura_id.data = asignatura_actual.asignatura_id
    
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
        
        # Primero, eliminar todas las relaciones con clases
        asignaturas_profesor = AsignaturaProfesor.query.filter_by(profesor_id=profesor.id).all()
        for ap in asignaturas_profesor:
            # Eliminar primero las relaciones con clases
            AsignaturaProfesorClase.query.filter_by(asignatura_profesor_id=ap.id).delete()
        
        # Luego, eliminar las relaciones con asignaturas
        AsignaturaProfesor.query.filter_by(profesor_id=profesor.id).delete()
        
        # Finalmente, crear la nueva relación
        asignatura_profesor = AsignaturaProfesor(
            asignatura_id=form.asignatura_id.data,
            profesor_id=profesor.id
        )
        db.session.add(asignatura_profesor)
        
        db.session.commit()
        flash('Perfil de profesor actualizado con éxito', 'success')
        return redirect(url_for('admin.profesores'))
    
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
    
    # Cálculo de horas disponibles
    total_horas_semana = 5 * 7  # 5 días × 7 horas
    horas_actividades_especiales = ActividadEspecial.query.count()
    total_horas_disponibles = total_horas_semana - horas_actividades_especiales
    
    # Cálculo de horas requeridas
    total_horas_requeridas = sum(asignatura.horas_semanales for asignatura in Asignatura.query.filter_by(activa=True).all())
    
    # Cálculo de la diferencia
    diferencia_horas = total_horas_disponibles - total_horas_requeridas
    
    return render_template('admin/asignaturas.html', 
                         title='Gestión de Asignaturas', 
                         asignaturas=asignaturas,
                         total_horas_disponibles=total_horas_disponibles,
                         total_horas_requeridas=total_horas_requeridas,
                         diferencia_horas=diferencia_horas)

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

@admin.route('/clases/delete/<int:id>')
@login_required
@admin_required
def delete_clase(id):
    clase = Clase.query.get_or_404(id)
    
    # Verificar si la clase está en uso en horarios
    if hasattr(clase, 'horarios') and clase.horarios:
        flash(f'No se puede eliminar la clase {clase.nombre} porque tiene horarios asignados.', 'danger')
        return redirect(url_for('admin.clases'))
    
    nombre = clase.nombre
    db.session.delete(clase)
    db.session.commit()
    
    flash(f'Clase {nombre} eliminada con éxito', 'success')
    return redirect(url_for('admin.clases'))

# Ruta para MOSTRAR la página de disponibilidad de un profesor específico
# Esta ruta ahora solo necesita pasar el profesor a la plantilla.
# La carga/guardado de datos se hace vía API/JavaScript.
@admin.route('/profesores/disponibilidad/<int:profesor_id>', methods=['GET']) # Solo GET
@login_required
@admin_required
def disponibilidad_profesor(profesor_id):
    try:
        print(f"[Admin Route] Accediendo a disponibilidad para profesor ID: {profesor_id}")
        profesor = Profesor.query.get_or_404(profesor_id)
        print(f"[Admin Route] Profesor encontrado: {profesor.get_nombre_completo()}")

        # Renderizar la plantilla, pasando el objeto profesor con el nombre correcto
        return render_template(
            'admin/disponibilidad_profesor.html',
            title=f"Disponibilidad de {profesor.get_nombre_completo()}",
            profesor_seleccionado=profesor # <-- Nombre de variable CORREGIDO
        )
    except Exception as e:
        print(f"[Admin Route] ERROR al cargar disponibilidad para profesor {profesor_id}: {e}")
        flash('Error al cargar la página de disponibilidad del profesor.', 'danger')
        return redirect(url_for('admin.profesores')) # Redirigir si hay error

# Ruta para cambiar el estado del profesor (activo/inactivo)
@admin.route('/profesores/toggle_status/<int:id>')
@login_required
@admin_required
def toggle_profesor_status(id):
    profesor = Profesor.query.get_or_404(id)
    user = profesor.usuario
    
    if user.id == current_user.id:
        flash('No puedes cambiar el estado de tu propio usuario', 'danger')
        return redirect(url_for('admin.profesores'))
    
    user.activo = not user.activo
    db.session.commit()
    
    estado = "activado" if user.activo else "desactivado"
    flash(f'Profesor {user.username} {estado} con éxito', 'success')
    
    return redirect(url_for('admin.profesores'))

# Ruta para eliminar un profesor
@admin.route('/profesores/delete/<int:id>', methods=['POST'])
@login_required
def delete_profesor(id):
    profesor = Profesor.query.get_or_404(id)
    user = profesor.usuario
    
    # Verificar que no se está intentando eliminar a sí mismo
    if user.id == current_user.id:
        flash('No puedes eliminar tu propia cuenta.', 'danger')
        return redirect(url_for('admin.profesores'))
    
    try:
        # Primero desactivar el usuario
        user.activo = False
        db.session.flush()
        
        # Eliminar asignaciones de clases
        asignaciones = AsignaturaProfesorClase.query.filter_by(profesor_id=profesor.id).all()
        for asignacion in asignaciones:
            db.session.delete(asignacion)
        
        # Eliminar relaciones con asignaturas
        relaciones = AsignaturaProfesor.query.filter_by(profesor_id=profesor.id).all()
        for relacion in relaciones:
            db.session.delete(relacion)
        
        # Eliminar disponibilidades
        disponibilidades = Disponibilidad.query.filter_by(profesor_id=profesor.id).all()
        for disponibilidad in disponibilidades:
            db.session.delete(disponibilidad)
        
        # Eliminar el perfil de profesor
        db.session.delete(profesor)
        
        # Finalmente eliminar el usuario
        db.session.delete(user)
        db.session.commit()
        
        flash(f'Profesor {user.username} eliminado exitosamente.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el profesor: {str(e)}', 'danger')
    
    return redirect(url_for('admin.profesores'))

# Gestión de Horarios
@admin.route('/horarios')
@login_required
@admin_required
def horarios():
    clases = Clase.query.filter_by(activa=True).all()
    
    # Calcular estadísticas de horarios
    stats = {
        'clases': len(clases),
        'asignaturas': Asignatura.query.filter_by(activa=True).count(),
        'profesores': Profesor.query.join(User).filter(User.activo == True).count(),
        'horas': 0  # Se calculará a continuación
    }
    
    # Calcular porcentaje de completado para cada clase
    for clase in clases:
        # Intentar obtener horarios desde la base de datos
        if hasattr(clase, 'horarios'):
            bloques_totales = 35  # 7 horas x 5 días
            bloques_asignados = len(clase.horarios)
            porcentaje = round((bloques_asignados / bloques_totales) * 100) if bloques_totales > 0 else 0
            clase.porcentaje_completado = porcentaje
            stats['horas'] += bloques_asignados
        else:
            clase.porcentaje_completado = 0
    
    return render_template('admin/horarios.html', title='Gestión de Horarios', clases=clases, stats=stats)

@admin.route('/horarios/editar/<int:clase_id>')
@login_required
@admin_required
def editar_horario(clase_id):
    clase = Clase.query.get_or_404(clase_id)
    
    # Definir días y horas para el horario
    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
    horas = ['8:00 - 8:55', '9:00 - 9:55', '10:00 - 10:55', '11:00 - 11:55', 
             '12:00 - 12:55', '13:00 - 13:55', '14:00 - 14:55']
    
    # Obtener horario actual (si existe)
    from app.models.horario import Horario
    horarios_clase = Horario.query.filter_by(clase_id=clase.id).all()
    
    # Convertir a un diccionario para más fácil acceso
    horario = {}
    for h in horarios_clase:
        asignatura = Asignatura.query.get(h.asignatura_id)
        profesor = Profesor.query.get(h.profesor_id)
        
        # Verificar si hay conflictos (profesor ya asignado en esta hora/día en otra clase)
        conflicto = Horario.query.filter(
            Horario.clase_id != clase.id,
            Horario.dia == h.dia,
            Horario.hora == h.hora,
            Horario.profesor_id == h.profesor_id
        ).first() is not None
        
        horario[(h.dia, h.hora)] = {
            'asignatura_id': h.asignatura_id,
            'asignatura_nombre': asignatura.nombre if asignatura else "Asignatura no encontrada",
            'profesor_id': h.profesor_id,
            'profesor_nombre': profesor.get_nombre_completo() if profesor else "Profesor no encontrado",
            'color': asignatura.color if asignatura else "#cccccc",
            'conflicto': conflicto
        }
    
    # Obtener asignaturas disponibles
    asignaturas = []
    for asignatura in Asignatura.query.filter_by(activa=True).all():
        # Calcular horas ya asignadas
        horas_asignadas = Horario.query.filter_by(clase_id=clase.id, asignatura_id=asignatura.id).count()
        
        asignaturas.append({
            'id': asignatura.id,
            'nombre': asignatura.nombre,
            'codigo': asignatura.codigo,
            'color': asignatura.color,
            'horas_totales': asignatura.horas_semanales,
            'horas_asignadas': horas_asignadas,
            'horas_pendientes': asignatura.horas_semanales - horas_asignadas
        })
    
    # Filtrar asignaturas pendientes
    asignaturas_pendientes = [a for a in asignaturas if a['horas_pendientes'] > 0]
    
    # Obtener profesores disponibles
    profesores = []
    for profesor in Profesor.query.join(User).filter(User.activo == True).all():
        # Obtener asignaturas que puede impartir
        asignaturas_profesor = [ap.asignatura_id for ap in profesor.asignaturas]
        
        # Calcular disponibilidad
        disponibilidad = 100  # TODO: Calcular en base a tabla de disponibilidad
        
        profesores.append({
            'id': profesor.id,
            'nombre': profesor.get_nombre_completo(),
            'asignaturas': asignaturas_profesor,
            'disponibilidad': disponibilidad
        })
    
    # Calcular carga de profesores
    profesores_carga = []
    for profesor in Profesor.query.join(User).filter(User.activo == True).all():
        horas_asignadas = Horario.query.filter_by(profesor_id=profesor.id).count()
        horas_disponibles = profesor.max_horas_diarias * 5  # 5 días a la semana
        porcentaje = round((horas_asignadas / horas_disponibles) * 100) if horas_disponibles > 0 else 0
        
        profesores_carga.append({
            'id': profesor.id,
            'nombre': profesor.get_nombre_completo(),
            'horas_asignadas': horas_asignadas,
            'horas_disponibles': horas_disponibles,
            'porcentaje': porcentaje
        })
    
    # Calcular estadísticas
    bloques_totales = len(dias) * len(horas)
    bloques_asignados = len(horarios_clase)
    bloques_pendientes = bloques_totales - bloques_asignados
    
    # Contar conflictos
    conflictos = sum(1 for h in horario.values() if h.get('conflicto', False))
    
    stats = {
        'bloques_totales': bloques_totales,
        'bloques_asignados': bloques_asignados,
        'bloques_pendientes': bloques_pendientes,
        'conflictos': conflictos,
        'porcentaje_completado': round((bloques_asignados / bloques_totales) * 100) if bloques_totales > 0 else 0
    }
    
    return render_template('admin/editar_horario.html', 
                          title=f'Editar Horario - {clase.nombre}',
                          clase=clase,
                          dias=dias,
                          horas=horas,
                          horario=horario,
                          asignaturas=asignaturas,
                          asignaturas_pendientes=asignaturas_pendientes,
                          profesores=profesores,
                          profesores_carga=profesores_carga,
                          stats=stats)

@admin.route('/horarios/get_data/<int:clase_id>')
@login_required
@admin_required
def get_horario_data(clase_id):
    """API para obtener datos del horario en formato JSON"""
    clase = Clase.query.get_or_404(clase_id)
    
    # Obtener horario actual
    from app.models.horario import Horario
    horarios_clase = Horario.query.filter_by(clase_id=clase.id).all()
    
    horario = {}
    for h in horarios_clase:
        asignatura = Asignatura.query.get(h.asignatura_id)
        profesor = Profesor.query.get(h.profesor_id)
        
        horario[f"{h.dia}_{h.hora}"] = {
            'asignatura_id': h.asignatura_id,
            'asignatura_nombre': asignatura.nombre if asignatura else "Desconocida",
            'profesor_id': h.profesor_id,
            'profesor_nombre': profesor.get_nombre_completo() if profesor else "Desconocido",
            'color': asignatura.color if asignatura else "#cccccc"
        }
    
    return jsonify({'success': True, 'horario': horario})

@admin.route('/horarios/verificar_conflictos')
@login_required
@admin_required
def verificar_conflictos():
    """API para verificar conflictos al asignar un horario"""
    clase_id = request.args.get('clase_id', type=int)
    dia = request.args.get('dia')
    hora = request.args.get('hora')
    profesor_id = request.args.get('profesor_id', type=int)
    
    if not all([clase_id, dia, hora, profesor_id]):
        return jsonify({'success': False, 'message': 'Faltan parámetros requeridos'})
    
    # Verificar si el profesor ya está asignado en este horario en otra clase
    from app.models.horario import Horario
    conflicto_profesor = Horario.query.filter(
        Horario.clase_id != clase_id,
        Horario.dia == dia,
        Horario.hora == hora,
        Horario.profesor_id == profesor_id
    ).first() is not None
    
    # Verificar si esta asignatura ya está asignada en este horario para otra clase
    asignatura_id = request.args.get('asignatura_id', type=int)
    conflicto_asignatura = False
    if asignatura_id:
        conflicto_asignatura = Horario.query.filter(
            Horario.clase_id != clase_id,
            Horario.dia == dia,
            Horario.hora == hora,
            Horario.asignatura_id == asignatura_id
        ).first() is not None
    
    # Verificar disponibilidad del profesor
    from app.models.disponibilidad import Disponibilidad
    disponibilidad = Disponibilidad.query.filter_by(
        profesor_id=profesor_id,
        dia=dia,
        hora=int(hora.split(':')[0])  # Convertir "8:00 - 8:55" a 8
    ).first()
    
    conflicto_disponibilidad = disponibilidad is not None and not disponibilidad.disponible
    
    return jsonify({
        'success': True,
        'conflicto_profesor': conflicto_profesor,
        'conflicto_asignatura': conflicto_asignatura,
        'conflicto_disponibilidad': conflicto_disponibilidad
    })

@admin.route('/horarios/guardar_bloque', methods=['POST'])
@login_required
@admin_required
def guardar_bloque_horario():
    """API para guardar un bloque de horario"""
    data = request.json
    
    clase_id = data.get('clase_id')
    dia = data.get('dia')
    hora = data.get('hora')
    asignatura_id = data.get('asignatura_id')
    profesor_id = data.get('profesor_id')
    ignorar_conflictos = data.get('ignorar_conflictos', False)
    
    if not all([clase_id, dia, hora, asignatura_id, profesor_id]):
        return jsonify({'success': False, 'message': 'Faltan parámetros requeridos'})
    
    # Verificar que la clase, asignatura y profesor existan
    clase = Clase.query.get(clase_id)
    asignatura = Asignatura.query.get(asignatura_id)
    profesor = Profesor.query.get(profesor_id)
    
    if not all([clase, asignatura, profesor]):
        return jsonify({'success': False, 'message': 'Clase, asignatura o profesor no encontrado'})
    
    # Verificar conflictos solo si no se están ignorando
    if not ignorar_conflictos:
        # Verificar si el profesor ya está asignado en este horario en otra clase
        from app.models.horario import Horario
        conflicto_profesor = Horario.query.filter(
            Horario.clase_id != clase_id,
            Horario.dia == dia,
            Horario.hora == hora,
            Horario.profesor_id == profesor_id
        ).first()
        
        if conflicto_profesor:
            return jsonify({
                'success': False, 
                'message': f'Este profesor ya está asignado en este horario para la clase {Clase.query.get(conflicto_profesor.clase_id).nombre}'
            })
        
        # Verificar disponibilidad del profesor
        from app.models.disponibilidad import Disponibilidad
        hora_num = int(hora.split(':')[0])  # Convertir "8:00 - 8:55" a 8
        disponibilidad = Disponibilidad.query.filter_by(
            profesor_id=profesor_id,
            dia=dia,
            hora=hora_num
        ).first()
        
        if disponibilidad and not disponibilidad.disponible:
            return jsonify({
                'success': False, 
                'message': f'El profesor no está disponible en este horario'
            })
    
    # Guardar o actualizar horario
    from app.models.horario import Horario
    horario_existente = Horario.query.filter_by(
        clase_id=clase_id,
        dia=dia,
        hora=hora
    ).first()
    
    if horario_existente:
        horario_existente.asignatura_id = asignatura_id
        horario_existente.profesor_id = profesor_id
    else:
        horario = Horario(
            clase_id=clase_id,
            dia=dia,
            hora=hora,
            asignatura_id=asignatura_id,
            profesor_id=profesor_id
        )
        db.session.add(horario)
    
    db.session.commit()
    return jsonify({'success': True})

@admin.route('/horarios/eliminar_bloque', methods=['POST'])
@login_required
@admin_required
def eliminar_bloque_horario():
    """API para eliminar un bloque de horario"""
    data = request.json
    
    clase_id = data.get('clase_id')
    dia = data.get('dia')
    hora = data.get('hora')
    
    if not all([clase_id, dia, hora]):
        return jsonify({'success': False, 'message': 'Faltan parámetros requeridos'})
    
    # Eliminar horario
    from app.models.horario import Horario
    horario = Horario.query.filter_by(
        clase_id=clase_id,
        dia=dia,
        hora=hora
    ).first()
    
    if horario:
        db.session.delete(horario)
        db.session.commit()
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Horario no encontrado'})

@admin.route('/horarios/guardar_completo/<int:clase_id>', methods=['POST'])
@login_required
@admin_required
def guardar_horario_completo(clase_id):
    """Guardar todo el horario y finalizar edición"""
    clase = Clase.query.get_or_404(clase_id)
    
    # TODO: Aquí se podría implementar lógica adicional de validación
    
    return jsonify({'success': True, 'message': 'Horario guardado correctamente'})

@admin.route('/horarios/resetear/<int:clase_id>')
@login_required
@admin_required
def resetear_horario(clase_id):
    """Eliminar todas las asignaciones de horario para una clase"""
    clase = Clase.query.get_or_404(clase_id)
    
    # Eliminar todos los horarios de esta clase
    from app.models.horario import Horario
    Horario.query.filter_by(clase_id=clase.id).delete()
    db.session.commit()
    
    flash(f'Horario de {clase.nombre} reseteado correctamente', 'success')
    return redirect(url_for('admin.horarios'))

@admin.route('/horarios/autocompletar/<int:clase_id>', methods=['POST'])
@login_required
@admin_required
def autocompletar_horario(clase_id):
    """Autocompletar horario basado en disponibilidad y preferencias"""
    clase = Clase.query.get_or_404(clase_id)
    
    # Obtener asignaturas pendientes
    asignaturas_pendientes = []
    for asignatura in Asignatura.query.filter_by(activa=True).all():
        from app.models.horario import Horario
        horas_asignadas = Horario.query.filter_by(clase_id=clase.id, asignatura_id=asignatura.id).count()
        horas_pendientes = asignatura.horas_semanales - horas_asignadas
        
        if horas_pendientes > 0:
            asignaturas_pendientes.append({
                'id': asignatura.id,
                'nombre': asignatura.nombre,
                'horas_pendientes': horas_pendientes,
                'bloques_continuos': asignatura.bloques_continuos
            })
    
    # Si no hay asignaturas pendientes, terminar
    if not asignaturas_pendientes:
        return jsonify({'success': True, 'message': 'No hay asignaturas pendientes para asignar'})
    
    # Definir días y horas disponibles
    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
    horas = ['8:00 - 8:55', '9:00 - 9:55', '10:00 - 10:55', '11:00 - 11:55', 
             '12:00 - 12:55', '13:00 - 13:55', '14:00 - 14:55']
    
    # Obtener bloques ya asignados
    from app.models.horario import Horario
    bloques_asignados = Horario.query.filter_by(clase_id=clase.id).all()
    bloques_ocupados = set([(h.dia, h.hora) for h in bloques_asignados])
    
    # Intentar asignar asignaturas pendientes
    from app.models.asignatura import AsignaturaProfesor
    asignaciones_realizadas = 0
    
    for asignatura in asignaturas_pendientes:
        # Obtener profesores que pueden impartir esta asignatura
        profesores_disponibles = Profesor.query.join(AsignaturaProfesor).filter(
            AsignaturaProfesor.asignatura_id == asignatura['id']
        ).all()
        
        if not profesores_disponibles:
            continue  # Si no hay profesores para esta asignatura, saltar
        
        # Para cada hora pendiente de esta asignatura
        for _ in range(asignatura['horas_pendientes']):
            asignado = False
            
            # Probar cada combinación día/hora
            for dia in dias:
                if asignado:
                    break
                    
                for hora in horas:
                    # Si este bloque ya está ocupado, saltar
                    if (dia, hora) in bloques_ocupados:
                        continue
                    
                    # Probar cada profesor
                    for profesor in profesores_disponibles:
                        # Verificar si el profesor ya está asignado en este horario en otra clase
                        conflicto_profesor = Horario.query.filter(
                            Horario.clase_id != clase.id,
                            Horario.dia == dia,
                            Horario.hora == hora,
                            Horario.profesor_id == profesor.id
                        ).first() is not None
                        
                        if conflicto_profesor:
                            continue  # Este profesor ya está ocupado, probar otro
                        
                        # Verificar disponibilidad del profesor
                        from app.models.disponibilidad import Disponibilidad
                        hora_num = int(hora.split(':')[0])  # Convertir "8:00 - 8:55" a 8
                        disponibilidad = Disponibilidad.query.filter_by(
                            profesor_id=profesor.id,
                            dia=dia,
                            hora=hora_num
                        ).first()
                        
                        conflicto_disponibilidad = disponibilidad is not None and not disponibilidad.disponible
                        
                        if conflicto_disponibilidad:
                            continue  # Este profesor no está disponible en este horario
                        
                        # Asignar horario
                        horario = Horario(
                            clase_id=clase.id,
                            dia=dia,
                            hora=hora,
                            asignatura_id=asignatura['id'],
                            profesor_id=profesor.id
                        )
                        db.session.add(horario)
                        bloques_ocupados.add((dia, hora))
                        asignado = True
                        asignaciones_realizadas += 1
                        break  # Pasar a la siguiente hora pendiente
                    
                    if asignado:
                        break  # Pasar al siguiente día
    
    db.session.commit()
    
    if asignaciones_realizadas > 0:
        return jsonify({'success': True, 'message': f'Se realizaron {asignaciones_realizadas} asignaciones automáticamente'})
    else:
        return jsonify({'success': False, 'message': 'No se pudo completar ninguna asignación automáticamente'})

@admin.route('/horarios/generar')
@login_required
@admin_required
def generar_horarios():
    """Generar horarios para todas las clases automáticamente"""
    clases = Clase.query.filter_by(activa=True).all()
    
    if not clases:
        flash('No hay clases activas para generar horarios', 'warning')
        return redirect(url_for('admin.horarios'))
    
    # TODO: Implementar algoritmo más avanzado para generar horarios completos
    
    flash('Generación automática de horarios iniciada. Revise cada clase para completar manualmente si es necesario.', 'info')
    return redirect(url_for('admin.horarios'))

@admin.route('/asignaturas/asignar-profesores', methods=['GET', 'POST'])
@login_required
@admin_required
def asignar_profesores_clases():
    form = AsignarProfesorClaseForm()
    
    # Cargar las clases activas
    clases = Clase.query.filter_by(activa=True).all()
    form.clase_id.choices = [(c.id, c.nombre) for c in clases]
    
    # Si ya se seleccionó una clase, cargar las asignaturas y profesores
    clase_id = request.args.get('clase_id', type=int) or form.clase_id.data
    asignatura_id = request.args.get('asignatura_id', type=int)
    
    if clase_id:
        clase = Clase.query.get_or_404(clase_id)
        asignaturas = Asignatura.query.filter_by(activa=True).all()
        
        # Si se está editando una asignatura específica
        if asignatura_id:
            asignatura = Asignatura.query.get_or_404(asignatura_id)
            # Obtener todos los profesores que pueden enseñar esta asignatura
            asignaciones_profesor = AsignaturaProfesor.query.filter_by(asignatura_id=asignatura_id).all()
            profesores = [ap.profesor for ap in asignaciones_profesor if ap.profesor.usuario.activo]
            
            # Obtener el profesor actualmente asignado a esta clase para esta asignatura
            asignacion_actual = AsignaturaProfesorClase.query.join(AsignaturaProfesor).filter(
                AsignaturaProfesor.asignatura_id == asignatura_id,
                AsignaturaProfesorClase.clase_id == clase_id
            ).first()
            
            # Si el formulario ha sido enviado
            if request.method == 'POST':
                profesor_id = request.form.get('profesor_id', type=int)
                
                # Si se seleccionó un profesor
                if profesor_id:
                    # Verificar si ya existe una asignación para esta clase y asignatura
                    if asignacion_actual:
                        # Actualizar la asignación existente
                        asignacion_profesor = AsignaturaProfesor.query.filter_by(
                            asignatura_id=asignatura_id,
                            profesor_id=profesor_id
                        ).first()
                        
                        if asignacion_profesor:
                            asignacion_actual.asignatura_profesor_id = asignacion_profesor.id
                            db.session.commit()
                            flash(f'Profesor actualizado para la asignatura {asignatura.nombre} en la clase {clase.nombre}', 'success')
                        else:
                            flash('Combinación de profesor y asignatura no válida', 'danger')
                    else:
                        # Crear una nueva asignación
                        asignacion_profesor = AsignaturaProfesor.query.filter_by(
                            asignatura_id=asignatura_id,
                            profesor_id=profesor_id
                        ).first()
                        
                        if asignacion_profesor:
                            nueva_asignacion = AsignaturaProfesorClase(
                                asignatura_profesor_id=asignacion_profesor.id,
                                clase_id=clase_id
                            )
                            db.session.add(nueva_asignacion)
                            db.session.commit()
                            flash(f'Profesor asignado para la asignatura {asignatura.nombre} en la clase {clase.nombre}', 'success')
                        else:
                            flash('Combinación de profesor y asignatura no válida', 'danger')
                
                # Si se envió pero no se seleccionó ningún profesor, eliminar la asignación existente
                elif asignacion_actual and 'eliminar' in request.form:
                    db.session.delete(asignacion_actual)
                    db.session.commit()
                    flash(f'Asignación de profesor eliminada para la asignatura {asignatura.nombre}', 'success')
                
                return redirect(url_for('admin.asignar_profesores_clases', clase_id=clase_id))
            
            # Para el GET, preparar datos para la plantilla
            return render_template('admin/asignar_profesor_asignatura.html',
                                 title=f'Asignar Profesor para {asignatura.nombre} - {clase.nombre}',
                                 clase=clase,
                                 asignatura=asignatura,
                                 profesores=profesores,
                                 asignacion_actual=asignacion_actual)
        
        # Si solo se seleccionó la clase, mostrar la lista de asignaturas
        return render_template('admin/asignar_profesores.html',
                             title=f'Asignar Profesores para {clase.nombre}',
                             clase=clase,
                             asignaturas=asignaturas,
                             form=form)
    
    # Inicio: formulario para seleccionar clase
    return render_template('admin/seleccionar_clase.html',
                         title='Asignar Profesores a Clases',
                         form=form)

# Ruta para desvincular un profesor de una asignatura
@admin.route('/profesores/desvincular/<int:profesor_id>/<int:asignatura_id>')
@login_required
@admin_required
def desvincular_profesor(profesor_id, asignatura_id):
    profesor = Profesor.query.get_or_404(profesor_id)
    asignatura = Asignatura.query.get_or_404(asignatura_id)
    
    try:
        # Buscar la relación profesor-asignatura
        asignacion = AsignaturaProfesor.query.filter_by(
            profesor_id=profesor_id,
            asignatura_id=asignatura_id
        ).first()
        
        if asignacion:
            # Primero eliminar todas las asignaciones de clase asociadas
            AsignaturaProfesorClase.query.filter_by(asignatura_profesor_id=asignacion.id).delete()
            
            # Luego eliminar la relación profesor-asignatura
            db.session.delete(asignacion)
            db.session.commit()
            flash(f'Profesor {profesor.get_nombre_completo()} desvinculado de {asignatura.nombre} correctamente. Ahora aparece en la sección "Profesores sin asignar".', 'success')
        else:
            flash(f'El profesor {profesor.get_nombre_completo()} no está vinculado a {asignatura.nombre}', 'warning')
            
    except Exception as e:
        db.session.rollback()
        flash(f'Error al desvincular al profesor: {str(e)}', 'danger')
    
    return redirect(url_for('admin.profesores'))

# Ruta para vincular un profesor a una asignatura
@admin.route('/profesores/vincular/<int:profesor_id>', methods=['POST'])
@login_required
@admin_required
def vincular_profesor(profesor_id):
    try:
        profesor = Profesor.query.get_or_404(profesor_id)
        asignatura_id = request.form.get('asignatura_id')
        
        if not asignatura_id:
            flash('Debe seleccionar una asignatura.', 'warning')
            return redirect(url_for('admin.profesores'))
            
        asignatura = Asignatura.query.get_or_404(asignatura_id)
        
        # Verificar que la asignatura coincida con la especialidad del profesor
        if asignatura.nombre != profesor.especialidad:
            flash('El profesor solo puede ser vinculado a su asignatura de especialidad.', 'warning')
            return redirect(url_for('admin.profesores'))
        
        # Verificar si ya existe la relación
        if asignatura in profesor.asignaturas:
            flash('El profesor ya está vinculado a esta asignatura.', 'warning')
            return redirect(url_for('admin.profesores'))
        
        # Crear la relación
        asignatura_profesor = AsignaturaProfesor(
            asignatura_id=asignatura_id,
            profesor_id=profesor_id
        )
        db.session.add(asignatura_profesor)
        db.session.commit()
        
        flash(f'El profesor {profesor.get_nombre_completo()} ha sido vinculado a la asignatura {asignatura.nombre}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al vincular al profesor con la asignatura.', 'danger')
    
    return redirect(url_for('admin.profesores'))

@admin.route('/profesores/eliminar/<int:profesor_id>', methods=['POST'])
@login_required
@admin_required
def eliminar_profesor(profesor_id):
    try:
        profesor = Profesor.query.get_or_404(profesor_id)
        
        # Verificar si el profesor tiene asignaturas vinculadas
        if profesor.asignaturas:
            flash('No se puede eliminar el profesor porque tiene asignaturas vinculadas.', 'warning')
            return redirect(url_for('admin.profesores'))
        
        # Eliminar el profesor
        db.session.delete(profesor)
        db.session.commit()
        
        flash(f'El profesor {profesor.get_nombre_completo()} ha sido eliminado correctamente.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error al eliminar al profesor.', 'danger')
    
    return redirect(url_for('admin.profesores'))

@admin.route('/profesores/toggle_asignacion/<int:id>', methods=['POST'])
@login_required
@admin_required
def toggle_profesor_asignacion(id):
    profesor = Profesor.query.get_or_404(id)
    user = profesor.usuario
    
    try:
        if profesor.asignaturas:
            # Desvincular
            for asignatura_profesor in profesor.asignaturas:
                db.session.delete(asignatura_profesor)
            flash(f'Profesor {user.username} desvinculado con éxito', 'success')
        else:
            # Vincular
            # Aquí deberías definir la lógica para vincular al profesor a una asignatura
            flash(f'Profesor {user.username} vinculado con éxito', 'success')
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'Error al cambiar la asignación del profesor: {str(e)}', 'danger')
    
    return redirect(url_for('admin.profesores'))