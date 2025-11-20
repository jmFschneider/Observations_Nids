/**
 * Script pour améliorer l'expérience de saisie des observations
 * Version: 1.0
 */

document.addEventListener('DOMContentLoaded', function() {
    // ====================================
    // Détection des modifications du formulaire
    // ====================================

    let formInitialState = {};
    let hasUnsavedChanges = false;

    // Fonction pour capturer l'état initial du formulaire PRINCIPAL
    function captureFormInitialState() {
        const mainForm = document.querySelector('form[method="post"]:not([action*="logout"])');
        if (!mainForm) return;

        formInitialState = {};

        // Capturer tous les champs input, textarea et select du formulaire PRINCIPAL
        const formElements = mainForm.querySelectorAll('input, textarea, select');
        formElements.forEach(element => {
            const name = element.name;
            if (!name) return;

            // Ignorer les champs de management form du formset (ils changent dynamiquement)
            if (name.includes('TOTAL_FORMS') || name.includes('INITIAL_FORMS')) return;

            if (element.type === 'checkbox') {
                formInitialState[name] = element.checked;
            } else if (element.type === 'radio') {
                if (element.checked) {
                    formInitialState[name] = element.value;
                }
            } else {
                formInitialState[name] = element.value;
            }
        });
    }

    // Fonction pour vérifier si le formulaire a des modifications
    function checkForUnsavedChanges() {
        const mainForm = document.querySelector('form[method="post"]:not([action*="logout"])');
        if (!mainForm) return false;

        const formElements = mainForm.querySelectorAll('input, textarea, select');
        let hasChanges = false;

        formElements.forEach(element => {
            const name = element.name;
            if (!name) return;

            // Ignorer les champs de management form
            if (name.includes('TOTAL_FORMS') || name.includes('INITIAL_FORMS')) return;

            let currentValue;
            if (element.type === 'checkbox') {
                currentValue = element.checked;
            } else if (element.type === 'radio') {
                if (element.checked) {
                    currentValue = element.value;
                }
            } else {
                currentValue = element.value;
            }

            // Comparer avec l'état initial
            if (formInitialState[name] !== currentValue) {
                hasChanges = true;
            }
        });

        return hasChanges;
    }

    // Capturer l'état initial au chargement
    captureFormInitialState();

    // Surveiller les changements sur le formulaire PRINCIPAL
    const mainForm = document.querySelector('form[method="post"]:not([action*="logout"])');
    if (mainForm) {
        mainForm.addEventListener('change', function() {
            hasUnsavedChanges = checkForUnsavedChanges();
        });

        mainForm.addEventListener('input', function() {
            hasUnsavedChanges = checkForUnsavedChanges();
        });
    }

    // Note: Cette fonction n'est plus utilisée directement, remplacée par l'approche globale ci-dessous
    // Conservée pour référence historique uniquement

    // ========================================
    // APPROCHE GLOBALE : Intercepter TOUS les clics sur les liens et boutons
    // qui pourraient naviguer hors de la page
    // ========================================

    document.addEventListener('click', function(event) {
        // Vérifier si le clic provient d'un lien <a> ou d'un bouton qui navigue
        let target = event.target;

        // Remonter jusqu'à trouver un lien <a>
        while (target && target.tagName !== 'A' && target.tagName !== 'BUTTON') {
            target = target.parentElement;
        }

        if (!target) return; // Pas de lien ou bouton trouvé

        // Liste des liens/boutons à intercepter (qui causent une navigation)
        const shouldCheckChanges = (
            // Lien "Ajouter une observation"
            (target.id === 'ajouter-observation-link') ||
            (target.href && target.href.includes('ajouter_observation')) ||
            // Bouton "Ajouter/Modifier remarques"
            (target.id === 'open-remarques-modal-btn') ||
            // Attribut data-check-changes explicite
            (target.dataset && target.dataset.checkChanges === 'true')
        );

        if (!shouldCheckChanges) return; // Ce lien/bouton n'est pas concerné

        // Vérifier s'il y a des modifications
        const hasChanges = checkForUnsavedChanges();

        if (!hasChanges) {
            return; // Pas de modifications, laisser la navigation se faire
        }

        // Il y a des modifications - bloquer et demander confirmation
        event.preventDefault();
        event.stopPropagation();

        const linkText = target.textContent.trim();
        const userChoice = confirm(
            `Vous avez des modifications non sauvegardées sur cette fiche.\n\n` +
            `Voulez-vous sauvegarder avant de continuer vers "${linkText}" ?\n\n` +
            `• Cliquez sur OK pour sauvegarder puis continuer\n` +
            `• Cliquez sur Annuler pour continuer SANS sauvegarder (les modifications seront perdues)`
        );

        if (userChoice) {
            // L'utilisateur veut sauvegarder
            const form = document.querySelector('form[method="post"]:not([action*="logout"])');
            if (form) {
                // Si c'est un lien avec href, rediriger après sauvegarde
                if (target.href) {
                    const redirectInput = document.createElement('input');
                    redirectInput.type = 'hidden';
                    redirectInput.name = 'redirect_after_save';
                    redirectInput.value = target.href;
                    form.appendChild(redirectInput);
                }
                // Si c'est le bouton remarques, rouvrir la modal après sauvegarde
                else if (target.id === 'open-remarques-modal-btn') {
                    const reopenModalInput = document.createElement('input');
                    reopenModalInput.type = 'hidden';
                    reopenModalInput.name = 'reopen_remarques_modal';
                    reopenModalInput.value = '1';
                    form.appendChild(reopenModalInput);
                }

                form.submit();
            }
        } else {
            // L'utilisateur ne veut PAS sauvegarder
            if (target.href) {
                window.location.href = target.href;
            } else if (target.id === 'open-remarques-modal-btn') {
                // Ouvrir la modal des remarques sans sauvegarder
                const tempFlag = window._skipChangeCheck;
                window._skipChangeCheck = true;
                target.click();
                window._skipChangeCheck = tempFlag;
            }
        }
    }, true); // useCapture = true pour capturer l'événement en phase de capture

    // Réinitialiser l'état après sauvegarde réussie
    if (mainForm) {
        mainForm.addEventListener('submit', function() {
            // Après soumission, on considère qu'il n'y a plus de modifications non sauvegardées
            hasUnsavedChanges = false;
        });
    }

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
    // Note: mainForm est déjà déclaré au début du script
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

                        // Afficher automatiquement les communes à proximité
                        const communeInput = document.getElementById('id_commune');
                        if (communeInput) {
                            // Si le champ est vide, on affiche un message encourageant à taper
                            if (!communeInput.value.trim()) {
                                alert(`Position GPS récupérée:\nLatitude: ${lat}\nLongitude: ${lon}\n\nVous pouvez maintenant taper dans le champ "Commune".\nLes résultats seront automatiquement filtrés dans un rayon de 10 km.`);
                                // Mettre le focus sur le champ commune
                                communeInput.focus();
                            } else {
                                // Si le champ contient déjà du texte, relancer la recherche
                                alert(`Position GPS récupérée:\nLatitude: ${lat}\nLongitude: ${lon}\n\nMise à jour de la liste des communes (rayon 10 km)...`);
                                const event = new Event('input', { bubbles: true });
                                communeInput.dispatchEvent(event);
                            }
                        } else {
                            alert(`Position GPS récupérée:\nLatitude: ${lat}\nLongitude: ${lon}`);
                        }
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

    // ====================================
    // Gestion du champ "Heure connue" pour les observations
    // ====================================

    // Fonction pour obtenir/définir uniquement la date (sans heure) d'un datetime-local
    function getDateOnly(datetimeValue) {
        if (!datetimeValue) return '';
        return datetimeValue.split('T')[0];
    }

    function setTimeToMidnight(timeInput) {
        if (timeInput) {
            timeInput.value = '00:00';
        }
    }

    // Fonction pour basculer le style de l'heure selon l'état de la checkbox
    function toggleTimeStyle(observationRow, isTimeKnown) {
        const dateTimeContainer = observationRow.querySelector('.date-time-container');

        if (dateTimeContainer) {
            if (isTimeKnown) {
                dateTimeContainer.classList.remove('time-unknown');
            } else {
                dateTimeContainer.classList.add('time-unknown');
            }
        }
    }

    // Fonction pour initialiser les gestionnaires d'événements pour une ligne d'observation
    function initHeureConnueHandlers(observationRow) {
        // Éviter d'initialiser deux fois la même ligne
        if (observationRow.dataset.heureConnueInitialized === 'true') {
            return;
        }

        const prefix = observationRow.dataset.formPrefix;
        if (!prefix) return;

        // IMPORTANT: Avec SplitDateTimeWidget, Django crée deux inputs séparés
        const dateInput = observationRow.querySelector(`input[name="${prefix}-date_observation_0"]`);
        const timeInput = observationRow.querySelector(`input[name="${prefix}-date_observation_1"]`);
        const heureCheckbox = observationRow.querySelector(`input[name="${prefix}-heure_connue"]`);

        if (!dateInput || !timeInput || !heureCheckbox) return;

        // Marquer comme initialisé
        observationRow.dataset.heureConnueInitialized = 'true';

        // Utiliser l'attribut data-heure-connue de la row pour l'initialisation
        // Cela garantit que le style correspond à la valeur en BDD
        const heureConnueData = observationRow.dataset.heureConnue;
        const isTimeKnown = heureConnueData === 'true' || heureCheckbox.checked;

        // Initialisation : appliquer le style selon la valeur de heure_connue
        if (!isTimeKnown) {
            if (timeInput.value) {
                setTimeToMidnight(timeInput);
            }
            toggleTimeStyle(observationRow, false);
        } else {
            toggleTimeStyle(observationRow, true);
        }

        // Gestionnaire pour la checkbox
        heureCheckbox.addEventListener('change', function() {
            if (!this.checked) {
                // Si décoché, mettre l'heure à 00:00 et griser
                setTimeToMidnight(timeInput);
                toggleTimeStyle(observationRow, false);
            } else {
                // Si coché, enlever le grisage
                toggleTimeStyle(observationRow, true);
            }
        });

        // Gestionnaire pour le champ heure
        timeInput.addEventListener('change', function() {
            const timeValue = this.value;
            if (!timeValue) return;

            // Si l'utilisateur a saisi une heure différente de 00:00, cocher la checkbox
            if (timeValue !== '00:00') {
                heureCheckbox.checked = true;
                toggleTimeStyle(observationRow, true);
            }
        });

        // Aussi surveiller l'input en temps réel (pour les modifications manuelles)
        timeInput.addEventListener('input', function() {
            const timeValue = this.value;
            if (!timeValue) return;

            // Si l'utilisateur modifie l'heure manuellement et que ce n'est pas 00:00
            if (timeValue && timeValue !== '00:00') {
                heureCheckbox.checked = true;
                toggleTimeStyle(observationRow, true);
            }
        });
    }

    // Initialiser tous les gestionnaires pour les lignes d'observation existantes
    const observationRows = document.querySelectorAll('.observation-row');

    observationRows.forEach((row) => {
        initHeureConnueHandlers(row);
    });

    // Observer les changements dans le DOM pour gérer les nouvelles lignes ajoutées dynamiquement
    const observationsTable = document.querySelector('.observations-table tbody');
    if (observationsTable) {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1 && node.classList.contains('observation-row')) {
                        initHeureConnueHandlers(node);
                    }
                });
            });
        });

        observer.observe(observationsTable, {
            childList: true,
            subtree: true
        });
    }
});
