from app import db
from datetime import datetime

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
    horarios = db.relationship('Horario', back_populates='clase', cascade='all, delete-orphan')
    
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
            horario[h.dia][h.hora - 1] = {
                'id': h.id,
                'asignatura': h.asignatura.nombre,
                'profesor': h.profesor.get_nombre_completo() if h.profesor else None,
                'color': h.asignatura.color,
                'icono': h.asignatura.icono
            }
        
        return horario 