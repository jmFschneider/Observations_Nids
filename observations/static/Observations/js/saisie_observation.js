/**
 * Script pour améliorer l'expérience de saisie des observations
 * Version: 1.0
 */

document.addEventListener('DOMContentLoaded', function() {
    // ====================================
    // Amélioration du champ Espèce avec recherche intelligente
    // ====================================

    const especeSelect = document.querySelector('.espece-select');
    if (especeSelect) {
        // Convertir le <select> en champ de recherche amélioré
        const wrapper = document.createElement('div');
        wrapper.className = 'espece-search-wrapper';
        wrapper.style.position = 'relative';

        // Créer un champ de texte pour la recherche
        const searchInput = document.createElement('input');
        searchInput.type = 'text';
        searchInput.className = 'form-control espece-search-input';
        searchInput.placeholder = 'Tapez pour rechercher une espèce...';
        searchInput.autocomplete = 'off';

        // Créer une liste déroulante pour les résultats
        const resultsList = document.createElement('div');
        resultsList.className = 'espece-results';
        resultsList.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            max-height: 300px;
            overflow-y: auto;
            background: white;
            border: 1px solid #ced4da;
            border-top: none;
            display: none;
            z-index: 1000;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        // Récupérer toutes les options
        const allOptions = Array.from(especeSelect.options).map(opt => ({
            value: opt.value,
            text: opt.textContent,
            selected: opt.selected
        }));

        // Masquer le select original mais le garder pour la soumission du formulaire
        especeSelect.style.display = 'none';

        // Insérer les nouveaux éléments
        especeSelect.parentNode.insertBefore(wrapper, especeSelect);
        wrapper.appendChild(searchInput);
        wrapper.appendChild(resultsList);
        wrapper.appendChild(especeSelect);

        // Afficher l'espèce sélectionnée dans le champ de recherche
        const selectedOption = allOptions.find(opt => opt.selected);
        if (selectedOption && selectedOption.value) {
            searchInput.value = selectedOption.text;
        }

        let searchTimeout;
        let currentSearchTerm = '';

        // Fonction pour filtrer et afficher les résultats
        function filterAndDisplayResults(searchTerm) {
            currentSearchTerm = searchTerm.toLowerCase();

            if (!currentSearchTerm) {
                resultsList.style.display = 'none';
                return;
            }

            // Filtrer les options (recherche dans le texte complet, pas lettre par lettre)
            const filtered = allOptions.filter(opt => {
                if (!opt.value) return false; // Ignorer l'option vide
                return opt.text.toLowerCase().includes(currentSearchTerm);
            });

            // Afficher les résultats
            if (filtered.length > 0) {
                resultsList.innerHTML = '';
                filtered.forEach(opt => {
                    const resultItem = document.createElement('div');
                    resultItem.className = 'espece-result-item';
                    resultItem.style.cssText = `
                        padding: 8px 12px;
                        cursor: pointer;
                        border-bottom: 1px solid #f0f0f0;
                    `;
                    resultItem.textContent = opt.text;
                    resultItem.dataset.value = opt.value;

                    // Surligner le terme recherché
                    const regex = new RegExp(`(${currentSearchTerm})`, 'gi');
                    resultItem.innerHTML = opt.text.replace(regex, '<strong>$1</strong>');

                    // Au clic, sélectionner cette espèce
                    resultItem.addEventListener('click', function() {
                        selectEspece(opt.value, opt.text);
                    });

                    // Survol
                    resultItem.addEventListener('mouseenter', function() {
                        this.style.backgroundColor = '#e9ecef';
                    });
                    resultItem.addEventListener('mouseleave', function() {
                        this.style.backgroundColor = 'white';
                    });

                    resultsList.appendChild(resultItem);
                });
                resultsList.style.display = 'block';
            } else {
                resultsList.innerHTML = '<div style="padding: 8px 12px; color: #6c757d;">Aucune espèce trouvée</div>';
                resultsList.style.display = 'block';
            }
        }

        // Fonction pour sélectionner une espèce
        function selectEspece(value, text) {
            // Mettre à jour le select original (pour la soumission)
            especeSelect.value = value;

            // Mettre à jour le champ de recherche
            searchInput.value = text;

            // Masquer les résultats
            resultsList.style.display = 'none';
        }

        // Événement de saisie avec délai (debounce)
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value;

            // Annuler le timeout précédent
            clearTimeout(searchTimeout);

            // Attendre 800ms après la dernière frappe avant de filtrer
            searchTimeout = setTimeout(function() {
                filterAndDisplayResults(searchTerm);
            }, 800); // 800ms = 0.8 seconde
        });

        // Focus : afficher tous les résultats si le champ est vide
        searchInput.addEventListener('focus', function() {
            if (!this.value) {
                filterAndDisplayResults('');
            }
        });

        // Clic en dehors : masquer les résultats
        document.addEventListener('click', function(e) {
            if (!wrapper.contains(e.target)) {
                resultsList.style.display = 'none';
            }
        });

        // Navigation au clavier
        searchInput.addEventListener('keydown', function(e) {
            const items = resultsList.querySelectorAll('.espece-result-item');
            const currentFocus = resultsList.querySelector('.espece-result-item.focused');
            let currentIndex = -1;

            if (currentFocus) {
                currentIndex = Array.from(items).indexOf(currentFocus);
            }

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (currentIndex < items.length - 1) {
                    if (currentFocus) currentFocus.classList.remove('focused');
                    items[currentIndex + 1].classList.add('focused');
                    items[currentIndex + 1].style.backgroundColor = '#007bff';
                    items[currentIndex + 1].style.color = 'white';
                    items[currentIndex + 1].scrollIntoView({ block: 'nearest' });
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (currentIndex > 0) {
                    if (currentFocus) {
                        currentFocus.classList.remove('focused');
                        currentFocus.style.backgroundColor = 'white';
                        currentFocus.style.color = 'black';
                    }
                    items[currentIndex - 1].classList.add('focused');
                    items[currentIndex - 1].style.backgroundColor = '#007bff';
                    items[currentIndex - 1].style.color = 'white';
                    items[currentIndex - 1].scrollIntoView({ block: 'nearest' });
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (currentFocus) {
                    const value = currentFocus.dataset.value;
                    const text = currentFocus.textContent;
                    selectEspece(value, text);
                }
            } else if (e.key === 'Escape') {
                resultsList.style.display = 'none';
            }
        });
    }

    // ====================================
    // Autocomplétion des communes
    // ====================================

    const communeInput = document.getElementById('id_commune');
    if (communeInput) {
        let communeTimeout;
        let communeResultsDiv;
        let selectedCommune = null;

        // Créer la div pour les résultats
        communeResultsDiv = document.createElement('div');
        communeResultsDiv.className = 'commune-autocomplete-results';
        communeResultsDiv.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            max-height: 300px;
            overflow-y: auto;
            background: white;
            border: 1px solid #ced4da;
            border-top: none;
            display: none;
            z-index: 1050;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        `;

        // Wrapper pour position relative
        const wrapper = document.createElement('div');
        wrapper.style.position = 'relative';
        wrapper.style.display = 'inline-block';
        wrapper.style.width = '100%';
        communeInput.parentNode.insertBefore(wrapper, communeInput);
        wrapper.appendChild(communeInput);
        wrapper.appendChild(communeResultsDiv);

        // Fonction pour rechercher les communes
        function rechercherCommunes(query) {
            if (query.length < 2) {
                communeResultsDiv.style.display = 'none';
                return;
            }

            // Annuler la recherche précédente
            clearTimeout(communeTimeout);

            // Attendre 300ms après la dernière frappe
            communeTimeout = setTimeout(function() {
                // Récupérer coordonnées GPS si disponibles
                const latInput = document.getElementById('id_latitude');
                const lonInput = document.getElementById('id_longitude');
                const lat = latInput ? latInput.value : '';
                const lon = lonInput ? lonInput.value : '';

                // Construire l'URL
                let url = `/geo/rechercher-communes/?q=${encodeURIComponent(query)}`;
                if (lat && lon) {
                    url += `&lat=${lat}&lon=${lon}`;
                }

                // Appel AJAX
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        afficherResultatsCommunes(data.communes || []);
                    })
                    .catch(error => {
                        console.error('Erreur recherche communes:', error);
                        communeResultsDiv.innerHTML = '<div style="padding: 8px 12px; color: #dc3545;">Erreur lors de la recherche</div>';
                        communeResultsDiv.style.display = 'block';
                    });
            }, 300);
        }

        // Fonction pour afficher les résultats
        function afficherResultatsCommunes(communes) {
            communeResultsDiv.innerHTML = '';

            if (!communes || communes.length === 0) {
                communeResultsDiv.innerHTML = '<div style="padding: 8px 12px; color: #6c757d;">Aucune commune trouvée</div>';
                communeResultsDiv.style.display = 'block';
                return;
            }

            communes.forEach(commune => {
                const item = document.createElement('div');
                item.className = 'commune-result-item';
                item.style.cssText = `
                    padding: 8px 12px;
                    cursor: pointer;
                    border-bottom: 1px solid #f0f0f0;
                `;
                item.textContent = commune.label;
                item.dataset.commune = JSON.stringify(commune);

                // Événements
                item.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    selectionnerCommune(commune);
                });

                item.addEventListener('mouseenter', function() {
                    this.style.backgroundColor = '#e9ecef';
                });

                item.addEventListener('mouseleave', function() {
                    this.style.backgroundColor = 'white';
                });

                communeResultsDiv.appendChild(item);
            });

            communeResultsDiv.style.display = 'block';
        }

        // Fonction pour sélectionner une commune
        function selectionnerCommune(commune) {
            selectedCommune = commune;

            // Remplir le champ commune
            communeInput.value = commune.nom;

            // Remplir automatiquement le département (si vide ou valeur par défaut "00")
            const departementInput = document.getElementById('id_departement');
            if (departementInput && (!departementInput.value || departementInput.value === '' || departementInput.value === '00')) {
                departementInput.value = commune.departement;
            }

            // Remplir les coordonnées GPS si vides ou valeurs par défaut (0, 0.0)
            const latInput = document.getElementById('id_latitude');
            const lonInput = document.getElementById('id_longitude');
            if (latInput && lonInput) {
                const latValue = latInput.value;
                const lonValue = lonInput.value;
                // Considérer comme vide si: vide, "0", "0.0", "0.00", etc.
                const isLatEmpty = !latValue || latValue === '' || parseFloat(latValue) === 0;
                const isLonEmpty = !lonValue || lonValue === '' || parseFloat(lonValue) === 0;

                if (isLatEmpty && commune.latitude) {
                    latInput.value = commune.latitude;
                }
                if (isLonEmpty && commune.longitude) {
                    lonInput.value = commune.longitude;
                }
            }

            // Remplir l'altitude si vide ou valeur par défaut (0)
            const altitudeInput = document.getElementById('id_altitude');
            if (altitudeInput && commune.altitude) {
                const currentAltitude = altitudeInput.value;
                // Considérer comme vide si: vide, "0", "0.0", "0.00", etc.
                const isAltEmpty = !currentAltitude || currentAltitude === '' || parseFloat(currentAltitude) === 0;

                if (isAltEmpty) {
                    if (confirm(`Utiliser l'altitude de la commune ${commune.nom} : ${commune.altitude}m ?`)) {
                        altitudeInput.value = commune.altitude;
                    }
                }
            }

            // Masquer les résultats
            communeResultsDiv.style.display = 'none';
        }

        // Événement de saisie
        communeInput.addEventListener('input', function() {
            const query = this.value.trim();
            rechercherCommunes(query);
        });

        // Focus : ne rien faire (pas comme pour les espèces)
        communeInput.addEventListener('focus', function() {
            // Ne rien afficher au focus, seulement à la saisie
        });

        // Clic en dehors : masquer les résultats
        document.addEventListener('click', function(e) {
            if (!wrapper.contains(e.target)) {
                communeResultsDiv.style.display = 'none';
            }
        });

        // Navigation au clavier
        communeInput.addEventListener('keydown', function(e) {
            const items = communeResultsDiv.querySelectorAll('.commune-result-item');
            const currentFocus = communeResultsDiv.querySelector('.commune-result-item.focused');
            let currentIndex = -1;

            if (currentFocus) {
                currentIndex = Array.from(items).indexOf(currentFocus);
            }

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                if (currentIndex < items.length - 1) {
                    if (currentFocus) {
                        currentFocus.classList.remove('focused');
                        currentFocus.style.backgroundColor = 'white';
                    }
                    items[currentIndex + 1].classList.add('focused');
                    items[currentIndex + 1].style.backgroundColor = '#007bff';
                    items[currentIndex + 1].style.color = 'white';
                    items[currentIndex + 1].scrollIntoView({ block: 'nearest' });
                }
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (currentIndex > 0) {
                    if (currentFocus) {
                        currentFocus.classList.remove('focused');
                        currentFocus.style.backgroundColor = 'white';
                        currentFocus.style.color = 'black';
                    }
                    items[currentIndex - 1].classList.add('focused');
                    items[currentIndex - 1].style.backgroundColor = '#007bff';
                    items[currentIndex - 1].style.color = 'white';
                    items[currentIndex - 1].scrollIntoView({ block: 'nearest' });
                }
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (currentFocus) {
                    const communeData = JSON.parse(currentFocus.dataset.commune);
                    selectionnerCommune(communeData);
                }
            } else if (e.key === 'Escape') {
                communeResultsDiv.style.display = 'none';
            }
        });
    }

    // ====================================
    // Gestion des observations (suppression, etc.)
    // ====================================

    // Code existant pour la gestion des observations...
    // (Vous pouvez ajouter ici le code pour les remarques, GPS, etc.)

    // ====================================
    // Gestion des remarques (modal)
    // ====================================

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

    // ====================================
    // Géolocalisation GPS
    // ====================================

    const getGpsBtn = document.getElementById('get-gps-btn');
    if (getGpsBtn) {
        getGpsBtn.addEventListener('click', function() {
            if (!navigator.geolocation) {
                alert('La géolocalisation n\'est pas supportée par votre navigateur');
                return;
            }

            // Afficher un indicateur de chargement
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Localisation...';
            this.disabled = true;

            navigator.geolocation.getCurrentPosition(
                // Succès
                function(position) {
                    const lat = position.coords.latitude.toFixed(6);
                    const lon = position.coords.longitude.toFixed(6);

                    // Remplir les champs
                    const latInput = document.getElementById('id_latitude');
                    const lonInput = document.getElementById('id_longitude');

                    if (latInput && lonInput) {
                        latInput.value = lat;
                        lonInput.value = lon;
                        alert(`Position GPS récupérée:\nLatitude: ${lat}\nLongitude: ${lon}`);
                    }

                    // Restaurer le bouton
                    getGpsBtn.innerHTML = originalText;
                    getGpsBtn.disabled = false;
                },
                // Erreur
                function(error) {
                    let message = 'Erreur lors de la récupération de la position';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            message = 'Permission refusée pour accéder à votre position';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message = 'Position non disponible';
                            break;
                        case error.TIMEOUT:
                            message = 'Délai d\'attente dépassé';
                            break;
                    }
                    alert(message);

                    // Restaurer le bouton
                    getGpsBtn.innerHTML = originalText;
                    getGpsBtn.disabled = false;
                }
            );
        });
    }
});
