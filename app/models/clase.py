from app.extensions import db
from datetime import datetime

class ClaseAsignatura(db.Model):
    """Modelo para la relación entre clases y asignaturas"""
    __tablename__ = 'clases_asignaturas'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    horas_semanales = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    clase = db.relationship('Clase', backref=db.backref('asignaturas_rel', lazy=True))
    asignatura = db.relationship('Asignatura', backref=db.backref('clases_rel', lazy=True))
    
    def __repr__(self):
        return f'<ClaseAsignatura {self.clase_id}-{self.asignatura_id}>'

class Clase(db.Model):
    __tablename__ = 'clases'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False, unique=True)
    descripcion = db.Column(db.Text)
    nivel = db.Column(db.String(50))  # Primaria, Secundaria, etc.
    curso = db.Column(db.String(50))  # 1°, 2°, etc.
    color = db.Column(db.String(7), default='#2ecc71')
    activa = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    horarios = db.relationship('Horario', back_populates='clase', foreign_keys='[Horario.clase_id]', cascade='all, delete-orphan')
    asignaciones_profesor = db.relationship('AsignaturaProfesorClase', back_populates='clase', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Clase {self.nombre}>'
    
    def get_horario_completo(self):
        """Retorna un diccionario organizado del horario semanal"""
        horario = {
            'lunes': [None] * 7,
            'martes': [None] * 7,
            'miercoles': [None] * 7,
            'jueves': [None] * 7,
            'viernes': [None] * 7
        }
        
        for h in self.horarios:
            # Convertir hora a índice (hora viene como texto "1", "2", etc.)
            try:
                hora_idx = int(h.hora) - 1
                if h.es_actividad_especial:
                    horario[h.dia][hora_idx] = {
                        'id': h.id,
                        'asignatura': h.nombre_actividad_especial,
                        'profesor': None,
                        'color': h.color_actividad_especial,
                        'icono': None,
                        'asignatura_id': None,
                        'profesor_id': None,
                        'es_actividad_especial': True
                    }
                else:
                    horario[h.dia][hora_idx] = {
                        'id': h.id,
                        'asignatura': h.asignatura.nombre,
                        'profesor': h.profesor.get_nombre_completo() if h.profesor else None,
                        'color': h.asignatura.color,
                        'icono': h.asignatura.icono,
                        'asignatura_id': h.asignatura_id,
                        'profesor_id': h.profesor_id,
                        'es_actividad_especial': False
                    }
            except (ValueError, IndexError) as e:
                # Manejar errores de conversión o índices fuera de rango
                print(f"Error al procesar hora '{h.hora}' para día '{h.dia}': {str(e)}")
        
        return horario
    
    def get_profesor_asignado(self, asignatura_id):
        """Obtiene el profesor asignado a una asignatura específica para esta clase"""
        from app.models.asignatura import AsignaturaProfesorClase, AsignaturaProfesor
        
        asignacion = AsignaturaProfesorClase.query.join(AsignaturaProfesor).filter(
            AsignaturaProfesor.asignatura_id == asignatura_id,
            AsignaturaProfesorClase.clase_id == self.id
        ).first()
        
        if asignacion:
            return asignacion.asignatura_profesor.profesor
        return None 