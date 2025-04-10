document.addEventListener('DOMContentLoaded', function() {
    // Crear un contenedor oculto para la generación de PDF
    const pdfContainer = document.createElement('div');
    pdfContainer.style.position = 'absolute';
    pdfContainer.style.left = '-9999px';
    pdfContainer.style.top = '-9999px';
    document.body.appendChild(pdfContainer);

    // Botón de exportar todos a CSV
    document.getElementById('btn-exportar-todos').addEventListener('click', function() {
        const btnExportar = document.getElementById('btn-exportar-todos');
        const originalText = btnExportar.innerHTML;
        btnExportar.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Exportando...';
        btnExportar.disabled = true;
        
        generateAllCSV(btnExportar, originalText);
    });
    
    // Función para generar CSV de todos los horarios
    async function generateAllCSV(btnElement, originalBtnText) {
        const tabla = document.querySelector('.table');
        const filas = tabla.querySelectorAll('tbody tr');
        let csv = [];
        
        try {
            // Para cada horario en la tabla
            for (const fila of filas) {
                const nombre = fila.cells[0].textContent.trim();
                const periodo = fila.cells[1].textContent.trim();
                const viewLink = fila.querySelector('a[href*="/view/"]');
                
                if (viewLink) {
                    // Obtener ID de la clase desde el enlace
                    const claseId = viewLink.href.split('/').pop();
                    
                    // Obtener los detalles del horario
                    const response = await fetch(`/schedules/view/${claseId}`);
                    const text = await response.text();
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(text, 'text/html');
                    
                    // Añadir encabezado para este horario
                    csv.push(`\nHorario: ${nombre}`);
                    csv.push(`Periodo: ${periodo}`);
                    csv.push('Hora,Lunes,Martes,Miércoles,Jueves,Viernes');
                    
                    // Obtener datos del horario
                    const horarioTabla = doc.querySelector('.horario-tabla');
                    if (horarioTabla) {
                        const filasSemana = horarioTabla.querySelectorAll('tbody tr');
                        filasSemana.forEach(filaSemana => {
                            let rowData = [];
                            
                            // Obtener hora
                            const hora = filaSemana.querySelector('th').textContent.trim();
                            rowData.push(`"${hora}"`);
                            
                            // Obtener datos de cada día
                            const celdasDia = filaSemana.querySelectorAll('td');
                            celdasDia.forEach(celda => {
                                const asignaturaElement = celda.querySelector('.asignatura-nombre');
                                const profesorElement = celda.querySelector('.profesor-nombre');
                                
                                if (asignaturaElement && profesorElement) {
                                    const asignatura = asignaturaElement.textContent.trim();
                                    const profesor = profesorElement.textContent.trim();
                                    rowData.push(`"${asignatura} (${profesor})"`);
                                } else {
                                    rowData.push('""');
                                }
                            });
                            
                            csv.push(rowData.join(','));
                        });
                        
                        // Añadir resumen de asignaturas
                        csv.push('\nResumen de Asignaturas:');
                        const resumenTabla = doc.querySelector('.table-striped');
                        if (resumenTabla) {
                            const filasResumen = resumenTabla.querySelectorAll('tbody tr');
                            filasResumen.forEach(filaResumen => {
                                const asignatura = filaResumen.cells[0].textContent.trim();
                                const profesor = filaResumen.cells[1].textContent.trim();
                                const horas = filaResumen.cells[2].textContent.trim();
                                csv.push(`"${asignatura}","${profesor}","${horas} horas"`);
                            });
                        }
                        
                        // Añadir línea en blanco entre horarios
                        csv.push('');
                    }
                }
            }
            
            // Unir todas las filas y descargar
            const csvContent = csv.join('\n');
            const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            const url = URL.createObjectURL(blob);
            
            link.setAttribute('href', url);
            link.setAttribute('download', 'Todos_los_horarios.csv');
            link.style.visibility = 'hidden';
            
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error generando CSV:', error);
            alert('Error generando el archivo CSV. Por favor, intente nuevamente.');
        }
        
        // Restaurar el botón
        btnElement.innerHTML = originalBtnText;
        btnElement.disabled = false;
    }
    
    // Botón de exportar todos a PDF
    document.getElementById('btn-pdf-todos').addEventListener('click', function() {
        const btnPdf = document.getElementById('btn-pdf-todos');
        const originalText = btnPdf.innerHTML;
        btnPdf.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i> Generando PDF...';
        btnPdf.disabled = true;
        
        generateAllPDF(btnPdf, originalText);
    });
    
    // Función para generar PDF de todos los horarios
    async function generateAllPDF(btnElement, originalBtnText) {
        try {
            const tabla = document.querySelector('.table');
            const filas = tabla.querySelectorAll('tbody tr');
            
            // Crear un nuevo documento PDF
            const { jsPDF } = window.jspdf;
            const doc = new jsPDF('landscape', 'pt', 'a4');
            const pageWidth = doc.internal.pageSize.getWidth();
            const pageHeight = doc.internal.pageSize.getHeight();
            const margin = 40;
            
            // Añadir título principal
            doc.setFontSize(18);
            doc.text('Horarios de Todas las Clases', pageWidth / 2, margin, { align: 'center' });
            
            let yPos = margin + 40;
            
            // Para cada horario en la tabla
            for (const [index, fila] of Array.from(filas).entries()) {
                const nombre = fila.cells[0].textContent.trim();
                const periodo = fila.cells[1].textContent.trim();
                const viewLink = fila.querySelector('a[href*="/view/"]');
                
                if (viewLink) {
                    // Limpiar el contenedor antes de cada iteración
                    pdfContainer.innerHTML = '';
                    
                    // Si no es el primer horario, añadir nueva página
                    if (index > 0) {
                        doc.addPage();
                        yPos = margin;
                    }
                    
                    const claseId = viewLink.href.split('/').pop();
                    
                    // Obtener los detalles del horario
                    const response = await fetch(`/schedules/view/${claseId}`);
                    const text = await response.text();
                    const parser = new DOMParser();
                    const doc_html = parser.parseFromString(text, 'text/html');
                    
                    // Añadir título del horario
                    doc.setFontSize(14);
                    doc.text(`${nombre} - ${periodo}`, pageWidth / 2, yPos, { align: 'center' });
                    
                    // Procesar la tabla de horario
                    const horarioTabla = doc_html.querySelector('.horario-tabla');
                    if (horarioTabla) {
                        // Clonar la tabla en el contenedor oculto
                        const tablaClone = horarioTabla.cloneNode(true);
                        tablaClone.style.width = '1000px';
                        pdfContainer.appendChild(tablaClone);
                        
                        // Capturar la tabla como imagen
                        const canvas = await html2canvas(tablaClone, { 
                            scale: 2,
                            logging: false,
                            useCORS: true
                        });
                        
                        const imgData = canvas.toDataURL('image/png');
                        const imgWidth = pageWidth - (margin * 2);
                        const imgHeight = (canvas.height * imgWidth) / canvas.width;
                        
                        // Añadir la imagen al PDF
                        doc.addImage(imgData, 'PNG', margin, yPos + 20, imgWidth, imgHeight);
                        yPos += imgHeight + 60;
                        
                        // Procesar el resumen de asignaturas
                        if (yPos + 200 <= pageHeight - margin) {
                            const resumenTabla = doc_html.querySelector('.table-striped');
                            if (resumenTabla) {
                                // Limpiar el contenedor y añadir la tabla de resumen
                                pdfContainer.innerHTML = '';
                                const resumenClone = resumenTabla.cloneNode(true);
                                resumenClone.style.width = '500px';
                                pdfContainer.appendChild(resumenClone);
                                
                                const resumenCanvas = await html2canvas(resumenClone, {
                                    scale: 2,
                                    logging: false,
                                    useCORS: true
                                });
                                
                                const resumenImgData = resumenCanvas.toDataURL('image/png');
                                const resumenImgWidth = pageWidth / 2;
                                const resumenImgHeight = (resumenCanvas.height * resumenImgWidth) / resumenCanvas.width;
                                
                                doc.text('Resumen de Asignaturas', pageWidth / 2, yPos, { align: 'center' });
                                doc.addImage(resumenImgData, 'PNG', margin, yPos + 20, resumenImgWidth, resumenImgHeight);
                            }
                        }
                    }
                }
            }
            
            // Limpiar el contenedor oculto
            pdfContainer.innerHTML = '';
            
            // Guardar y descargar el PDF
            doc.save('Todos_los_horarios.pdf');
        } catch (error) {
            console.error('Error generando PDF:', error);
            alert('Error generando el archivo PDF. Por favor, intente nuevamente.');
        }
        
        // Restaurar el botón
        btnElement.innerHTML = originalBtnText;
        btnElement.disabled = false;
    }
});