# Generador de Horarios

Aplicación web para la generación automática de horarios escolares. Diseñada para centros educativos que necesitan planificar eficientemente horarios de clases, profesores y aulas.

## Características Principales

- **Generación automática de horarios**: Algoritmo voraz que respeta restricciones de disponibilidad y preferencias.
- **Visualización intuitiva**: Interfaz visual para ver y editar horarios con código de colores.
- **Gestión de disponibilidad**: Los profesores pueden registrar sus horas disponibles e indisponibles.
- **Estadísticas detalladas**: Análisis de carga lectiva por asignaturas, profesores y clases.
- **Múltiples roles**: Administradores, profesores y alumnos con diferentes niveles de acceso.
- **Diseño modular**: Arquitectura escalable basada en blueprints de Flask.

## Tecnologías

- **Backend**: Python con Flask
- **Base de datos**: PostgreSQL
- **ORM**: SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5
- **Gráficos**: Chart.js
- **Iconos**: Font Awesome

## Requisitos

- Python 3.8+
- PostgreSQL 12+
- Dependencias listadas en `requirements.txt`

## Instalación

1. Clonar el repositorio:
   ```
   git clone https://github.com/tu-usuario/generador-horarios.git
   cd generador-horarios
   ```

2. Crear y activar un entorno virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   - Crear un archivo `.env` basado en el ejemplo
   - Configurar la conexión a PostgreSQL y la clave secreta

5. Inicializar la base de datos:
   ```
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. Crear usuario administrador inicial:
   ```
   flask shell
   >>> from app import db
   >>> from app.models.user import User
   >>> user = User(username="admin", email="admin@example.com", nombre="Admin", apellido="Usuario", rol="admin")
   >>> user.set_password("admin123")
   >>> db.session.add(user)
   >>> db.session.commit()
   >>> exit()
   ```

7. Ejecutar la aplicación:
   ```
   flask run
   ```

## Estructura del Proyecto

```
generador_horarios/
│
├── app/                         # Lógica principal
│   ├── __init__.py              # Inicializa Flask y blueprints
│   ├── config.py                # Configuración
│   │
│   ├── auth/                    # Módulo de autenticación
│   ├── admin/                   # Panel de administración
│   ├── schedules/               # Módulo de horarios
│   │   └── generator.py         # Algoritmo de generación
│   ├── stats/                   # Módulo de estadísticas
│   │
│   ├── models/                  # Modelos de BD
│   ├── templates/               # Plantillas HTML
│   └── static/                  # Archivos estáticos
│
├── migrations/                  # Migraciones de BD
├── venv/                        # Entorno virtual
├── .env                         # Variables de entorno
├── requirements.txt             # Dependencias
├── run.py                       # Punto de entrada
└── README.md                    # Esta documentación
```

## Algoritmo de Generación

El sistema utiliza un algoritmo voraz (greedy) para la generación de horarios que:

1. Prioriza asignaturas con mayor número de horas semanales
2. Respeta la disponibilidad de profesores
3. Intenta mantener bloques continuos para asignaturas que lo requieren
4. Balancea la carga diaria de cada profesor
5. Asegura que cada asignatura sea impartida por el mismo profesor en una clase

## Capturas de Pantalla

*(Aquí irían capturas de pantalla de la aplicación cuando estén disponibles)*

## Contribución

1. Hacer fork del repositorio
2. Crear una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Hacer commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Hacer push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear un Pull Request

## Licencia

Este proyecto está licenciado bajo [MIT License](LICENSE). 