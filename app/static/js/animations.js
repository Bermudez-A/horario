/**
 * Script para animaciones y efectos visuales
 */
document.addEventListener('DOMContentLoaded', function() {
    // Aplicar animaciones de entrada
    applyEntryAnimations();
    
    // Inicializar indicador de scroll
    initScrollIndicator();
    
    // Inicializar botón volver arriba
    initBackToTop();
    
    // Inicializar efecto de partículas si estamos en inicio o login
    const currentPath = window.location.pathname;
    if (currentPath === '/' || currentPath.includes('/auth/login')) {
        initParticles();
    }
    
    // Aplicar efecto spring a botones
    initSpringButtons();
    
    // Generar avatares para profesores
    generateAvatars();
});

/**
 * Aplica animaciones de entrada a los elementos principales
 */
function applyEntryAnimations() {
    // Animar elementos con clase específica
    const fadeElements = document.querySelectorAll('.animate-fade-in');
    fadeElements.forEach(el => {
        // Asegurar que la animación se reproduzca después de cargarse
        el.style.opacity = '0';
        setTimeout(() => {
            el.style.opacity = '1';
            el.style.animation = 'fadeIn 0.5s ease forwards';
        }, 100);
    });
    
    // Animar tarjetas de forma escalonada
    animateStaggered('.profesor-card', 'animate-scale-in', 100);
    animateStaggered('.stats-card', 'animate-slide-up', 150);
}

/**
 * Anima elementos de forma escalonada
 */
function animateStaggered(selector, animationClass, delay) {
    const elements = document.querySelectorAll(selector);
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        setTimeout(() => {
            el.classList.add(animationClass);
        }, delay * index);
    });
}

/**
 * Inicializa el indicador de scroll
 */
function initScrollIndicator() {
    // Crear elemento del indicador si no existe
    if (!document.querySelector('.scroll-indicator')) {
        const indicator = document.createElement('div');
        indicator.className = 'scroll-indicator';
        document.body.appendChild(indicator);
        
        // Actualizar ancho basado en el scroll
        window.addEventListener('scroll', () => {
            const winScroll = document.body.scrollTop || document.documentElement.scrollTop;
            const height = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            const scrolled = (winScroll / height) * 100;
            indicator.style.width = scrolled + '%';
        });
    }
}

/**
 * Inicializa el botón de volver arriba
 */
function initBackToTop() {
    // Crear el botón si no existe
    if (!document.querySelector('.back-to-top')) {
        const backToTop = document.createElement('div');
        backToTop.className = 'back-to-top';
        backToTop.innerHTML = '<i class="fas fa-arrow-up"></i>';
        document.body.appendChild(backToTop);
        
        // Mostrar u ocultar según el scroll
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                backToTop.classList.add('visible');
            } else {
                backToTop.classList.remove('visible');
            }
        });
        
        // Volver arriba al hacer clic
        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
}

/**
 * Inicializa efecto de partículas en el fondo
 */
function initParticles() {
    // Crear contenedor de partículas si no existe
    if (!document.querySelector('.particles-bg')) {
        const container = document.createElement('div');
        container.className = 'particles-bg';
        document.body.appendChild(container);
        
        // Crear partículas
        for (let i = 0; i < 20; i++) {
            const particle = document.createElement('div');
            particle.className = 'particle';
            
            // Posición aleatoria
            const posX = Math.random() * 100;
            const posY = Math.random() * 100;
            
            // Tamaño aleatorio entre 5 y 30px
            const size = Math.random() * 25 + 5;
            
            // Estilo de la partícula
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            particle.style.left = `${posX}%`;
            particle.style.top = `${posY}%`;
            particle.style.opacity = (Math.random() * 0.5 + 0.1).toString();
            
            // Añadir al contenedor
            container.appendChild(particle);
            
            // Animación con retraso aleatorio
            particle.style.animationDelay = `${Math.random() * 5}s`;
        }
    }
}

/**
 * Aplica efecto spring a los botones principales
 */
function initSpringButtons() {
    const buttons = document.querySelectorAll('.btn-primary, .btn-success, .btn-danger');
    buttons.forEach(btn => {
        btn.classList.add('btn-spring');
    });
}

/**
 * Genera avatares automáticos para profesores sin foto
 */
function generateAvatars() {
    const avatarPlaceholders = document.querySelectorAll('.profesor-avatar:not(:has(img))');
    
    avatarPlaceholders.forEach(placeholder => {
        // Obtener nombre del profesor del elemento hermano
        const nameElement = placeholder.parentElement.querySelector('.profesor-name');
        
        if (nameElement) {
            const fullName = nameElement.textContent.trim();
            const initials = getInitials(fullName);
            const bgColor = stringToColor(fullName);
            
            // Si solo tiene un icono genérico, reemplazarlo con avatar generado
            if (placeholder.querySelector('.fa-user-circle')) {
                placeholder.innerHTML = '';
                placeholder.classList.add('avatar-generated');
                placeholder.style.backgroundColor = bgColor;
                placeholder.textContent = initials;
            }
        }
    });
}

/**
 * Obtiene las iniciales de un nombre completo
 */
function getInitials(name) {
    return name
        .split(' ')
        .map(part => part.charAt(0))
        .join('')
        .toUpperCase()
        .substring(0, 2);
}

/**
 * Genera un color basado en un string
 */
function stringToColor(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
        hash = str.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    const colors = [
        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6',
        '#1abc9c', '#d35400', '#c0392b', '#16a085', '#8e44ad'
    ];
    
    // Usar el hash para seleccionar un color del array
    return colors[Math.abs(hash) % colors.length];
}

/**
 * Función para lanzar confeti en celebraciones
 */
function launchConfetti(container) {
    const confettiCount = 100;
    const confettiColors = ['#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'];
    
    // Si no se proporcionó un contenedor, usar el body
    const targetElement = container || document.body;
    
    // Crear confetis
    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.className = 'confetti';
        
        // Posición
        const startX = Math.random() * 100;
        const startY = -20;
        
        // Tamaño y rotación
        const size = Math.random() * 10 + 5;
        const rotation = Math.random() * 360;
        
        // Color aleatorio
        const colorIndex = Math.floor(Math.random() * confettiColors.length);
        const color = confettiColors[colorIndex];
        
        // Estilos
        confetti.style.width = `${size}px`;
        confetti.style.height = `${size}px`;
        confetti.style.left = `${startX}%`;
        confetti.style.top = `${startY}px`;
        confetti.style.backgroundColor = color;
        confetti.style.transform = `rotate(${rotation}deg)`;
        
        targetElement.appendChild(confetti);
        
        // Animación
        setTimeout(() => {
            confetti.style.transition = 'top 1s ease-out, left 1s ease-out, opacity 0.5s ease-out';
            confetti.style.opacity = '1';
            confetti.style.top = `${Math.random() * 100 + 20}%`;
            confetti.style.left = `${startX + (Math.random() * 40 - 20)}%`;
            
            // Eliminar después de caer
            setTimeout(() => {
                confetti.style.opacity = '0';
                setTimeout(() => {
                    confetti.remove();
                }, 500);
            }, 1000);
        }, Math.random() * 500);
    }
} 