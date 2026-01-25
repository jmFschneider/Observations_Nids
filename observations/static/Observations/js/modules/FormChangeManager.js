/**
 * Gestion des modifications du formulaire
 * Détecte les changements non sauvegardés et avertit l'utilisateur
 * s'il tente de quitter la page ou de naviguer ailleurs.
 */
export default function initFormChangeManager() {
    'use strict';

    let formInitialState = {};
    let hasUnsavedChanges = false;
    
    // Référence au formulaire principal
    const mainForm = document.querySelector('form[method="post"]:not([action*="logout"])');

    // Fonction pour capturer l'état initial du formulaire PRINCIPAL
    function captureFormInitialState() {
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
    if (mainForm) {
        mainForm.addEventListener('change', function() {
            hasUnsavedChanges = checkForUnsavedChanges();
        });

        mainForm.addEventListener('input', function() {
            hasUnsavedChanges = checkForUnsavedChanges();
        });
        
        // Réinitialiser l'état après sauvegarde réussie
        mainForm.addEventListener('submit', function() {
            // Après soumission, on considère qu'il n'y a plus de modifications non sauvegardées
            hasUnsavedChanges = false;
        });
    }

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
        const isSpecialSubmit = (
            target.tagName === 'BUTTON' && 
            target.type === 'submit' && 
            target.hasAttribute('formaction') && 
            (target.getAttribute('formaction').includes('soumettre') || target.getAttribute('formaction').includes('valider'))
        );

        const shouldCheckChanges = (
            // Lien "Ajouter une observation"
            (target.id === 'ajouter-observation-link') ||
            (target.href && target.href.includes('ajouter_observation')) ||
            // Bouton "Ajouter/Modifier remarques"
            (target.id === 'open-remarques-modal-btn') ||
            // Boutons de soumission/validation (statut)
            isSpecialSubmit ||
            // Attribut data-check-changes explicite
            (target.dataset && target.dataset.checkChanges === 'true')
        );

        if (!shouldCheckChanges) return; // Ce lien/bouton n'est pas concerné

        // Vérifier s'il y a des modifications
        const hasChanges = checkForUnsavedChanges();

        if (!hasChanges) {
            return; // Pas de modifications, laisser l'action se faire
        }

        // Il y a des modifications - bloquer et demander confirmation
        event.preventDefault();
        event.stopPropagation();

        if (isSpecialSubmit) {
            alert(
                `ATTENTION : Vous avez des modifications non sauvegardées.\n\n` +
                `Vous devez cliquer sur le bouton "Enregistrer" avant de pouvoir ` +
                `${target.textContent.trim().toLowerCase()}.\n\n` +
                `Vos modifications actuelles ne sont pas encore enregistrées en base de données.`
            );
            return;
        }

        const linkText = target.textContent.trim();
        const userChoice = confirm(
            `Vous avez des modifications non sauvegardées sur cette fiche.\n\n` +
            `Voulez-vous sauvegarder avant de continuer vers "${linkText}" ?\n\n` +
            `• Cliquez sur OK pour sauvegarder puis continuer\n` +
            `• Cliquez sur Annuler pour continuer SANS sauvegarder (les modifications seront perdues)`
        );

        if (userChoice) {
            // ... (reste du code inchangé)
            const form = document.querySelector('form[method="post"]:not([action*="logout"])');
            if (form) {
                if (target.href) {
                    const redirectInput = document.createElement('input');
                    redirectInput.type = 'hidden';
                    redirectInput.name = 'redirect_after_save';
                    redirectInput.value = target.href;
                    form.appendChild(redirectInput);
                } else if (target.id === 'open-remarques-modal-btn') {
                    const reopenModalInput = document.createElement('input');
                    reopenModalInput.type = 'hidden';
                    reopenModalInput.name = 'reopen_remarques_modal';
                    reopenModalInput.value = '1';
                    form.appendChild(reopenModalInput);
                }
                form.submit();
            }
        } else {
            if (target.href) {
                window.location.href = target.href;
            } else if (target.id === 'open-remarques-modal-btn') {
                window._skipChangeCheck = true;
                target.click();
                window._skipChangeCheck = false;
            }
        }
    }, true);

    // Gérer les clics sur les boutons de soumission spéciale (avec data-confirm-message)
    // même s'il n'y a PAS de modifications non sauvegardées.
    // On utilise un autre listener en phase de bubbling (false) pour ne pas entrer en conflit avec le capture précédent
    document.addEventListener('click', function(event) {
        let target = event.target;
        while (target && target.tagName !== 'BUTTON') {
            target = target.parentElement;
        }
        if (!target) return;

        const confirmMessage = target.dataset.confirmMessage;
        if (confirmMessage && target.type === 'submit') {
            // Vérifier s'il y a des modifs (déjà géré par le listener précédent en capture)
            // Si le listener précédent a bloqué (preventDefault), on ne sera pas ici.
            // Si on est ici, c'est qu'il n'y a pas de modifs non sauvegardées.
            
            if (!confirm(confirmMessage)) {
                event.preventDefault();
            }
        }
    });
    
    console.log('Module Gestion Formulaire initialisé');
}

