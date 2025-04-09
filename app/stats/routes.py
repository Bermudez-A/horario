from flask import render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.stats import stats_bp
from app.models.clase import Clase
from app.models.profesor import Profesor
from app.models.asignatura import Asignatura
from app.models.horario import Horario
from app.models.user import User
from app.stats.charts import generate_carga_chart_data, generate_comparacion_chart_data
from sqlalchemy import func
import json
import random

@stats_bp.route('/')
@login_required
def index():
    """Vista principal de estadísticas"""
    
    # Obtener datos de asignaturas para el menú de selección
    asignaturas = Asignatura.query.filter_by(activa=True).all()
    
    # Contar elementos para métricas globales
    total_asignaturas = Asignatura.query.count()
    total_profesores = Profesor.query.count()
    total_clases = Clase.query.count()
    
    # Calcular porcentaje de avance global (simulado)
    porcentaje_avance = 65  # En un sistema real se calcularía desde la base de datos
    
    # Calcular porcentajes de finalización por asignatura
    asignaturas_progreso = []
    for asignatura in asignaturas:
        # En un sistema real, estos valores se calcularían desde la base de datos
        # basándose en clases impartidas, horas registradas, etc.
        horas_totales = asignatura.horas_semanales or 0
        # Simulación - aquí deberías implementar la lógica real para calcular las horas cursadas
        horas_cursadas = int(horas_totales * (random.randint(30, 90) / 100))  # Simulación: entre 30% y 90%
        porcentaje = int((horas_cursadas / horas_totales) * 100) if horas_totales > 0 else 0
        
        asignaturas_progreso.append({
            'nombre': asignatura.nombre,
            'id': asignatura.id,
            'horas_totales': horas_totales,
            'horas_cursadas': horas_cursadas,
            'porcentaje': porcentaje
        })
    
    return render_template('stats/index.html', 
                          title='Estadísticas',
                          asignaturas=asignaturas,
                          asignaturas_progreso=asignaturas_progreso,
                          total_asignaturas=total_asignaturas,
                          total_profesores=total_profesores,
                          total_clases=total_clases,
                          porcentaje_avance=porcentaje_avance)

@stats_bp.route('/carga_asignaturas')
@login_required
def carga_asignaturas():
    # Filtrar por rol
    if current_user.rol == 'profesor':
        profesor = Profesor.query.filter_by(usuario_id=current_user.id).first_or_404()
        asignaturas = db.session.query(
            Asignatura.nombre,
            func.count(Horario.id).label('horas')
        ).join(
            Horario, Horario.asignatura_id == Asignatura.id
        ).filter(
            Horario.profesor_id == profesor.id
        ).group_by(
            Asignatura.nombre
        ).all()
    else:
        asignaturas = db.session.query(
            Asignatura.nombre,
            func.count(Horario.id).label('horas')
        ).join(
            Horario, Horario.asignatura_id == Asignatura.id
        ).group_by(
            Asignatura.nombre
        ).all()

    # Generar datos para la gráfica
    chart_data = generate_carga_chart_data(asignaturas)
    
    return render_template('stats/carga_asignaturas.html', 
                          title='Carga de Asignaturas',
                          chart_data=json.dumps(chart_data))

@stats_bp.route('/comparacion_clases')
@login_required
def comparacion_clases():
    clases = Clase.query.filter_by(activa=True).all()
    
    # Obtener datos de horas por asignatura para cada clase
    data = {}
    asignaturas_set = set()
    
    for clase in clases:
        resultado = db.session.query(
            Asignatura.nombre,
            func.count(Horario.id).label('horas')
        ).join(
            Horario, Horario.asignatura_id == Asignatura.id
        ).filter(
            Horario.clase_id == clase.id
        ).group_by(
            Asignatura.nombre
        ).all()
        
        data[clase.nombre] = {asig.nombre: 0 for asig in Asignatura.query.all()}
        
        for asignatura, horas in resultado:
            data[clase.nombre][asignatura] = horas
            asignaturas_set.add(asignatura)
    
    # Convertir a formato adecuado para la gráfica
    chart_data = generate_comparacion_chart_data(data, list(asignaturas_set))
    
    return render_template('stats/comparacion_clases.html', 
                          title='Comparación entre Clases',
                          chart_data=json.dumps(chart_data))

@stats_bp.route('/carga_profesores')
@login_required
def carga_profesores():
    if current_user.rol == 'profesor' and not current_user.rol == 'admin':
        flash('No tienes permiso para ver esta página', 'warning')
        return redirect(url_for('stats.index'))
    
    profesores = db.session.query(
        Profesor.id,
        func.concat(User.nombre, ' ', User.apellido).label('nombre'),
        func.count(Horario.id).label('horas')
    ).join(
        User, User.id == Profesor.usuario_id
    ).join(
        Horario, Horario.profesor_id == Profesor.id
    ).group_by(
        Profesor.id, User.nombre, User.apellido
    ).all()
    
    # Preparar datos para la gráfica
    labels = [p.nombre for p in profesores]
    values = [p.horas for p in profesores]
    
    chart_data = {
        'labels': labels,
        'datasets': [{
            'label': 'Horas semanales',
            'backgroundColor': [
                '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', 
                '#1abc9c', '#d35400', '#34495e', '#7f8c8d', '#27ae60'
            ],
            'data': values
        }]
    }
    
    return render_template('stats/carga_profesores.html', 
                          title='Carga de Profesores',
                          chart_data=json.dumps(chart_data))

@stats_bp.route('/api/datos_profesor/<int:profesor_id>')
@login_required
def api_datos_profesor(profesor_id):
    # Verificar permisos
    if current_user.rol == 'profesor':
        profesor = Profesor.query.filter_by(usuario_id=current_user.id).first()
        if not profesor or profesor.id != profesor_id:
            return jsonify({'error': 'No tienes permiso para ver estos datos'}), 403
    
    # Obtener datos de carga por día
    carga_por_dia = db.session.query(
        Horario.dia,
        func.count(Horario.id).label('horas')
    ).filter(
        Horario.profesor_id == profesor_id
    ).group_by(
        Horario.dia
    ).all()
    
    dias = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes']
    horas_por_dia = {dia: 0 for dia in dias}
    
    for dia, horas in carga_por_dia:
        horas_por_dia[dia] = horas
    
    # Obtener datos de carga por asignatura
    carga_por_asignatura = db.session.query(
        Asignatura.nombre,
        func.count(Horario.id).label('horas')
    ).join(
        Horario, Horario.asignatura_id == Asignatura.id
    ).filter(
        Horario.profesor_id == profesor_id
    ).group_by(
        Asignatura.nombre
    ).all()
    
    return jsonify({
        'carga_por_dia': {
            'labels': dias,
            'values': [horas_por_dia[dia] for dia in dias]
        },
        'carga_por_asignatura': {
            'labels': [asig for asig, _ in carga_por_asignatura],
            'values': [horas for _, horas in carga_por_asignatura]
        }
    })

@stats_bp.route('/asignatura/<int:asignatura_id>')
@login_required
def asignatura(asignatura_id):
    asignatura = Asignatura.query.get_or_404(asignatura_id)
    
    # Datos para las estadísticas
    horas_totales = asignatura.horas_semanales or 0
    
    # Simulación - en un sistema real, estos datos se calcularían desde la base de datos
    horas_cursadas = int(horas_totales * 0.65)  # Supongamos que se ha cursado el 65%
    horas_restantes = horas_totales - horas_cursadas
    porcentaje_cursado = int((horas_cursadas / horas_totales) * 100) if horas_totales > 0 else 0
    
    # Obtener profesores que imparten esta asignatura
    profesores_data = []
    profesores_count = 0
    
    for ap in asignatura.profesores:
        if ap.profesor and ap.profesor.usuario:
            profesores_count += 1
            # En un sistema real, las horas serían datos reales
            horas_asignadas = 20  # Ejemplo
            profesores_data.append({
                'nombre': ap.profesor.get_nombre_completo(),
                'horas': horas_asignadas,
                'porcentaje': int((horas_asignadas / horas_totales) * 100) if horas_totales > 0 else 0
            })
    
    # Datos de distribución por día (simulados)
    dias_data = [
        {'nombre': 'Lunes', 'horas': 4, 'porcentaje': 20},
        {'nombre': 'Martes', 'horas': 6, 'porcentaje': 30},
        {'nombre': 'Miércoles', 'horas': 4, 'porcentaje': 20},
        {'nombre': 'Jueves', 'horas': 4, 'porcentaje': 20},
        {'nombre': 'Viernes', 'horas': 2, 'porcentaje': 10}
    ]
    
    # Número de grupos (simulado)
    grupos_count = 3
    
    return render_template('stats/asignatura.html',
                           asignatura=asignatura,
                           horas_cursadas=horas_cursadas,
                           horas_restantes=horas_restantes,
                           porcentaje_cursado=porcentaje_cursado,
                           profesores=profesores_data,
                           profesores_count=profesores_count,
                           dias=dias_data,
                           grupos_count=grupos_count)

@stats_bp.route('/progreso/<int:asignatura_id>')
@login_required
def progreso_asignatura(asignatura_id):
    """Vista para mostrar el progreso detallado de una asignatura"""
    
    # Obtener la asignatura
    asignatura = Asignatura.query.get_or_404(asignatura_id)
    
    # Obtener horas totales y calcular progreso
    horas_totales = asignatura.horas_semanales or 0
    
    # En un sistema real, estas horas cursadas se obtendrían de la base de datos
    # Aquí simulamos con datos de ejemplo
    horas_cursadas = int(horas_totales * 0.65)  # Simulación del 65% de avance
    horas_restantes = horas_totales - horas_cursadas
    
    # Calcular el porcentaje de avance
    porcentaje_cursado = int((horas_cursadas / horas_totales) * 100) if horas_totales > 0 else 0
    
    # Datos para la distribución por día
    dias_semana = [
        {'nombre': 'Lunes', 'horas_programadas': 2, 'horas_impartidas': 2},
        {'nombre': 'Martes', 'horas_programadas': 2, 'horas_impartidas': 2},
        {'nombre': 'Miércoles', 'horas_programadas': 1, 'horas_impartidas': 1},
        {'nombre': 'Jueves', 'horas_programadas': 2, 'horas_impartidas': 1},
        {'nombre': 'Viernes', 'horas_programadas': 1, 'horas_impartidas': 0}
    ]
    
    # Datos para el gráfico semanal (simulados para el ejemplo)
    # En un sistema real, estos datos se obtendrían de la base de datos
    datos_semanales = [
        {'semana': 'Semana 1', 'horas_programadas': 8, 'horas_realizadas': 8},
        {'semana': 'Semana 2', 'horas_programadas': 8, 'horas_realizadas': 8},
        {'semana': 'Semana 3', 'horas_programadas': 8, 'horas_realizadas': 7},
        {'semana': 'Semana 4', 'horas_programadas': 8, 'horas_realizadas': 8},
        {'semana': 'Semana 5', 'horas_programadas': 8, 'horas_realizadas': 6},
        {'semana': 'Semana 6', 'horas_programadas': 8, 'horas_realizadas': 4},
        {'semana': 'Semana 7', 'horas_programadas': 8, 'horas_realizadas': 0},
        {'semana': 'Semana 8', 'horas_programadas': 8, 'horas_realizadas': 0}
    ]
    
    return render_template('stats/progreso_asignatura.html',
                           asignatura=asignatura,
                           horas_cursadas=horas_cursadas,
                           horas_restantes=horas_restantes,
                           porcentaje_cursado=porcentaje_cursado,
                           dias_semana=dias_semana,
                           datos_semanales=datos_semanales)