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
    
    // Animaciones específicas para el dashboard estadístico
    if (currentPath.includes('/stats')) {
        initDashboardAnimations();
    }
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

/**
 * Inicializa animaciones específicas para el dashboard estadístico
 */
function initDashboardAnimations() {
    // Activar animaciones para barras de progreso
    animateProgressBars();
    
    // Activar contadores numéricos
    animateCounters();
    
    // Animar alertas
    animateAlerts();
    
    // Inicializar gráficos con animación
    initDashboardCharts();
}

/**
 * Anima las barras de progreso en el dashboard
 */
function animateProgressBars() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const targetWidth = bar.getAttribute('data-progress') || '100';
        
        // Usar CSS Custom Properties para la animación
        bar.style.setProperty('--target-width', targetWidth + '%');
        
        // Agregar clase para iniciar la animación con un ligero retraso
        setTimeout(() => {
            bar.classList.add('animate-progress-bar');
        }, 300);
    });
}

/**
 * Anima los contadores numéricos incrementando gradualmente
 */
function animateCounters() {
    const counters = document.querySelectorAll('.animate-counter');
    
    counters.forEach(counter => {
        const target = parseInt(counter.textContent, 10);
        const duration = 1500; // Duración de la animación en ms
        const frameRate = 30; // Frames por segundo
        const frameDuration = 1000 / frameRate;
        const totalFrames = duration / frameDuration;
        
        // Guardar el valor original para que podamos restaurarlo si es necesario
        counter.setAttribute('data-target', counter.textContent);
        
        // Empezar desde 0
        counter.textContent = '0';
        counter.style.opacity = '1';
        
        let currentFrame = 0;
        
        // Crear intervalo para incrementar el contador
        const interval = setInterval(() => {
            currentFrame++;
            
            // Cálculo suavizado del progreso usando easeOutQuad
            const progress = 1 - Math.pow(1 - currentFrame / totalFrames, 2);
            const currentCount = Math.round(progress * target);
            
            counter.textContent = currentCount;
            
            if (currentFrame === totalFrames) {
                clearInterval(interval);
                counter.textContent = target;
            }
        }, frameDuration);
    });
}

/**
 * Anima las alertas en el dashboard
 */
function animateAlerts() {
    const alertsContainer = document.getElementById('alertsContainer');
    if (!alertsContainer) return;
    
    const alerts = alertsContainer.querySelectorAll('.alert');
    
    alerts.forEach((alert, index) => {
        alert.style.opacity = '0';
        alert.style.transform = 'translateX(50px)';
        
        setTimeout(() => {
            alert.classList.add('alert-animate');
        }, 300 + (index * 150));
    });
}

/**
 * Inicializa los gráficos del dashboard con animaciones
 */
function initDashboardCharts() {
    // Comprobar si Chart.js está disponible
    if (typeof Chart === 'undefined') {
        console.warn('Chart.js no está disponible');
        return;
    }
    
    // Gráfico de evolución temporal
    const evolucionCtx = document.getElementById('evolucionChart');
    if (evolucionCtx) {
        // Datos de ejemplo para el gráfico
        const data = {
            labels: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio'],
            datasets: [{
                label: 'Progreso Académico',
                data: [30, 45, 60, 70, 85, 95],
                borderColor: '#3498db',
                backgroundColor: 'rgba(52, 152, 219, 0.1)',
                tension: 0.4,
                fill: true
            }]
        };
        
        // Opciones de animación
        const config = {
            type: 'line',
            data: data,
            options: {
                responsive: true,
                animation: {
                    duration: 2000,
                    easing: 'easeOutQuart'
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        };
        
        // Crear el gráfico con una breve pausa para permitir que la página cargue
        setTimeout(() => {
            new Chart(evolucionCtx, config);
            
            // Añadir clase de animación al contenedor
            evolucionCtx.closest('.chart-container').classList.add('animate-chart');
        }, 500);
    }
}

/**
 * Lanza un confeti para celebrar un logro o estadística destacada
 */
function celebrateAchievement(elementId) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    // Primero destacar el elemento
    element.classList.add('animate-pulse');
    
    // Luego lanzar confeti centrado en ese elemento
    launchConfetti(element);
    
    // Quitar la clase después de la animación
    setTimeout(() => {
        element.classList.remove('animate-pulse');
    }, 3000);
} 