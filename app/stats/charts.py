"""
Módulo para generar datos de gráficas para el módulo de estadísticas.
"""

import random

def generate_carga_chart_data(asignaturas):
    """
    Genera los datos para la gráfica de carga de asignaturas.
    
    Args:
        asignaturas: Lista de tuplas (nombre_asignatura, horas)
    
    Returns:
        dict: Datos formateados para usar con Chart.js
    """
    # Colores para las gráficas
    background_colors = [
        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', 
        '#1abc9c', '#d35400', '#34495e', '#7f8c8d', '#27ae60'
    ]
    
    # Asegurar que tenemos suficientes colores
    while len(background_colors) < len(asignaturas):
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        background_colors.append(f'rgb({r}, {g}, {b})')
    
    # Formato para gráficos (pie y bar)
    labels = [asignatura[0] for asignatura in asignaturas]
    values = [asignatura[1] for asignatura in asignaturas]
    
    # Datos para gráfico circular
    pie_data = {
        'labels': labels,
        'datasets': [{
            'data': values,
            'backgroundColor': background_colors[:len(asignaturas)],
            'hoverOffset': 4
        }]
    }
    
    # Datos para gráfico de barras
    bar_data = {
        'labels': labels,
        'datasets': [{
            'label': 'Horas semanales',
            'data': values,
            'backgroundColor': background_colors[:len(asignaturas)],
            'borderWidth': 1
        }]
    }
    
    return {
        'pie': pie_data,
        'bar': bar_data,
        'total_horas': sum(values)
    }

def generate_comparacion_chart_data(data, asignaturas):
    """
    Genera los datos para la gráfica de comparación entre clases.
    
    Args:
        data: Diccionario {clase: {asignatura: horas, ...}, ...}
        asignaturas: Lista de asignaturas
    
    Returns:
        dict: Datos formateados para usar con Chart.js
    """
    # Colores para las clases
    class_colors = {
        'A': '#3498db',  # Azul
        'B': '#2ecc71',  # Verde
        'C': '#e74c3c',  # Rojo
        'D': '#f39c12',  # Naranja
        'E': '#9b59b6'   # Púrpura
    }
    
    # Para otras clases, generar colores aleatorios
    for clase in data.keys():
        if clase not in class_colors:
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            class_colors[clase] = f'rgb({r}, {g}, {b})'
    
    # Datos para gráfico de barras agrupadas
    datasets = []
    for clase, horas in data.items():
        datasets.append({
            'label': f'Clase {clase}',
            'data': [horas.get(asig, 0) for asig in asignaturas],
            'backgroundColor': class_colors.get(clase, '#7f8c8d')
        })
    
    return {
        'labels': asignaturas,
        'datasets': datasets
    }

def generate_profesor_chart_data(profesor, data_semanal, data_mensual, data_anual):
    """
    Genera los datos para la gráfica de carga de un profesor.
    
    Args:
        profesor: Objeto Profesor
        data_semanal: Datos de carga semanal
        data_mensual: Datos de carga mensual
        data_anual: Datos de carga anual
    
    Returns:
        dict: Datos formateados para usar con Chart.js
    """
    # Datos para gráfico de línea temporal
    line_data = {
        'labels': ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4'],
        'datasets': [{
            'label': 'Horas impartidas',
            'data': [d.horas for d in data_semanal],
            'borderColor': '#3498db',
            'backgroundColor': 'rgba(52, 152, 219, 0.2)',
            'fill': True,
            'tension': 0.4
        }]
    }
    
    # Datos para gráfico de radar (distribución diaria)
    dias = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
    horas_por_dia = {dia: sum(1 for h in profesor.horarios if h.dia.lower() == dia.lower()) for dia in dias}
    
    radar_data = {
        'labels': dias,
        'datasets': [{
            'label': 'Horas por día',
            'data': [horas_por_dia.get(dia, 0) for dia in dias],
            'backgroundColor': 'rgba(39, 174, 96, 0.2)',
            'borderColor': '#27ae60',
            'pointBackgroundColor': '#27ae60',
            'pointBorderColor': '#fff',
            'pointHoverBackgroundColor': '#fff',
            'pointHoverBorderColor': '#27ae60'
        }]
    }
    
    return {
        'line': line_data,
        'radar': radar_data
    } 