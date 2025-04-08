from app.extensions import db
from datetime import datetime

class DisponibilidadComun(db.Model):
    """Modelo para manejar bloques de actividades comunes que afectan a todas las clases"""
    
    __tablename__ = 'disponibilidad_comun'
    
    id = db.Column(db.Integer, primary_key=True)
    dia = db.Column(db.String(15), nullable=False)
    hora = db.Column(db.String(10), nullable=False)
    titulo = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), default='#3498db')
    icono = db.Column(db.String(30), default='fa-coffee')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('dia', 'hora', name='uq_disponibilidad_comun_dia_hora'),
    )
    
    def __init__(self, dia, hora, titulo, color="#3498db", icono="fa-coffee"):
        self.dia = dia
        self.hora = hora
        self.titulo = titulo
        self.color = color
        self.icono = icono
    
    def to_dict(self):
        """Convierte el objeto a un diccionario"""
        return {
            'id': self.id,
            'dia': self.dia,
            'hora': self.hora,
            'titulo': self.titulo,
            'color': self.color,
            'icono': self.icono
        }
    
    @classmethod
    def get_by_dia_hora(cls, dia, hora):
        """Obtiene un bloque de disponibilidad por día y hora"""
        return cls.query.filter_by(dia=dia, hora=hora).first()
    
    @classmethod
    def get_all(cls):
        """Obtiene todos los bloques de disponibilidad común"""
        return cls.query.all()
    
    @classmethod
    def get_all_as_dict(cls):
        """Obtiene todos los bloques como un diccionario, donde la clave es 'dia_hora'"""
        bloques = {}
        for bloque in cls.get_all():
            key = f"{bloque.dia}_{bloque.hora}"
            bloques[key] = bloque.to_dict()
        return bloques
    
    @classmethod
    def crear_o_actualizar(cls, dia, hora, titulo, color='#3498db', icono='fa-coffee'):
        """Crea o actualiza un bloque de disponibilidad común"""
        bloque = cls.get_by_dia_hora(dia, hora)
        
        if bloque:
            # Actualizar bloque existente
            bloque.titulo = titulo
            bloque.color = color
            bloque.icono = icono
        else:
            # Crear nuevo bloque
            bloque = cls(
                dia=dia,
                hora=hora,
                titulo=titulo,
                color=color,
                icono=icono
            )
            db.session.add(bloque)
        
        return bloque
    
    @classmethod
    def eliminar(cls, dia, hora):
        """Elimina un bloque de disponibilidad común"""
        bloque = cls.get_by_dia_hora(dia, hora)
        if bloque:
            db.session.delete(bloque)
            return True
        return False 