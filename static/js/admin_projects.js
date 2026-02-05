alert("ADMIN PROJECTS JS NOUVELLE VERSION CHARGÉE");
// static/js/admin_projects.js
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 admin_projects.js chargé');
    
    // Variables globales
    let currentProjectId = null;
    let currentProjectName = null;

    // Gestion des clics sur les boutons d'action des projets
    document.addEventListener('click', function(e) {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;

    const action = btn.dataset.action;
    const projectId = btn.dataset.projectId;

    if (action === 'valider_projet') {
        validerProjet(projectId, btn);

    } else if (action === 'refuser_projet') {
        ouvrirModalRefusProjet(projectId, btn.dataset.projectName);

    } else if (action === 'partager_projet') {
        partagerProjet(projectId, btn);

    } else if (action === 'suspendre_projet') {
        changerStatutProjet(projectId, 'suspendre', btn);

    } else if (action === 'reactiver_projet') {
        changerStatutProjet(projectId, 'reactiver', btn);
    }
});

    // Soumission du formulaire de refus de projet
    const refuseProjetForm = document.getElementById('refuseProjetForm');
    if (refuseProjetForm) {
        refuseProjetForm.addEventListener('submit', function(e) {
            e.preventDefault();
            refuserProjet(currentProjectId, this);
        });
    }
});

// Fonction pour valider un projet
function validerProjet(projectId, button) {
    if (!confirm('Êtes-vous sûr de vouloir valider ce projet ?')) {
        return;
    }

    showLoading(button);
    
    fetch(`/projects/admin/projet/${projectId}/valider/`, {
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
            // Mettre à jour la ligne du tableau
            updateProjectRow(projectId, data.nouveau_statut, data.statut_color);
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading(button);
        console.error('Error:', error);
        showNotification('error', 'Erreur lors de la validation du projet.');
    });
}

// Fonction pour ouvrir le modal de refus de projet
function ouvrirModalRefusProjet(projectId, projectName) {
    currentProjectId = projectId;
    currentProjectName = projectName;
    
    document.getElementById('refuseProjetName').textContent = projectName;
    document.getElementById('motifRefusProjet').value = '';
    
    const refuseModal = new bootstrap.Modal(document.getElementById('refuseProjetModal'));
    refuseModal.show();
    
    // Focus sur le textarea
    setTimeout(() => {
        document.getElementById('motifRefusProjet').focus();
    }, 500);
}

// Fonction pour refuser un projet
function refuserProjet(projectId, form) {
    const motif = document.getElementById('motifRefusProjet').value.trim();
    
    if (!motif) {
        showNotification('warning', 'Veuillez saisir un motif de refus.');
        return;
    }

    const submitBtn = form.querySelector('button[type="submit"]');
    showLoading(submitBtn);
    
    const formData = new FormData();
    formData.append('motif', motif);
    formData.append('csrfmiddlewaretoken', getCSRFToken());
    
    fetch(`/projects/admin/projet/${projectId}/refuser/`, {
        method: 'POST',
        body: formData,
    })
    .then(response => response.json())
    .then(data => {
        hideLoading(submitBtn);
        
        if (data.success) {
            showNotification('success', data.message);
            // Fermer le modal
            const refuseModal = bootstrap.Modal.getInstance(document.getElementById('refuseProjetModal'));
            refuseModal.hide();
            
            // Mettre à jour la ligne du tableau
            updateProjectRow(projectId, data.nouveau_statut, data.statut_color);
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading(submitBtn);
        console.error('Error:', error);
        showNotification('error', 'Erreur lors du refus du projet.');
    });
}

// Fonction pour partager un projet
function partagerProjet(projectId, button) {
    showLoading(button);
    
    fetch(`/projects/admin/projet/${projectId}/partager/`, {
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
            // Ouvrir les options de partage
            if (data.url) {
                openShareOptions(data.url, data.titre, data.description);
            }
        } else {
            showNotification('error', data.message);
        }
    })
    .catch(error => {
        hideLoading(button);
        console.error('Error:', error);
        showNotification('error', 'Erreur lors du partage du projet.');
    });
}

// Fonction pour mettre à jour la ligne du projet dans le tableau
function updateProjectUI(projectId, data) {
    const row = document.querySelector(`[data-project-id="${projectId}"]`);
    if (!row) return;

    // 🔹 Badge statut
    const badge = row.querySelector(".badge-status");
    badge.textContent = data.statut_label;
    badge.className = `badge badge-status status-${data.statut_color}`;

    // 🔹 Boutons actions
    const actions = row.querySelector(".action-buttons");
    actions.innerHTML = `
        <button class="action-btn btn-view" title="Voir">
            <i class="fas fa-eye"></i>
        </button>
    `;

    if (data.nouveau_statut === "SUSPENDU") {
        actions.innerHTML += `
            <button class="action-btn btn-warning"
                data-action="reactiver_projet"
                data-project-id="${projectId}">
                <i class="fas fa-play"></i>
            </button>
        `;
    } else {
        actions.innerHTML += `
            <button class="action-btn btn-danger"
                data-action="suspendre_projet"
                data-project-id="${projectId}">
                <i class="fas fa-pause"></i>
            </button>
        `;
    }
}

// Fonction pour ouvrir les options de partage
// Fonction pour ouvrir les options de partage
function openShareOptions(url, titre, description) {
    console.log('🔗 URL de partage:', url); // Debug
    
    // Vérifier que l'URL est valide
    if (!url || url.includes('undefined')) {
        showNotification('error', 'Erreur: URL de partage invalide');
        return;
    }
    
    const shareText = encodeURIComponent(`${titre} - ${description}`);
    const shareUrl = encodeURIComponent(url);
    
    // Créer un modal de partage simple
    const shareModalHtml = `
        <div class="modal fade" id="shareModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-primary text-white">
                        <h5 class="modal-title">
                            <i class="fas fa-share-alt me-2"></i>
                            Partager le projet
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            Le projet est maintenant visible sur la plateforme et peut être partagé.
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label fw-bold">Lien de partage :</label>
                            <div class="input-group">
                                <input type="text" class="form-control" value="${url}" id="shareUrl" readonly>
                                <button class="btn btn-outline-primary" type="button" onclick="copyShareUrl()">
                                    <i class="fas fa-copy me-1"></i>Copier
                                </button>
                            </div>
                            <div class="form-text">
                                Partagez ce lien pour permettre aux investisseurs de voir le projet.
                            </div>
                        </div>
                        
                        <div class="mb-3">
                            <label class="form-label fw-bold">Partager sur les réseaux :</label>
                            <div class="share-buttons d-flex gap-2 flex-wrap">
                                <a href="https://www.facebook.com/sharer/sharer.php?u=${shareUrl}" 
                                   target="_blank" 
                                   class="btn btn-primary btn-sm">
                                    <i class="fab fa-facebook me-1"></i>Facebook
                                </a>
                                <a href="https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}" 
                                   target="_blank" 
                                   class="btn btn-info btn-sm">
                                    <i class="fab fa-twitter me-1"></i>Twitter
                                </a>
                                <a href="https://www.linkedin.com/sharing/share-offsite/?url=${shareUrl}" 
                                   target="_blank" 
                                   class="btn btn-secondary btn-sm">
                                    <i class="fab fa-linkedin me-1"></i>LinkedIn
                                </a>
                                <a href="https://wa.me/?text=${shareText}%20${shareUrl}" 
                                   target="_blank" 
                                   class="btn btn-success btn-sm">
                                    <i class="fab fa-whatsapp me-1"></i>WhatsApp
                                </a>
                                <a href="mailto:?subject=${encodeURIComponent(titre)}&body=${shareText}%0A%0A${shareUrl}" 
                                   class="btn btn-danger btn-sm">
                                    <i class="fas fa-envelope me-1"></i>Email
                                </a>
                            </div>
                        </div>
                        
                        <div class="mt-3 p-3 bg-light rounded">
                            <h6 class="fw-bold mb-2">📋 Instructions de partage :</h6>
                            <ul class="small mb-0">
                                <li>Le projet est maintenant <strong>public</strong> sur la plateforme</li>
                                <li>Les investisseurs peuvent visualiser et investir dans le projet</li>
                                <li>Partagez le lien sur vos réseaux pour maximiser la visibilité</li>
                                <li>Surveillez les investissements dans l'interface d'administration</li>
                            </ul>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        <button type="button" class="btn btn-primary" onclick="copyShareUrl()">
                            <i class="fas fa-copy me-1"></i>Copier le lien
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Ajouter le modal au DOM
    document.body.insertAdjacentHTML('beforeend', shareModalHtml);
    
    // Afficher le modal
    const shareModal = new bootstrap.Modal(document.getElementById('shareModal'));
    shareModal.show();
    
    // Sélectionner automatiquement le texte
    setTimeout(() => {
        const shareUrlInput = document.getElementById('shareUrl');
        if (shareUrlInput) {
            shareUrlInput.select();
        }
    }, 500);
    
    // Nettoyer après fermeture
    document.getElementById('shareModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}
// Fonction pour copier l'URL de partage
function copyShareUrl() {
    const shareUrlInput = document.getElementById('shareUrl');
    shareUrlInput.select();
    document.execCommand('copy');
    showNotification('success', 'Lien copié dans le presse-papier !');
}

// Fonctions utilitaires (réutilisées depuis admin_users.js)
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
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert" 
             style="position: fixed; top: 120px; right: 30px; z-index: 9999; min-width: 300px;">
            <div class="d-flex align-items-center">
                <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
                <div class="flex-grow-1">${message}</div>
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', alertHtml);
    
    setTimeout(() => {
        const alert = document.querySelector('.alert');
        if (alert) {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }
    }, 4000);
}

function getCSRFToken() {
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
    return csrfToken ? csrfToken.value : '';
}

function changerStatutProjet(projectId, action, button) {
    if (!confirm(`Confirmer l'action : ${action} ?`)) return;

    showLoading(button);

    fetch(`/projects/admin/projet/${projectId}/${action}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCSRFToken(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(res => res.json())
    .then(data => {
        hideLoading(button);

        if (!data.success) {
            showNotification('error', data.message || 'Erreur serveur');
            return;
        }

        showNotification('success', data.message);

        // 🔥 Mise à jour immédiate du statut (SANS REFRESH)
        updateProjectRow(
            projectId,
            data.statut_label,
            data.statut_color
        );
    })
    .catch(err => {
        hideLoading(button);
        console.error(err);
        showNotification('error', 'Erreur réseau');
    });
}
