@schedules_bp.route('/check_conflicts')
def check_conflicts():
    """API para verificar conflictos al asignar una clase"""
    profesor_id = request.args.get('profesor_id', type=int)
    dia = request.args.get('dia')
    hora = request.args.get('hora', type=int)
    clase_id = request.args.get('clase_id', type=int)
    
    if not all([profesor_id, dia, hora, clase_id]):
        return jsonify({
            'conflict': True,
            'message': 'Faltan parámetros necesarios para verificar conflictos'
        })
    
    # Verificar disponibilidad del profesor en ese horario
    disponibilidad = Disponibilidad.query.filter_by(
        profesor_id=profesor_id,
        dia=dia,
        hora=hora
    ).first()
    
    if disponibilidad and not disponibilidad.disponible:
        return jsonify({
            'conflict': True,
            'message': f'El profesor no está disponible en este horario. Motivo: {disponibilidad.motivo or "No especificado"}'
        })
    
    # Verificar si el profesor ya está asignado en este horario en otra clase
    conflicto_profesor = Horario.query.filter(
        Horario.clase_id != clase_id,
        Horario.dia == dia,
        Horario.hora == hora,
        Horario.profesor_id == profesor_id
    ).first()
    
    if conflicto_profesor:
        # Obtener información adicional para el modal de unir clases
        clase_existente = Clase.query.get(conflicto_profesor.clase_id)
        asignatura_existente = Asignatura.query.get(conflicto_profesor.asignatura_id)
        
        return jsonify({
            'conflict': True,
            'conflict_type': 'profesor_asignado',
            'message': f'El profesor ya está asignado a otra clase en este horario',
            'conflicting_class': {
                'clase_id': conflicto_profesor.clase_id,
                'clase_nombre': clase_existente.nombre if clase_existente else 'Clase desconocida',
                'asignatura_id': conflicto_profesor.asignatura_id,
                'asignatura_nombre': asignatura_existente.nombre if asignatura_existente else 'Asignatura desconocida'
            }
        })
    
    # Si no hay conflictos, devolver OK
    return jsonify({
        'conflict': False,
        'message': 'No hay conflictos'
    })

@schedules_bp.route('/update', methods=['POST'])
@login_required
def update():
    """Actualiza una celda de horario"""
    data = request.get_json()
    
    # Validar datos
    if not all(key in data for key in ['asignatura_id', 'profesor_id', 'dia', 'hora']):
        return jsonify({'success': False, 'message': 'Faltan datos requeridos'})
    
    asignatura_id = data.get('asignatura_id')
    profesor_id = data.get('profesor_id')
    dia = data.get('dia')
    hora = data.get('hora')
    ajustar_otras_celdas = data.get('ajustar_otras_celdas', False)
    
    # Obtener el ID de la clase del cuerpo de la solicitud o del usuario actual
    clase_id = data.get('clase_id')
    if not clase_id and hasattr(current_user, 'clase_id'):
        clase_id = current_user.clase_id
    
    if not clase_id:
        return jsonify({'success': False, 'message': 'No se pudo determinar la clase'})
    
    try:
        # No validar conflictos aquí - ahora el frontend los muestra como advertencia
        # y es decisión del usuario si quiere guardar o no
        
        # Obtener o crear el horario para esta celda
        horario = Horario.get_by_clase_dia_hora(clase_id, dia, hora)
        
        if horario:
            # Actualizar existente
            horario.asignatura_id = asignatura_id
            horario.profesor_id = profesor_id
        else:
            # Crear nuevo
            horario = Horario(
                clase_id=clase_id,
                dia=dia,
                hora=hora,
                asignatura_id=asignatura_id,
                profesor_id=profesor_id
            )
            db.session.add(horario)
        
        cells_adjusted = []
        
        # Si se solicitó ajustar otras celdas con la misma asignatura
        if ajustar_otras_celdas:
            # Buscar otras celdas con la misma asignatura
            otros_horarios = Horario.query.filter_by(
                clase_id=clase_id,
                asignatura_id=asignatura_id
            ).filter(
                Horario.dia != dia, 
                Horario.hora != hora
            ).all()
            
            # Actualizar profesor
            for h in otros_horarios:
                h.profesor_id = profesor_id
                cells_adjusted.append({
                    'dia': h.dia, 
                    'hora': h.hora, 
                    'asignatura_id': h.asignatura_id, 
                    'profesor_id': h.profesor_id
                })
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Horario actualizado',
            'adjusted_cells': cells_adjusted
        })
        
    except Exception as e:
        current_app.logger.error(f"Error al actualizar horario: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'})

@schedules_bp.route('/api/actividades-especiales', methods=['GET'])
@login_required
def get_actividades_especiales():
    """Obtener todas las actividades especiales"""
    actividades = ActividadEspecial.query.all()
    return jsonify([{
        'id': a.id,
        'nombre': a.nombre,
        'descripcion': a.descripcion,
        'dia': a.dia,
        'hora': a.hora,
        'color': a.color
    } for a in actividades])

@schedules_bp.route('/api/actividades-especiales', methods=['POST'])
@login_required
def create_actividad_especial():
    """Crear una nueva actividad especial"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not all(key in data for key in ['nombre', 'slots']):
            return jsonify({'success': False, 'message': 'Faltan datos requeridos'})
        
        # Crear la actividad para cada slot seleccionado
        for slot in data['slots']:
            actividad = ActividadEspecial(
                nombre=data['nombre'],
                descripcion=data.get('descripcion', ''),
                dia=slot['dia'],
                hora=slot['hora'],
                color=data.get('color', '#3498db')
            )
            db.session.add(actividad)
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Actividad especial creada correctamente'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@schedules_bp.route('/api/actividades-especiales/<int:id>', methods=['DELETE'])
@login_required
def delete_actividad_especial(id):
    """Eliminar una actividad especial"""
    try:
        actividad = ActividadEspecial.query.get_or_404(id)
        db.session.delete(actividad)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Actividad especial eliminada correctamente'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}) 