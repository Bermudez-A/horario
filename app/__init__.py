import os
import sys
from flask import Flask, request
from dotenv import load_dotenv
from app.extensions import db, migrate, login_manager, babel

# Cargar variables de entorno
load_dotenv()

def get_locale():
    return request.accept_languages.best_match(['es', 'en'])

def create_app():
    app = Flask(__name__)
    
    # Configuración
    app.config.from_object('app.config.Config')
    
    # Asegurar que Flask use UTF-8
    app.config['JSON_AS_ASCII'] = False
    
    # Inicializar extensiones con la app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # Inicializar Babel para internacionalización
    babel.init_app(app, locale_selector=get_locale)
    
    # Registrar blueprints
    from app.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    from app.schedules import schedules as schedules_blueprint
    app.register_blueprint(schedules_blueprint, url_prefix='/schedules')
    
    from app.stats import stats_bp as stats_blueprint
    app.register_blueprint(stats_blueprint, url_prefix='/stats')
    
    # Ruta principal
    from flask import render_template
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app 