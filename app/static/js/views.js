document.addEventListener('DOMContentLoaded', function() {
    // Gráfico de distribución de horas
    const ctxPie = document.getElementById('grafico-distribucion').getContext('2d');
    
    // Get data from data attributes
    const chartData = {
        lunes: parseInt(document.getElementById('data-dias').dataset.lunes),
        martes: parseInt(document.getElementById('data-dias').dataset.martes),
        miercoles: parseInt(document.getElementById('data-dias').dataset.miercoles),
        jueves: parseInt(document.getElementById('data-dias').dataset.jueves),
        viernes: parseInt(document.getElementById('data-dias').dataset.viernes)
    };

    new Chart(ctxPie, {
        type: 'bar',
        data: {
            labels: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes'],
            datasets: [{
                label: 'Horas de clase',
                data: [
                    chartData.lunes,
                    chartData.martes,
                    chartData.miercoles,
                    chartData.jueves,
                    chartData.viernes
                ],
                backgroundColor: [
                    'rgba(54, 162, 235, 0.6)',
                    'rgba(255, 99, 132, 0.6)',
                    'rgba(255, 206, 86, 0.6)',
                    'rgba(75, 192, 192, 0.6)',
                    'rgba(153, 102, 255, 0.6)'
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 99, 132, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 7,
                    ticks: {
                        stepSize: 1
                    }
                }
            }
        }
    });
    
    // Botón de exportar a CSV
    document.getElementById('btn-exportar').addEventListener('click', function() {
        // Mostrar un mensaje de espera mientras se genera el CSV
        const btnExportar = document.getElementById('btn-exportar');
        const originalText = btnExportar.innerHTML;
        btnExportar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Exportando...';
        btnExportar.disabled = true;
        
        // Dar tiempo al DOM para actualizar y mostrar el icono de carga
        setTimeout(function() {
            generateCSV(btnExportar, originalText);
        }, 200);
    });
    
    // Función para generar CSV desde la tabla de horario
    function generateCSV(btnElement, originalBtnText) {
        const horarioTabla = document.querySelector('.horario-tabla');
        const titulo = document.querySelector('h1').textContent;
        const exportUrl = document.getElementById('data-export').dataset.url;
        
        // Fetch the CSV data from the server
        fetch(exportUrl)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.text();
            })
            .then(csvContent => {
                // Create blob and download
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const link = document.createElement('a');
                const url = URL.createObjectURL(blob);
                
                link.setAttribute('href', url);
                link.setAttribute('download', `Horario_${titulo.replace(/[^a-zA-Z0-9]/g, '_')}.csv`);
                link.style.visibility = 'hidden';
                
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                
                // Restaurar el botón
                btnElement.innerHTML = originalBtnText;
                btnElement.disabled = false;
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('error', 'Error al exportar el horario');
                btnElement.innerHTML = originalBtnText;
                btnElement.disabled = false;
            });
    }
    
    // Botón de exportar a PDF
    document.getElementById('btn-pdf').addEventListener('click', function() {
        // Mostrar un mensaje de espera mientras se genera el PDF
        const btnPdf = document.getElementById('btn-pdf');
        const originalText = btnPdf.innerHTML;
        btnPdf.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Generando PDF...';
        btnPdf.disabled = true;
        
        // Dar tiempo al DOM para actualizar y mostrar el icono de carga
        setTimeout(function() {
            generatePDF(btnPdf, originalText);
        }, 200);
    });
    
    // Función para generar PDF usando jsPDF y html2canvas
    function generatePDF(btnElement, originalBtnText) {
        // Elementos que queremos incluir en el PDF
        const horarioTabla = document.querySelector('.horario-tabla');
        const resumenTabla = document.querySelector('.card .table-striped');
        const titulo = document.querySelector('h1').textContent;
        
        // Crear un nuevo documento PDF
        const { jsPDF } = window.jspdf;
        const doc = new jsPDF('landscape', 'pt', 'a4');
        const pageWidth = doc.internal.pageSize.getWidth();
        const pageHeight = doc.internal.pageSize.getHeight();
        const margin = 40;
        
        // Añadir título
        doc.setFontSize(18);
        doc.text(titulo, pageWidth / 2, margin, { align: 'center' });
        
        // Capturar la tabla de horario como imagen
        html2canvas(horarioTabla, { scale: 2 }).then(canvas => {
            const imgData = canvas.toDataURL('image/png');
            const imgWidth = pageWidth - (margin * 2);
            const imgHeight = (canvas.height * imgWidth) / canvas.width;
            
            // Añadir la imagen al PDF
            doc.addImage(imgData, 'PNG', margin, margin + 20, imgWidth, imgHeight);
            
            // Comprobar si necesitamos una nueva página para el resumen
            if (margin + imgHeight + 40 > pageHeight - margin) {
                doc.addPage();
                doc.text("Resumen de Asignaturas", pageWidth / 2, margin, { align: 'center' });
                
                // Capturar la tabla de resumen
                if (resumenTabla) {
                    html2canvas(resumenTabla, { scale: 2 }).then(resumenCanvas => {
                        const resumenImgData = resumenCanvas.toDataURL('image/png');
                        const resumenImgWidth = pageWidth / 2;
                        const resumenImgHeight = (resumenCanvas.height * resumenImgWidth) / resumenCanvas.width;
                        
                        doc.addImage(resumenImgData, 'PNG', margin, margin + 40, resumenImgWidth, resumenImgHeight);
                        
                        // Guardar y descargar el PDF
                        doc.save(`Horario_${titulo.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`);
                        
                        // Restaurar el botón
                        btnElement.innerHTML = originalBtnText;
                        btnElement.disabled = false;
                    });
                } else {
                    doc.save(`Horario_${titulo.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`);
                    btnElement.innerHTML = originalBtnText;
                    btnElement.disabled = false;
                }
            } else {
                // Añadir resumen en la misma página
                doc.text("Resumen de Asignaturas", pageWidth / 2, margin + imgHeight + 40, { align: 'center' });
                
                if (resumenTabla) {
                    html2canvas(resumenTabla, { scale: 2 }).then(resumenCanvas => {
                        const resumenImgData = resumenCanvas.toDataURL('image/png');
                        const resumenImgWidth = pageWidth / 2;
                        const resumenImgHeight = (resumenCanvas.height * resumenImgWidth) / resumenCanvas.width;
                        
                        doc.addImage(resumenImgData, 'PNG', margin, margin + imgHeight + 60, resumenImgWidth, resumenImgHeight);
                        
                        // Guardar y descargar el PDF
                        doc.save(`Horario_${titulo.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`);
                        
                        // Restaurar el botón
                        btnElement.innerHTML = originalBtnText;
                        btnElement.disabled = false;
                    });
                } else {
                    doc.save(`Horario_${titulo.replace(/[^a-zA-Z0-9]/g, '_')}.pdf`);
                    btnElement.innerHTML = originalBtnText;
                    btnElement.disabled = false;
                }
            }
        });
    }
    
    // Manejar la eliminación del horario
    const deleteForm = document.querySelector('#confirmDeleteModal form');
    if (deleteForm) {
        deleteForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Mostrar indicador de carga
            const submitBtn = this.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Eliminando...';
            submitBtn.disabled = true;
            
            // Enviar la solicitud
            fetch(this.action, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Mostrar mensaje de éxito
                    showToast('success', 'Horario eliminado correctamente');
                    
                    // Redirigir después de un breve retraso
                    setTimeout(() => {
                        window.location.href = document.getElementById('data-export').dataset.url.split('?')[0];
                    }, 1500);
                } else {
                    // Mostrar mensaje de error
                    showToast('danger', data.message || 'Error al eliminar el horario');
                    submitBtn.innerHTML = originalText;
                    submitBtn.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showToast('danger', 'Error al eliminar el horario');
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            });
        });
    }
    
    // Función para mostrar notificaciones toast
    function showToast(type, message) {
        const toastContainer = document.querySelector('.toast-container') || createToastContainer();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Eliminar el toast después de que se oculte
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
    
    // Función para crear el contenedor de toasts si no existe
    function createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(container);
        return container;
    }
});
