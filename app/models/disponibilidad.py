from app.extensions import db
from datetime import datetime

class Disponibilidad(db.Model):
    """Modelo para registrar la disponibilidad de profesores en diferentes días y horas"""
    __tablename__ = 'disponibilidades'
    
    id = db.Column(db.Integer, primary_key=True)
    profesor_id = db.Column(db.Integer, db.ForeignKey('profesores.id', ondelete='CASCADE'), nullable=False)
    dia = db.Column(db.String(10), nullable=False)  # lunes, martes, etc.
    hora = db.Column(db.String(20), nullable=False)  # formato: "8:00 - 8:55"
    disponible = db.Column(db.Boolean, default=True)
    motivo = db.Column(db.String(255), default='')  # Motivo de la indisponibilidad
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    profesor = db.relationship('Profesor', backref=db.backref('disponibilidades', lazy='dynamic', cascade='all, delete-orphan'))
    
    __table_args__ = (
        db.UniqueConstraint('profesor_id', 'dia', 'hora', name='uq_disponibilidad_profesor_dia_hora'),
    )
    
    def __repr__(self):
        return f'<Disponibilidad: Profesor {self.profesor_id}, {self.dia} {self.hora}, Disponible: {self.disponible}>'
    
    @classmethod
    def es_disponible(cls, profesor_id, dia, hora):
        """Verifica si un profesor está disponible en un horario específico"""
        disp = cls.query.filter_by(profesor_id=profesor_id, dia=dia, hora=hora).first()
        return disp.disponible if disp else True  # Si no hay registro, se asume disponible
    
    @classmethod
    def set_disponible(cls, profesor_id, dia, hora, disponible=True, motivo=None):
        """Establece la disponibilidad de un profesor en un horario específico"""
        disp = cls.query.filter_by(profesor_id=profesor_id, dia=dia, hora=hora).first()
        
        if disp:
            disp.disponible = disponible
            disp.motivo = motivo
        else:
            disp = cls(profesor_id=profesor_id, dia=dia, hora=hora, disponible=disponible, motivo=motivo)
            db.session.add(disp)
        
        db.session.commit()
        return disp