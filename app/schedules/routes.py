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
from app.models.actividad_especial import ActividadEspecial

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
        horario_reciente = Horario.query.filter_by(clase_id=clase.id).order_by(Horario.fecha_creacion.desc()).first()
        if horario_reciente:
            horarios_activos += 1
            # Crear un objeto simplificado para la vista
            horarios.append({
                'id': clase.id,
                'nombre': clase.nombre,
                'periodo': f"{clase.nivel} - {clase.curso}",
                'fecha_creacion': horario_reciente.fecha_creacion,
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
        for hora_data in horario.get(dia, []):
            if hora_data and 'asignatura_id' in hora_data:
                asignaturas_ids.add(hora_data['asignatura_id'])
    
    # Obtener información de cada asignatura
    for asignatura_id in asignaturas_ids:
        asignatura = Asignatura.query.get(asignatura_id)
        if not asignatura:
            continue
            
        # Contar horas
        horas = 0
        profesor_nombre = None
        
        for dia in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']:
             for hora_data in horario.get(dia, []):
                if hora_data and hora_data.get('asignatura_id') == asignatura_id:
                    horas += 1
                    if not profesor_nombre and hora_data.get('profesor'):
                        profesor_nombre = hora_data.get('profesor')
        
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
    
    # Obtener actividades comunes
    try:
        from app.models.disponibilidad_comun import DisponibilidadComun
        actividades_comunes = DisponibilidadComun.get_all_as_dict()
    except Exception as e:
        # Si la tabla no existe o hay algún error, usamos un diccionario vacío
        actividades_comunes = {}
        print(f"Error al obtener actividades comunes: {str(e)}")
    
    return render_template('schedules/edit.html', 
                          title=f'Editar Horario de {clase.nombre}', 
                          clase=clase, 
                          horario=horario,
                          asignaturas=asignaturas,
                          profesores=profesores,
                          actividades_comunes=actividades_comunes)

@schedules.route('/update', methods=['POST'])
@login_required
def update_schedule():
    # Solo administradores pueden actualizar horarios
    if not current_user.rol == 'admin':
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'}), 403
    
    try:
        data = request.json
        clase_id = data.get('clase_id')
        dia = data.get('dia')
        hora = data.get('hora') # Esperamos formato '7:00 - 8:00'
        asignatura_id = data.get('asignatura_id')
        profesor_id = data.get('profesor_id')
        ajustar_clases = data.get('ajustar_clases', False)
        
        print(f"[Update Schedule] Recibido: clase={clase_id}, dia={dia}, hora={hora}, asig={asignatura_id}, prof={profesor_id}")
        
        # Validar que todos los datos necesarios están presentes
        if not all([clase_id, dia, hora, asignatura_id, profesor_id]):
             print("[Update Schedule] Error: Faltan datos")
             return jsonify({'success': False, 'message': 'Faltan datos necesarios'}), 400
        
        # Verificar si hay conflictos antes de actualizar
        if not Disponibilidad.es_disponible(profesor_id, dia, hora):
            print(f"[Update Schedule] Conflicto: Profesor {profesor_id} no disponible en {dia} {hora}")
            return jsonify({'success': False, 'message': 'El profesor no está disponible en este horario'}), 409
        
        # Verificar si el profesor ya tiene clase asignada en este horario
        clases_existentes = Horario.query.filter_by(
            profesor_id=profesor_id, 
            dia=dia, 
            hora=hora
        ).filter(Horario.clase_id != clase_id).all()
        
        if clases_existentes:
            clases_nombres = [h.clase.nombre for h in clases_existentes]
            print(f"[Update Schedule] Conflicto: Profesor {profesor_id} ya asignado en {dia} {hora} a {', '.join(clases_nombres)}")
            return jsonify({
                'success': False, 
                'message': 'El profesor ya tiene clase asignada en: ' + ', '.join(clases_nombres)
            }), 409
        
        # Lista para almacenar las celdas ajustadas
        adjusted_cells = []
        
        # Verificar si ya existe una asignación para esta clase en este horario
        horario_existente = Horario.get_by_clase_dia_hora(clase_id, dia, hora)
        
        if horario_existente:
            print(f"[Update Schedule] Actualizando horario existente ID: {horario_existente.id}")
            # Actualizar la asignación existente
            horario_existente.asignatura_id = asignatura_id
            horario_existente.profesor_id = profesor_id
            # horario_existente.modificado_por = current_user.id # Eliminado
        else:
            print(f"[Update Schedule] Creando nuevo horario para {dia} {hora}")
            # Crear una nueva asignación
            horario = Horario(
                clase_id=clase_id,
                dia=dia,
                hora=hora, # Asegurarse que el modelo acepta este formato string
                asignatura_id=asignatura_id,
                profesor_id=profesor_id
                # modificado_por=current_user.id # Eliminado
            )
            db.session.add(horario)
        
        # Si se solicita ajustar otras clases, buscar todas las de la misma asignatura en el mismo horario
        if ajustar_clases:
            print(f"[Update Schedule] Ajustando otras clases para Asignatura ID {asignatura_id}")
            # Buscar todas las clases de la misma asignatura en el horario
            clases_misma_asignatura = Horario.query.filter_by(
                clase_id=clase_id,
                asignatura_id=asignatura_id
            ).all()
            
            # Obtener el profesor preferido para esta asignatura
            # Esta lógica podría necesitar revisión si se quiere usar el profesor recién asignado
            profesor_preferido = AsignaturaProfesor.query.filter_by(
                asignatura_id=asignatura_id
            ).order_by(AsignaturaProfesor.prioridad).first()
            
            if profesor_preferido:
                profesor_id_preferido = profesor_preferido.profesor_id
                print(f"[Update Schedule] Profesor preferido para ajuste: {profesor_id_preferido}")
                
                # Actualizar todas las demás clases de la misma asignatura con el mismo profesor
                for h in clases_misma_asignatura:
                    # No modificar la clase que acabamos de actualizar
                    if h.dia == dia and h.hora == hora:
                        continue
                    
                    # Verificar si el profesor está disponible en ese horario
                    if Disponibilidad.es_disponible(profesor_id_preferido, h.dia, h.hora):
                        # Verificar si el profesor tiene conflicto con otra clase
                        conflicto = Horario.query.filter_by(
                            profesor_id=profesor_id_preferido,
                            dia=h.dia,
                            hora=h.hora
                        ).filter(Horario.clase_id != clase_id).first()
                        
                        if not conflicto:
                            print(f"[Update Schedule] Ajustando {h.dia} {h.hora} al profesor {profesor_id_preferido}")
                            h.profesor_id = profesor_id_preferido
                            # h.modificado_por = current_user.id # Eliminado
                            adjusted_cells.append({
                                'dia': h.dia,
                                'hora': h.hora,
                                'asignatura_id': h.asignatura_id,
                                'profesor_id': h.profesor_id
                            })
        
        db.session.commit()
        print("[Update Schedule] Cambios guardados con éxito.")
        return jsonify({
            'success': True, 
            'message': 'Horario actualizado con éxito',
            'adjusted_cells': adjusted_cells
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"[Update Schedule] ERROR: {str(e)}")
        import traceback
        traceback.print_exc() # Imprime traceback en consola Flask
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500

@schedules.route('/delete', methods=['POST'])
@login_required
def delete_schedule():
    # Solo administradores pueden eliminar horarios
    if not current_user.rol == 'admin':
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'}), 403
    
    try:
        data = request.json
        horario_id = data.get('horario_id')
        
        if not horario_id:
            return jsonify({'success': False, 'message': 'ID de horario no proporcionado'}), 400
        
        horario = Horario.query.get(horario_id)
        
        if not horario:
            return jsonify({'success': False, 'message': 'Horario no encontrado'}), 404
        
        db.session.delete(horario)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Horario eliminado con éxito'})
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500

@schedules.route('/delete_by_position', methods=['POST'])
@login_required
def delete_by_position():
    # Solo administradores pueden eliminar horarios
    if not current_user.rol == 'admin':
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'}), 403
    
    try:
        data = request.json
        clase_id = data.get('clase_id')
        dia = data.get('dia')
        hora = data.get('hora') # Esperamos formato '7:00 - 8:00'
        
        print(f"[Delete Position] Solicitud: clase={clase_id}, dia={dia}, hora={hora}")
        
        if not all([clase_id, dia, hora]):
            print("[Delete Position] Error: Faltan datos")
            return jsonify({'success': False, 'message': 'Faltan datos necesarios'}), 400
        
        # Buscar el horario por clase, día y hora
        horario = Horario.get_by_clase_dia_hora(clase_id, dia, hora)
        
        if not horario:
            print("[Delete Position] Error: Horario no encontrado")
            return jsonify({'success': False, 'message': 'Horario no encontrado'}), 404
            
        print(f"[Delete Position] Eliminando horario ID: {horario.id}")
        db.session.delete(horario)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Horario eliminado con éxito'})
    
    except Exception as e:
        db.session.rollback()
        print(f"[Delete Position] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500

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
        # NO HACEMOS COMMIT aquí todavía, el generador lo hará al final si tiene éxito
        
        # Llamar al algoritmo para generar el horario
        from .generator import generate_schedule, reset_asignaciones_globales
        reset_asignaciones_globales() # Asegurarse de reiniciar el estado global
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
            # Eliminar horarios existentes para esta clase ANTES de generar
            Horario.query.filter_by(clase_id=clase.id).delete()
            # db.session.commit() # Es mejor hacer commit después del bucle o dentro del generador
            
            # Llamar al algoritmo para generar el horario
            result = generate_schedule(clase.id) 
            
            if result['success']:
                success_count += 1
            else:
                error_messages.append(f"Error en {clase.nombre}: {result['message']}")
        
        # Commit final después de intentar generar todos
        try:
            db.session.commit()
            print("[Generate All] Commit final exitoso.")
        except Exception as e:
             db.session.rollback()
             print(f"[Generate All] ERROR en commit final: {str(e)}")
             flash(f'Error crítico al guardar los horarios generados: {str(e)}', 'danger')
             # Los mensajes de error individuales ya se acumularon
        
        if not error_messages:
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
    """Vista para gestionar actividades especiales"""
    if not current_user.rol == 'admin':
        flash('No tienes permiso para acceder a esta sección', 'warning')
        return redirect(url_for('schedules.index'))
    
    # Obtener todas las asignaturas para el selector de exámenes
    asignaturas = Asignatura.query.filter_by(activa=True).all()
    
    # Obtener actividades especiales existentes
    actividades = ActividadEspecial.query.all()
    actividades_dict = {}
    
    for actividad in actividades:
        # Convertir hora a nombre de sesión
        sesiones_map = {
            1: 'Primera', 2: 'Segunda', 3: 'Tercera', 4: 'Cuarta',
            5: 'Quinta', 6: 'Sexta', 7: 'Séptima'
        }
        sesion = sesiones_map.get(actividad.hora)
        
        if not sesion:
            continue
            
        if actividad.dia not in actividades_dict:
            actividades_dict[actividad.dia] = {}
            
        if sesion not in actividades_dict[actividad.dia]:
            actividades_dict[actividad.dia][sesion] = []
            
        nombre_actividad = actividad.nombre
        if actividad.nombre == 'Examen' and actividad.descripcion:
            nombre_actividad += f' - {actividad.descripcion}'
            
        actividades_dict[actividad.dia][sesion].append(nombre_actividad)
    
    return render_template('schedules/availability.html',
                          title='Actividades Especiales',
                          asignaturas=asignaturas,
                          actividades_existentes=actividades_dict)

@schedules.route('/availability/update', methods=['POST'])
@login_required
def update_availability():
    print("[Update Availability] Recibida solicitud POST")
    try:
        data = request.json
        print(f"[Update Availability] Datos recibidos: {data}")
        profesor_id = data.get('profesor_id')
        dia = data.get('dia') # Esperamos 'lunes', etc.
        hora = data.get('hora') # Esperamos '7:00 - 8:00', etc.
        disponible = data.get('disponible', False)
        motivo = data.get('motivo', '')
        
        # Validar datos básicos
        if not all([profesor_id, dia, hora]):
             print("[Update Availability] Error: Faltan datos clave (profesor, dia, hora)")
             return jsonify({'success': False, 'message': 'Faltan datos necesarios'}), 400
             
        if dia not in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']:
             print(f"[Update Availability] Error: Día inválido '{dia}'")
             return jsonify({'success': False, 'message': f'Día inválido: {dia}'}), 400
             
        # Aquí podríamos añadir validación del formato de hora si fuera necesario
        
        # Verificar permisos
        if current_user.rol == 'profesor':
            profesor = Profesor.query.filter_by(usuario_id=current_user.id).first()
            # Convertir profesor_id a int para comparación segura
            if not profesor or profesor.id != int(profesor_id):
                 print("[Update Availability] Error Permiso: Profesor intentando modificar otro ID")
                 return jsonify({'success': False, 'message': 'No tienes permiso para modificar esta disponibilidad'}), 403
        elif current_user.rol != 'admin':
            print("[Update Availability] Error Permiso: Rol no autorizado")
            return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'}), 403
        
        # Actualizar o crear disponibilidad
        print(f"[Update Availability] Llamando a Disponibilidad.set_disponible para prof {profesor_id}, {dia}, {hora}, disp={disponible}")
        disp_obj = Disponibilidad.set_disponible(profesor_id, dia, hora, disponible, motivo)
        print(f"[Update Availability] Operación set_disponible completada. Objeto: {disp_obj}")
        
        return jsonify({'success': True, 'message': 'Disponibilidad actualizada con éxito'})
    
    except Exception as e:
        print(f"[Update Availability] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500

@schedules.route('/check_conflicts')
@login_required
def check_conflicts():
    """Verifica conflictos de horario para un profesor en un día y hora específicos"""
    profesor_id = request.args.get('profesor_id', type=int)
    dia = request.args.get('dia')
    hora = request.args.get('hora') # Asume formato '7:00 - 8:00'
    clase_id = request.args.get('clase_id', type=int)
    
    print(f"[Check Conflicts] Solicitud: prof={profesor_id}, dia={dia}, hora={hora}, clase_actual={clase_id}")
    
    if not all([profesor_id, dia, hora]):
        return jsonify({'success': False, 'message': 'Faltan parámetros requeridos'}), 400
    
    # Verificar disponibilidad del profesor
    if not Disponibilidad.es_disponible(profesor_id, dia, hora):
        print("[Check Conflicts] Conflicto: Profesor no disponible.")
        return jsonify({
            'conflict': True,
            'message': 'El profesor no está disponible en este horario'
        })
    
    # Verificar si el profesor ya tiene clase asignada en este horario (excluyendo la clase actual si se edita)
    query = Horario.query.filter_by(
        profesor_id=profesor_id, 
        dia=dia, 
        hora=hora
    )
    if clase_id: # Si estamos editando, excluimos la propia clase
        query = query.filter(Horario.clase_id != clase_id)
        
    clases_existentes = query.all()
    
    if clases_existentes:
        clases_nombres = [h.clase.nombre for h in clases_existentes]
        print(f"[Check Conflicts] Conflicto: Profesor ya asignado a: {', '.join(clases_nombres)}")
        return jsonify({
            'conflict': True,
            'message': 'El profesor ya tiene clase asignada en: ' + ', '.join(clases_nombres)
        })
    
    # Verificar si hay algún bloque de disponibilidad común en este horario
    try:
        from app.models.disponibilidad_comun import DisponibilidadComun
        bloque_comun = DisponibilidadComun.get_by_dia_hora(dia, hora)
        if bloque_comun:
            print("[Check Conflicts] Conflicto: Actividad común encontrada.")
            return jsonify({
                'conflict': True, 
                'message': f'Hay una actividad común programada: {bloque_comun.titulo}'
            })
    except Exception as e:
        # Si la tabla no existe o hay algún error, ignoramos esta verificación
        print(f"[Check Conflicts] WARN al verificar actividades comunes: {str(e)}")
    
    print("[Check Conflicts] No se encontraron conflictos.")
    return jsonify({'conflict': False})

# app/schedules/routes.py (Revisión de la función get_disponibilidad)

@schedules.route('/get_disponibilidad/<int:profesor_id>')
@login_required
def get_disponibilidad(profesor_id):
    print(f"[Get Disponibilidad] Solicitud para profesor ID: {profesor_id}")
    # Verificar permisos
    if current_user.rol == 'profesor':
        profesor = Profesor.query.filter_by(usuario_id=current_user.id).first()
        if not profesor or profesor.id != profesor_id:
            print("[Get Disponibilidad] Error Permiso: Profesor intentando ver otro ID")
            return jsonify({'success': False, 'message': 'No tienes permiso para ver esta disponibilidad'}), 403
    elif current_user.rol != 'admin':
        print("[Get Disponibilidad] Error Permiso: Rol no autorizado")
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'}), 403
    
    try:
        import traceback # Para logs de error detallados

        disponibilidades = Disponibilidad.query.filter_by(profesor_id=profesor_id).all()
        print(f"[Get Disponibilidad] Encontradas {len(disponibilidades)} entradas en BD.")

        disponibilidad_dict = {}
        for disp in disponibilidades:
            # Asegurarse que dia y hora son strings no nulos
            dia_str = str(disp.dia).lower().strip() if disp.dia else None
            hora_str = str(disp.hora).strip() if disp.hora else None

            if dia_str and hora_str and dia_str in ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']:
                key = f"{dia_str}_{hora_str}" # ej: "lunes_7:00 - 8:00"
                disponibilidad_dict[key] = {
                    'id': disp.id,
                    'disponible': disp.disponible,
                    'motivo': getattr(disp, 'motivo', '') or '' # Usar getattr por si acaso
                }
            else:
                 print(f"[Get Disponibilidad] WARN: Entrada omitida por dia/hora inválidos o dia no estándar. ID: {disp.id}, Dia: {disp.dia}, Hora: {disp.hora}")

        print(f"[Get Disponibilidad] Diccionario final a enviar (Keys: {len(disponibilidad_dict)}): {disponibilidad_dict}")

        return jsonify({
            'success': True, 
            'disponibilidad': disponibilidad_dict
        })

    except Exception as e:
        print(f"[Get Disponibilidad] ERROR CRÍTICO para profesor {profesor_id}: {str(e)}")
        print(traceback.format_exc()) # Imprime el traceback completo en la consola del servidor Flask
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500

@schedules.route('/move_class', methods=['POST'])
@login_required
def move_class():
    """Mueve una clase de una posición a otra en el horario"""
    # Solo administradores pueden mover clases
    if not current_user.rol == 'admin':
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'}), 403
    
    try:
        data = request.json
        clase_id = data.get('clase_id')
        origen_dia = data.get('origen_dia')
        origen_hora = data.get('origen_hora') # Formato '7:00 - 8:00'
        destino_dia = data.get('destino_dia')
        destino_hora = data.get('destino_hora') # Formato '7:00 - 8:00'
        
        print(f"[Move Class] Solicitud: clase={clase_id} de {origen_dia} {origen_hora} a {destino_dia} {destino_hora}")
        
        if not all([clase_id, origen_dia, origen_hora, destino_dia, destino_hora]):
             print("[Move Class] Error: Faltan datos")
             return jsonify({'success': False, 'message': 'Faltan datos necesarios'}), 400
        
        # Buscar la asignación de horario original
        horario_origen = Horario.get_by_clase_dia_hora(clase_id, origen_dia, origen_hora)
        
        if not horario_origen:
            print("[Move Class] Error: Horario origen no encontrado")
            return jsonify({'success': False, 'message': 'Horario origen no encontrado'}), 404
        
        print(f"[Move Class] Horario origen encontrado ID: {horario_origen.id}")
        
        # Verificar si el destino ya está ocupado por OTRA asignatura en la MISMA clase
        horario_destino = Horario.get_by_clase_dia_hora(clase_id, destino_dia, destino_hora)
        if horario_destino:
            print("[Move Class] Error: Posición destino ya ocupada en esta clase")
            return jsonify({'success': False, 'message': 'La posición destino ya está ocupada'}), 409
        
        # Verificar disponibilidad del profesor en el nuevo horario
        if not Disponibilidad.es_disponible(horario_origen.profesor_id, destino_dia, destino_hora):
            print("[Move Class] Conflicto: Profesor no disponible en destino.")
            return jsonify({'success': False, 'message': 'El profesor no está disponible en el nuevo horario'}), 409
        
        # Verificar si el profesor ya tiene clase en ese horario en otra clase diferente
        clases_existentes_destino = Horario.query.filter_by(
            profesor_id=horario_origen.profesor_id,
            dia=destino_dia,
            hora=destino_hora
        ).filter(Horario.clase_id != clase_id).all()
        
        if clases_existentes_destino:
            clases_nombres = [h.clase.nombre for h in clases_existentes_destino]
            print(f"[Move Class] Conflicto: Profesor ya asignado a otras clases en destino: {', '.join(clases_nombres)}")
            return jsonify({
                'success': False,
                'message': 'El profesor ya tiene clase asignada en: ' + ', '.join(clases_nombres)
            }), 409
        
        # Crear nuevo registro de horario para el destino
        # NO creamos uno nuevo, simplemente actualizamos el existente
        print(f"[Move Class] Actualizando horario ID {horario_origen.id} a {destino_dia} {destino_hora}")
        horario_origen.dia = destino_dia
        horario_origen.hora = destino_hora
        # horario_origen.modificado_por = current_user.id # Eliminado
        
        # Guardar el cambio
        db.session.commit()
        print("[Move Class] Horario movido con éxito.")
        
        return jsonify({'success': True, 'message': 'Horario movido con éxito'})
        
    except Exception as e:
        db.session.rollback()
        print(f"[Move Class] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500 

<<<<<<< HEAD
@schedules.route('/save_special_activities', methods=['POST'])
@login_required
def save_special_activities():
    """Guardar actividades especiales"""
=======
@schedules.route('/unir_clases', methods=['POST'])
@login_required
def unir_clases():
    """Unir dos clases para que el mismo profesor imparta la misma asignatura a ambos grupos"""
    try:
        data = request.json
        if not data:
            return jsonify({'success': False, 'message': 'No se recibieron datos'})
        
        # Obtener datos necesarios
        clase_actual_id = data.get('clase_actual_id')
        profesor_id = data.get('profesor_id')
        asignatura_actual_id = data.get('asignatura_actual_id')
        dia = data.get('dia')
        hora = data.get('hora')
        
        # Validar datos obligatorios
        if not all([clase_actual_id, profesor_id, asignatura_actual_id, dia, hora]):
            return jsonify({'success': False, 'message': 'Faltan datos obligatorios'})
        
        # Verificar que la clase exista
        clase_actual = Clase.query.get(clase_actual_id)
        if not clase_actual:
            return jsonify({'success': False, 'message': 'La clase no existe'})
        
        # Verificar que el profesor exista
        profesor = Profesor.query.get(profesor_id)
        if not profesor:
            return jsonify({'success': False, 'message': 'El profesor no existe'})
        
        # Verificar la asignatura
        asignatura_actual = Asignatura.query.get(asignatura_actual_id)
        if not asignatura_actual:
            return jsonify({'success': False, 'message': 'La asignatura no existe'})
        
        # Verificar si ya existe un horario en esta posición
        horario_existente = Horario.query.filter_by(
            clase_id=clase_actual_id,
            dia=dia,
            hora=hora
        ).first()
        
        if horario_existente:
            # Si existe, actualizarlo
            horario_existente.asignatura_id = asignatura_actual_id
            horario_existente.profesor_id = profesor_id
        else:
            # Si no existe, crear uno nuevo
            horario = Horario(
                clase_id=clase_actual_id,
                dia=dia,
                hora=hora,
                asignatura_id=asignatura_actual_id,
                profesor_id=profesor_id
            )
            db.session.add(horario)
        
        # Eliminar cualquier otro horario de la misma asignatura en esta clase
        # pero en diferente posición
        Horario.query.filter(
            Horario.clase_id == clase_actual_id,
            Horario.asignatura_id == asignatura_actual_id,
            Horario.dia != dia,
            Horario.hora != hora
        ).delete()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Clase actualizada correctamente'
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"[Unir Clases] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500

@schedules.route('/clear_all/<int:clase_id>', methods=['POST'])
@login_required
def clear_all(clase_id):
    """Elimina todas las asignaciones de horario para una clase específica"""
    # Solo administradores pueden limpiar horarios
>>>>>>> 270550446b4b8a77cc12f49870042ae8af22be5e
    if not current_user.rol == 'admin':
        return jsonify({'success': False, 'message': 'No tienes permiso para esta acción'}), 403
    
    try:
<<<<<<< HEAD
        data = request.get_json()
        
        # Primero, eliminar todas las actividades especiales existentes
        ActividadEspecial.query.delete()
        
        # Crear las nuevas actividades
        for dia, sesiones in data.items():
            for sesion, actividades in sesiones.items():
                # Convertir la sesión a número de hora (1-7)
                sesiones_map = {
                    'Primera': 1, 'Segunda': 2, 'Tercera': 3, 'Cuarta': 4,
                    'Quinta': 5, 'Sexta': 6, 'Séptima': 7
                }
                hora = sesiones_map.get(sesion)
                
                if not hora:
                    continue
                
                for actividad_nombre in actividades:
                    # Si es un examen, extraer el nombre de la asignatura
                    if ' - ' in actividad_nombre:
                        nombre, asignatura = actividad_nombre.split(' - ', 1)
                    else:
                        nombre = actividad_nombre
                        asignatura = None
                    
                    # Determinar el color basado en el tipo de actividad
                    colores = {
                        'Deporte': '#4caf50',
                        'Inglés': '#2196f3',
                        'Barón de Warsage': '#ff9800',
                        'Tutoría': '#9c27b0',
                        'Disposición BON': '#e91e63',
                        'Examen': '#f44336'
                    }
                    
                    actividad = ActividadEspecial(
                        nombre=nombre,
                        descripcion=asignatura if asignatura else '',
                        dia=dia,
                        hora=hora,
                        color=colores.get(nombre, '#3498db')
                    )
                    db.session.add(actividad)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Actividades especiales guardadas correctamente'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar actividades especiales: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500 
=======
        # Verificar que la clase existe
        clase = Clase.query.get(clase_id)
        if not clase:
            return jsonify({'success': False, 'message': 'Clase no encontrada'}), 404
        
        # Eliminar todos los horarios de esta clase
        Horario.query.filter_by(clase_id=clase_id).delete()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Horario limpiado con éxito'})
    
    except Exception as e:
        db.session.rollback()
        print(f"[Clear All] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Error interno del servidor: {str(e)}'}), 500 
>>>>>>> 270550446b4b8a77cc12f49870042ae8af22be5e
