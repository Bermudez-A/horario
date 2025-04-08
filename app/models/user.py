from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    nombre = db.Column(db.String(100))
    apellido = db.Column(db.String(100))
    rol = db.Column(db.String(20), default='usuario')  # 'admin', 'profesor', 'alumno'
    activo = db.Column(db.Boolean, default=True)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultima_conexion = db.Column(db.DateTime)
    
    # Relaciones
    profesor = db.relationship('Profesor', backref='usuario', uselist=False, cascade='all, delete-orphan')
    
    def __init__(self, username, email, nombre=None, apellido=None, rol='usuario'):
        self.username = username
        self.email = email
        self.nombre = nombre
        self.apellido = apellido
        self.rol = rol
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<Usuario {self.username}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 