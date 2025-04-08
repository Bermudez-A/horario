from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.schedules import schedules
from app.models.clase import Clase
from app.models.horario import Horario
from app.models.profesor import Profesor
from app.models.asignatura import Asignatura, AsignaturaProfesor
from app.models.disponibilidad import Disponibilidad
from app.models.user import User
from app.schedules.generator import generate_schedule

@schedules.route('/')
@login_required
def index():
    clases = Clase.query.filter_by(activa=True).all()
    
    # Calcular estadísticas para la página de inicio
    horarios_activos = 0
    clases_total = len(clases)
    asignaturas_total = Asignatura.query.filter_by(activa=True).count()
    conflictos_total = 0  # Esto podría calcularse según tu lógica de conflictos
    
    # Obtener una lista de horarios recientes
    horarios = []
    for clase in clases:
        total_asignaciones = Horario.query.filter_by(clase_id=clase.id).count()
        if total_asignaciones > 0:
            horarios_activos += 1
            # Crear un objeto simplificado para la vista
            horarios.append({
                'id': clase.id,
                'nombre': clase.nombre,
                'periodo': f"{clase.nivel} - {clase.curso}",
                'fecha_creacion': Horario.query.filter_by(clase_id=clase.id).order_by(Horario.fecha_creacion.desc()).first().fecha_creacion,
                'activo': clase.activa
            })
    
    # Datos para el gráfico de carga semanal
    carga_semanal = [0, 0, 0, 0, 0]  # lunes a viernes
    for i, dia in enumerate(['lunes', 'martes', 'miercoles', 'jueves', 'viernes']):
        carga_semanal[i] = Horario.query.filter_by(dia=dia).count()
    
    return render_template('schedules/index.html', 
                          title='Horarios', 
                          clases=clases,
                          horarios=horarios,
                          horarios_activos=horarios_activos,
                          clases_total=clases_total,
                          asignaturas_total=asignaturas_total,
                          conflictos_total=conflictos_total,
                          carga_semanal=carga_semanal)

@schedules.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # Solo administradores pueden crear horarios
    if not current_user.rol == 'admin':
        flash('No tienes permiso para crear horarios', 'warning')
        return redirect(url_for('schedules.index'))
    
    clases = Clase.query.filter_by(activa=True).all()
    
    if request.method == 'POST':
        clase_id = request.form.get('clase_id')
        
        if not clase_id:
            flash('Debes seleccionar una clase', 'warning')
            return redirect(url_for('schedules.create'))
        
        # Redireccionar a la página de edición de horario para la clase seleccionada
        return redirect(url_for('schedules.edit_schedule', clase_id=clase_id))
    
    return render_template('schedules/create.html', 
                          title='Crear Nuevo Horario', 
                          clases=clases)

@schedules.route('/view/<int:clase_id>')
@login_required
def view_schedule(clase_id):
    clase = Clase.query.get_or_404(clase_id)
    horario = clase.get_horario_completo()
    
    # Verificar permisos
    if current_user.rol == 'alumno' and not current_user.id == clase_id:
        flash('No tienes permiso para ver este horario', 'warning')
        return redirect(url_for('schedules.index'))
    
    # Calcular distribución por día
    distribucion_dias = {
        'lunes': sum(1 for h in horario['lunes'] if h is not None),
        'martes': sum(1 for h in horario['martes'] if h is not None),
        'miercoles': sum(1 for h in horario['miercoles'] if h is not None),
        'jueves': sum(1 for h in horario['jueves'] if h is not None),
        'viernes': sum(1 for h in horario['viernes'] if h is not None)
    }
    
    # Generar resumen de asignaturas
    resumen_asignaturas = []
    asignaturas_ids = set()
    
    # Recopilar todas las asignaturas usadas en este horario
    for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']:
        for hora in horario[dia]:
            if hora and 'asignatura_id' in hora:
                asignaturas_ids.add(hora['asignatura_id'])
    
    # Obtener información de cada asignatura
    for asignatura_id in asignaturas_ids:
        asignatura = Asignatura.query.get(asignatura_id)
        if not asignatura:
            continue
            
        # Contar horas
        horas = 0
        profesor_nombre = None
        
        for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']:
            for hora in horario[dia]:
                if hora and hora.get('asignatura_id') == asignatura_id:
                    horas += 1
                    if not profesor_nombre and hora.get('profesor'):
                        profesor_nombre = hora.get('profesor')
        
        resumen_asignaturas.append({
            'nombre': asignatura.nombre,
            'profesor': profesor_nombre or 'Sin asignar',
            'horas': horas,
            'color': asignatura.color
        })
    
    return render_template('schedules/view.html', 
                          title=f'Horario de {clase.nombre}', 
                          clase=clase, 
                          horario=horario,
                          distribucion_dias=distribucion_dias,
                          resumen_asignaturas=resumen_asignaturas)

@schedules.route('/edit/<int:clase_id>')
@login_required
def edit_schedule(clase_id):
    # Solo administradores pueden editar horarios
    if not current_user.rol == 'admin':
        flash('No tienes permiso para editar horarios', 'warning')
        return redirect(url_for('schedules.view_schedule', clase_id=clase_id))
    
    clase = Clase.query.get_or_404(clase_id)
    asignaturas = Asignatura.query.filter_by(activa=True).all()
    profesores = Profesor.query.join(User).filter(User.activo == True).all()
    horario = clase.get_horario_completo()
    
    return render_template('schedules/edit.html', 
                          title=f'Editar Horario de {clase.nombre}', 
                          clase=clase, 
                          horario=horario,
                          asignaturas=asignaturas,
                          profesores=profesores)

@schedules.route('/update', methods=['POST'])
@login_required
def update_schedule():
    # Solo administradores pueden actualizar horarios
    if not current_user.rol == 'admin':
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'})
    
    try:
        data = request.json
        clase_id = data.get('clase_id')
        dia = data.get('dia')
        hora = data.get('hora')
        asignatura_id = data.get('asignatura_id')
        profesor_id = data.get('profesor_id')
        
        # Validar que todos los datos necesarios están presentes
        if not all([clase_id, dia, hora, asignatura_id, profesor_id]):
            return jsonify({'success': False, 'message': 'Faltan datos necesarios'})
        
        # Verificar si ya existe una asignación para esta clase en este horario
        horario_existente = Horario.get_by_clase_dia_hora(clase_id, dia, hora)
        
        if horario_existente:
            # Actualizar la asignación existente
            horario_existente.asignatura_id = asignatura_id
            horario_existente.profesor_id = profesor_id
            horario_existente.modificado_por = current_user.id
        else:
            # Crear una nueva asignación
            horario = Horario(
                clase_id=clase_id,
                dia=dia,
                hora=hora,
                asignatura_id=asignatura_id,
                profesor_id=profesor_id,
                modificado_por=current_user.id
            )
            db.session.add(horario)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Horario actualizado con éxito'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@schedules.route('/delete', methods=['POST'])
@login_required
def delete_schedule():
    # Solo administradores pueden eliminar horarios
    if not current_user.rol == 'admin':
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'})
    
    try:
        data = request.json
        horario_id = data.get('horario_id')
        
        if not horario_id:
            return jsonify({'success': False, 'message': 'ID de horario no proporcionado'})
        
        horario = Horario.query.get(horario_id)
        
        if not horario:
            return jsonify({'success': False, 'message': 'Horario no encontrado'})
        
        db.session.delete(horario)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Horario eliminado con éxito'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@schedules.route('/generate/<int:clase_id>', methods=['GET', 'POST'])
@login_required
def generate(clase_id):
    # Solo administradores pueden generar horarios
    if not current_user.rol == 'admin':
        flash('No tienes permiso para generar horarios', 'warning')
        return redirect(url_for('schedules.index'))
    
    clase = Clase.query.get_or_404(clase_id)
    
    if request.method == 'POST':
        # Eliminar horarios existentes para esta clase
        Horario.query.filter_by(clase_id=clase_id).delete()
        db.session.commit()
        
        # Llamar al algoritmo para generar el horario
        result = generate_schedule(clase_id)
        
        if result['success']:
            flash('Horario generado con éxito', 'success')
        else:
            flash(f'Error al generar el horario: {result["message"]}', 'danger')
        
        return redirect(url_for('schedules.view_schedule', clase_id=clase_id))
    
    return render_template('schedules/generate.html', 
                          title=f'Generar Horario para {clase.nombre}', 
                          clase=clase)

@schedules.route('/generate_all', methods=['GET', 'POST'])
@login_required
def generate_all():
    # Solo administradores pueden generar horarios
    if not current_user.rol == 'admin':
        flash('No tienes permiso para generar horarios', 'warning')
        return redirect(url_for('schedules.index'))
    
    clases = Clase.query.filter_by(activa=True).all()
    
    if request.method == 'POST':
        success_count = 0
        error_messages = []
        
        # Reiniciar el registro global de asignaciones para comenzar desde cero
        from app.schedules.generator import reset_asignaciones_globales
        reset_asignaciones_globales()
        
        for clase in clases:
            # Eliminar horarios existentes para esta clase
            Horario.query.filter_by(clase_id=clase.id).delete()
            
            # Llamar al algoritmo para generar el horario
            result = generate_schedule(clase.id)
            
            if result['success']:
                success_count += 1
            else:
                error_messages.append(f"Error en {clase.nombre}: {result['message']}")
        
        db.session.commit()
        
        if success_count == len(clases):
            flash(f'Horarios generados con éxito para {success_count} clases', 'success')
        else:
            flash(f'Generados {success_count} de {len(clases)} horarios. Errores: {", ".join(error_messages)}', 'warning')
        
        return redirect(url_for('schedules.index'))
    
    return render_template('schedules/generate_all.html', 
                          title='Generar Todos los Horarios', 
                          clases=clases)

@schedules.route('/availability')
@login_required
def availability():
    # Solo administradores y profesores pueden ver disponibilidad
    if not current_user.rol in ['admin', 'profesor']:
        flash('No tienes permiso para ver esta página', 'warning')
        return redirect(url_for('schedules.index'))
    
    if current_user.rol == 'profesor':
        # El profesor solo puede ver su propia disponibilidad
        profesor = Profesor.query.filter_by(usuario_id=current_user.id).first_or_404()
        profesores = [profesor]
    else:
        # El admin puede ver la disponibilidad de todos los profesores
        profesores = Profesor.query.all()
    
    return render_template('schedules/availability.html', 
                          title='Disponibilidad de Profesores', 
                          profesores=profesores)

@schedules.route('/availability/update', methods=['POST'])
@login_required
def update_availability():
    try:
        data = request.json
        profesor_id = data.get('profesor_id')
        dia = data.get('dia')
        hora = data.get('hora')
        disponible = data.get('disponible', False)
        motivo = data.get('motivo', '')
        
        # Verificar permisos
        if current_user.rol == 'profesor':
            profesor = Profesor.query.filter_by(usuario_id=current_user.id).first()
            if not profesor or profesor.id != int(profesor_id):
                return jsonify({'success': False, 'message': 'No tienes permiso para modificar esta disponibilidad'})
        elif current_user.rol != 'admin':
            return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'})
        
        # Actualizar o crear disponibilidad
        Disponibilidad.set_disponible(profesor_id, dia, hora, disponible, motivo)
        
        return jsonify({'success': True, 'message': 'Disponibilidad actualizada con éxito'})
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}) 