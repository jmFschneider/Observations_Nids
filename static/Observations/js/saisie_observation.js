/**
 * Script pour la saisie et modification d'observations
 * Gère les suppressions, remarques, autocomplétion et géolocalisation
 * Version: 3.3 - Confirmation avant remplacement altitude
 */

document.addEventListener('DOMContentLoaded', function() {
    // ===============================================
    // GESTION DES SUPPRESSIONS D'OBSERVATIONS
    // ===============================================
    let deletionCount = 0;

    function updateDeleteBanner() {
        const banner = document.getElementById('delete-confirmation-banner');
        const countElement = document.getElementById('delete-count');
        if (!banner || !countElement) return;

        deletionCount = document.querySelectorAll('.observation-row.marked-for-deletion').length;
        countElement.textContent = deletionCount;

        if (deletionCount > 0) {
            banner.classList.add('show');
        } else {
            banner.classList.remove('show');
        }
    }

    function setupRow(row) {
        const deleteBtn = row.querySelector('.delete-observation-btn');
        const restoreBtn = row.querySelector('.restore-observation-btn');
        const deleteCheckbox = row.querySelector('input[type="checkbox"][name*="-DELETE"]');

        if (!deleteBtn || !restoreBtn || !deleteCheckbox) return;

        // Action for the delete button
        deleteBtn.addEventListener('click', function() {
            deleteCheckbox.checked = true;
            row.classList.add('marked-for-deletion');
            row.querySelectorAll('input, textarea').forEach(el => {
                if (el !== deleteCheckbox) el.disabled = true;
            });
            deleteBtn.style.display = 'none';
            restoreBtn.style.display = 'inline-block';
            updateDeleteBanner();
        });

        // Action for the restore button
        restoreBtn.addEventListener('click', function() {
            deleteCheckbox.checked = false;
            row.classList.remove('marked-for-deletion');
            row.querySelectorAll('input, textarea').forEach(el => {
                el.disabled = false;
            });
            deleteBtn.style.display = 'inline-block';
            restoreBtn.style.display = 'none';
            updateDeleteBanner();
        });
    }

    // Setup all existing rows
    document.querySelectorAll('.observation-row').forEach(setupRow);

    // Setup the "Clear all deletions" button
    const clearAllBtn = document.getElementById('clear-all-deletions');
    if (clearAllBtn) {
        clearAllBtn.addEventListener('click', function(e) {
            e.preventDefault();
            document.querySelectorAll('.observation-row.marked-for-deletion .restore-observation-btn').forEach(btn => {
                btn.click();
            });
        });
    }

    // Add confirmation before submitting the form
    const mainForm = document.querySelector('form[method="post"]:not([action*="logout"])');
    if (mainForm) {
        mainForm.addEventListener('submit', function(e) {
            // Re-enable all disabled fields right before submission so their values are sent
            document.querySelectorAll('.observation-row.marked-for-deletion input, .observation-row.marked-for-deletion textarea').forEach(el => {
                el.disabled = false;
            });

            if (deletionCount > 0) {
                const message = `Voulez-vous vraiment supprimer ${deletionCount} observation${deletionCount > 1 ? 's' : ''} ?`;
                if (!confirm(message)) {
                    e.preventDefault();
                    // If submission is cancelled, re-disable the fields
                    document.querySelectorAll('.observation-row.marked-for-deletion input, .observation-row.marked-for-deletion textarea').forEach(el => {
                        const deleteCheckbox = el.closest('.observation-row').querySelector('input[type="checkbox"][name*="-DELETE"]');
                        if (el !== deleteCheckbox) {
                            el.disabled = true;
                        }
                    });
                    return false;
                }
            }
        });
    }

    // ===============================================
    // GESTION DES REMARQUES (MODAL)
    // ===============================================
    const ficheId = document.querySelector('[data-fiche-id]')?.dataset.ficheId;
    let remarquesData = [];
    let remarqueCounter = 0;

    // Load remarques via AJAX
    function loadRemarquesData() {
        if (!ficheId) {
            remarquesData = [];
            return;
        }

        fetch(window.location.pathname + '?get_remarques=1', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => response.json())
        .then(data => {
            remarquesData = data.remarques || [];
            if (remarquesData.length > 0) {
                remarqueCounter = Math.max(...remarquesData.map(r => r.id)) + 1;
            }
        })
        .catch(error => {
            console.error('Error loading remarques:', error);
            remarquesData = [];
        });
    }

    // Charger les données au démarrage
    loadRemarquesData();

    // Ajouter event listener pour double-clic sur tableau remarques
    const remarquesTable = document.getElementById('remarques-table');
    if (remarquesTable) {
        remarquesTable.addEventListener('dblclick', function(e) {
            if (e.target.closest('.remarque-row-readonly')) {
                openRemarquesModal();
            }
        });
    }

    // Event listener pour le bouton "Ajouter/Modifier"
    document.getElementById('open-remarques-modal-btn')?.addEventListener('click', openRemarquesModal);

    // Event listeners pour les boutons de la popup
    document.getElementById('close-remarques-modal')?.addEventListener('click', closeRemarquesModal);
    document.getElementById('cancel-remarques-btn')?.addEventListener('click', closeRemarquesModal);
    document.getElementById('save-remarques-btn')?.addEventListener('click', saveRemarques);
    document.getElementById('add-remarque-btn')?.addEventListener('click', addRemarqueForm);

    function openRemarquesModal() {
        populateRemarquesModal();
        document.getElementById('remarques-modal').style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Empêcher le scroll de la page
    }

    function closeRemarquesModal() {
        document.getElementById('remarques-modal').style.display = 'none';
        document.body.style.overflow = 'auto'; // Réactiver le scroll
    }

    function populateRemarquesModal() {
        const container = document.getElementById('remarques-formset-container');
        container.innerHTML = '';

        remarquesData.forEach((remarque, index) => {
            if (!remarque.toDelete) {
                const formItem = createRemarqueFormItem(remarque, index);
                container.appendChild(formItem);
            }
        });
    }

    function createRemarqueFormItem(remarque, index) {
        const div = document.createElement('div');
        div.className = 'remarque-form-item';
        div.dataset.remarqueId = remarque.id || 'new';

        div.innerHTML = `
            <div class="form-group">
                <label>Date: ${remarque.date_remarque || 'Nouvelle remarque'}</label>
            </div>
            <div class="form-group">
                <label for="remarque-${index}">Remarque:</label>
                <textarea id="remarque-${index}" name="remarque-${index}" placeholder="Saisissez votre remarque...">${remarque.remarque || ''}</textarea>
            </div>
            ${remarque.id ? `<button type="button" class="delete-btn" data-remarque-id="${remarque.id}">Supprimer</button>` : ''}
        `;

        // Ajouter event listener pour le bouton supprimer
        if (remarque.id) {
            const deleteBtn = div.querySelector('.delete-btn');
            deleteBtn?.addEventListener('click', function() {
                deleteRemarque(remarque.id);
            });
        }

        return div;
    }

    function addRemarqueForm() {
        const newRemarque = {
            id: null,
            remarque: '',
            date_remarque: null,
            toDelete: false
        };
        remarquesData.push(newRemarque);
        populateRemarquesModal();
    }

    function deleteRemarque(remarqueId) {
        const remarque = remarquesData.find(r => r.id === remarqueId);
        if (remarque && confirm('Êtes-vous sûr de vouloir supprimer cette remarque ?')) {
            remarque.toDelete = true;
            populateRemarquesModal();
        }
    }

    function saveRemarques() {
        // Récupérer les données du formulaire
        const formItems = document.querySelectorAll('.remarque-form-item');

        formItems.forEach((item, index) => {
            const textarea = item.querySelector('textarea');
            const remarqueId = item.dataset.remarqueId;

            if (remarqueId === 'new') {
                // Nouvelle remarque
                if (textarea.value.trim()) {
                    const newData = {
                        id: null,
                        remarque: textarea.value.trim(),
                        isNew: true
                    };
                    const newRemarqueIndex = remarquesData.findIndex(r => !r.id && !r.toDelete);
                    if (newRemarqueIndex >= 0) {
                        remarquesData[newRemarqueIndex] = newData;
                    }
                }
            } else {
                // Remarque existante
                const remarque = remarquesData.find(r => r.id == remarqueId);
                if (remarque) {
                    remarque.remarque = textarea.value.trim();
                }
            }
        });

        // Envoyer les données au serveur
        submitRemarquesChanges();
    }

    function submitRemarquesChanges() {
        // Créer les données pour l'envoi AJAX
        const formData = new FormData();

        // Ajouter le token CSRF
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        formData.append('csrfmiddlewaretoken', csrfToken);

        // Ajouter un indicateur que c'est une mise à jour des remarques uniquement
        formData.append('action', 'update_remarques');

        // Préparer toutes les remarques (y compris celles à supprimer)
        const toutesRemarques = remarquesData.filter(r => r.id || (!r.id && r.remarque && r.remarque.trim()));
        const initialRemarques = remarquesData.filter(r => r.id);

        // Ajouter les champs du formset
        formData.append('remarques-TOTAL_FORMS', toutesRemarques.length.toString());
        formData.append('remarques-INITIAL_FORMS', initialRemarques.length.toString());
        formData.append('remarques-MIN_NUM_FORMS', '0');
        formData.append('remarques-MAX_NUM_FORMS', '1000');

        toutesRemarques.forEach((remarque, index) => {
            if (remarque.id) {
                formData.append(`remarques-${index}-id`, remarque.id.toString());
            }
            formData.append(`remarques-${index}-remarque`, remarque.remarque || '');

            if (remarque.toDelete) {
                formData.append(`remarques-${index}-DELETE`, 'on');
            }
        });

        // Envoyer via AJAX
        fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(response => {
            if (response.ok) {
                // Succès - recharger la page pour voir les changements
                window.location.reload();
            } else {
                throw new Error('Erreur lors de la sauvegarde');
            }
        })
        .catch(error => {
            console.error('Error saving remarques:', error);
            alert('Erreur lors de la sauvegarde des remarques. Veuillez réessayer.');
        })
        .finally(() => {
            closeRemarquesModal();
        });
    }

    // ===============================================
    // AUTO-CLEAR DEFAULT VALUES ON FOCUS
    // ===============================================
    const allFields = document.querySelectorAll('input[type="text"], input[type="number"], textarea');

    allFields.forEach(field => {
        const defaultValue = field.value;

        // Vérifier si c'est une valeur par défaut à effacer
        const shouldClearOnFocus = (
            defaultValue === 'Non spécifié' ||
            defaultValue === 'Non spécifiée' ||
            defaultValue === '0' ||
            defaultValue === '0,0' ||
            defaultValue === '00'
        );

        if (shouldClearOnFocus) {
            // Au focus, effacer si c'est toujours la valeur par défaut
            field.addEventListener('focus', function() {
                if (this.value === defaultValue) {
                    this.value = '';
                }
            });

            // Au blur, remettre la valeur par défaut si le champ est vide
            field.addEventListener('blur', function() {
                if (this.value.trim() === '') {
                    this.value = defaultValue;
                }
            });
        }
    });

    // ===============================================
    // AUTOCOMPLÉTION COMMUNE
    // ===============================================
    const communeInput = document.getElementById('id_commune');
    const departementInput = document.getElementById('id_departement');
    const latitudeInput = document.querySelector('input[id*="latitude"]') || document.getElementById('id_latitude');
    const longitudeInput = document.querySelector('input[id*="longitude"]') || document.getElementById('id_longitude');
    const altitudeInput = document.querySelector('input[id*="altitude"]') || document.getElementById('id_altitude');

    // Variables globales pour l'autocomplétion
    let autocompleteList = null;
    let selectedIndex = -1;
    let currentRequest = null;

    // Créer la liste d'autocomplétion
    function createAutocompleteList() {
        if (!autocompleteList && communeInput) {
            autocompleteList = document.createElement('div');
            autocompleteList.className = 'commune-autocomplete-list';
            autocompleteList.style.cssText = `
                position: absolute;
                background: white;
                border: 1px solid #ced4da;
                border-top: none;
                border-radius: 0 0 4px 4px;
                max-height: 250px;
                overflow-y: auto;
                z-index: 1000;
                display: none;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                min-width: 400px;
                white-space: normal;
            `;
            communeInput.parentElement.style.position = 'relative';
            communeInput.parentElement.appendChild(autocompleteList);
        }
        return autocompleteList;
    }

    // Afficher les résultats
    function showResults(communes) {
        const list = createAutocompleteList();
        if (!list) return;

        list.innerHTML = '';
        selectedIndex = -1;

        if (communes.length === 0) {
            list.style.display = 'none';
            return;
        }

        communes.forEach((commune, index) => {
            const item = document.createElement('div');
            item.className = 'commune-autocomplete-item';
            item.style.cssText = `
                padding: 8px 12px;
                cursor: pointer;
                border-bottom: 1px solid #f0f0f0;
            `;
            item.textContent = commune.label;
            item.dataset.index = index;

            // Stocker les données de la commune
            item.dataset.nom = commune.nom;
            item.dataset.departement = commune.departement;
            item.dataset.latitude = commune.latitude;
            item.dataset.longitude = commune.longitude;
            item.dataset.altitude = commune.altitude !== null && commune.altitude !== undefined ? commune.altitude : '';

            item.addEventListener('mouseenter', function() {
                selectItem(index);
            });

            item.addEventListener('click', function() {
                // Vérifier si on a des coordonnées GPS déjà remplies
                const hasGPS = latitudeInput && longitudeInput &&
                              latitudeInput.value && longitudeInput.value &&
                              latitudeInput.value !== '0' && latitudeInput.value !== '0.0';
                selectCommune(commune, hasGPS);
            });

            list.appendChild(item);
        });

        list.style.display = 'block';
    }

    // Sélectionner un élément de la liste
    function selectItem(index) {
        if (!autocompleteList) return;
        const items = autocompleteList.querySelectorAll('.commune-autocomplete-item');
        items.forEach(item => item.style.backgroundColor = '');

        if (index >= 0 && index < items.length) {
            selectedIndex = index;
            items[index].style.backgroundColor = '#f0f0f0';
        }
    }

    // Sélectionner une commune
    function selectCommune(commune, keepGPS = false) {
        if (communeInput) {
            communeInput.value = commune.nom;
        }
        if (departementInput) {
            departementInput.value = commune.departement;
        }

        // Ne modifier lat/lon que si pas de position GPS récente (keepGPS = false)
        if (!keepGPS) {
            if (latitudeInput) {
                latitudeInput.value = commune.latitude;
            }
            if (longitudeInput) {
                longitudeInput.value = commune.longitude;
            }
        }

        // Altitude : utiliser celle de la commune si le champ est vide ou 0
        if (altitudeInput && commune.altitude !== null && commune.altitude !== undefined && commune.altitude !== '') {
            // Convertir en nombre si c'est une chaîne
            const altitudeValue = typeof commune.altitude === 'string' ? parseFloat(commune.altitude) : commune.altitude;

            // Vérifier si le champ actuel est vide, 0, ou une valeur non significative
            const currentValue = altitudeInput.value.trim();
            const currentNumeric = parseFloat(currentValue);
            const shouldUpdate = !currentValue ||
                                currentValue === '' ||
                                currentValue === '0' ||
                                currentValue === '0.0' ||
                                currentValue.match(/^0(\.0+)?m?$/i) || // Match "0", "0.0", "0m", "0.0m"
                                (currentNumeric === 0 || isNaN(currentNumeric));

            if (!isNaN(altitudeValue)) {
                if (shouldUpdate) {
                    // Mise à jour automatique pour valeurs vides ou nulles
                    altitudeInput.value = Math.round(altitudeValue);
                } else {
                    // Demander confirmation si une valeur existe déjà
                    const message = `L'altitude actuelle est ${currentValue}m.\nVoulez-vous la remplacer par ${Math.round(altitudeValue)}m (altitude de ${commune.nom}) ?`;
                    if (confirm(message)) {
                        altitudeInput.value = Math.round(altitudeValue);
                    }
                }
            }
        }

        if (autocompleteList) {
            autocompleteList.style.display = 'none';
        }
    }

    if (communeInput) {

        // Rechercher les communes
        function searchCommunes(query) {
            if (query.length < 2) {
                createAutocompleteList().style.display = 'none';
                return;
            }

            // Annuler la requête précédente
            if (currentRequest) {
                currentRequest.abort();
            }

            currentRequest = new XMLHttpRequest();
            currentRequest.open('GET', '/geo/rechercher-communes/?q=' + encodeURIComponent(query) + '&limit=10', true);

            currentRequest.onload = function() {
                if (currentRequest.status === 200) {
                    const data = JSON.parse(currentRequest.responseText);
                    showResults(data.communes);
                }
            };

            currentRequest.send();
        }

        // Événement input pour la recherche
        communeInput.addEventListener('input', function() {
            searchCommunes(this.value);
        });

        // Navigation au clavier
        communeInput.addEventListener('keydown', function(e) {
            const list = createAutocompleteList();
            const items = list.querySelectorAll('.commune-autocomplete-item');

            if (list.style.display === 'none' || items.length === 0) {
                return;
            }

            switch(e.key) {
                case 'ArrowDown':
                    e.preventDefault();
                    selectItem(Math.min(selectedIndex + 1, items.length - 1));
                    break;
                case 'ArrowUp':
                    e.preventDefault();
                    selectItem(Math.max(selectedIndex - 1, 0));
                    break;
                case 'Enter':
                    e.preventDefault();
                    if (selectedIndex >= 0 && selectedIndex < items.length) {
                        const item = items[selectedIndex];
                        // Vérifier si on a des coordonnées GPS déjà remplies
                        const hasGPS = latitudeInput && longitudeInput &&
                                      latitudeInput.value && longitudeInput.value &&
                                      latitudeInput.value !== '0' && latitudeInput.value !== '0.0';
                        selectCommune({
                            nom: item.dataset.nom,
                            departement: item.dataset.departement,
                            latitude: item.dataset.latitude,
                            longitude: item.dataset.longitude,
                            altitude: item.dataset.altitude,
                            label: item.textContent
                        }, hasGPS);
                    }
                    break;
                case 'Escape':
                    list.style.display = 'none';
                    break;
            }
        });

        // Fermer la liste quand on clique ailleurs
        document.addEventListener('click', function(e) {
            if (e.target !== communeInput && autocompleteList) {
                autocompleteList.style.display = 'none';
            }
        });
    }

    // ===============================================
    // GÉOLOCALISATION GPS
    // ===============================================
    const gpsBtn = document.getElementById('get-gps-btn');
    if (gpsBtn) {
        gpsBtn.addEventListener('click', function() {
            // Vérifier que la géolocalisation est disponible
            if (!navigator.geolocation) {
                alert('La géolocalisation n\'est pas supportée par votre navigateur.');
                return;
            }

            // Changer l'apparence du bouton pendant le chargement
            const originalHTML = gpsBtn.innerHTML;
            gpsBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Localisation...';
            gpsBtn.disabled = true;

            // Récupérer la position
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    // Succès : remplir les champs
                    const lat = position.coords.latitude.toFixed(6);
                    const lon = position.coords.longitude.toFixed(6);

                    if (latitudeInput) {
                        latitudeInput.value = lat;
                    }
                    if (longitudeInput) {
                        longitudeInput.value = lon;
                    }

                    // Récupérer l'altitude si disponible
                    if (position.coords.altitude !== null && position.coords.altitude !== undefined) {
                        const altitude = Math.round(position.coords.altitude);
                        if (altitudeInput && (!altitudeInput.value || altitudeInput.value === '0')) {
                            altitudeInput.value = altitude;
                            console.log(`Altitude GPS: ${altitude} mètres`);
                        }
                    } else {
                        console.log('Altitude GPS non disponible');
                    }

                    // Rechercher les communes proches
                    fetch('/geo/rechercher-communes/?lat=' + lat + '&lon=' + lon + '&limit=15')
                        .then(response => response.json())
                        .then(data => {
                            // Restaurer le bouton
                            gpsBtn.innerHTML = '<i class="fas fa-check"></i> Position récupérée';

                            // Afficher les communes proches si disponibles
                            if (data.communes && data.communes.length > 0) {
                                showResults(data.communes);
                            }

                            setTimeout(function() {
                                gpsBtn.innerHTML = originalHTML;
                                gpsBtn.disabled = false;
                            }, 2000);
                        })
                        .catch(() => {
                            // Restaurer le bouton même en cas d'erreur
                            gpsBtn.innerHTML = '<i class="fas fa-check"></i> Position récupérée';
                            setTimeout(function() {
                                gpsBtn.innerHTML = originalHTML;
                                gpsBtn.disabled = false;
                            }, 2000);
                        });
                },
                function(error) {
                    // Erreur
                    let message = '';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            message = 'Vous avez refusé l\'accès à votre position.';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message = 'Les informations de localisation ne sont pas disponibles.';
                            break;
                        case error.TIMEOUT:
                            message = 'La demande de localisation a expiré.';
                            break;
                        default:
                            message = 'Une erreur inconnue est survenue.';
                    }
                    alert('Erreur de géolocalisation: ' + message);

                    // Restaurer le bouton
                    gpsBtn.innerHTML = originalHTML;
                    gpsBtn.disabled = false;
                },
                {
                    enableHighAccuracy: true,  // Utiliser le GPS si disponible
                    timeout: 10000,            // 10 secondes max
                    maximumAge: 0              // Ne pas utiliser de position en cache
                }
            );
        });
    }
});
