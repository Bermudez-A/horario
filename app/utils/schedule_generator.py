def generate_schedule(clase_id, profesor_id=None):
    """Genera un horario para una clase específica"""
    # Obtener la clase y sus asignaturas
    clase = Clase.query.get_or_404(clase_id)
    asignaturas = Asignatura.query.join(ClaseAsignatura).filter(
        ClaseAsignatura.clase_id == clase_id
    ).all()
    
    # Obtener actividades especiales
    actividades_especiales = ActividadEspecial.query.all()
    slots_ocupados = {(a.dia, a.hora) for a in actividades_especiales}
    
    # Inicializar el horario
    horario = {}
    for dia in ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']:
        horario[dia] = {hora: None for hora in range(1, 9)}
    
    # Marcar slots ocupados por actividades especiales
    for dia, hora in slots_ocupados:
        horario[dia][hora] = {
            'tipo': 'actividad_especial',
            'nombre': next(a.nombre for a in actividades_especiales if a.dia == dia and a.hora == hora)
        }
    
    # Resto de la lógica de generación de horarios...
    # Asegurarse de no asignar clases en slots ocupados por actividades especiales
    
    return horario 