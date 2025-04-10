import os
from flask import Flask, render_template
from dotenv import load_dotenv
from app.extensions import db, migrate, login_manager, babel

# Cargar variables de entorno
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuración
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/horarios')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Inicializar extensiones
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    babel.init_app(app)
    
    # Importar modelos
    from .models import (
        User, Profesor, Asignatura, Clase, ClaseAsignatura,
        Horario, Disponibilidad, ActividadEspecial
    )
    
    # Registrar blueprints
    from app.auth import auth as auth_bp
    from app.admin import admin as admin_bp
    from app.schedules import schedules as schedules_bp
    from app.stats import stats_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(schedules_bp, url_prefix='/schedules')
    app.register_blueprint(stats_bp, url_prefix='/stats')
    
    # Configurar login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Ruta principal
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/developers')
    def developers():
        return render_template('developers.html')
    
    return app 