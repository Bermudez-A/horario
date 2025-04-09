/**
 * Función para mostrar vista previa de imágenes al subirlas
 */
document.addEventListener('DOMContentLoaded', function() {
    const fotoInput = document.getElementById('foto');
    const previewContainer = document.getElementById('preview-container');
    
    if (fotoInput && previewContainer) {
        // Crear elementos para la vista previa
        if (!document.getElementById('img-preview')) {
            const previewImage = document.createElement('img');
            previewImage.id = 'img-preview';
            previewImage.className = 'img-fluid rounded-circle mb-3';
            previewImage.style.maxWidth = '150px';
            previewImage.style.maxHeight = '150px';
            previewImage.style.objectFit = 'cover';
            previewImage.style.display = 'none';
            previewContainer.appendChild(previewImage);
        }
        
        // Elementos para mensaje de error
        if (!document.getElementById('preview-error')) {
            const errorMessage = document.createElement('div');
            errorMessage.id = 'preview-error';
            errorMessage.className = 'alert alert-danger';
            errorMessage.style.display = 'none';
            previewContainer.appendChild(errorMessage);
        }
        
        // Manejar cambio en el input de archivo
        fotoInput.addEventListener('change', function(event) {
            const imgPreview = document.getElementById('img-preview');
            const errorMessage = document.getElementById('preview-error');
            
            // Ocultar mensajes anteriores
            imgPreview.style.display = 'none';
            errorMessage.style.display = 'none';
            
            const file = event.target.files[0];
            
            if (file) {
                // Validar tipo de archivo
                const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/gif'];
                if (!validTypes.includes(file.type)) {
                    errorMessage.textContent = 'Por favor, selecciona una imagen válida (JPEG, PNG, GIF)';
                    errorMessage.style.display = 'block';
                    fotoInput.value = '';
                    return;
                }
                
                // Validar tamaño (max 5MB)
                if (file.size > 5 * 1024 * 1024) {
                    errorMessage.textContent = 'La imagen es demasiado grande. El tamaño máximo es 5MB.';
                    errorMessage.style.display = 'block';
                    fotoInput.value = '';
                    return;
                }
                
                // Crear URL para vista previa
                const reader = new FileReader();
                reader.onload = function(e) {
                    imgPreview.src = e.target.result;
                    imgPreview.style.display = 'block';
                    
                    // Añadir animación
                    imgPreview.style.animation = 'fadeIn 0.5s';
                };
                reader.readAsDataURL(file);
            }
        });
    }
}); 