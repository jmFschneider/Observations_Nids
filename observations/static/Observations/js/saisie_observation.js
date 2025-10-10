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
    // Gestion des observations (suppression, etc.)
    // ====================================

    // Code existant pour la gestion des observations...
    // (Vous pouvez ajouter ici le code pour les remarques, GPS, etc.)
});
