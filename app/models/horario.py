from app import db
from datetime import datetime

class Horario(db.Model):
    __tablename__ = 'horarios'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id'), nullable=False)
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id'), nullable=False)
    dia = db.Column(db.String(10), nullable=False)  # lunes, martes, miércoles, jueves, viernes
    hora = db.Column(db.Integer, nullable=False)  # 1-7
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    modificado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    
    # Relaciones
    clase = db.relationship('Clase', back_populates='horarios')
    asignatura = db.relationship('Asignatura', back_populates='horarios')
    profesor = db.relationship('Profesor', back_populates='horarios')
    
    __table_args__ = (
        db.UniqueConstraint('clase_id', 'dia', 'hora', name='uq_horario_clase_dia_hora'),
    )
    
    def __repr__(self):
        return f'<Horario {self.clase.nombre} - {self.dia} - Hora {self.hora}>'
    
    @classmethod
    def get_by_clase_dia_hora(cls, clase_id, dia, hora):
        return cls.query.filter_by(clase_id=clase_id, dia=dia, hora=hora).first()
    
    @classmethod
    def get_by_profesor_dia(cls, profesor_id, dia):
        return cls.query.filter_by(profesor_id=profesor_id, dia=dia).all()
    
    @classmethod
    def verificar_disponibilidad(cls, clase_id, dia, hora):
        """Verifica si una clase tiene disponible un horario específico"""
        return cls.query.filter_by(clase_id=clase_id, dia=dia, hora=hora).first() is None 