from app import db
from datetime import datetime

# Tabla de asociación entre Asignaturas y Profesores
class AsignaturaProfesor(db.Model):
    __tablename__ = 'asignaturas_profesores'
    
    id = db.Column(db.Integer, primary_key=True)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id'), nullable=False)
    asignado_en = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    asignatura = db.relationship('Asignatura', back_populates='profesores')
    profesor = db.relationship('Profesor', back_populates='asignaturas')
    
    def __repr__(self):
        return f'<AsignaturaProfesor {self.asignatura_id}-{self.profesor_id}>'


class Asignatura(db.Model):
    __tablename__ = 'asignaturas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False, unique=True)
    codigo = db.Column(db.String(20), unique=True)
    horas_semanales = db.Column(db.Integer, default=1, nullable=False)
    bloques_continuos = db.Column(db.Boolean, default=False)  # Preferencia por bloques de 2 horas
    color = db.Column(db.String(7), default='#3498db')  # Color para visualización en el horario
    icono = db.Column(db.String(50))  # Nombre del icono (FontAwesome, etc.)
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    profesores = db.relationship('AsignaturaProfesor', back_populates='asignatura', cascade='all, delete-orphan')
    horarios = db.relationship('Horario', back_populates='asignatura', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Asignatura {self.nombre}>'
    
    def get_profesores_ids(self):
        """Retorna una lista con los IDs de los profesores asignados"""
        return [ap.profesor_id for ap in self.profesores]
    
    def get_profesores_nombres(self):
        """Retorna una lista con los nombres de los profesores asignados"""
        return [ap.profesor.get_nombre_completo() for ap in self.profesores] 