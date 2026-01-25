/**
 * Gestion du champ "Heure connue" pour les observations
 * Gère l'interaction entre la case à cocher "Heure connue" et les champs date/heure.
 * Grise le champ heure et le met à 00:00 si l'heure n'est pas connue.
 */
export default function initTimeManager() {
    'use strict';

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
    
    console.log('Module Gestion Date/Heure initialisé');
}
