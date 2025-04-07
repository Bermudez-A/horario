# Sistema de Gestión de Horarios Escolares

Este es un sistema web desarrollado en Flask para la gestión de horarios escolares. Permite administrar profesores, asignaturas, clases y sus respectivos horarios.

## Características

- Gestión de profesores
- Gestión de asignaturas con horas semanales
- Gestión de clases
- Asignación de horarios
- Validación de conflictos de horarios
- Soporte para horarios fijos
- Interfaz web intuitiva y responsive

## Requisitos

- Python 3.8 o superior
- Flask
- SQLAlchemy
- Flask-Migrate

## Instalación

1. Clonar el repositorio:
```bash
git clone <url-del-repositorio>
cd horario
```

2. Crear un entorno virtual:
```bash
python -m venv venv
```

3. Activar el entorno virtual:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/Mac:
```bash
source venv/bin/activate
```

4. Instalar las dependencias:
```bash
pip install -r requirements.txt
```

5. Iniciar la aplicación:
```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## Uso

1. Primero, añade los profesores en la sección "Profesores"
2. Añade las asignaturas con sus horas semanales en "Asignaturas"
3. Crea las clases en la sección "Clases"
4. Finalmente, gestiona los horarios en la sección "Horarios"

## Estructura del Proyecto

```
horario/
├── app.py              # Aplicación principal
├── requirements.txt    # Dependencias
├── templates/          # Plantillas HTML
│   ├── base.html
│   ├── index.html
│   ├── profesores.html
│   ├── asignaturas.html
│   ├── clases.html
│   └── horarios.html
└── README.md
```

## Contribuir

Las contribuciones son bienvenidas. Por favor, abre un issue para discutir los cambios que te gustaría hacer.

## Licencia

Este proyecto está bajo la Licencia MIT. 