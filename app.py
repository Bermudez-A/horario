from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, time
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'tu_clave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///horarios.db'
db = SQLAlchemy(app)

# Modelos
class Profesor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    horarios = db.relationship('Horario', backref='profesor', lazy=True)

class Asignatura(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    horas_semanales = db.Column(db.Integer, nullable=False)
    horarios = db.relationship('Horario', backref='asignatura', lazy=True)

class Clase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    horarios = db.relationship('Horario', backref='clase', lazy=True)

class Horario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesor.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignatura.id'), nullable=False)
    clase_id = db.Column(db.Integer, db.ForeignKey('clase.id'), nullable=False)
    dia_semana = db.Column(db.String(10), nullable=False)  # Lunes, Martes, etc.
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    es_fijo = db.Column(db.Boolean, default=False)  # Para horarios que no se pueden mover

# Rutas
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/profesores', methods=['GET', 'POST'])
def profesores():
    if request.method == 'POST':
        nombre = request.form['nombre']
        profesor = Profesor(nombre=nombre)
        db.session.add(profesor)
        db.session.commit()
        flash('Profesor añadido exitosamente')
        return redirect(url_for('profesores'))
    profesores = Profesor.query.all()
    return render_template('profesores.html', profesores=profesores)

@app.route('/asignaturas', methods=['GET', 'POST'])
def asignaturas():
    if request.method == 'POST':
        nombre = request.form['nombre']
        horas = int(request.form['horas_semanales'])
        asignatura = Asignatura(nombre=nombre, horas_semanales=horas)
        db.session.add(asignatura)
        db.session.commit()
        flash('Asignatura añadida exitosamente')
        return redirect(url_for('asignaturas'))
    asignaturas = Asignatura.query.all()
    return render_template('asignaturas.html', asignaturas=asignaturas)

@app.route('/clases', methods=['GET', 'POST'])
def clases():
    if request.method == 'POST':
        nombre = request.form['nombre']
        clase = Clase(nombre=nombre)
        db.session.add(clase)
        db.session.commit()
        flash('Clase añadida exitosamente')
        return redirect(url_for('clases'))
    clases = Clase.query.all()
    return render_template('clases.html', clases=clases)

@app.route('/horarios', methods=['GET', 'POST'])
def horarios():
    if request.method == 'POST':
        profesor_id = int(request.form['profesor_id'])
        asignatura_id = int(request.form['asignatura_id'])
        clase_id = int(request.form['clase_id'])
        dia_semana = request.form['dia_semana']
        hora_inicio = datetime.strptime(request.form['hora_inicio'], '%H:%M').time()
        hora_fin = datetime.strptime(request.form['hora_fin'], '%H:%M').time()
        es_fijo = 'es_fijo' in request.form

        # Verificar conflictos de horario
        conflicto = Horario.query.filter_by(
            profesor_id=profesor_id,
            dia_semana=dia_semana
        ).filter(
            ((Horario.hora_inicio <= hora_inicio) & (Horario.hora_fin > hora_inicio)) |
            ((Horario.hora_inicio < hora_fin) & (Horario.hora_fin >= hora_fin))
        ).first()

        if conflicto:
            flash('Conflicto de horario detectado')
            return redirect(url_for('horarios'))

        horario = Horario(
            profesor_id=profesor_id,
            asignatura_id=asignatura_id,
            clase_id=clase_id,
            dia_semana=dia_semana,
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            es_fijo=es_fijo
        )
        db.session.add(horario)
        db.session.commit()
        flash('Horario añadido exitosamente')
        return redirect(url_for('horarios'))

    profesores = Profesor.query.all()
    asignaturas = Asignatura.query.all()
    clases = Clase.query.all()
    horarios = Horario.query.all()
    return render_template('horarios.html', 
                         profesores=profesores,
                         asignaturas=asignaturas,
                         clases=clases,
                         horarios=horarios)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 