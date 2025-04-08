from app.extensions import db
from datetime import datetime

class Excepcion(db.Model):
    __tablename__ = 'excepciones'
    
    id = db.Column(db.Integer, primary_key=True)
    horario_id = db.Column(db.Integer, db.ForeignKey('horarios.id'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # 'festivo', 'ausencia', 'cambio'
    motivo = db.Column(db.String(255))
    profesor_suplente_id = db.Column(db.Integer, db.ForeignKey('profesores.id'))
    creado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Excepcion {self.id} - {self.tipo} - {self.fecha}>'
    
    @classmethod
    def get_by_fecha(cls, fecha):
        """Obtiene todas las excepciones para una fecha específica"""
        return cls.query.filter_by(fecha=fecha).all()
    
    @classmethod
    def get_by_horario(cls, horario_id):
        """Obtiene todas las excepciones para un horario específico"""
        return cls.query.filter_by(horario_id=horario_id).all() 