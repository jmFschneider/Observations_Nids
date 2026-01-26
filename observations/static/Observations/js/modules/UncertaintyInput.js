/**
 * Gestion de l'incertitude pour les champs numériques
 * Détecte la présence de "?" à la fin de la saisie (ex: "5?" ou "?")
 * et affiche une icône d'avertissement correspondante.
 */
export default function initUncertaintyInput() {
    'use strict';

    /**
     * Gère la détection du "?" dans les champs nombre_oeufs et nombre_poussins
     * et affiche/masque l'icône d'incertitude
     */
    function handleIncertitudeInput(event) {
        const input = event.target;
        const value = input.value.trim();
        
        // Trouver l'icône associée
        const container = input.closest('.nombre-input-container');
        if (!container) return;
        
        const icon = container.querySelector('.incertitude-icon');
        const hiddenField = container.querySelector('input[type="hidden"]');
        
        if (!icon || !hiddenField) return;
        
        // Validation : uniquement chiffres avec "?" optionnel, ou "?" seul
        const validPattern = /^(?:\d+\??|\?)$/;
        const isEmpty = value === '';
        
        // Si la valeur n'est pas vide et n'est pas valide, la nettoyer
        if (!isEmpty && !validPattern.test(value)) {
            // Garder uniquement les chiffres et le dernier "?" s'il y en a un
            const cleaned = value.replace(/[^\d?]/g, '');
            const hasQuestionMark = cleaned.includes('?');
            const digits = cleaned.replace(/\?/g, '');
            input.value = digits + (hasQuestionMark ? '?' : '');
            return; // On sort ici et on laisse l'événement suivant gérer l'icône
        }
        
        // Détection du "?"
        const hasQuestionMark = value.endsWith('?');
        
        // Afficher/masquer l'icône
        icon.style.display = hasQuestionMark ? 'inline-block' : 'none';
        
        // Mettre à jour le champ caché _incertain
        hiddenField.value = hasQuestionMark ? 'on' : '';
    }

    /**
     * Initialise les handlers au chargement de la page
     */
    function initOnPageLoad() {
        // Sélectionner tous les champs concernés (formset dynamique)
        const inputs = document.querySelectorAll('input.nombre-avec-incertitude');
        
        inputs.forEach(input => {
            // Écouter les changements de valeur
            input.addEventListener('input', handleIncertitudeInput);
            input.addEventListener('change', handleIncertitudeInput);
            
            // État initial : vérifier si le champ contient déjà "?"
            const value = input.value.trim();
            if (value.endsWith('?')) {
                const container = input.closest('.nombre-input-container');
                if (container) {
                    const icon = container.querySelector('.incertitude-icon');
                    const hiddenField = container.querySelector('input[type="hidden"]');
                    
                    if (icon) icon.style.display = 'inline-block';
                    if (hiddenField) hiddenField.value = 'on';
                }
            }
        });
    }

    /**
     * Delegation d'événements pour les champs ajoutés dynamiquement
     * (formset observations)
     */
    document.addEventListener('input', function(event) {
        if (event.target.matches('input.nombre-avec-incertitude')) {
            handleIncertitudeInput(event);
        }
    });

    // Initialiser
    initOnPageLoad();
    
    console.log('Module Incertitude initialisé');
}
