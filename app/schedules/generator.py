"""
Algoritmo Mejorado para Generación de Horarios Multiclase con Iteraciones Adicionales 
y Control sobre el Máximo de Horas que Pueden Dar los Profesores

Este módulo genera los horarios para todas las clases de un mismo nivel y curso, 
respetando las restricciones de asignación:
  • Asignación específica de profesores por clase, si está configurada.
  • Disponibilidad de profesores (personal y global) y actividades especiales.
  • (Opcional) Restricción del número máximo de horas diarias que puede impartir un profesor.
  
Se realizan múltiples iteraciones (configurables mediante max_iteraciones) para que cada clase 
obtenga un horario, y en caso de ser necesario se puede activar una fase forzada (force_assignment)
para asignar las horas pendientes, incluso ignorando el límite de horas diarias del profesor (si 
respect_profesor_max=False, esta restricción se ignora).
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

# Constantes de configuración
DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
HORAS = list(range(1, 8))  # Horas de 1 a 7
MAX_HORAS_DIARIAS_POR_ASIGNATURA = 2  # Restricción habitual para la asignación de horas por asignatura

# Mapeo de horas a texto (necesario para algunas validaciones)
HORAS_TEXTO = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7"}

# Estructura global para rastrear asignaciones de profesores
# Formato: {(profesor_id, dia, hora): clase_id}
asignaciones_globales = {}

def reset_asignaciones_globales():
    """Reinicia el registro global de asignaciones (incluyendo las de la base de datos)."""
    global asignaciones_globales
    asignaciones_globales = {}
    horarios_existentes = Horario.query.all()
    for h in horarios_existentes:
        try:
            hora_numerica = int(h.hora) if h.hora.isdigit() else 0
            asignaciones_globales[(h.profesor_id, h.dia, hora_numerica)] = h.clase_id
        except Exception as e:
            print(f"Error al cargar asignación existente: {str(e)}")

def profesor_disponible_globalmente(profesor_id, dia, hora):
    """Verifica que el profesor no esté asignado en otro turno (misma hora y día)."""
    return (profesor_id, dia, hora) not in asignaciones_globales

def registrar_asignacion_global(profesor_id, dia, hora, clase_id):
    """Registra la asignación global de un profesor para un turno dado."""
    asignaciones_globales[(profesor_id, dia, hora)] = clase_id

def get_profesores_by_asignatura(asignatura_id, clase_id=None):
    """
    Obtiene la lista de profesores asociados a una asignatura.
    Si se especifica clase_id, primero se consulta si existe una asignación específica 
    (en AsignaturaProfesorClase) para esa clase y se retorna ese profesor (único).
    """
    if clase_id is not None:
        try:
            profesor_asignado = AsignaturaProfesorClase.obtener_profesor_para_asignatura_clase(asignatura_id, clase_id)
            if profesor_asignado and profesor_asignado.usuario.activo:
                return [profesor_asignado]
        except Exception as e:
            print(f"Error al buscar profesor específico para clase {clase_id}: {str(e)}")
    asignaciones = AsignaturaProfesor.query.filter_by(asignatura_id=asignatura_id).all()
    profesores = [asig.profesor for asig in asignaciones if asig.profesor.usuario.activo]
    return profesores

def hay_actividad_especial(dia, hora):
    """Determina si existe una actividad especial programada en el día y hora indicados."""
    return ActividadEspecial.query.filter_by(dia=dia, hora=hora).first() is not None

def asignar_bloque(clase_id, asignatura, profesores, horario_matriz, asignaciones, tamano_bloque=2, force=False, respect_profesor_max=False):
    """
    Intenta asignar un bloque continuo (por defecto 2 horas) para una asignatura,
    respetando la disponibilidad, actividades especiales y el límite de horas diarias 
    de la asignatura (salvo que force sea True).
    
    El parámetro respect_profesor_max permite habilitar o no la verificación de que 
    un profesor no supere su máximo de horas diarias.
    """
    for dia in DIAS:
        for hora_inicio in range(1, len(HORAS) - tamano_bloque + 2):
            # Verificar que todo el bloque esté libre y sin actividades especiales
            bloque_disponible = True
            for i in range(tamano_bloque):
                hora_actual = hora_inicio + i
                if hay_actividad_especial(dia, hora_actual) or horario_matriz[dia][hora_actual - 1] is not None:
                    bloque_disponible = False
                    break
            if not bloque_disponible:
                continue

            # Evitar el bloque si hay asignación en disponibilidad común
            hay_bloque_comun = False
            for i in range(tamano_bloque):
                hora_actual = hora_inicio + i
                if DisponibilidadComun.get_by_dia_hora(dia, HORAS_TEXTO[hora_actual]) is not None:
                    hay_bloque_comun = True
                    break
            if hay_bloque_comun:
                continue

            # Verificar el límite diario para la asignatura (se puede omitir en modo forzado)
            if not force:
                horas_asignatura_dia = sum(
                    1 for h in range(len(HORAS))
                    if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['asignatura_id'] == asignatura.id
                )
                if horas_asignatura_dia + tamano_bloque > MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                    continue

            # Buscar un profesor disponible para todo el bloque
            for profesor in profesores:
                profesor_disponible = True
                for i in range(tamano_bloque):
                    hora_actual = hora_inicio + i
                    if not Disponibilidad.es_disponible(profesor.id, dia, HORAS_TEXTO[hora_actual]):
                        profesor_disponible = False
                        break
                    if not profesor_disponible_globalmente(profesor.id, dia, hora_actual):
                        profesor_disponible = False
                        break
                # Verificar que el profesor no supere su máximo de horas diarias (si se respeta la restricción)
                horas_asignadas_prof = sum(
                    1 for h in range(len(HORAS))
                    if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['profesor_id'] == profesor.id
                )
                if respect_profesor_max and (horas_asignadas_prof + tamano_bloque > profesor.max_horas_diarias):
                    profesor_disponible = False

                if profesor_disponible:
                    for i in range(tamano_bloque):
                        hora_actual = hora_inicio + i
                        horario_matriz[dia][hora_actual - 1] = {
                            'asignatura_id': asignatura.id,
                            'profesor_id': profesor.id
                        }
                        registrar_asignacion_global(profesor.id, dia, hora_actual, clase_id)
                    asignaciones[asignatura.id] += tamano_bloque
                    return True
    return False

def asignar_hora_individual(clase_id, asignatura, profesores, horario_matriz, asignaciones, force=False, respect_profesor_max=False):
    """
    Intenta asignar una hora individual para una asignatura, verificando que la celda esté libre,
    sin actividad especial y que se cumplan las restricciones de disponibilidad y límite diario.
    
    El parámetro respect_profesor_max permite omitir la restricción de máximo de horas por profesor.
    """
    for dia in DIAS:
        for hora in HORAS:
            if horario_matriz[dia][hora - 1] is not None or hay_actividad_especial(dia, hora):
                continue
            if DisponibilidadComun.get_by_dia_hora(dia, HORAS_TEXTO[hora]) is not None:
                continue
            if not force:
                horas_asignatura_dia = sum(
                    1 for h in range(len(HORAS))
                    if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['asignatura_id'] == asignatura.id
                )
                if horas_asignatura_dia >= MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                    continue
            for profesor in profesores:
                if not Disponibilidad.es_disponible(profesor.id, dia, HORAS_TEXTO[hora]):
                    continue
                if not profesor_disponible_globalmente(profesor.id, dia, hora):
                    continue
                horas_profesor = sum(
                    1 for h in HORAS
                    if horario_matriz[dia][h-1] is not None and
                    horario_matriz[dia][h-1]['profesor_id'] == profesor.id
                )
                if respect_profesor_max and (horas_profesor >= profesor.max_horas_diarias):
                    continue
                horario_matriz[dia][hora-1] = {
                    'asignatura_id': asignatura.id,
                    'profesor_id': profesor.id
                }
                registrar_asignacion_global(profesor.id, dia, hora, clase_id)
                asignaciones[asignatura.id] += 1
                return True
    return False

def save_schedule_to_db(clase_id, horario_matriz):
    """
    Guarda en la base de datos la matriz de horario generada, incluyendo las actividades especiales.
    Se eliminan previamente los horarios existentes para la clase.
    """
    try:
        print(f"Iniciando guardado de horario para clase {clase_id}")
        if not isinstance(horario_matriz, dict):
            raise Exception("La matriz de horario debe ser un diccionario")
        for dia in DIAS:
            if dia not in horario_matriz:
                raise Exception(f"Falta el día {dia} en la matriz de horario")
            if not isinstance(horario_matriz[dia], list):
                raise Exception(f"El día {dia} debe ser una lista")
            if len(horario_matriz[dia]) != len(HORAS):
                raise Exception(f"El día {dia} debe tener {len(HORAS)} horas")
        print(f"Eliminando horarios existentes para clase {clase_id}")
        Horario.query.filter_by(clase_id=clase_id).delete()
        db.session.commit()
        registros_creados = 0
        for dia in DIAS:
            for hora in HORAS:
                celda = horario_matriz[dia][hora - 1]
                actividad_especial = ActividadEspecial.query.filter_by(dia=dia, hora=hora).first()
                if actividad_especial:
                    print(f"Creando registro de actividad especial para {dia} hora {hora}: {actividad_especial.nombre}")
                    try:
                        horario = Horario(
                            clase_id=clase_id,
                            dia=dia,
                            hora=str(hora),
                            asignatura_id=None,
                            profesor_id=None,
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
                    print(f"Creando registro para {dia} hora {hora}: {celda}")
                    try:
                        if not isinstance(celda, dict):
                            raise Exception(f"La celda debe ser un diccionario, se recibió: {type(celda)}")
                        if 'asignatura_id' not in celda:
                            raise Exception("Falta asignatura_id en la celda")
                        if 'profesor_id' not in celda:
                            raise Exception("Falta profesor_id en la celda")
                        asignatura_id = int(celda['asignatura_id'])
                        profesor_id = int(celda['profesor_id'])
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
        print(f"Intentando commit de {registros_creados} registros")
        db.session.commit()
        registros_guardados = Horario.query.filter_by(clase_id=clase_id).count()
        print(f"Horario guardado correctamente para la clase {clase_id}. Registros creados: {registros_creados} - Verificados: {registros_guardados}")
        if registros_guardados != registros_creados:
            raise Exception(f"Discrepancia en número de registros. Creados: {registros_creados}, Guardados: {registros_guardados}")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error al guardar el horario: {str(e)}")
        return False

def generate_schedule(clase_id, reset_global=True, max_iteraciones=100, force_assignment=False, respect_profesor_max=False):
    """
    Genera el horario para una clase específica intentando cumplir con todas las horas semanales 
    requeridas por cada asignatura.

    Parámetros:
      - reset_global: reinicia las asignaciones globales (True para la primera clase del grupo).
      - max_iteraciones: número máximo de iteraciones en la fase normal.
      - force_assignment: activa la fase forzada para asignar horas pendientes, ignorando (en parte)
        la restricción diaria para la asignatura.
      - respect_profesor_max: si True (por defecto) se respeta el límite de horas diarias del profesor.
      
    Retorna un diccionario con 'success' y 'message'.
    """
    try:
        clase = Clase.query.get(clase_id)
        if not clase:
            return {'success': False, 'message': 'La clase no existe'}
        print(f"Generando horario para la clase {clase.nombre}")

        asignaturas = Asignatura.query.filter_by(activa=True).all()
        if not asignaturas:
            return {'success': False, 'message': 'No hay asignaturas disponibles'}

        # Diccionarios para las horas requeridas y asignadas
        horas_requeridas = {a.id: a.horas_semanales for a in asignaturas}
        horas_asignadas = {a.id: 0 for a in asignaturas}

        if reset_global:
            reset_asignaciones_globales()

        # Inicializar matriz de horario: cada día con una lista de tamaño len(HORAS)
        horario_matriz = {dia: [None] * len(HORAS) for dia in DIAS}

        iteracion = 0
        intentos_sin_progreso = 0
        while iteracion < max_iteraciones:
            iteracion += 1
            progreso = False
            # Ordenar asignaturas por horas pendientes (de mayor a menor)
            asignaturas_ordenadas = sorted(asignaturas, key=lambda a: horas_requeridas[a.id] - horas_asignadas[a.id], reverse=True)
            for asignatura in asignaturas_ordenadas:
                restantes = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
                if restantes <= 0:
                    continue
                profesores_disponibles = get_profesores_by_asignatura(asignatura.id, clase_id)
                if not profesores_disponibles:
                    continue

                # Intentar asignación en bloque (si se requieren 2 o más horas)
                if restantes >= 2:
                    dias_aleatorios = random.sample(DIAS, len(DIAS))
                    for dia in dias_aleatorios:
                        horas_en_dia = sum(1 for celda in horario_matriz[dia]
                                           if celda is not None and celda['asignatura_id'] == asignatura.id)
                        if horas_en_dia + 2 > MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                            continue
                        if asignar_bloque(clase_id, asignatura, profesores_disponibles, horario_matriz, horas_asignadas, tamano_bloque=2, force=False, respect_profesor_max=respect_profesor_max):
                            progreso = True
                            break
                # Asignación individual
                restantes = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
                if restantes > 0:
                    dias_aleatorios = random.sample(DIAS, len(DIAS))
                    for dia in dias_aleatorios:
                        horas_en_dia = sum(1 for celda in horario_matriz[dia]
                                           if celda is not None and celda['asignatura_id'] == asignatura.id)
                        if horas_en_dia >= MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                            continue
                        horas_aleatorias = random.sample(HORAS, len(HORAS))
                        for hora in horas_aleatorias:
                            if horario_matriz[dia][hora-1] is not None or hay_actividad_especial(dia, hora):
                                continue
                            if asignar_hora_individual(clase_id, asignatura, profesores_disponibles, horario_matriz, horas_asignadas, force=False, respect_profesor_max=respect_profesor_max):
                                progreso = True
                                break
                        if horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id] <= 0:
                            break
            if progreso:
                intentos_sin_progreso = 0
            else:
                intentos_sin_progreso += 1
            if intentos_sin_progreso >= 10:
                print(f"No hubo progreso en 10 iteraciones consecutivas (iteración {iteracion}).")
                break

        # Verificar si se asignaron todas las horas requeridas
        if not all(horas_asignadas[a.id] >= horas_requeridas[a.id] for a in asignaturas):
            print("Fase normal: No se asignaron todas las horas requeridas.")
            for a in asignaturas:
                faltante = horas_requeridas[a.id] - horas_asignadas[a.id]
                if faltante > 0:
                    print(f" - Asignatura {a.nombre} (ID {a.id}): faltan {faltante} horas")
            if force_assignment:
                print("Iniciando fase forzada (relajando límite de asignatura)...")
                for asignatura in asignaturas:
                    restantes = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
                    if restantes <= 0:
                        continue
                    profesores_disponibles = get_profesores_by_asignatura(asignatura.id, clase_id)
                    if not profesores_disponibles:
                        continue
                    while restantes > 0:
                        asignado = False
                        for dia in DIAS:
                            for hora in HORAS:
                                if horario_matriz[dia][hora-1] is None and not hay_actividad_especial(dia, hora):
                                    for profesor in profesores_disponibles:
                                        if not Disponibilidad.es_disponible(profesor.id, dia, HORAS_TEXTO[hora]):
                                            continue
                                        if not profesor_disponible_globalmente(profesor.id, dia, hora):
                                            continue
                                        horas_profesor = sum(1 for h in HORAS
                                                              if horario_matriz[dia][h-1] is not None and
                                                              horario_matriz[dia][h-1]['profesor_id'] == profesor.id)
                                        if respect_profesor_max and (horas_profesor >= profesor.max_horas_diarias):
                                            continue
                                        # Asignar sin validar el límite diario de asignatura
                                        horario_matriz[dia][hora-1] = {
                                            'asignatura_id': asignatura.id,
                                            'profesor_id': profesor.id
                                        }
                                        registrar_asignacion_global(profesor.id, dia, hora, clase_id)
                                        horas_asignadas[asignatura.id] += 1
                                        asignado = True
                                        break
                                    if asignado:
                                        break
                            if asignado:
                                break
                        if not asignado:
                            print(f"No se pudo forzar la asignación para la asignatura {asignatura.nombre} (faltan {restantes} horas).")
                            break
                        restantes = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
            if not all(horas_asignadas[a.id] >= horas_requeridas[a.id] for a in asignaturas):
                return {'success': False, 'message': 'No se pudo asignar todas las horas requeridas para todas las asignaturas.'}

        if not save_schedule_to_db(clase_id, horario_matriz):
            print("Error al guardar el horario en la base de datos.")
            return {'success': False, 'message': 'Error al guardar el horario en la base de datos.'}

        print(f"Horario generado y guardado correctamente para la clase {clase.nombre}.")
        return {'success': True, 'message': 'Horario generado correctamente.'}

    except Exception as e:
        db.session.rollback()
        print(f"Error en generate_schedule para la clase {clase.nombre if clase else ''}: {str(e)}")
        return {'success': False, 'message': f'Error al generar el horario: {str(e)}'}

def generate_schedules_for_group(nivel, curso, force_assignment=False, max_iteraciones=100, respect_profesor_max=False):
    """
    Genera los horarios para todas las clases activas de un mismo nivel y curso, 
    utilizando un único reset global para evitar conflictos en la asignación de profesores.
    
    Parámetros adicionales:
      - force_assignment: activa la fase forzada en generate_schedule.
      - max_iteraciones: número máximo de iteraciones que se intentarán en cada clase.
      - respect_profesor_max: habilita o no la restricción de las horas máximas que puede impartir un profesor.
    """
    resultados = {}
    clases = Clase.query.filter_by(nivel=nivel, curso=curso, activa=True).all()
    if not clases:
        return {'success': False, 'message': 'No hay clases activas para el nivel y curso indicados.'}
    reset_asignaciones_globales()
    for clase in clases:
        print(f"Generando horario para la clase {clase.nombre}...")
        resultado = generate_schedule(clase.id, reset_global=False, max_iteraciones=max_iteraciones, force_assignment=force_assignment, respect_profesor_max=respect_profesor_max)
        resultados[clase.id] = resultado
    return resultados
