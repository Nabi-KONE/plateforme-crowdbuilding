// static/js/admin_users.js
document.addEventListener('DOMContentLoaded', function() {
    // Éléments DOM
    const searchInput = document.getElementById('searchInput');
    const statutFilter = document.getElementById('statutFilter');
    const roleFilter = document.getElementById('roleFilter');
    const searchButton = document.getElementById('searchButton');
    
    // Variables pour les modals
    let currentUserId = null;
    let currentUserName = null;

    // Fonction pour effectuer la recherche
    function performSearch() {
        const searchQuery = searchInput ? searchInput.value : '';
        const statut = statutFilter ? statutFilter.value : '';
        const role = roleFilter ? roleFilter.value : '';
        
        // Construire l'URL avec les paramètres
        const params = new URLSearchParams();
        if (searchQuery) params.append('search', searchQuery);
        if (statut) params.append('statut', statut);
        if (role) params.append('role', role);
        
        // Rediriger vers la même page avec les paramètres
        const currentUrl = window.location.pathname;
        window.location.href = currentUrl + '?' + params.toString();
    }

    // Recherche instantanée avec debounce
    if (searchInput) {
        searchInput.addEventListener('keyup', debounce(function() {
            performSearch();
        }, 500));
    }

    // Bouton de recherche
    if (searchButton) {
        searchButton.addEventListener('click', function() {
            performSearch();
        });
    }

    // Filtres
    if (statutFilter) {
        statutFilter.addEventListener('change', function() {
            performSearch();
        });
    }

    if (roleFilter) {
        roleFilter.addEventListener('change', function() {
            performSearch();
        });
    }

    // Fonction debounce personnalisée (au cas où CROWDBUILDING.utils n'existe pas)
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Gestion des actions (valider, refuser, suspendre)
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.action-btn');
        if (!btn) return;

        const action = btn.dataset.action;
        const userId = btn.dataset.userId;
        const userName = btn.dataset.userName;

        if (action === 'valider') {
            validerUtilisateur(userId, btn);
        } else if (action === 'refuser') {
            ouvrirModalRefus(userId, userName);
        } else if (action === 'suspendre') {
            ouvrirModalSuspension(userId, userName);
        }
    });

    // Soumission du formulaire de refus
    const refuseForm = document.getElementById('refuseForm');
    if (refuseForm) {
        refuseForm.addEventListener('submit', function(e) {
            e.preventDefault();
            refuserUtilisateur(currentUserId, this);
        });
    }

    // Soumission du formulaire de suspension
    const suspendForm = document.getElementById('suspendForm');
    if (suspendForm) {
        suspendForm.addEventListener('submit', function(e) {
            e.preventDefault();
            suspendreUtilisateur(currentUserId, this);
        });
    }

    // Fonction pour valider un utilisateur
    function validerUtilisateur(userId, button) {
        if (!confirm('Êtes-vous sûr de vouloir valider ce compte ?')) {
            return;
        }

        showLoading(button);
        
        fetch(`/accounts/admin/users/${userId}/validate/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCSRFToken(),
            },
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(button);
            
            if (data.success) {
                showNotification('success', data.message);
                // Recharger la page après un délai
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification('error', data.message);
            }
        })
        .catch(error => {
            hideLoading(button);
            console.error('Error:', error);
            showNotification('error', 'Erreur lors de la validation du compte.');
        });
    }

    // Fonction pour ouvrir le modal de refus
    function ouvrirModalRefus(userId, userName) {
        currentUserId = userId;
        currentUserName = userName;
        
        document.getElementById('refuseUserName').textContent = userName;
        document.getElementById('motifRefus').value = '';
        
        const refuseModal = new bootstrap.Modal(document.getElementById('refuseModal'));
        refuseModal.show();
        
        // Focus sur le textarea
        setTimeout(() => {
            document.getElementById('motifRefus').focus();
        }, 500);
    }

    // Fonction pour refuser un utilisateur
    function refuserUtilisateur(userId, form) {
        const motif = document.getElementById('motifRefus').value.trim();
        
        if (!motif) {
            showNotification('warning', 'Veuillez saisir un motif de refus.');
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        showLoading(submitBtn);
        
        const formData = new FormData();
        formData.append('motif', motif);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        fetch(`/accounts/admin/users/${userId}/reject/`, {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(submitBtn);
            
            if (data.success) {
                showNotification('success', data.message);
                // Fermer le modal
                const refuseModal = bootstrap.Modal.getInstance(document.getElementById('refuseModal'));
                refuseModal.hide();
                
                // Recharger la page après un délai
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification('error', data.message);
            }
        })
        .catch(error => {
            hideLoading(submitBtn);
            console.error('Error:', error);
            showNotification('error', 'Erreur lors du refus du compte.');
        });
    }

    // Fonction pour ouvrir le modal de suspension
    function ouvrirModalSuspension(userId, userName) {
        currentUserId = userId;
        currentUserName = userName;
        
        document.getElementById('suspendUserName').textContent = userName;
        document.getElementById('motifSuspend').value = '';
        
        const suspendModal = new bootstrap.Modal(document.getElementById('suspendModal'));
        suspendModal.show();
        
        // Focus sur le textarea
        setTimeout(() => {
            document.getElementById('motifSuspend').focus();
        }, 500);
    }

    // Fonction pour suspendre un utilisateur
    function suspendreUtilisateur(userId, form) {
        const motif = document.getElementById('motifSuspend').value.trim();
        
        if (!motif) {
            showNotification('warning', 'Veuillez saisir un motif de suspension.');
            return;
        }

        const submitBtn = form.querySelector('button[type="submit"]');
        showLoading(submitBtn);
        
        const formData = new FormData();
        formData.append('motif', motif);
        formData.append('csrfmiddlewaretoken', getCSRFToken());
        
        fetch(`/accounts/admin/users/${userId}/suspend/`, {
            method: 'POST',
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            hideLoading(submitBtn);
            
            if (data.success) {
                showNotification('success', data.message);
                // Fermer le modal
                const suspendModal = bootstrap.Modal.getInstance(document.getElementById('suspendModal'));
                suspendModal.hide();
                
                // Recharger la page après un délai
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                showNotification('error', data.message);
            }
        })
        .catch(error => {
            hideLoading(submitBtn);
            console.error('Error:', error);
            showNotification('error', 'Erreur lors de la suspension du compte.');
        });
    }

    // Fonctions utilitaires
    function showLoading(element) {
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
            const originalText = element.innerHTML;
            element.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            element.dataset.originalText = originalText;
        }
    }

    function hideLoading(element) {
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
            if (element.dataset.originalText) {
                element.innerHTML = element.dataset.originalText;
            }
        }
    }

    function showNotification(type, message) {
        // Créer une alerte Bootstrap simple
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // Insérer l'alerte en haut de la page
        const container = document.querySelector('.container-fluid');
        if (container) {
            container.insertAdjacentHTML('afterbegin', alertHtml);
            
            // Auto-supprimer après 5 secondes
            setTimeout(() => {
                const alert = document.querySelector('.alert');
                if (alert) {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                }
            }, 5000);
        }
    }

    function getCSRFToken() {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        return csrfToken ? csrfToken.value : '';
    }

    // Auto-focus sur le champ de recherche au chargement
    if (searchInput) {
        searchInput.focus();
    }

    // Gestion de la fermeture des modals
    document.addEventListener('hidden.bs.modal', function (event) {
        if (event.target.id === 'refuseModal' || event.target.id === 'suspendModal') {
            currentUserId = null;
            currentUserName = null;
        }
    });
});