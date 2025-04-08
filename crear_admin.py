from app import create_app, db
from app.models.user import User

app = create_app()
with app.app_context():
    # Verificar si el usuario admin ya existe
    admin = User.query.filter_by(username='admin').first()

    if admin:
        # Si existe, actualizar su contraseña
        admin.rol = 'admin'
        admin.set_password('admin')
        print("Contraseña actualizada")
    else:
        # Si no existe, crear nuevo administrador
        admin = User(
            username='admin',
            email='admin@example.com',
            nombre='Administrador',
            apellido='Sistema',
            rol='admin'
        )
        admin.set_password('admin')
        admin.activo = True
        db.session.add(admin)
        print("Usuario creado")

    # Guardar cambios
    db.session.commit()
    print("Operación completada")