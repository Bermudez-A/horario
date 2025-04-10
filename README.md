# Sistema de Gestión de Horarios Escolares

## Descripción
Sistema web para la gestión y generación automática de horarios escolares. Permite la administración de profesores, asignaturas, clases y la generación de horarios optimizados basados en las disponibilidades de los profesores.

## Características Principales
- Gestión completa de usuarios y permisos
- Administración de profesores y sus disponibilidades
- Gestión de asignaturas y clases
- Generación automática de horarios
- Gestión de actividades especiales y personalizadas
- Interfaz intuitiva y responsiva
- Exportación de horarios en diferentes formatos

## Requisitos del Sistema
- Python 3.8 o superior
- PostgreSQL 12 o superior
- Navegador web moderno (Chrome, Firefox, Edge, Safari)

## Instalación

### 1. Clonar el repositorio
```bash
git clone [URL_DEL_REPOSITORIO]
cd horario
```

### 2. Crear y activar entorno virtual
```bash
python -m venv venv
# En Windows
venv\Scripts\activate
# En Linux/Mac
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno
Crear un archivo `.env` en la raíz del proyecto con:
```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=tu_clave_secreta
DATABASE_URL=postgresql://usuario:contraseña@localhost:5432/nombre_bd
```

### 5. Inicializar la base de datos
```bash
flask db init
flask db migrate
flask db upgrade
```

### 6. Crear usuario administrador
```bash
flask create-admin
```

## Estructura del Proyecto
```
horario/
├── app/
│   ├── __init__.py
│   ├── admin/
│   │   ├── __init__.py
│   │   ├── routes.py
│   │   ├── forms.py
│   │   └── utils.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── profesor.py
│   │   ├── asignatura.py
│   │   ├── clase.py
│   │   ├── disponibilidad.py
│   │   ├── disponibilidad_comun.py
│   │   ├── actividad_especial.py
│   │   ├── actividad_personalizada.py
│   │   └── horario.py
│   ├── schedules/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── img/
│   └── templates/
│       ├── base.html
│       ├── admin/
│       │   ├── users.html
│       │   ├── user_form.html
│       │   ├── profesores.html
│       │   ├── profesor_form.html
│       │   ├── asignaturas.html
│       │   ├── asignatura_form.html
│       │   ├── clases.html
│       │   ├── clase_form.html
│       │   ├── horarios.html
│       │   ├── editar_horario.html
│       │   ├── disponibilidad_profesor.html
│       │   ├── asignar_profesores.html
│       │   ├── asignar_profesor_asignatura.html
│       │   └── seleccionar_clase.html
│       └── schedules/
│           ├── availability.html
│           └── actividades_personalizadas.html
├── venv/
├── requirements.txt
└── README.md

```

## Módulos Principales

### 1. Administración (app/admin/)
- Gestión de usuarios y permisos
- Administración de profesores
- Gestión de asignaturas
- Control de clases
- Configuración del sistema

### 2. Modelos (app/models/)
- User: Gestión de usuarios y autenticación
- Profesor: Información de profesores
- Asignatura: Detalles de asignaturas
- Clase: Configuración de clases
- Disponibilidad: Horarios de profesores
- Horario: Generación y gestión de horarios
- ActividadEspecial: Eventos especiales
- ActividadPersonalizada: Actividades personalizadas

### 3. Horarios (app/schedules/)
- Generación automática de horarios
- Gestión de disponibilidades
- Actividades especiales
- Personalización de actividades

## Uso del Sistema

### 1. Acceso al Sistema
- URL: http://localhost:5000
- Usuario administrador por defecto:
  - Email: admin@example.com
  - Contraseña: admin123

### 2. Gestión de Profesores
1. Ir a "Administración > Profesores"
2. Agregar nuevo profesor
3. Configurar disponibilidad
4. Asignar asignaturas

### 3. Generación de Horarios
1. Ir a "Horarios > Generar Horario"
2. Seleccionar clase
3. Configurar preferencias
4. Generar horario
5. Revisar y ajustar si es necesario

### 4. Actividades Especiales
1. Ir a "Horarios > Actividades Especiales"
2. Crear nueva actividad
3. Asignar a horarios específicos

## API Endpoints

### Autenticación
- POST /login
- POST /logout
- POST /register

### Profesores
- GET /admin/profesores
- POST /admin/profesores
- GET /admin/profesores/<id>
- PUT /admin/profesores/<id>
- DELETE /admin/profesores/<id>

### Horarios
- GET /schedules/horarios
- POST /schedules/generar
- GET /schedules/horarios/<id>
- PUT /schedules/horarios/<id>

## Desarrollo

### Estructura de Código
- Patrón MVC (Modelo-Vista-Controlador)
- Flask como framework web
- SQLAlchemy para ORM
- Bootstrap para interfaz
- JavaScript para interacciones

### Convenciones de Código
- PEP 8 para Python
- CamelCase para JavaScript
- snake_case para Python
- Comentarios en inglés

### Pruebas
```bash
# Ejecutar pruebas
flask test

# Cobertura de pruebas
coverage run -m pytest
coverage report
```

## Despliegue

### Producción
1. Configurar servidor web (Nginx/Apache)
2. Configurar WSGI (Gunicorn/uWSGI)
3. Configurar base de datos PostgreSQL
4. Configurar variables de entorno de producción
5. Configurar SSL/TLS

### Docker
```bash
# Construir imagen
docker build -t horario-app .

# Ejecutar contenedor
docker run -p 5000:5000 horario-app
```

## Contribución
1. Fork el repositorio
2. Crear rama de feature
3. Commit cambios
4. Push a la rama
5. Crear Pull Request

## Licencia
Este proyecto está bajo la licencia MIT. Ver el archivo LICENSE para más detalles.

## Contacto
- Email: contacto@example.com
- Sitio web: https://www.example.com
- Documentación: https://docs.example.com 