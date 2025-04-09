from app.extensions import db
from datetime import datetime

class Horario(db.Model):
    """Modelo para los bloques de horario"""
    __tablename__ = 'horarios'
    
    id = db.Column(db.Integer, primary_key=True)
    clase_id = db.Column(db.Integer, db.ForeignKey('clases.id', ondelete='CASCADE'), nullable=False)
    dia = db.Column(db.String(15), nullable=False)  # lunes, martes, etc.
    hora = db.Column(db.String(15), nullable=False)  # formato: "8:00 - 8:55"
    asignatura_id = db.Column(db.Integer, db.ForeignKey('asignaturas.id'), nullable=False)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id'), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    clase = db.relationship('Clase', back_populates='horarios', foreign_keys=[clase_id])
    asignatura = db.relationship('Asignatura', back_populates='horarios')
    profesor = db.relationship('Profesor', back_populates='horarios')
    
    def __repr__(self):
        return f'<Horario: {self.clase.nombre}, {self.dia} {self.hora}, {self.asignatura.nombre}>'
    
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