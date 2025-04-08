"""
Algoritmo Voraz para generación de horarios

Este módulo implementa un algoritmo voraz para la generación automática
de horarios escolares, respetando las restricciones de disponibilidad
de profesores, horas semanales de asignaturas, y preferencias horarias.
"""

from app import db
from app.models.clase import Clase
from app.models.horario import Horario
from app.models.profesor import Profesor
from app.models.asignatura import Asignatura, AsignaturaProfesor
from app.models.disponibilidad import Disponibilidad

# Constantes
DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
HORAS = list(range(1, 8))  # 1-7

def generate_schedule(clase_id):
    """
    Genera un horario automático para una clase específica
    utilizando un algoritmo voraz.
    
    Args:
        clase_id: ID de la clase para la que se generará el horario
        
    Returns:
        dict: Resultado de la operación con claves 'success' y 'message'
    """
    try:
        # Verificar que la clase existe
        clase = Clase.query.get(clase_id)
        if not clase:
            return {'success': False, 'message': 'La clase no existe'}
        
        # Obtener todas las asignaturas activas
        asignaturas = Asignatura.query.filter_by(activa=True).all()
        if not asignaturas:
            return {'success': False, 'message': 'No hay asignaturas disponibles'}
        
        # Crear una matriz para el horario (dias x horas)
        horario_matriz = {dia: [None] * len(HORAS) for dia in DIAS}
        
        # Seguimiento de horas asignadas por asignatura
        asignaciones = {asig.id: 0 for asig in asignaturas}
        
        # Ordenar asignaturas por prioridad (horas semanales, preferencia por bloques)
        asignaturas_ordenadas = sorted(
            asignaturas, 
            key=lambda a: (a.horas_semanales, a.bloques_continuos), 
            reverse=True
        )
        
        # Para cada asignatura, intentar colocarla en el horario
        for asignatura in asignaturas_ordenadas:
            # Verificar si ya se asignaron todas las horas para esta asignatura
            horas_restantes = asignatura.horas_semanales - asignaciones[asignatura.id]
            if horas_restantes <= 0:
                continue
            
            # Obtener profesores para esta asignatura
            profesores_disponibles = get_profesores_by_asignatura(asignatura.id)
            if not profesores_disponibles:
                return {
                    'success': False, 
                    'message': f'No hay profesores asignados a la asignatura {asignatura.nombre}'
                }
            
            # Si la asignatura prefiere bloques continuos, intentar asignar en bloques de 2
            if asignatura.bloques_continuos and horas_restantes >= 2:
                for _ in range(horas_restantes // 2):
                    if not asignar_bloque(
                        clase_id, asignatura, profesores_disponibles, 
                        horario_matriz, asignaciones, 2
                    ):
                        # Si no se puede asignar el bloque, intentar asignar horas individuales
                        for _ in range(2):
                            if asignaciones[asignatura.id] < asignatura.horas_semanales:
                                asignar_hora_individual(
                                    clase_id, asignatura, profesores_disponibles, 
                                    horario_matriz, asignaciones
                                )
            
            # Asignar las horas restantes individualmente
            horas_restantes = asignatura.horas_semanales - asignaciones[asignatura.id]
            for _ in range(horas_restantes):
                asignar_hora_individual(
                    clase_id, asignatura, profesores_disponibles, 
                    horario_matriz, asignaciones
                )
        
        # Verificar si se asignaron todas las horas requeridas
        total_horas_requeridas = sum(asig.horas_semanales for asig in asignaturas)
        total_horas_asignadas = sum(asignaciones.values())
        
        if total_horas_asignadas < total_horas_requeridas:
            return {
                'success': False, 
                'message': f'No se pudieron asignar todas las horas requeridas. Asignadas: {total_horas_asignadas}/{total_horas_requeridas}'
            }
        
        # Guardar el horario generado en la base de datos
        save_schedule_to_db(clase_id, horario_matriz)
        
        return {'success': True, 'message': 'Horario generado correctamente'}
    
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'message': f'Error al generar el horario: {str(e)}'}

def get_profesores_by_asignatura(asignatura_id):
    """Obtiene la lista de profesores asignados a una asignatura"""
    asignaciones = AsignaturaProfesor.query.filter_by(asignatura_id=asignatura_id).all()
    profesores = [asig.profesor for asig in asignaciones if asig.profesor.usuario.activo]
    return profesores

def asignar_bloque(clase_id, asignatura, profesores, horario_matriz, asignaciones, tamano_bloque=2):
    """Intenta asignar un bloque continuo de horas para una asignatura"""
    for dia in DIAS:
        for hora_inicio in range(1, len(HORAS) - tamano_bloque + 2):
            # Verificar si el bloque está disponible
            bloque_disponible = True
            for i in range(tamano_bloque):
                if horario_matriz[dia][hora_inicio + i - 1] is not None:
                    bloque_disponible = False
                    break
            
            if not bloque_disponible:
                continue
            
            # Encontrar un profesor disponible para todo el bloque
            for profesor in profesores:
                profesor_disponible = True
                
                # Verificar la disponibilidad del profesor para todo el bloque
                for i in range(tamano_bloque):
                    if not Disponibilidad.es_disponible(profesor.id, dia, hora_inicio + i):
                        profesor_disponible = False
                        break
                
                # Verificar que el profesor no exceda su máximo de horas diarias
                horas_asignadas_dia = sum(
                    1 for h in range(len(HORAS)) 
                    if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['profesor_id'] == profesor.id
                )
                if horas_asignadas_dia + tamano_bloque > profesor.max_horas_diarias:
                    profesor_disponible = False
                
                if profesor_disponible:
                    # Asignar el bloque
                    for i in range(tamano_bloque):
                        horario_matriz[dia][hora_inicio + i - 1] = {
                            'asignatura_id': asignatura.id,
                            'profesor_id': profesor.id
                        }
                    
                    # Actualizar contador de horas asignadas
                    asignaciones[asignatura.id] += tamano_bloque
                    
                    return True
    
    # No se pudo asignar el bloque
    return False

def asignar_hora_individual(clase_id, asignatura, profesores, horario_matriz, asignaciones):
    """Intenta asignar una hora individual para una asignatura"""
    for dia in DIAS:
        for hora in HORAS:
            # Verificar si el espacio está disponible
            if horario_matriz[dia][hora - 1] is not None:
                continue
            
            # Encontrar un profesor disponible
            for profesor in profesores:
                # Verificar la disponibilidad del profesor
                if not Disponibilidad.es_disponible(profesor.id, dia, hora):
                    continue
                
                # Verificar que el profesor no exceda su máximo de horas diarias
                horas_asignadas_dia = sum(
                    1 for h in range(len(HORAS)) 
                    if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['profesor_id'] == profesor.id
                )
                if horas_asignadas_dia + 1 > profesor.max_horas_diarias:
                    continue
                
                # Asignar la hora
                horario_matriz[dia][hora - 1] = {
                    'asignatura_id': asignatura.id,
                    'profesor_id': profesor.id
                }
                
                # Actualizar contador de horas asignadas
                asignaciones[asignatura.id] += 1
                
                return True
    
    # No se pudo asignar la hora
    return False

def save_schedule_to_db(clase_id, horario_matriz):
    """Guarda el horario generado en la base de datos"""
    # Primero eliminar cualquier horario existente para esta clase
    Horario.query.filter_by(clase_id=clase_id).delete()
    
    # Crear los nuevos registros de horario
    for dia in DIAS:
        for hora in HORAS:
            celda = horario_matriz[dia][hora - 1]
            if celda is not None:
                horario = Horario(
                    clase_id=clase_id,
                    dia=dia,
                    hora=hora,
                    asignatura_id=celda['asignatura_id'],
                    profesor_id=celda['profesor_id']
                )
                db.session.add(horario)
    
    db.session.commit() 