/**
 * Point d'entrée principal pour le script de saisie d'observation.
 * Orchestre les différents modules ES6.
 */

import initUncertaintyInput from './modules/UncertaintyInput.js';
import initGeolocation from './modules/GeolocationManager.js';
import initTimeManager from './modules/TimeManager.js';
import initSpeciesSearch from './modules/SpeciesSearch.js';
import initCommuneAutocomplete from './modules/CommuneAutocomplete.js';
import initObservationRowsManager from './modules/ObservationRowsManager.js';
import initFormChangeManager from './modules/FormChangeManager.js';
import initRemarksManager from './modules/RemarksManager.js';
import initObserverCorrectionManager from './modules/ObserverCorrectionManager.js';

// Forcer un rechargement réseau si Firefox restaure la page depuis le bfcache
// (cas typique : retour arrière après une fusion d'observateur)
window.addEventListener('pageshow', function(event) {
    if (event.persisted) {
        window.location.reload();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation séquentielle des modules
    
    // UI de base & Champs spéciaux
    initUncertaintyInput();
    initTimeManager();
    
    // Géo & Localisation
    initGeolocation();
    initCommuneAutocomplete();
    
    // Formulaires & Champs de recherche
    initSpeciesSearch();
    initObserverCorrectionManager();
    initObservationRowsManager();
    
    // Modales & Gestion d'état
    initRemarksManager();
    initFormChangeManager();

    console.log('Orchestrateur Saisie Observation initialisé');
});