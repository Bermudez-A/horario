from datetime import datetime
from app.extensions import db

class ActividadEspecial(db.Model):
    """Modelo para actividades especiales fijas en el horario general"""
    __tablename__ = 'actividades_especiales'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    dia = db.Column(db.String(10), nullable=False)  # Lunes, Martes, etc.
    hora = db.Column(db.Integer, nullable=False)  # Hora del día (1-8)
    color = db.Column(db.String(20), default="#3498db")  # Color para visualización
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ActividadEspecial {self.nombre} - {self.dia} {self.hora}>'

    def to_dict(self):
        return {
            'id': self.id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'dia': self.dia,
            'hora': self.hora,
            'color': self.color,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_dia_hora(cls, dia, hora):
        """Obtiene una actividad especial por día y hora"""
        return cls.query.filter_by(dia=dia, hora=hora).first()
    
    @classmethod
    def get_all(cls):
        """Obtiene todas las actividades especiales"""
        return cls.query.all()
    
    @classmethod
    def get_all_as_dict(cls):
        """Obtiene todas las actividades como un diccionario"""
        actividades = {}
        for actividad in cls.get_all():
            key = f"{actividad.dia}_{actividad.hora}"
            actividades[key] = actividad.to_dict()
        return actividades
    
    @classmethod
    def crear_o_actualizar(cls, nombre, dia, hora, descripcion=None, color='#ff9800', icono='fa-star', es_fija=True):
        """Crea o actualiza una actividad especial"""
        actividad = cls.get_by_dia_hora(dia, hora)
        
        if actividad:
            # Actualizar actividad existente
            actividad.nombre = nombre
            actividad.descripcion = descripcion
            actividad.color = color
            actividad.icono = icono
            actividad.es_fija = es_fija
        else:
            # Crear nueva actividad
            actividad = cls(
                nombre=nombre,
                dia=dia,
                hora=hora,
                descripcion=descripcion,
                color=color,
                icono=icono,
                es_fija=es_fija
            )
            db.session.add(actividad)
        
        return actividad
    
    @classmethod
    def eliminar(cls, dia, hora):
        """Elimina una actividad especial"""
        actividad = cls.get_by_dia_hora(dia, hora)
        if actividad:
            db.session.delete(actividad)
            return True
        return False 