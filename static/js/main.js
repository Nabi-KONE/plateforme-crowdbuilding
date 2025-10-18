/*
crowdBuilding - Plateforme de Financement Participatif Immobilier
JavaScript principal pour les interactions utilisateur
*/

// Variables globales
const CROWDBUILDING = {
    config: {
        apiUrl: '/api/',
        csrfToken: document.querySelector('[name=csrfmiddlewaretoken]')?.value,
        locale: 'fr-FR',
        currency: 'FCFA'
    },
    utils: {},
    components: {},
    notifications: {}
};

// Utilitaires
CROWDBUILDING.utils = {
    // Formatage des nombres
    formatNumber: function(number, decimals = 0) {
        return new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: decimals,
            maximumFractionDigits: decimals
        }).format(number);
    },

    // Formatage des montants
    formatCurrency: function(amount, currency = 'FCFA') {
        return this.formatNumber(amount) + ' ' + currency;
    },

    // Formatage des pourcentages
    formatPercentage: function(value, decimals = 1) {
        return this.formatNumber(value, decimals) + '%';
    },

    // Formatage des dates
    formatDate: function(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        };
        return new Intl.DateTimeFormat('fr-FR', {...defaultOptions, ...options}).format(new Date(date));
    },

    // Formatage des dates relatives
    formatRelativeDate: function(date) {
        const now = new Date();
        const targetDate = new Date(date);
        const diffInSeconds = Math.floor((now - targetDate) / 1000);

        if (diffInSeconds < 60) {
            return 'Il y a quelques secondes';
        } else if (diffInSeconds < 3600) {
            const minutes = Math.floor(diffInSeconds / 60);
            return `Il y a ${minutes} minute${minutes > 1 ? 's' : ''}`;
        } else if (diffInSeconds < 86400) {
            const hours = Math.floor(diffInSeconds / 3600);
            return `Il y a ${hours} heure${hours > 1 ? 's' : ''}`;
        } else {
            const days = Math.floor(diffInSeconds / 86400);
            return `Il y a ${days} jour${days > 1 ? 's' : ''}`;
        }
    },

    // Validation des emails
    validateEmail: function(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    },

    // Validation des téléphones burkinabè
    validatePhone: function(phone) {
        const re = /^(\+226|226)?[0-9]{8}$/;
        return re.test(phone.replace(/\s/g, ''));
    },

    // Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle function
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Scroll to element
    scrollToElement: function(element, offset = 0) {
        const elementPosition = element.offsetTop - offset;
        window.scrollTo({
            top: elementPosition,
            behavior: 'smooth'
        });
    },

    // Show loading state
    showLoading: function(element) {
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    },

    // Hide loading state
    hideLoading: function(element) {
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    }
};

// Composants
CROWDBUILDING.components = {
    // Initialisation des tooltips Bootstrap
    initTooltips: function() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    },

    // Initialisation des popovers Bootstrap
    initPopovers: function() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function (popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    },

    // Initialisation des modales Bootstrap
    initModals: function() {
        // Auto-hide success alerts after 5 seconds
        const alerts = document.querySelectorAll('.alert-success');
        alerts.forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    },

    // Formatage automatique des montants
    initCurrencyFormatting: function() {
        const currencyElements = document.querySelectorAll('[data-currency]');
        currencyElements.forEach(element => {
            const amount = parseFloat(element.dataset.currency);
            if (!isNaN(amount)) {
                element.textContent = CROWDBUILDING.utils.formatCurrency(amount);
            }
        });
    },

    // Formatage automatique des pourcentages
    initPercentageFormatting: function() {
        const percentageElements = document.querySelectorAll('[data-percentage]');
        percentageElements.forEach(element => {
            const value = parseFloat(element.dataset.percentage);
            if (!isNaN(value)) {
                element.textContent = CROWDBUILDING.utils.formatPercentage(value);
            }
        });
    },

    // Formatage automatique des dates
    initDateFormatting: function() {
        const dateElements = document.querySelectorAll('[data-date]');
        dateElements.forEach(element => {
            const date = element.dataset.date;
            if (date) {
                element.textContent = CROWDBUILDING.utils.formatDate(date);
            }
        });

        const relativeDateElements = document.querySelectorAll('[data-relative-date]');
        relativeDateElements.forEach(element => {
            const date = element.dataset.relativeDate;
            if (date) {
                element.textContent = CROWDBUILDING.utils.formatRelativeDate(date);
            }
        });
    },

    // Initialisation des barres de progression
    initProgressBars: function() {
        const progressBars = document.querySelectorAll('.progress-bar');
        progressBars.forEach(bar => {
            const percentage = bar.dataset.percentage || bar.style.width;
            if (percentage) {
                // Animation de la barre de progression
                setTimeout(() => {
                    bar.style.width = percentage;
                }, 100);
            }
        });
    },

    // Initialisation des compteurs animés
    initCounters: function() {
        const counters = document.querySelectorAll('[data-counter]');
        
        const animateCounter = (element) => {
            const target = parseInt(element.dataset.counter);
            const duration = parseInt(element.dataset.duration) || 2000;
            const start = performance.now();
            
            const updateCounter = (currentTime) => {
                const elapsed = currentTime - start;
                const progress = Math.min(elapsed / duration, 1);
                const current = Math.floor(progress * target);
                
                element.textContent = CROWDBUILDING.utils.formatNumber(current);
                
                if (progress < 1) {
                    requestAnimationFrame(updateCounter);
                }
            };
            
            requestAnimationFrame(updateCounter);
        };

        // Observer pour déclencher l'animation quand l'élément devient visible
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounter(entry.target);
                    observer.unobserve(entry.target);
                }
            });
        });

        counters.forEach(counter => {
            observer.observe(counter);
        });
    }
};

// Gestion des notifications
CROWDBUILDING.notifications = {
    // Afficher une notification toast
    show: function(message, type = 'info', duration = 5000) {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        
        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div class="toast" id="${toastId}" role="alert" aria-live="assertive" aria-atomic="true">
                <div class="toast-header">
                    <i class="fas fa-${this.getIcon(type)} text-${type} me-2"></i>
                    <strong class="me-auto">crowdBuilding</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;
        
        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: duration > 0,
            delay: duration
        });
        
        toast.show();
        
        // Supprimer l'élément du DOM après fermeture
        toastElement.addEventListener('hidden.bs.toast', () => {
            toastElement.remove();
        });
    },

    // Créer le conteneur de toasts
    createToastContainer: function() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    },

    // Obtenir l'icône selon le type
    getIcon: function(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-circle',
            'warning': 'exclamation-triangle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    },

    // Notifications de succès
    success: function(message, duration) {
        this.show(message, 'success', duration);
    },

    // Notifications d'erreur
    error: function(message, duration) {
        this.show(message, 'error', duration);
    },

    // Notifications d'avertissement
    warning: function(message, duration) {
        this.show(message, 'warning', duration);
    },

    // Notifications d'information
    info: function(message, duration) {
        this.show(message, 'info', duration);
    }
};

// Fonctions de validation de formulaire
CROWDBUILDING.forms = {
    // Validation en temps réel
    initRealTimeValidation: function() {
        const forms = document.querySelectorAll('form[data-validate]');
        
        forms.forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
                
                input.addEventListener('input', CROWDBUILDING.utils.debounce(() => {
                    this.validateField(input);
                }, 300));
            });
        });
    },

    // Valider un champ
    validateField: function(field) {
        const value = field.value.trim();
        const fieldType = field.type;
        const isRequired = field.hasAttribute('required');
        const minLength = field.getAttribute('minlength');
        const maxLength = field.getAttribute('maxlength');
        
        let isValid = true;
        let errorMessage = '';
        
        // Validation requise
        if (isRequired && !value) {
            isValid = false;
            errorMessage = 'Ce champ est obligatoire';
        }
        
        // Validation email
        if (fieldType === 'email' && value && !CROWDBUILDING.utils.validateEmail(value)) {
            isValid = false;
            errorMessage = 'Format d\'email invalide';
        }
        
        // Validation téléphone
        if (fieldType === 'tel' && value && !CROWDBUILDING.utils.validatePhone(value)) {
            isValid = false;
            errorMessage = 'Format de téléphone invalide';
        }
        
        // Validation longueur
        if (value && minLength && value.length < parseInt(minLength)) {
            isValid = false;
            errorMessage = `Minimum ${minLength} caractères requis`;
        }
        
        if (value && maxLength && value.length > parseInt(maxLength)) {
            isValid = false;
            errorMessage = `Maximum ${maxLength} caractères autorisés`;
        }
        
        this.updateFieldValidation(field, isValid, errorMessage);
        return isValid;
    },

    // Mettre à jour l'état de validation d'un champ
    updateFieldValidation: function(field, isValid, errorMessage) {
        const feedback = field.parentNode.querySelector('.invalid-feedback') || 
                        field.parentNode.querySelector('.valid-feedback');
        
        if (feedback) {
            feedback.remove();
        }
        
        field.classList.remove('is-valid', 'is-invalid');
        
        if (field.value.trim()) {
            if (isValid) {
                field.classList.add('is-valid');
            } else {
                field.classList.add('is-invalid');
                const invalidFeedback = document.createElement('div');
                invalidFeedback.className = 'invalid-feedback';
                invalidFeedback.textContent = errorMessage;
                field.parentNode.appendChild(invalidFeedback);
            }
        }
    }
};

// Gestion des fichiers upload
CROWDBUILDING.upload = {
    // Initialiser les zones de drop
    initDropZones: function() {
        const dropZones = document.querySelectorAll('[data-drop-zone]');
        
        dropZones.forEach(zone => {
            const input = zone.querySelector('input[type="file"]');
            
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, this.preventDefaults, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.add('dragover'), false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                zone.addEventListener(eventName, () => zone.classList.remove('dragover'), false);
            });
            
            zone.addEventListener('drop', (e) => this.handleDrop(e, input), false);
            zone.addEventListener('click', () => input.click());
        });
    },

    // Empêcher les comportements par défaut
    preventDefaults: function(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    // Gérer le drop de fichiers
    handleDrop: function(e, input) {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            input.files = files;
            input.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }
};

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Initialiser tous les composants
    CROWDBUILDING.components.initTooltips();
    CROWDBUILDING.components.initPopovers();
    CROWDBUILDING.components.initModals();
    CROWDBUILDING.components.initCurrencyFormatting();
    CROWDBUILDING.components.initPercentageFormatting();
    CROWDBUILDING.components.initDateFormatting();
    CROWDBUILDING.components.initProgressBars();
    CROWDBUILDING.components.initCounters();
    
    // Initialiser les formulaires
    CROWDBUILDING.forms.initRealTimeValidation();
    
    // Initialiser les uploads
    CROWDBUILDING.upload.initDropZones();
    
    // Animation d'apparition des éléments
    const animatedElements = document.querySelectorAll('.fade-in-up');
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    });
    
    animatedElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
    
    // Gestion du scroll pour la navbar
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        let lastScrollTop = 0;
        
        window.addEventListener('scroll', CROWDBUILDING.utils.throttle(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Scroll vers le bas
                navbar.style.transform = 'translateY(-100%)';
            } else {
                // Scroll vers le haut
                navbar.style.transform = 'translateY(0)';
            }
            
            lastScrollTop = scrollTop;
        }, 100));
    }
    
    // Gestion des liens externes
    const externalLinks = document.querySelectorAll('a[href^="http"]');
    externalLinks.forEach(link => {
        link.setAttribute('target', '_blank');
        link.setAttribute('rel', 'noopener noreferrer');
    });
});

// Exposer les utilitaires globalement
window.CROWDBUILDING = CROWDBUILDING;
