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
from app.models.asignatura import Asignatura, AsignaturaProfesor, AsignaturaProfesorClase
from app.models.disponibilidad import Disponibilidad
from app.models.disponibilidad_comun import DisponibilidadComun
from app.models.actividad_especial import ActividadEspecial
import random

# Constantes
DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
HORAS = list(range(1, 8))  # 1-7
MAX_HORAS_DIARIAS_POR_ASIGNATURA = 2  # Máximo de horas para una asignatura por día en una clase

# Mapeo de números a texto para horas
HORAS_TEXTO = {
    1: "1",
    2: "2",
    3: "3",
    4: "4",
    5: "5",
    6: "6",
    7: "7"
}

# Estructura global para rastrear asignaciones de profesores
# Formato: {(profesor_id, dia, hora): clase_id}
asignaciones_globales = {}

def reset_asignaciones_globales():
    """Reinicia el registro global de asignaciones de profesores"""
    global asignaciones_globales
    asignaciones_globales = {}
    
    # Cargar las asignaciones existentes en la base de datos
    horarios_existentes = Horario.query.all()
    for h in horarios_existentes:
        hora_numerica = int(h.hora) if h.hora.isdigit() else 0
        asignaciones_globales[(h.profesor_id, h.dia, hora_numerica)] = h.clase_id

def profesor_disponible_globalmente(profesor_id, dia, hora):
    """Verifica si un profesor ya está asignado en otra clase a la misma hora y día"""
    return (profesor_id, dia, hora) not in asignaciones_globales

def registrar_asignacion_global(profesor_id, dia, hora, clase_id):
    """Registra la asignación de un profesor en el horario global"""
    asignaciones_globales[(profesor_id, dia, hora)] = clase_id

def get_profesores_by_asignatura(asignatura_id, clase_id=None):
    """
    Obtiene la lista de profesores asignados a una asignatura.
    Si se proporciona clase_id, primero busca si hay un profesor específicamente asignado
    a esa clase para la asignatura.
    """
    # Si hay una clase específica, intentar obtener el profesor asignado a esa clase
    if clase_id is not None:
        try:
            profesor_asignado = AsignaturaProfesorClase.obtener_profesor_para_asignatura_clase(asignatura_id, clase_id)
            if profesor_asignado and profesor_asignado.usuario.activo:
                return [profesor_asignado]
        except Exception as e:
            # Si hay un error (por ejemplo, la tabla no existe), loguear y continuar
            print(f"Error al buscar profesor específico: {str(e)}")
    
    # Si no hay profesor específico o no se proporcionó clase_id, devolver todos los profesores
    asignaciones = AsignaturaProfesor.query.filter_by(asignatura_id=asignatura_id).all()
    profesores = [asig.profesor for asig in asignaciones if asig.profesor.usuario.activo]
    return profesores

def generate_schedule(clase_id):
    """Genera un horario automático para una clase específica"""
    try:
        # Verificar que la clase existe
        clase = Clase.query.get(clase_id)
        if not clase:
            return {'success': False, 'message': 'La clase no existe'}
        
        print(f"Generando horario para clase {clase.nombre}")
        
        # Obtener todas las asignaturas activas
        asignaturas = Asignatura.query.filter_by(activa=True).all()
        if not asignaturas:
            return {'success': False, 'message': 'No hay asignaturas disponibles'}
        
        print(f"Asignaturas disponibles: {[a.nombre for a in asignaturas]}")
        
        # Obtener todas las clases activas del mismo nivel y curso
        clases_mismo_nivel = Clase.query.filter_by(
            nivel=clase.nivel,
            curso=clase.curso,
            activa=True
        ).all()
        
        print(f"Clases del mismo nivel: {[c.nombre for c in clases_mismo_nivel]}")
        
        # Verificar que todas las clases tengan las mismas asignaturas
        asignaturas_por_clase = {}
        for otra_clase in clases_mismo_nivel:
            # Obtener las asignaturas de cada clase a través de sus horarios
            asignaturas_clase = set(
                h.asignatura_id for h in Horario.query.filter_by(clase_id=otra_clase.id).all()
            )
            asignaturas_por_clase[otra_clase.id] = asignaturas_clase
            print(f"Asignaturas de clase {otra_clase.nombre}: {asignaturas_clase}")
        
        # Si ninguna clase tiene asignaturas asignadas, usar las asignaturas activas como base
        if all(len(asignaturas) == 0 for asignaturas in asignaturas_por_clase.values()):
            print("Ninguna clase tiene asignaturas asignadas, usando asignaturas activas como base")
            # Todas las clases usarán las mismas asignaturas activas
            asignaturas_base = set(a.id for a in asignaturas)
            for otra_clase in clases_mismo_nivel:
                asignaturas_por_clase[otra_clase.id] = asignaturas_base
        else:
            # Verificar que todas las clases tengan las mismas asignaturas
            asignaturas_base = None
            for otra_clase in clases_mismo_nivel:
                if len(asignaturas_por_clase[otra_clase.id]) > 0:
                    if asignaturas_base is None:
                        asignaturas_base = asignaturas_por_clase[otra_clase.id]
                    elif asignaturas_por_clase[otra_clase.id] != asignaturas_base:
                        return {
                            'success': False,
                            'message': f'Las asignaturas no coinciden con la clase {otra_clase.nombre}'
                        }
            
            # Si alguna clase no tiene asignaturas, usar las asignaturas base
            for otra_clase in clases_mismo_nivel:
                if len(asignaturas_por_clase[otra_clase.id]) == 0:
                    asignaturas_por_clase[otra_clase.id] = asignaturas_base
        
        # Crear una matriz para el horario (dias x horas)
        horario_matriz = {dia: [None] * len(HORAS) for dia in DIAS}
        
        # Seguimiento de horas asignadas por asignatura
        asignaciones = {asig.id: 0 for asig in asignaturas}
        
        # Obtener el número de horas por asignatura que deben tener todas las clases
        horas_por_asignatura = {}
        for asignatura in asignaturas:
            # Verificar que todas las clases tengan el mismo número de horas para esta asignatura
            horas_en_clases = []
            for otra_clase in clases_mismo_nivel:
                horas = Horario.query.filter_by(
                    clase_id=otra_clase.id,
                    asignatura_id=asignatura.id
                ).count()
                horas_en_clases.append(horas)
            
            # Si todas las clases tienen 0 horas, usar las horas semanales
            if all(h == 0 for h in horas_en_clases):
                horas_por_asignatura[asignatura.id] = asignatura.horas_semanales
                print(f"Usando horas semanales para {asignatura.nombre}: {asignatura.horas_semanales}")
            else:
                # Si hay clases con horas asignadas, verificar que todas tengan el mismo número
                horas_no_cero = [h for h in horas_en_clases if h > 0]
                if len(set(horas_no_cero)) > 1:
                    return {
                        'success': False,
                        'message': f'Las clases no tienen el mismo número de horas para {asignatura.nombre}'
                    }
                horas_por_asignatura[asignatura.id] = horas_no_cero[0] if horas_no_cero else asignatura.horas_semanales
        
        print(f"Horas por asignatura: {horas_por_asignatura}")
        
        # Ordenar asignaturas por prioridad (horas semanales, preferencia por bloques)
        asignaturas_ordenadas = sorted(
            asignaturas, 
            key=lambda a: (horas_por_asignatura[a.id], a.bloques_continuos), 
            reverse=True
        )
        
        print(f"Asignaturas ordenadas: {[a.nombre for a in asignaturas_ordenadas]}")
        
        # Para cada asignatura, intentar colocarla en el horario
        for asignatura in asignaturas_ordenadas:
            print(f"Intentando asignar {asignatura.nombre} ({horas_por_asignatura[asignatura.id]} horas)")
            # Verificar si ya se asignaron todas las horas para esta asignatura
            horas_restantes = horas_por_asignatura[asignatura.id] - asignaciones[asignatura.id]
            if horas_restantes <= 0:
                print(f"Ya se asignaron todas las horas para {asignatura.nombre}")
                continue
            
            # Obtener profesores para esta asignatura, priorizando los asignados específicamente a esta clase
            profesores_disponibles = get_profesores_by_asignatura(asignatura.id, clase_id)
            
            if not profesores_disponibles:
                return {
                    'success': False, 
                    'message': f'No hay profesores asignados a la asignatura {asignatura.nombre}'
                }
            
            print(f"Profesores disponibles para {asignatura.nombre}: {[p.usuario.nombre for p in profesores_disponibles]}")
            
            # Si la asignatura prefiere bloques continuos, intentar asignar en bloques de 2
            if asignatura.bloques_continuos and horas_restantes >= 2:
                print(f"Intentando asignar bloque de 2 horas para {asignatura.nombre}")
                for _ in range(horas_restantes // 2):
                    if not asignar_bloque(
                        clase_id, asignatura, profesores_disponibles, 
                        horario_matriz, asignaciones, 2
                    ):
                        # Si no se puede asignar el bloque, intentar asignar horas individuales
                        for _ in range(2):
                            if asignaciones[asignatura.id] < horas_por_asignatura[asignatura.id]:
                                asignar_hora_individual(
                                    clase_id, asignatura, profesores_disponibles, 
                                    horario_matriz, asignaciones
                                )
            
            # Asignar las horas restantes individualmente
            horas_restantes = horas_por_asignatura[asignatura.id] - asignaciones[asignatura.id]
            print(f"Horas restantes para {asignatura.nombre}: {horas_restantes}")
            for _ in range(horas_restantes):
                if not asignar_hora_individual(
                    clase_id, asignatura, profesores_disponibles, 
                    horario_matriz, asignaciones
                ):
                    print(f"No se pudo asignar hora individual para {asignatura.nombre}")
        
        # Verificar si se asignaron todas las horas requeridas
        total_horas_requeridas = sum(horas_por_asignatura.values())
        total_horas_asignadas = sum(asignaciones.values())
        
        print(f"Total horas requeridas: {total_horas_requeridas}")
        print(f"Total horas asignadas: {total_horas_asignadas}")
        
        if total_horas_asignadas < total_horas_requeridas:
            return {
                'success': False, 
                'message': f'No se pudieron asignar todas las horas requeridas. Asignadas: {total_horas_asignadas}/{total_horas_requeridas}'
            }
        
        # Guardar el horario generado en la base de datos
        if not save_schedule_to_db(clase_id, horario_matriz):
            return {
                'success': False,
                'message': 'Error al guardar el horario en la base de datos'
            }
        
        # Verificar que el horario se guardó correctamente
        horario_guardado = Horario.query.filter_by(clase_id=clase_id).count()
        if horario_guardado == 0:
            return {
                'success': False,
                'message': 'El horario se generó pero no se guardó correctamente'
            }
        
        return {
            'success': True, 
            'message': f'Horario generado correctamente. Se guardaron {horario_guardado} asignaciones.'
        }
    
    except Exception as e:
        db.session.rollback()
        print(f"Error en generate_schedule: {str(e)}")
        return {'success': False, 'message': f'Error al generar el horario: {str(e)}'}

def hay_actividad_especial(dia, hora):
    """Verifica si hay una actividad especial programada para el día y hora especificados"""
    return ActividadEspecial.query.filter_by(dia=dia, hora=hora).first() is not None

def asignar_bloque(clase_id, asignatura, profesores, horario_matriz, asignaciones, tamano_bloque=2):
    """Intenta asignar un bloque continuo de horas para una asignatura"""
    for dia in DIAS:
        for hora_inicio in range(1, len(HORAS) - tamano_bloque + 2):
            # Verificar si el bloque está disponible
            bloque_disponible = True
            for i in range(tamano_bloque):
                hora_actual = hora_inicio + i
                # Verificar si hay actividad especial en alguna hora del bloque
                if hay_actividad_especial(dia, hora_actual) or horario_matriz[dia][hora_actual - 1] is not None:
                    bloque_disponible = False
                    break
            
            if not bloque_disponible:
                continue
            
            # Verificar que no hay bloques comunes en este horario
            hay_bloque_comun = False
            for i in range(tamano_bloque):
                hora_actual = hora_inicio + i
                hora_texto = HORAS_TEXTO[hora_actual]
                if DisponibilidadComun.get_by_dia_hora(dia, hora_texto) is not None:
                    hay_bloque_comun = True
                    break
            
            if hay_bloque_comun:
                continue
            
            # Verificar que no se exceda el máximo de horas diarias por asignatura
            horas_asignatura_dia = sum(
                1 for h in range(len(HORAS)) 
                if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['asignatura_id'] == asignatura.id
            )
            
            if horas_asignatura_dia + tamano_bloque > MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                # Ya se alcanzó el máximo para esta asignatura en este día
                continue
            
            # Encontrar un profesor disponible para todo el bloque
            for profesor in profesores:
                profesor_disponible = True
                
                # Verificar la disponibilidad del profesor para todo el bloque
                for i in range(tamano_bloque):
                    hora_actual = hora_inicio + i
                    hora_texto = HORAS_TEXTO[hora_actual]
                    
                    # Verificar disponibilidad personal del profesor
                    if not Disponibilidad.es_disponible(profesor.id, dia, hora_texto):
                        profesor_disponible = False
                        break
                    
                    # Verificar que el profesor no esté asignado a otra clase en este horario
                    if not profesor_disponible_globalmente(profesor.id, dia, hora_actual):
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
                        hora_actual = hora_inicio + i
                        horario_matriz[dia][hora_actual - 1] = {
                            'asignatura_id': asignatura.id,
                            'profesor_id': profesor.id
                        }
                        # Registrar la asignación global del profesor
                        registrar_asignacion_global(profesor.id, dia, hora_actual, clase_id)
                    
                    # Actualizar contador de horas asignadas
                    asignaciones[asignatura.id] += tamano_bloque
                    
                    return True
    
    # No se pudo asignar el bloque
    return False

def asignar_hora_individual(clase_id, asignatura, profesores, horario_matriz, asignaciones):
    """Intenta asignar una hora individual para una asignatura"""
    for dia in DIAS:
        for hora in HORAS:
            # Verificar si el espacio está disponible y no hay actividad especial
            if horario_matriz[dia][hora - 1] is not None or hay_actividad_especial(dia, hora):
                continue
            
            # Verificar que no hay bloques comunes en este horario
            hora_texto = HORAS_TEXTO[hora]
            if DisponibilidadComun.get_by_dia_hora(dia, hora_texto) is not None:
                continue
            
            # Verificar que no se exceda el máximo de horas diarias por asignatura
            horas_asignatura_dia = sum(
                1 for h in range(len(HORAS)) 
                if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['asignatura_id'] == asignatura.id
            )
            
            if horas_asignatura_dia >= MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                # Ya se alcanzó el máximo para esta asignatura en este día
                continue
            
            # Encontrar un profesor disponible
            for profesor in profesores:
                # Verificar la disponibilidad del profesor
                if not Disponibilidad.es_disponible(profesor.id, dia, hora_texto):
                    continue
                
                # Verificar que el profesor no esté asignado a otra clase en este horario
                if not profesor_disponible_globalmente(profesor.id, dia, hora):
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
                
                # Registrar la asignación global del profesor
                registrar_asignacion_global(profesor.id, dia, hora, clase_id)
                
                # Actualizar contador de horas asignadas
                asignaciones[asignatura.id] += 1
                
                return True
    
    # No se pudo asignar la hora
    return False

def save_schedule_to_db(clase_id, horario_matriz):
    """Guarda el horario generado en la base de datos"""
    try:
        print(f"Iniciando guardado de horario para clase {clase_id}")
        print(f"Matriz de horario recibida: {horario_matriz}")
        
        # Validar la estructura de la matriz
        if not isinstance(horario_matriz, dict):
            raise Exception("La matriz de horario debe ser un diccionario")
        
        for dia in DIAS:
            if dia not in horario_matriz:
                raise Exception(f"Falta el día {dia} en la matriz de horario")
            if not isinstance(horario_matriz[dia], list):
                raise Exception(f"El día {dia} debe ser una lista")
            if len(horario_matriz[dia]) != len(HORAS):
                raise Exception(f"El día {dia} debe tener {len(HORAS)} horas")
        
        # Primero eliminar cualquier horario existente para esta clase
        print(f"Eliminando horarios existentes para clase {clase_id}")
        Horario.query.filter_by(clase_id=clase_id).delete()
        db.session.commit()
        
        # Crear los nuevos registros de horario
        registros_creados = 0
        for dia in DIAS:
            for hora in HORAS:
                celda = horario_matriz[dia][hora - 1]  # Las horas son 1-indexadas
                
                # Verificar si hay actividad especial para este día y hora
                actividad_especial = ActividadEspecial.query.filter_by(dia=dia, hora=hora).first()
                
                if actividad_especial:
                    # Si hay actividad especial, crear un registro especial
                    print(f"Creando registro de actividad especial para {dia} hora {hora}: {actividad_especial.nombre}")
                    try:
                        horario = Horario(
                            clase_id=clase_id,
                            dia=dia,
                            hora=str(hora),
                            asignatura_id=None,  # No hay asignatura para actividades especiales
                            profesor_id=None,    # No hay profesor para actividades especiales
                            es_actividad_especial=True,
                            nombre_actividad_especial=actividad_especial.nombre,
                            color_actividad_especial=actividad_especial.color
                        )
                        db.session.add(horario)
                        registros_creados += 1
                    except Exception as e:
                        print(f"Error al crear registro de actividad especial para {dia} hora {hora}: {str(e)}")
                        raise
                elif celda is not None:
                    # Si no hay actividad especial y hay una asignatura asignada
                    print(f"Creando registro para {dia} hora {hora}: {celda}")
                    try:
                        # Validar la estructura de la celda
                        if not isinstance(celda, dict):
                            raise Exception(f"La celda debe ser un diccionario, se recibió: {type(celda)}")
                        if 'asignatura_id' not in celda:
                            raise Exception("Falta asignatura_id en la celda")
                        if 'profesor_id' not in celda:
                            raise Exception("Falta profesor_id en la celda")
                        
                        # Convertir IDs a enteros
                        asignatura_id = int(celda['asignatura_id'])
                        profesor_id = int(celda['profesor_id'])
                        
                        # Verificar que los IDs existen
                        if not Asignatura.query.get(asignatura_id):
                            raise Exception(f"Asignatura con ID {asignatura_id} no existe")
                        if not Profesor.query.get(profesor_id):
                            raise Exception(f"Profesor con ID {profesor_id} no existe")
                        
                        horario = Horario(
                            clase_id=clase_id,
                            dia=dia,
                            hora=str(hora),
                            asignatura_id=asignatura_id,
                            profesor_id=profesor_id,
                            es_actividad_especial=False
                        )
                        db.session.add(horario)
                        registros_creados += 1
                    except Exception as e:
                        print(f"Error al crear registro para {dia} hora {hora}: {str(e)}")
                        raise
        
        # Hacer commit de los cambios
        print(f"Intentando commit de {registros_creados} registros")
        db.session.commit()
        print(f"Horario guardado correctamente para la clase {clase_id}. Registros creados: {registros_creados}")
        
        # Verificar que los registros se guardaron
        registros_guardados = Horario.query.filter_by(clase_id=clase_id).count()
        print(f"Registros verificados en BD: {registros_guardados}")
        
        if registros_guardados != registros_creados:
            raise Exception(f"Discrepancia en número de registros. Creados: {registros_creados}, Guardados: {registros_guardados}")
        
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar el horario: {str(e)}")
        return False 