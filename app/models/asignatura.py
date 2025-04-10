from app.extensions import db
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
    clase_asignaciones = db.relationship('AsignaturaProfesorClase', back_populates='asignatura_profesor')
    
    def __repr__(self):
        return f'<AsignaturaProfesor {self.asignatura_id}-{self.profesor_id}>'


# Tabla para asignar un profesor específico a una asignatura para una clase específica
class AsignaturaProfesorClase(db.Model):
    __tablename__ = 'asignaturas_profesores_clases'
    
    id = db.Column(db.Integer, primary_key=True)
    asignatura_profesor_id = db.Column(db.Integer, db.ForeignKey('asignaturas_profesores.id'), nullable=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    asignatura_profesor = db.relationship('AsignaturaProfesor', back_populates='clase_asignaciones')
    clase = db.relationship('Clase', back_populates='asignaciones_profesor')
    
    # Índices y restricciones
    __table_args__ = (
        db.UniqueConstraint('asignatura_profesor_id', 'clase_id', name='uix_asignatura_profesor_clase'),
    )
    
    def __repr__(self):
        return f'<AsignaturaProfesorClase {self.asignatura_profesor_id}-{self.clase_id}>'
    
    @classmethod
    def obtener_profesor_para_asignatura_clase(cls, asignatura_id, clase_id):
        """Obtiene el profesor asignado a una asignatura específica para una clase específica"""
        asignacion = cls.query.join(AsignaturaProfesor).filter(
            AsignaturaProfesor.asignatura_id == asignatura_id,
            cls.clase_id == clase_id
        ).first()
        
        if asignacion:
            return asignacion.asignatura_profesor.profesor
        return None


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
    
    def get_profesor_para_clase(self, clase_id):
        """Obtiene el profesor asignado a esta asignatura para una clase específica"""
        return AsignaturaProfesorClase.obtener_profesor_para_asignatura_clase(self.id, clase_id) 