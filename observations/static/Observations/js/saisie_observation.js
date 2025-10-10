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
});
