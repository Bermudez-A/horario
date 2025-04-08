from app import db
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
    disponibilidad = db.relationship('Disponibilidad', back_populates='profesor', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Profesor {self.id}>'
    
    def get_nombre_completo(self):
        return f"{self.usuario.nombre} {self.usuario.apellido}" if self.usuario else "Sin nombre"
    
    def get_carga_actual(self, dia=None):
        """Retorna la carga actual total o filtrada por día"""
        if dia:
            return sum(1 for h in self.horarios if h.dia == dia)
        return len(self.horarios) 