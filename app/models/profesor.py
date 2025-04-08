from app.extensions import db
from datetime import datetime

class Profesor(db.Model):
    __tablename__ = 'profesores'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    especialidad = db.Column(db.String(100))
    foto = db.Column(db.String(255))  # Ruta a la imagen
    bio = db.Column(db.Text)
    max_horas_diarias = db.Column(db.Integer, default=4)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    asignaturas = db.relationship('AsignaturaProfesor', back_populates='profesor', cascade='all, delete-orphan')
    horarios = db.relationship('Horario', back_populates='profesor', cascade='all, delete-orphan')
    # La relación para disponibilidades se define mediante el backref en el modelo Disponibilidad
    # No es necesario definirla aquí si ya existe un backref='disponibilidades' en Disponibilidad.profesor
    # disponibilidades = db.relationship(
    #     'Disponibilidad', # Corregido: Nombre de la clase en singular
    #     back_populates='profesor', 
    #     cascade='all, delete-orphan',
    #     lazy='dynamic'
    # )
    
    def __repr__(self):
        return f'<Profesor {self.id}>'
    
    def get_nombre_completo(self):
        return f"{self.usuario.nombre} {self.usuario.apellido}" if self.usuario else "Sin nombre"
    
    def get_carga_actual(self, dia=None):
        """Retorna la carga actual total o filtrada por día"""
        if dia:
            # Asume que el backref 'disponibilidades' existe y funciona
            # Si el backref no funciona, necesitaríamos ajustar cómo accedemos a los horarios
            # o descomentar y arreglar la relación directa aquí.
            # return sum(1 for h in self.horarios if h.dia == dia) # Esto cuenta horarios, no disponibilidades
            # Necesitamos una forma clara de contar carga desde la perspectiva del profesor
            # Por ahora, devolvemos la cuenta de horarios como antes
             return len(self.horarios.filter_by(dia=dia).all()) if hasattr(self.horarios, 'filter_by') else 0
        return len(self.horarios) # Longitud de la colección de horarios
    
    def get_asignaturas_ids(self):
        """Retorna una lista con los IDs de las asignaturas que imparte el profesor"""
        return [ap.asignatura_id for ap in self.asignaturas]
    
    def get_asignaturas_nombres(self):
        """Retorna una lista con los nombres de las asignaturas que imparte el profesor"""
        return [ap.asignatura.nombre for ap in self.asignaturas if ap.asignatura] # Añadir comprobación 