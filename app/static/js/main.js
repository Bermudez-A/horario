/**
 * Funcionalidades JavaScript principales para el Generador de Horarios
 * Versión: 1.0
 */

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar tooltips de Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Inicializar popovers de Bootstrap
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function(popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-cerrar alertas después de 5 segundos
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert:not(.alert-persistent)');
        alerts.forEach(function(alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Manejar interacción con celdas de disponibilidad
    setupDisponibilidadCells();

    // Manejar drag and drop en el editor de horarios
    setupHorarioDragDrop();

    // Inicializar gráficos si existen contenedores
    initializeCharts();

    /**
     * Inicializa la funcionalidad del sidebar si existe
     */
    setupSidebar();
});

/**
 * Configura la interacción con las celdas de disponibilidad
 */
function setupDisponibilidadCells() {
    const disponibilidadCells = document.querySelectorAll('.disponibilidad-cell');
    
    disponibilidadCells.forEach(cell => {
        cell.addEventListener('click', function() {
            const profesorId = this.dataset.profesorId;
            const dia = this.dataset.dia;
            const hora = this.dataset.hora;
            const disponible = !this.classList.contains('disponible');
            
            // Alternar clase visual
            this.classList.toggle('disponible');
            this.classList.toggle('no-disponible');
            
            // Enviar actualización al servidor
            updateDisponibilidad(profesorId, dia, hora, disponible);
        });
    });
}

/**
 * Actualiza la disponibilidad de un profesor
 */
function updateDisponibilidad(profesorId, dia, hora, disponible, motivo = '') {
    fetch('/schedules/availability/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            profesor_id: profesorId,
            dia: dia,
            hora: hora,
            disponible: disponible,
            motivo: motivo
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Disponibilidad actualizada correctamente', 'success');
        } else {
            showToast('Error al actualizar disponibilidad: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error de conexión al actualizar disponibilidad', 'danger');
    });
}

/**
 * Configura la funcionalidad de arrastrar y soltar para el editor de horarios
 */
function setupHorarioDragDrop() {
    const draggables = document.querySelectorAll('.horario-draggable');
    const dropzones = document.querySelectorAll('.horario-dropzone');
    
    draggables.forEach(draggable => {
        draggable.addEventListener('dragstart', function(e) {
            e.dataTransfer.setData('text/plain', this.id);
            this.classList.add('dragging');
        });
        
        draggable.addEventListener('dragend', function() {
            this.classList.remove('dragging');
        });
    });
    
    dropzones.forEach(dropzone => {
        dropzone.addEventListener('dragover', function(e) {
            e.preventDefault();
            this.classList.add('dropzone-active');
        });
        
        dropzone.addEventListener('dragleave', function() {
            this.classList.remove('dropzone-active');
        });
        
        dropzone.addEventListener('drop', function(e) {
            e.preventDefault();
            this.classList.remove('dropzone-active');
            
            const id = e.dataTransfer.getData('text/plain');
            const draggable = document.getElementById(id);
            
            if (draggable) {
                const asignaturaId = draggable.dataset.asignaturaId;
                const profesorId = draggable.dataset.profesorId;
                const claseId = this.dataset.claseId;
                const dia = this.dataset.dia;
                const hora = this.dataset.hora;
                
                updateHorario(claseId, dia, hora, asignaturaId, profesorId, this);
            }
        });
    });
}

/**
 * Actualiza el horario en el servidor
 */
function updateHorario(claseId, dia, hora, asignaturaId, profesorId, dropzoneElement) {
    fetch('/schedules/update', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            clase_id: claseId,
            dia: dia,
            hora: hora,
            asignatura_id: asignaturaId,
            profesor_id: profesorId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Horario actualizado correctamente', 'success');
            
            // Actualizar visualmente la celda
            const asignaturaNombre = document.querySelector(`[data-asignatura-id="${asignaturaId}"]`).dataset.asignaturaNombre;
            const profesorNombre = document.querySelector(`[data-profesor-id="${profesorId}"]`).dataset.profesorNombre;
            
            dropzoneElement.innerHTML = `
                <div class="cell-content">
                    <div class="asignatura">${asignaturaNombre}</div>
                    <div class="profesor">${profesorNombre}</div>
                </div>
            `;
        } else {
            showToast('Error al actualizar horario: ' + data.message, 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('Error de conexión al actualizar horario', 'danger');
    });
}

/**
 * Inicializa los gráficos en la página si existen contenedores
 */
function initializeCharts() {
    // Gráfico de carga de asignaturas (circular)
    const pieChartContainer = document.getElementById('carga-asignaturas-pie');
    if (pieChartContainer) {
        const chartData = JSON.parse(pieChartContainer.dataset.chartData);
        new Chart(pieChartContainer, {
            type: 'pie',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Distribución de Horas por Asignatura'
                    }
                }
            }
        });
    }
    
    // Gráfico de carga de asignaturas (barras)
    const barChartContainer = document.getElementById('carga-asignaturas-bar');
    if (barChartContainer) {
        const chartData = JSON.parse(barChartContainer.dataset.chartData);
        new Chart(barChartContainer, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Horas Semanales por Asignatura'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Horas'
                        }
                    }
                }
            }
        });
    }
    
    // Gráfico de comparación entre clases
    const comparisonChartContainer = document.getElementById('comparacion-clases-chart');
    if (comparisonChartContainer) {
        const chartData = JSON.parse(comparisonChartContainer.dataset.chartData);
        new Chart(comparisonChartContainer, {
            type: 'bar',
            data: chartData,
            options: {
                responsive: true,
                plugins: {
                    title: {
                        display: true,
                        text: 'Comparación de Horas por Asignatura entre Clases'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Horas'
                        }
                    }
                }
            }
        });
    }
}

/**
 * Muestra un toast de notificación
 */
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        // Crear contenedor de toasts si no existe
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center border-0 text-white bg-${type}" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHTML);
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, { delay: 5000 });
    toast.show();
}

/**
 * Obtiene el token CSRF de la cookie
 */
function getCSRFToken() {
    const name = 'csrftoken=';
    const decodedCookie = decodeURIComponent(document.cookie);
    const cookieArray = decodedCookie.split(';');
    
    for (let i = 0; i < cookieArray.length; i++) {
        let cookie = cookieArray[i].trim();
        if (cookie.indexOf(name) === 0) {
            return cookie.substring(name.length, cookie.length);
        }
    }
    
    return '';
}

/**
 * Configura la funcionalidad del sidebar para administradores
 * Versión mejorada sin animaciones
 */
function setupSidebar() {
    const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
    const sidebarCollapseBtn = document.getElementById('sidebarCollapseBtn');
    const sidebar = document.getElementById('sidebar');
    const contentWrapper = document.getElementById('content-wrapper');
    const sidebarCollapse = document.getElementById('sidebarCollapse');
    
    // Si no hay sidebar, no hacemos nada
    if (!sidebar) return;
    
    // Establecer estado inicial desde localStorage si existe
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        sidebar.classList.add('collapsed');
        contentWrapper.classList.add('expanded');
    }
    
    // Botón de hamburguesa en móviles - aplicamos cambios directamente sin animaciones
    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('active');
            // Evitar comportamiento de scroll
            document.body.style.overflow = sidebar.classList.contains('active') ? 'hidden' : '';
        });
    }
    
    // Botón de cierre en móviles - acción inmediata sin animaciones
    if (sidebarCollapseBtn) {
        sidebarCollapseBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.remove('active');
            document.body.style.overflow = '';
        });
    }
    
    // Botón de colapso en desktop - cambio instantáneo sin transiciones
    if (sidebarCollapse) {
        sidebarCollapse.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('collapsed');
            contentWrapper.classList.toggle('expanded');
            // Guardar estado en localStorage
            localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
        });
    }
    
    // Cerrar sidebar al hacer clic en un enlace (en dispositivos móviles)
    const sidebarLinks = document.querySelectorAll('#sidebar .nav-link');
    sidebarLinks.forEach(link => {
        link.addEventListener('click', function() {
            if (window.innerWidth < 768 && sidebar) {
                sidebar.classList.remove('active');
                document.body.style.overflow = '';
            }
        });
    });

    // Cerrar sidebar al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (window.innerWidth < 768 && 
            sidebar && 
            sidebar.classList.contains('active') && 
            !sidebar.contains(e.target) && 
            e.target !== sidebarToggleBtn) {
            sidebar.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
}