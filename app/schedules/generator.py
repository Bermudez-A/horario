"""
Algoritmo de Generación de Horarios Multiclase con Diagnóstico y Marcado de Errores

Este módulo genera el horario para cada una de las clases de un mismo nivel y curso,
respetando las restricciones de:
  • Asignación específica de profesores por clase (si se configura).
  • Disponibilidad (individual y global) y actividades especiales.
  • Límite de horas diarias por asignatura y, opcionalmente, el máximo de horas que
    puede impartir un profesor (controlado con RESPECT_PROFESOR_MAX).

Si no se logra asignar todas las horas requeridas para una asignatura, se marca en la
celda correspondiente el error "Falta profesor disponible", permitiendo generar el horario
completo y conocer el problema.
"""

### VARIABLES DE CONFIGURACIÓN (editar aquí)
DIAS = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
HORAS = list(range(1, 8))                # Horas de 1 a 7
MAX_HORAS_DIARIAS_POR_ASIGNATURA = 2       # Máximo de horas que se pueden asignar de una asignatura por día
MAX_ITERACIONES = 100                    # Iteraciones internas en la generación normal de horario
MAX_RETRIES = 5                          # Reintentos por clase si falla la generación
RESPECT_PROFESOR_MAX = True              # Si se debe respetar el límite de horas diarias de un profesor
### FIN DE VARIABLES DE CONFIGURACIÓN

from app import db
from app.models.clase import Clase
from app.models.horario import Horario
from app.models.profesor import Profesor
from app.models.asignatura import Asignatura, AsignaturaProfesor, AsignaturaProfesorClase
from app.models.disponibilidad import Disponibilidad
from app.models.disponibilidad_comun import DisponibilidadComun
from app.models.actividad_especial import ActividadEspecial
import random

# Mapeo de horas a texto (usando la configuración de HORAS)
HORAS_TEXTO = {h: str(h) for h in HORAS}

# Registro global de asignaciones: {(profesor_id, dia, hora): clase_id}
asignaciones_globales = {}

def reset_asignaciones_globales():
    """Reinicia el registro global usando los horarios ya guardados en la base de datos."""
    global asignaciones_globales
    asignaciones_globales = {}
    horarios_existentes = Horario.query.all()
    for h in horarios_existentes:
        try:
            hora_numerica = int(h.hora) if h.hora.isdigit() else 0
            asignaciones_globales[(h.profesor_id, h.dia, hora_numerica)] = h.clase_id
        except Exception as e:
            print(f"Error al cargar asignación existente: {str(e)}")

def remove_class_assignments(clase_id):
    """Elimina del registro global las asignaciones pertenecientes a la clase indicada."""
    global asignaciones_globales
    keys_to_remove = [key for key, value in asignaciones_globales.items() if value == clase_id]
    for key in keys_to_remove:
        del asignaciones_globales[key]

def profesor_disponible_globalmente(profesor_id, dia, hora):
    """Retorna True si el profesor no tiene asignado otro turno (misma hora y día)."""
    return (profesor_id, dia, hora) not in asignaciones_globales

def registrar_asignacion_global(profesor_id, dia, hora, clase_id):
    """Registra en el registro global la asignación de un profesor para el turno (dia, hora) de la clase."""
    asignaciones_globales[(profesor_id, dia, hora)] = clase_id

def get_profesores_by_asignatura(asignatura_id, clase_id=None):
    """
    Devuelve la lista de profesores asociados a la asignatura.
    Si se especifica clase_id, primero se consulta si existe asignación específica en
    AsignaturaProfesorClase para esa clase y se retorna ese profesor si existe.
    Solo retorna profesores activos y disponibles.
    """
    if clase_id is not None:
        try:
            profesor_asignado = AsignaturaProfesorClase.obtener_profesor_para_asignatura_clase(asignatura_id, clase_id)
            if profesor_asignado and profesor_asignado.usuario.activo:
                return [profesor_asignado]
        except Exception as e:
            print(f"Error al buscar profesor específico para clase {clase_id}: {str(e)}")
    
    asignaciones = AsignaturaProfesor.query.filter_by(asignatura_id=asignatura_id).all()
    profesores = []
    for asig in asignaciones:
        if asig.profesor.usuario.activo:
            # Verificar que el profesor tenga disponibilidad configurada para todas las horas
            disponibilidad_completa = True
            for dia in DIAS:
                for hora in HORAS:
                    if not Disponibilidad.es_disponible(asig.profesor.id, dia, HORAS_TEXTO[hora]):
                        disponibilidad_completa = False
                        break
                if not disponibilidad_completa:
                    break
            if disponibilidad_completa:
                profesores.append(asig.profesor)
    
    return profesores

def hay_actividad_especial(dia, hora):
    """Retorna True si en el turno (dia, hora) hay una actividad especial programada."""
    return ActividadEspecial.query.filter_by(dia=dia, hora=hora).first() is not None

def asignar_bloque(clase_id, asignatura, profesores, horario_matriz, asignaciones, tamano_bloque=2, force=False, respect_profesor_max=RESPECT_PROFESOR_MAX):
    """
    Intenta asignar un bloque continuo (por defecto de 2 horas) para la asignatura,
    verificando disponibilidad, actividad especial y restricciones.
    Si 'force' es True, se omite la restricción del límite de horas por asignatura.
    """
    for dia in DIAS:
        for hora_inicio in range(1, len(HORAS) - tamano_bloque + 2):
            # Verifica que el bloque completo esté libre y sin actividad especial
            bloque_disponible = True
            for i in range(tamano_bloque):
                hora_actual = hora_inicio + i
                if hay_actividad_especial(dia, hora_actual) or horario_matriz[dia][hora_actual - 1] is not None:
                    bloque_disponible = False
                    break
            if not bloque_disponible:
                continue

            # Descartar el bloque si hay asignación en disponibilidad común
            hay_bloque_comun = False
            for i in range(tamano_bloque):
                hora_actual = hora_inicio + i
                if DisponibilidadComun.get_by_dia_hora(dia, HORAS_TEXTO[hora_actual]) is not None:
                    hay_bloque_comun = True
                    break
            if hay_bloque_comun:
                continue

            # Validar límite diario para la asignatura (salvo modo forzado)
            if not force:
                horas_asignatura_dia = sum(1 for h in range(len(HORAS))
                                           if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['asignatura_id'] == asignatura.id)
                if horas_asignatura_dia + tamano_bloque > MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                    continue

            # Buscar un profesor que cumpla las condiciones para el bloque
            for profesor in profesores:
                profesor_disponible = True
                for i in range(tamano_bloque):
                    hora_actual = hora_inicio + i
                    # Verificar disponibilidad del profesor en cada hora del bloque
                    if not Disponibilidad.es_disponible(profesor.id, dia, HORAS_TEXTO[hora_actual]):
                        profesor_disponible = False
                        break
                    if not profesor_disponible_globalmente(profesor.id, dia, hora_actual):
                        profesor_disponible = False
                        break
                horas_asignadas_prof = sum(1 for h in range(len(HORAS))
                                           if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['profesor_id'] == profesor.id)
                if respect_profesor_max and (horas_asignadas_prof + tamano_bloque > profesor.max_horas_diarias):
                    profesor_disponible = False

                if profesor_disponible:
                    for i in range(tamano_bloque):
                        hora_actual = hora_inicio + i
                        horario_matriz[dia][hora_actual - 1] = {'asignatura_id': asignatura.id, 'profesor_id': profesor.id}
                        registrar_asignacion_global(profesor.id, dia, hora_actual, clase_id)
                    asignaciones[asignatura.id] += tamano_bloque
                    return True
    return False

def asignar_hora_individual(clase_id, asignatura, profesores, horario_matriz, asignaciones, force=False, respect_profesor_max=RESPECT_PROFESOR_MAX):
    """
    Intenta asignar una hora individual para la asignatura comprobando que la celda esté libre,
    sin actividad especial y cumpliendo las restricciones (salvo modo forzado).
    """
    for dia in DIAS:
        for hora in HORAS:
            if horario_matriz[dia][hora - 1] is not None or hay_actividad_especial(dia, hora):
                continue
            if DisponibilidadComun.get_by_dia_hora(dia, HORAS_TEXTO[hora]) is not None:
                continue
            if not force:
                horas_asignatura_dia = sum(1 for h in range(len(HORAS))
                                           if horario_matriz[dia][h] is not None and horario_matriz[dia][h]['asignatura_id'] == asignatura.id)
                if horas_asignatura_dia >= MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                    continue
            for profesor in profesores:
                # Verificar disponibilidad del profesor en la hora específica
                if not Disponibilidad.es_disponible(profesor.id, dia, HORAS_TEXTO[hora]):
                    continue
                if not profesor_disponible_globalmente(profesor.id, dia, hora):
                    continue
                horas_profesor = sum(1 for h in HORAS
                                     if horario_matriz[dia][h-1] is not None and
                                     horario_matriz[dia][h-1]['profesor_id'] == profesor.id)
                if respect_profesor_max and (horas_profesor >= profesor.max_horas_diarias):
                    continue
                horario_matriz[dia][hora-1] = {'asignatura_id': asignatura.id, 'profesor_id': profesor.id}
                registrar_asignacion_global(profesor.id, dia, hora, clase_id)
                asignaciones[asignatura.id] += 1
                return True
    return False

def diagnosticar_fallo(asignaturas, horas_requeridas, horas_asignadas, clase_id, horario_matriz):
    """
    Recorre las asignaturas con horas pendientes y, para cada celda libre (que no sea actividad especial),
    evalúa las condiciones de cada profesor disponible para construir un diagnóstico detallado.
    """
    diagnostico = ""
    for asignatura in asignaturas:
        faltan = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
        if faltan > 0:
            diagnostico += f"Asignatura '{asignatura.nombre}' (ID {asignatura.id}): faltan {faltan} horas.\n"
            diagnostico += "  Turnos libres:\n"
            for dia in DIAS:
                for idx, celda in enumerate(horario_matriz[dia]):
                    hora = idx + 1
                    if celda is None and not hay_actividad_especial(dia, hora):
                        profesores_disp = get_profesores_by_asignatura(asignatura.id, clase_id)
                        condiciones_turno = []
                        for profesor in profesores_disp:
                            conds = []
                            # Verificar disponibilidad del profesor
                            if not Disponibilidad.es_disponible(profesor.id, dia, HORAS_TEXTO[hora]):
                                conds.append("No disponible (personal)")
                            if not profesor_disponible_globalmente(profesor.id, dia, hora):
                                conds.append("Ya asignado en otro turno")
                            horas_prof = sum(1 for h in HORAS if horario_matriz[dia][h-1] is not None and
                                             horario_matriz[dia][h-1]['profesor_id'] == profesor.id)
                            if RESPECT_PROFESOR_MAX and horas_prof >= profesor.max_horas_diarias:
                                conds.append("Ha alcanzado máximo")
                            if conds:
                                condiciones_turno.append(f"Profesor {profesor.id}: " + ", ".join(conds))
                            else:
                                condiciones_turno.append(f"Profesor {profesor.id}: DISPONIBLE")
                        if condiciones_turno:
                            diagnostico += f"    {dia} hora {hora}: " + "; ".join(condiciones_turno) + "\n"
                        else:
                            diagnostico += f"    {dia} hora {hora}: Ningún profesor disponible.\n"
            diagnostico += "\n"
    return diagnostico

def completar_celdas_error(asignaturas, horas_requeridas, horas_asignadas, clase_id, horario_matriz):
    """
    Para cada asignatura que aún tiene horas pendientes, recorre la matriz de horario y en cada celda libre (que no sea actividad especial)
    asigna un marcador de error indicando que falta profesor.
    """
    for asignatura in asignaturas:
        pendientes = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
        if pendientes > 0:
            for dia in DIAS:
                for idx, celda in enumerate(horario_matriz[dia]):
                    if pendientes <= 0:
                        break
                    if celda is None and not hay_actividad_especial(dia, idx+1):
                        # Se asigna el error; se marca la celda con un diccionario que incluye el error.
                        horario_matriz[dia][idx] = {'asignatura_id': asignatura.id, 'error': 'Falta profesor disponible'}
                        pendientes -= 1
                        # Se considera que esa hora ya fue "asignada" (como error)
                        horas_asignadas[asignatura.id] += 1
    return

def save_schedule_to_db(clase_id, horario_matriz):
    """
    Guarda en la base de datos la matriz de horario generada, incluyendo registros con error (si no hay profesor).
    Se eliminan previamente los registros existentes para la clase.
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
                    # Si la celda tiene clave 'error', se asigna profesor_id = None y se usa el mensaje de error.
                    if isinstance(celda, dict) and 'error' in celda:
                        print(f"Creando registro de error para {dia} hora {hora}: {celda}")
                        try:
                            horario = Horario(
                                clase_id=clase_id,
                                dia=dia,
                                hora=str(hora),
                                asignatura_id=int(celda['asignatura_id']),
                                profesor_id=None,
                                es_actividad_especial=False,
                                nombre_actividad_especial=celda['error']
                            )
                            db.session.add(horario)
                            registros_creados += 1
                        except Exception as e:
                            print(f"Error al crear registro de error para {dia} hora {hora}: {str(e)}")
                            raise
                    else:
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

def generate_schedule(clase_id, reset_global=True, max_iteraciones=MAX_ITERACIONES, force_assignment=False, respect_profesor_max=RESPECT_PROFESOR_MAX):
    """
    Genera el horario para una clase específica intentando asignar todas las horas semanales requeridas.
    
    Parámetros:
      - reset_global: reinicia las asignaciones globales (True para la primera clase del grupo).
      - max_iteraciones: número máximo de iteraciones en la fase normal.
      - force_assignment: activa la fase forzada para asignar horas pendientes.
      - respect_profesor_max: si True, se respeta el límite de horas diarias del profesor.
    
    Retorna un diccionario con 'success' y 'message'. Si falla, incluye en 'diagnostico'
    información detallada de los turnos sin profesor.
    """
    try:
        clase = Clase.query.get(clase_id)
        if not clase:
            return {'success': False, 'message': 'La clase no existe'}
        print(f"Generando horario para la clase {clase.nombre}")

        asignaturas = Asignatura.query.filter_by(activa=True).all()
        if not asignaturas:
            return {'success': False, 'message': 'No hay asignaturas disponibles'}

        # Inicializa diccionarios de horas requeridas y asignadas (por cada asignatura)
        horas_requeridas = {a.id: a.horas_semanales for a in asignaturas}
        horas_asignadas = {a.id: 0 for a in asignaturas}

        if reset_global:
            reset_asignaciones_globales()

        # Matriz de horario: una lista de celdas por cada día
        horario_matriz = {dia: [None] * len(HORAS) for dia in DIAS}

        iteracion = 0
        intentos_sin_progreso = 0
        while iteracion < max_iteraciones:
            iteracion += 1
            progreso = False
            # Ordena asignaturas por horas pendientes (de mayor a menor)
            asignaturas_ordenadas = sorted(asignaturas, key=lambda a: horas_requeridas[a.id] - horas_asignadas[a.id], reverse=True)
            for asignatura in asignaturas_ordenadas:
                restantes = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
                if restantes <= 0:
                    continue
                profesores_disponibles = get_profesores_by_asignatura(asignatura.id, clase_id)
                if not profesores_disponibles:
                    continue

                # Asignación en bloque si se requieren 2 o más horas
                if restantes >= 2:
                    dias_aleatorios = random.sample(DIAS, len(DIAS))
                    for dia in dias_aleatorios:
                        horas_en_dia = sum(1 for celda in horario_matriz[dia] if celda is not None and celda.get('asignatura_id') == asignatura.id)
                        if horas_en_dia + 2 > MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                            continue
                        if asignar_bloque(clase_id, asignatura, profesores_disponibles, horario_matriz, horas_asignadas,
                                          tamano_bloque=2, force=False, respect_profesor_max=respect_profesor_max):
                            progreso = True
                            break
                # Asignación individual
                restantes = horas_requeridas[asignatura.id] - horas_asignadas[asignatura.id]
                if restantes > 0:
                    dias_aleatorios = random.sample(DIAS, len(DIAS))
                    for dia in dias_aleatorios:
                        horas_en_dia = sum(1 for celda in horario_matriz[dia] if celda is not None and celda.get('asignatura_id') == asignatura.id)
                        if horas_en_dia >= MAX_HORAS_DIARIAS_POR_ASIGNATURA:
                            continue
                        horas_aleatorias = random.sample(HORAS, len(HORAS))
                        for hora in horas_aleatorias:
                            if horario_matriz[dia][hora-1] is not None or hay_actividad_especial(dia, hora):
                                continue
                            if asignar_hora_individual(clase_id, asignatura, profesores_disponibles, horario_matriz, horas_asignadas,
                                                       force=False, respect_profesor_max=respect_profesor_max):
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

        # Si quedan horas sin asignar, se completa llenando las celdas libres con un marcador de error.
        if not all(horas_asignadas[a.id] >= horas_requeridas[a.id] for a in asignaturas):
            print("Fase normal: No se asignaron todas las horas requeridas.")
            for a in asignaturas:
                faltan = horas_requeridas[a.id] - horas_asignadas[a.id]
                if faltan > 0:
                    print(f" - Asignatura {a.nombre} (ID {a.id}): faltan {faltan} horas")
            # Completar las celdas libres con un marcador de error
            completar_celdas_error(asignaturas, horas_requeridas, horas_asignadas, clase_id, horario_matriz)
            # Tras esto, se considerarán todas las horas asignadas (aunque con error)
        
        if not save_schedule_to_db(clase_id, horario_matriz):
            print("Error al guardar el horario en la base de datos.")
            return {'success': False, 'message': 'Error al guardar el horario en la base de datos.'}

        print(f"Horario generado y guardado correctamente para la clase {clase.nombre}.")
        return {'success': True, 'message': 'Horario generado correctamente.'}

    except Exception as e:
        db.session.rollback()
        print(f"Error en generate_schedule para la clase {clase.nombre if clase else ''}: {str(e)}")
        return {'success': False, 'message': f'Error al generar el horario: {str(e)}'}

def generate_schedules_for_group(nivel, curso, force_assignment=False, max_iteraciones=MAX_ITERACIONES, respect_profesor_max=RESPECT_PROFESOR_MAX, max_retries=MAX_RETRIES):
    """
    Genera los horarios para todas las clases activas de un mismo nivel y curso.
    Se realiza un reset global y, para cada clase, si la generación falla se reintenta (hasta max_retries)
    eliminando las asignaciones previas de esa clase.
    """
    resultados = {}
    clases = Clase.query.filter_by(nivel=nivel, curso=curso, activa=True).all()
    if not clases:
        return {'success': False, 'message': 'No hay clases activas para el nivel y curso indicados.'}
    reset_asignaciones_globales()
    for clase in clases:
        print(f"Generando horario para la clase {clase.nombre}...")
        success = False
        attempt = 0
        result = None
        while not success and attempt < max_retries:
            print(f" - Intento {attempt + 1} para la clase {clase.nombre}")
            result = generate_schedule(clase.id, reset_global=False, max_iteraciones=max_iteraciones,
                                       force_assignment=force_assignment, respect_profesor_max=respect_profesor_max)
            if result['success']:
                success = True
            else:
                print(f" -- Fallo en intento {attempt + 1} para la clase {clase.nombre}: {result['message']}")
                if 'diagnostico' in result:
                    print(" -- Diagnóstico:\n" + result['diagnostico'])
                remove_class_assignments(clase.id)
                attempt += 1
        if not success:
            resultados[clase.id] = {'success': False, 'message': f'No se pudo generar el horario para {clase.nombre} tras {max_retries} intentos.'}
        else:
            resultados[clase.id] = result
    return resultados
