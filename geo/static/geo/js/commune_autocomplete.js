/**
 * Autocomplétion pour le champ "Commune actuelle" (fusion de communes)
 * Utilise l'API /geo/rechercher-communes/ existante
 */

(function() {
    'use strict';

    // Configuration
    const CONFIG = {
        minChars: 2,
        debounceDelay: 300,
        maxResults: 10,
    };

    let debounceTimer = null;
    let currentFocus = -1;
    let communesList = [];

    /**
     * Initialise l'autocomplétion sur un champ
     */
    function initAutocomplete(inputId, hiddenId, initialName = '') {
        const input = document.getElementById(inputId);
        const hidden = document.getElementById(hiddenId);

        if (!input || !hidden) {
            console.error('Champs autocomplétion non trouvés:', inputId, hiddenId);
            return;
        }

        // Afficher le nom initial si disponible
        if (initialName) {
            input.value = initialName;
        }

        // Créer le conteneur des résultats
        const resultsContainer = createResultsContainer(input);

        // Écouteur sur la saisie
        input.addEventListener('input', function(e) {
            const query = this.value.trim();

            // Effacer le champ caché si l'utilisateur modifie le texte
            if (hidden.value && this.value !== input.dataset.selectedName) {
                hidden.value = '';
                input.dataset.selectedName = '';
            }

            // Recherche seulement si assez de caractères
            if (query.length < CONFIG.minChars) {
                hideResults(resultsContainer);
                return;
            }

            // Debounce : attendre que l'utilisateur arrête de taper
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(() => {
                searchCommunes(query, input, hidden, resultsContainer);
            }, CONFIG.debounceDelay);
        });

        // Gestion des touches clavier
        input.addEventListener('keydown', function(e) {
            const items = resultsContainer.querySelectorAll('.autocomplete-item');

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                currentFocus++;
                addActive(items);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                currentFocus--;
                addActive(items);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (currentFocus > -1 && items[currentFocus]) {
                    items[currentFocus].click();
                }
            } else if (e.key === 'Escape') {
                hideResults(resultsContainer);
            }
        });

        // Fermer si clic en dehors
        document.addEventListener('click', function(e) {
            if (!input.contains(e.target) && !resultsContainer.contains(e.target)) {
                hideResults(resultsContainer);
            }
        });
    }

    /**
     * Crée le conteneur des résultats d'autocomplétion
     */
    function createResultsContainer(input) {
        const container = document.createElement('div');
        container.className = 'autocomplete-results';
        container.style.display = 'none';
        input.parentNode.style.position = 'relative';
        input.parentNode.appendChild(container);
        return container;
    }

    /**
     * Recherche les communes via l'API
     */
    function searchCommunes(query, input, hidden, resultsContainer) {
        const url = `/geo/rechercher-communes/?q=${encodeURIComponent(query)}&limit=${CONFIG.maxResults}`;

        fetch(url)
            .then(response => response.json())
            .then(data => {
                communesList = data.communes || [];
                displayResults(communesList, input, hidden, resultsContainer);
            })
            .catch(error => {
                console.error('Erreur recherche communes:', error);
                hideResults(resultsContainer);
            });
    }

    /**
     * Affiche les résultats de la recherche
     */
    function displayResults(communes, input, hidden, resultsContainer) {
        resultsContainer.innerHTML = '';
        currentFocus = -1;

        if (communes.length === 0) {
            const noResult = document.createElement('div');
            noResult.className = 'autocomplete-item autocomplete-no-result';
            noResult.textContent = 'Aucune commune trouvée';
            resultsContainer.appendChild(noResult);
            resultsContainer.style.display = 'block';
            return;
        }

        communes.forEach((commune, index) => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.dataset.id = commune.id || '';
            item.dataset.name = commune.nom;

            // Contenu de l'item
            const nameSpan = document.createElement('strong');
            nameSpan.textContent = commune.nom;

            const detailsSpan = document.createElement('span');
            detailsSpan.className = 'autocomplete-details';
            detailsSpan.textContent = ` (${commune.code_departement}) - ${commune.departement}`;

            item.appendChild(nameSpan);
            item.appendChild(detailsSpan);

            // Clic sur un résultat
            item.addEventListener('click', function() {
                selectCommune(commune, input, hidden, resultsContainer);
            });

            resultsContainer.appendChild(item);
        });

        resultsContainer.style.display = 'block';
    }

    /**
     * Sélectionne une commune
     */
    function selectCommune(commune, input, hidden, resultsContainer) {
        // Remplir le champ de recherche avec le nom
        input.value = commune.nom;
        input.dataset.selectedName = commune.nom;

        // Remplir le champ caché avec l'ID
        hidden.value = commune.id || '';

        // Afficher un message de confirmation
        const info = document.getElementById('commune-actuelle-info');
        if (info) {
            info.innerHTML = `<div class="alert alert-success mt-2">
                <i class="fas fa-check-circle"></i>
                Commune sélectionnée : <strong>${commune.nom}</strong> (${commune.code_departement}) - ID: ${commune.id}
            </div>`;
        }

        hideResults(resultsContainer);
    }

    /**
     * Ajoute la classe active à un élément
     */
    function addActive(items) {
        if (!items || items.length === 0) return;

        removeActive(items);

        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;

        items[currentFocus].classList.add('autocomplete-active');
    }

    /**
     * Retire la classe active de tous les éléments
     */
    function removeActive(items) {
        items.forEach(item => item.classList.remove('autocomplete-active'));
    }

    /**
     * Cache les résultats
     */
    function hideResults(resultsContainer) {
        resultsContainer.style.display = 'none';
        currentFocus = -1;
    }

    // Initialisation au chargement du DOM
    document.addEventListener('DOMContentLoaded', function() {
        // Récupérer le nom initial si présent
        const initialId = document.getElementById('commune_actuelle_id')?.value;
        const initialName = document.getElementById('commune_actuelle_name_hidden')?.value || '';

        initAutocomplete('commune_actuelle_search', 'commune_actuelle_id', initialName);
    });

})();
