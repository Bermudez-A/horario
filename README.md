# Sistema de Gestión de Horarios Escolares

Aplicación web desarrollada en Flask para la creación y gestión de horarios escolares, con funcionalidades avanzadas de visualización estadística y análisis de carga docente.

## Características principales

- Gestión de profesores, asignaturas y clases
- Generación y asignación de horarios
- Visualización de estadísticas y métricas
- Análisis de carga docente
- Exportación de datos a PDF y Excel

## Instalación y configuración

### Requisitos previos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)

### Instalación

1. Clona este repositorio:
   ```
   git clone <url-del-repositorio>
   cd horario
   ```

2. Crea un entorno virtual:
   ```
   # En Windows
   python -m venv venv
   venv\Scripts\activate

   # En macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Configura las variables de entorno:
   - Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:
     ```
     FLASK_APP=app.py
     FLASK_ENV=development
     SECRET_KEY=tu_clave_secreta_aqui
     ```

### Ejecución de la aplicación

1. Activa el entorno virtual (si no está activado):
   ```
   # En Windows
   venv\Scripts\activate

   # En macOS/Linux
   source venv/bin/activate
   ```

2. Inicia la aplicación:
   ```
   python app.py
   ```

3. Accede a la aplicación en tu navegador web:
   ```
   http://localhost:5000
   ```

## Estructura del proyecto

```
horario/
│
├── app/                # Paquete principal de la aplicación
│   ├── admin/          # Módulo para administración
│   ├── auth/           # Módulo para autenticación
│   ├── models/         # Modelos de la base de datos
│   ├── stats/          # Módulo para estadísticas
│   ├── static/         # Archivos estáticos (CSS, JS, imágenes)
│   └── templates/      # Plantillas HTML
│
├── migrations/         # Migraciones de la base de datos
├── venv/               # Entorno virtual (ignorado en git)
├── .env                # Variables de entorno (ignorado en git)
├── .gitignore          # Archivos y directorios ignorados por git
├── app.py              # Punto de entrada de la aplicación
└── requirements.txt    # Dependencias del proyecto
```

## Contribución

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un nuevo Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles. 