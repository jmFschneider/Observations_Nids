/**
 * Gestion des remarques
 * Gère l'affichage, l'ajout, la suppression et la sauvegarde des remarques
 * via une fenêtre modale AJAX.
 */
export default function initRemarksManager() {
    'use strict';

    const openRemarquesModalBtn = document.getElementById('open-remarques-modal-btn');
    const remarquesModal = document.getElementById('remarques-modal');
    const closeRemarquesModalBtn = document.getElementById('close-remarques-modal');
    const cancelRemarquesBtn = document.getElementById('cancel-remarques-btn');
    const saveRemarquesBtn = document.getElementById('save-remarques-btn');
    const addRemarqueBtn = document.getElementById('add-remarque-btn');
    const remarquesFormsetContainer = document.getElementById('remarques-formset-container');

    let remarquesData = [];
    let remarqueCounter = 0;

    // Ouvrir le modal
    if (openRemarquesModalBtn) {
        openRemarquesModalBtn.addEventListener('click', function() {
            // Charger les remarques existantes via AJAX
            const ficheIdDiv = document.querySelector('[data-fiche-id]');
            if (ficheIdDiv) {
                const ficheId = ficheIdDiv.dataset.ficheId;
                chargerRemarques(ficheId);
            }
            remarquesModal.style.display = 'flex';
        });
    }

    // Fermer le modal
    if (closeRemarquesModalBtn) {
        closeRemarquesModalBtn.addEventListener('click', function() {
            remarquesModal.style.display = 'none';
        });
    }

    if (cancelRemarquesBtn) {
        cancelRemarquesBtn.addEventListener('click', function() {
            remarquesModal.style.display = 'none';
        });
    }

    // Clic en dehors du modal pour fermer
    if (remarquesModal) {
        remarquesModal.addEventListener('click', function(e) {
            if (e.target === remarquesModal) {
                remarquesModal.style.display = 'none';
            }
        });
    }

    // Fonction pour charger les remarques via AJAX
    function chargerRemarques(ficheId) {
        fetch(`/observations/modifier/${ficheId}/?get_remarques=1`, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            remarquesData = data.remarques || [];
            remarqueCounter = remarquesData.length;
            afficherRemarquesDansModal();
        })
        .catch(error => {
            console.error('Erreur lors du chargement des remarques:', error);
            alert('Erreur lors du chargement des remarques');
        });
    }

    // Exposer une fonction globale pour ouvrir la modale des remarques
    // (utilisée pour la réouverture automatique après sauvegarde)
    window.ouvrirModalRemarques = function() {
        const ficheIdDiv = document.querySelector('[data-fiche-id]');
        if (ficheIdDiv && remarquesModal) {
            const ficheId = ficheIdDiv.dataset.ficheId;
            chargerRemarques(ficheId);
            remarquesModal.style.display = 'flex';
        }
    };

    // Fonction pour afficher les remarques dans le modal
    function afficherRemarquesDansModal() {
        remarquesFormsetContainer.innerHTML = '';

        remarquesData.forEach((remarque, index) => {
            const remarqueDiv = creerRemarqueFormItem(remarque, index);
            remarquesFormsetContainer.appendChild(remarqueDiv);
        });
    }

    // Fonction pour créer un item de formulaire de remarque
    function creerRemarqueFormItem(remarque, index) {
        const div = document.createElement('div');
        div.className = 'remarque-form-item';
        div.dataset.remarqueIndex = index;
        div.dataset.remarqueId = remarque.id || '';

        const dateInfo = remarque.date_remarque ? `<p class="remarques-info">Date: ${remarque.date_remarque}</p>` : '';

        div.innerHTML = `
            ${dateInfo}
            <div class="form-group">
                <label>Remarque:</label>
                <textarea class="remarque-textarea" data-index="${index}">${remarque.remarque || ''}</textarea>
            </div>
            <button type="button" class="delete-btn delete-remarque-btn" data-index="${index}">
                ${remarque.id ? 'Supprimer' : 'Retirer'}
            </button>
        `;

        // Événement de suppression
        const deleteBtn = div.querySelector('.delete-remarque-btn');
        deleteBtn.addEventListener('click', function() {
            const idx = parseInt(this.dataset.index);
            if (remarquesData[idx].id) {
                // Marquer pour suppression
                remarquesData[idx].toDelete = !remarquesData[idx].toDelete;
                if (remarquesData[idx].toDelete) {
                    div.style.opacity = '0.5';
                    div.style.textDecoration = 'line-through';
                    this.textContent = 'Annuler suppression';
                    this.style.backgroundColor = '#28a745';
                } else {
                    div.style.opacity = '1';
                    div.style.textDecoration = 'none';
                    this.textContent = 'Supprimer';
                    this.style.backgroundColor = '#dc3545';
                }
            } else {
                // Retirer de la liste (nouvelle remarque non sauvegardée)
                remarquesData.splice(idx, 1);
                afficherRemarquesDansModal();
            }
        });

        // Événement de modification du texte
        const textarea = div.querySelector('.remarque-textarea');
        textarea.addEventListener('input', function() {
            const idx = parseInt(this.dataset.index);
            remarquesData[idx].remarque = this.value;
        });

        return div;
    }

    // Ajouter une nouvelle remarque
    if (addRemarqueBtn) {
        addRemarqueBtn.addEventListener('click', function() {
            const nouvelleRemarque = {
                id: null,
                remarque: '',
                date_remarque: null,
                toDelete: false
            };
            remarquesData.push(nouvelleRemarque);
            afficherRemarquesDansModal();
        });
    }

    // Sauvegarder les remarques
    if (saveRemarquesBtn) {
        saveRemarquesBtn.addEventListener('click', function() {
            const ficheIdDiv = document.querySelector('[data-fiche-id]');
            if (!ficheIdDiv) {
                alert('Erreur: ID de fiche non trouvé');
                return;
            }

            const ficheId = ficheIdDiv.dataset.ficheId;
            sauvegarderRemarques(ficheId);
        });
    }

    // Fonction pour sauvegarder les remarques via AJAX
    function sauvegarderRemarques(ficheId) {
        // Préparer les données du formset
        const formData = new FormData();
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);
        formData.append('action', 'update_remarques');

        // Management form - IMPORTANT: utiliser le préfixe 'remarques' pour le formset
        formData.append('remarques-TOTAL_FORMS', remarquesData.length);
        formData.append('remarques-INITIAL_FORMS', remarquesData.filter(r => r.id).length);
        formData.append('remarques-MIN_NUM_FORMS', '0');
        formData.append('remarques-MAX_NUM_FORMS', '1000');

        // Ajouter chaque remarque
        remarquesData.forEach((remarque, index) => {
            if (remarque.id) {
                formData.append(`remarques-${index}-id`, remarque.id);
            }
            formData.append(`remarques-${index}-remarque`, remarque.remarque || '');
            formData.append(`remarques-${index}-DELETE`, remarque.toDelete ? 'on' : '');
        });

        // Envoyer via AJAX
        fetch(`/observations/modifier/${ficheId}/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert('Remarques sauvegardées avec succès');
                remarquesModal.style.display = 'none';
                // Recharger la page pour afficher les remarques mises à jour
                location.reload();
            } else {
                alert('Erreur lors de la sauvegarde: ' + (data.message || 'Erreur inconnue'));
            }
        })
        .catch(error => {
            console.error('Erreur lors de la sauvegarde:', error);
            alert('Erreur lors de la sauvegarde des remarques');
        });
    }
    
    console.log('Module Gestion Remarques initialisé');
}
