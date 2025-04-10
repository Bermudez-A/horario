# Sistema de Gestión de Horarios Escolares

Aplicación web desarrollada en Flask para la creación y gestión de horarios escolares, con funcionalidades avanzadas de visualización estadística y análisis de carga docente.

## Características principales

- Gestión completa de profesores, asignaturas y clases
- Generación automática de horarios mediante algoritmos voraces
- Interfaz visual para edición manual de horarios con drag & drop
- Sistema de gestión de disponibilidad de profesores
- Panel de estadísticas avanzado con:
  - Análisis de carga docente
  - Comparativa entre secciones y grupos
  - Seguimiento del progreso curricular
  - Visualización de métricas en tiempo real
- Exportación de datos a PDF y Excel
- Interfaz moderna y responsiva con:
  - Animaciones suaves y efectos visuales
  - Diseño adaptable a dispositivos móviles
  - Temas claros y oscuros
  - Efectos de glassmorphism
- Sistema de notificaciones en tiempo real
- Gestión de usuarios y roles (admin/profesor)

## Instalación y configuración

### Requisitos previos

- Python 3.9 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno con soporte para JavaScript ES6+

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
│   ├── static/         # Archivos estáticos
│   │   ├── css/        # Estilos CSS
│   │   │   ├── style.css
│   │   │   └── animations.css
│   │   └── js/         # Scripts JavaScript
│   │       ├── main.js
│   │       └── animations.js
│   └── templates/      # Plantillas HTML
│
├── migrations/         # Migraciones de la base de datos
├── venv/               # Entorno virtual (ignorado en git)
├── .env                # Variables de entorno (ignorado en git)
├── .gitignore          # Archivos y directorios ignorados por git
├── app.py              # Punto de entrada de la aplicación
└── requirements.txt    # Dependencias del proyecto
```

## Características técnicas

- **Frontend:**
  - Bootstrap 5.3 para la interfaz de usuario
  - Chart.js para visualización de datos
  - Animaciones CSS personalizadas
  - Efectos de glassmorphism
  - Diseño responsivo y adaptable

- **Backend:**
  - Flask como framework web
  - SQLAlchemy para ORM
  - Sistema de autenticación y autorización
  - API RESTful para interacciones

- **Características avanzadas:**
  - Drag & drop para edición de horarios
  - Gráficos interactivos y actualizables
  - Sistema de notificaciones en tiempo real
  - Exportación de datos en múltiples formatos
  - Optimización de carga docente

## Contribución

1. Haz un fork del repositorio
2. Crea una rama para tu funcionalidad (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -am 'Añadir nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un nuevo Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles. 