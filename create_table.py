from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Eliminar la restricción de clave foránea si existe
    db.session.execute(text("ALTER TABLE actividades_personalizadas DROP CONSTRAINT IF EXISTS actividades_personalizadas_creado_por_fkey;"))
    
    # Crear la tabla users primero
    sql_users = text("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(128) NOT NULL,
        rol VARCHAR(20) NOT NULL DEFAULT 'usuario',
        activo BOOLEAN DEFAULT TRUE,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    # Luego crear la tabla actividades_personalizadas
    sql_actividades = text("""
    CREATE TABLE IF NOT EXISTS actividades_personalizadas (
        id SERIAL PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        color VARCHAR(7) NOT NULL,
        icono VARCHAR(50),
        creado_por INTEGER NOT NULL,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        activo BOOLEAN DEFAULT TRUE
    );
    """)
    
    try:
        # Crear tabla users
        db.session.execute(sql_users)
        print("Tabla users creada correctamente.")
        
        # Crear tabla actividades_personalizadas
        db.session.execute(sql_actividades)
        print("Tabla actividades_personalizadas creada correctamente.")
        
        db.session.commit()
    except Exception as e:
        print(f"Error al crear las tablas: {str(e)}")
        db.session.rollback() 