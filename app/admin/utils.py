import os
import secrets
from PIL import Image
from flask import current_app, flash, redirect, url_for
from flask_login import current_user
from functools import wraps

def admin_required(f):
    """Decorador que verifica si el usuario es administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.rol == 'admin':
            flash('Se requieren permisos de administrador para acceder a esta página', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def save_picture(form_picture, subfolder=''):
    """Guarda una imagen subida y devuelve el nombre de archivo"""
    # Generar un nombre aleatorio para el archivo
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    
    # Crear la ruta para guardar la imagen
    uploads_folder = os.path.join(current_app.root_path, 'static', 'uploads')
    if subfolder:
        uploads_folder = os.path.join(uploads_folder, subfolder)
    
    # Asegurarse de que la carpeta exista
    os.makedirs(uploads_folder, exist_ok=True)
    
    picture_path = os.path.join(uploads_folder, picture_fn)
    
    # Redimensionar y guardar la imagen
    output_size = (300, 300)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)
    
    # Devolver la ruta relativa para guardarla en la BD
    relative_path = os.path.join('uploads', subfolder, picture_fn) if subfolder else os.path.join('uploads', picture_fn)
    return relative_path 