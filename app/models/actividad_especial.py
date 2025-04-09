from datetime import datetime
from app.extensions import db

class ActividadEspecial(db.Model):
    """Modelo para manejar actividades especiales en el horario"""
    __tablename__ = 'actividades_especiales'
    
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(255))
    dia = db.Column(db.String(15), nullable=False)  # lunes, martes, etc.
    hora = db.Column(db.Integer, nullable=False)  # 1-7 para las horas de clase
    color = db.Column(db.String(20), default='#3498db')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ActividadEspecial {self.nombre} - {self.dia} hora {self.hora}>'
    
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
        """Obtiene todas las actividades especiales como un diccionario organizado por día y hora"""
        actividades = cls.get_all()
        actividades_dict = {}
        
        for actividad in actividades:
            if actividad.dia not in actividades_dict:
                actividades_dict[actividad.dia] = {}
            
            actividades_dict[actividad.dia][actividad.hora] = {
                'id': actividad.id,
                'nombre': actividad.nombre,
                'descripcion': actividad.descripcion,
                'color': actividad.color
            }
        
        return actividades_dict
    
    @classmethod
    def crear_o_actualizar(cls, nombre, dia, hora, descripcion=None, color='#ff9800'):
        """Crea o actualiza una actividad especial"""
        actividad = cls.get_by_dia_hora(dia, hora)
        
        if actividad:
            # Actualizar actividad existente
            actividad.nombre = nombre
            actividad.descripcion = descripcion
            actividad.color = color
        else:
            # Crear nueva actividad
            actividad = cls(
                nombre=nombre,
                dia=dia,
                hora=hora,
                descripcion=descripcion,
                color=color
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