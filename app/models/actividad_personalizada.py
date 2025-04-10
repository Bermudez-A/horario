from app import db
from datetime import datetime

class ActividadPersonalizada(db.Model):
    __tablename__ = 'actividades_personalizadas'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(7), nullable=False)  # Hex color code
    icono = db.Column(db.String(50), nullable=True)  # Font Awesome icon class
    creado_por = db.Column(db.Integer, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<ActividadPersonalizada {self.nombre}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'color': self.color,
            'icono': self.icono,
            'creado_por': self.creado_por,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'activo': self.activo
        } 