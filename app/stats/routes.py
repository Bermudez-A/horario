from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app import db
from app.stats import stats
from app.models.clase import Clase
from app.models.profesor import Profesor
from app.models.asignatura import Asignatura
from app.models.horario import Horario
from app.stats.charts import generate_carga_chart_data, generate_comparacion_chart_data
from sqlalchemy import func
import json

@stats.route('/')
@login_required
def index():
    return render_template('stats/index.html', title='Estadísticas')

@stats.route('/carga_asignaturas')
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

@stats.route('/comparacion_clases')
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

@stats.route('/carga_profesores')
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

@stats.route('/api/datos_profesor/<int:profesor_id>')
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