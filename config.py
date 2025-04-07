import os
from datetime import timedelta

class Config:
    # Configuración básica
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-very-secret'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///horario.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Configuración de JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # Configuración de Celery
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379/0'
    
    # Configuración de Redis
    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    
    # Configuración por defecto del horario
    HORARIO_DEFAULT = {
        "horas_por_dia": {
            "Lunes": ["08:00-09:00", "09:15-10:15", "10:30-11:30", "11:45-12:45",
                     "14:00-15:00", "15:15-16:15", "16:30-17:30"],
            "Martes": ["08:00-09:00", "09:15-10:15", "10:30-11:30", "11:45-12:45",
                      "14:00-15:00", "15:15-16:15", "16:30-17:30"],
            "Miércoles": ["08:00-09:00", "09:15-10:15", "10:30-11:30", "11:45-12:45",
                         "14:00-15:00", "15:15-16:15", "16:30-17:30"],
            "Jueves": ["08:00-09:00", "09:15-10:15", "10:30-11:30", "11:45-12:45",
                      "14:00-15:00", "15:15-16:15", "16:30-17:30"],
            "Viernes": ["08:00-09:00", "09:15-10:15", "10:30-11:30", "11:45-12:45",
                       "14:00-15:00", "15:15-16:15"]
        },
        "bloques_fijos": []
    } 