/**
 * Gestion de la correction des observateurs
 * Permet de corriger les noms issus de l'OCR, rechercher des observateurs similaires,
 * en créer de nouveaux ou fusionner des doublons.
 */
export default function initObserverCorrectionManager() {
    'use strict';

    // Variables du module
    let observateurActuelId = null;
    let observateurActuelNom = null;
    let observateurCible = null;
    let ficheCouranteId = null;
    let nomOcrOriginal = null;
    let nomSaisiCorrect = '';

    // Elements DOM
    const modalObservateur = document.getElementById('modalRechercheObservateur');
    const modalConfirmation = document.getElementById('modalConfirmationFusion');
    const btnRechercher = document.getElementById('btn-rechercher-observateur');
    const btnVoirSuggestions = document.getElementById('btn-voir-suggestions');
    const inputSaisieNom = document.getElementById('saisie-nom-correct');
    const btnValiderNom = document.getElementById('btn-valider-nom');
    const btnCreerObservateur = document.getElementById('btn-creer-observateur');
    const sectionCreerObservateur = document.getElementById('section-creer-observateur');
    const alerteTranscription = document.getElementById('alerte-observateur-transcription');

    // Si les elements n'existent pas, ne pas initialiser
    if (!modalObservateur) {
        console.log('Module correction observateurs: modale non trouvee, initialisation annulee');
        return;
    }

    console.log('Module correction observateurs: initialisation...');

    // Recuperer l'ID de la fiche
    const ficheIdDiv = document.querySelector('[data-fiche-id]');
    if (ficheIdDiv) {
        ficheCouranteId = ficheIdDiv.dataset.ficheId;
    }

    // Recuperer l'observateur actuel depuis le select
    const selectObservateur = document.getElementById('id_observateur');
    if (selectObservateur) {
        observateurActuelId = selectObservateur.value;
        const selectedOption = selectObservateur.options[selectObservateur.selectedIndex];
        observateurActuelNom = selectedOption ? selectedOption.text : '';
    }

    // === Indicateur d'étape active ===
    var sectionsEtapes = [
        'section-contexte',
        'suggestions-automatiques',
        'section-saisie',
        'resultats-recherche-observateur',
        'section-creer-observateur'
    ];

    function setEtapeActive(num) {
        sectionsEtapes.forEach(function(id) {
            var el = document.getElementById(id);
            if (el) el.classList.remove('etape-active');
        });
        var activeId = sectionsEtapes[num - 1];
        if (activeId) {
            var activeEl = document.getElementById(activeId);
            if (activeEl) activeEl.classList.add('etape-active');
        }
    }

    // === Utilitaire d'echappement HTML ===
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // === Detection automatique au chargement ===
    function verifierObservateurTranscription() {
        if (!observateurActuelId || !alerteTranscription) return;

        // Appel API pour verifier si suggestions disponibles
        fetch('/api/observateurs/similaires/?observateur_id=' + observateurActuelId + '&seuil=0.8', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function(response) {
            if (!response.ok) return null;
            return response.json();
        })
        .then(function(data) {
            if (data && data.observateur_actuel && data.observateur_actuel.est_transcription &&
                data.suggestions && data.suggestions.length > 0) {
                // Afficher l'alerte
                alerteTranscription.style.display = 'block';
            }
        })
        .catch(function(error) {
            console.error('Erreur verification observateur:', error);
        });
    }

    // === Charger le nom OCR depuis le JSON ===
    function chargerNomOcr() {
        const nomOcrElement = document.getElementById('nom-ocr-original');
        if (!ficheCouranteId) {
            nomOcrElement.innerHTML = '<span class="text-muted">Fiche non enregistree</span>';
            return;
        }

        fetch('/api/observateurs/nom-ocr/?fiche_id=' + ficheCouranteId, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success && data.nom_ocr) {
                nomOcrOriginal = data.nom_ocr;
                nomOcrElement.innerHTML = '<strong>' + escapeHtml(data.nom_ocr) + '</strong>';
                // Pre-remplir le champ de saisie avec le nom OCR
                if (inputSaisieNom && !inputSaisieNom.value) {
                    inputSaisieNom.value = data.nom_ocr;
                }
            } else {
                nomOcrElement.innerHTML = '<span class="text-muted"><i class="fas fa-info-circle"></i> Pas de fichier JSON</span>';
            }
        })
        .catch(function(error) {
            console.error('Erreur chargement nom OCR:', error);
            nomOcrElement.innerHTML = '<span class="text-danger">Erreur de chargement</span>';
        });
    }

    // === Ouverture modale ===
    function ouvrirModalObservateur() {
        if (!modalObservateur) return;

        // Afficher info observateur actuel
        document.getElementById('nom-observateur-actuel').innerHTML = '<strong>' + escapeHtml(observateurActuelNom) + '</strong>';

        // Étape 1 active à l'ouverture
        setEtapeActive(1);

        // Charger le nom OCR depuis le JSON
        chargerNomOcr();

        // Charger les suggestions automatiques
        chargerSuggestionsAutomatiques();

        // Reinitialiser l interface
        if (sectionCreerObservateur) sectionCreerObservateur.style.display = 'none';
        const tbody = document.getElementById('tbody-observateurs');
        if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Tapez un nom ci-dessus pour rechercher</td></tr>';

        // Afficher la modale
        modalObservateur.style.display = 'flex';
        modalObservateur.style.alignItems = 'center';
        modalObservateur.style.justifyContent = 'center';
        document.body.style.overflow = 'hidden';

        // Fermer en cliquant sur le fond (mais pas sur le contenu)
        modalObservateur.onclick = function(e) {
            if (e.target === modalObservateur) {
                window.fermerModalObservateur();
            }
        };

        // Focus sur le champ de saisie
        if (inputSaisieNom) {
            setTimeout(function() { inputSaisieNom.focus(); }, 100);
        }
    }

    // Fonctions globales pour le HTML
    window.fermerModalObservateur = function() {
        if (modalObservateur) {
            modalObservateur.style.display = 'none';
        }
        document.body.style.overflow = '';
    };

    window.fermerModalConfirmation = function() {
        if (modalConfirmation) {
            modalConfirmation.style.display = 'none';
        }
        document.body.style.overflow = '';
    };

    // === Chargement suggestions automatiques ===
    function chargerSuggestionsAutomatiques() {
        if (!observateurActuelId) return;

        fetch('/api/observateurs/similaires/?observateur_id=' + observateurActuelId + '&seuil=0.8', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            const container = document.getElementById('liste-suggestions-auto');
            const section = document.getElementById('suggestions-automatiques');

            if (data.success && data.suggestions && data.suggestions.length > 0) {
                section.style.display = 'block';
                setEtapeActive(2); // Des suggestions existent → attirer l'attention dessus
                container.innerHTML = data.suggestions.map(function(obs) {
                    var scorePercent = Math.round(obs.score_similarite * 100);
                    var badgeClass = scorePercent >= 90 ? '-subtle text-primary-emphasis' : '-subtle text-primary-emphasis';
                    return '<div class="card mb-2">' + 
                        '<div class="card-body py-2 d-flex justify-content-between align-items-center">' + 
                        '<div>' + 
                        '<strong>' + escapeHtml(obs.nom_complet) + '</strong> ' + 
                        '<span class="badge ' + badgeClass + ' ms-2">' + scorePercent + '%</span>' + 
                        '<br><small class="text-muted">' + obs.nombre_fiches + ' fiche(s)</small>' + 
                        '</div>' + 
                        '<button type="button" class="btn btn-sm btn-primary" onclick="selectionnerObservateur(' + 
                        obs.id + ', \'' + escapeHtml(obs.nom_complet).replace(/'/g, "\'") + '\', ' + obs.nombre_fiches + ')">' + 
                        'Selectionner</button>' + 
                        '</div></div>';
                }).join('');

                // Stats observateur actuel
                if (data.observateur_actuel) {
                    var typeObs = data.observateur_actuel.est_transcription ? 'Transcription OCR' : 'Compte valide';
                    document.getElementById('stats-observateur-actuel').textContent =
                        data.observateur_actuel.nombre_fiches + ' fiche(s) - ' + typeObs;
                }
            } else {
                section.style.display = 'none';
                setEtapeActive(3); // Pas de suggestions → guider vers la saisie
                if (data && data.observateur_actuel) {
                    var typeObs2 = data.observateur_actuel.est_transcription ? 'Transcription OCR' : 'Compte valide';
                    document.getElementById('stats-observateur-actuel').textContent =
                        data.observateur_actuel.nombre_fiches + ' fiche(s) - ' + typeObs2;
                }
            }
        })
        .catch(function(error) {
            console.error('Erreur chargement suggestions:', error);
        });
    }

    // === Recherche manuelle avec debounce ===
    var rechercheTimeout = null;
    var derniereRecherche = '';

    function rechercherObservateurs(query) {
        var tbody = document.getElementById('tbody-observateurs');
        nomSaisiCorrect = query;

        if (query.length < 2) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Tapez au moins 2 caracteres</td></tr>';
            if (sectionCreerObservateur) sectionCreerObservateur.style.display = 'none';
            return;
        }

        // Afficher indicateur de chargement
        tbody.innerHTML = '<tr><td colspan="5" class="text-center"><i class="fas fa-spinner fa-spin"></i> Recherche...</td></tr>';

        clearTimeout(rechercheTimeout);
        rechercheTimeout = setTimeout(function() {
            derniereRecherche = query;
            var url = '/api/observateurs/rechercher/?q=' + encodeURIComponent(query);
            if (observateurActuelId) {
                url += '&reference_id=' + observateurActuelId;
            }

            fetch(url, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            })
            .then(function(response) {
                return response.json();
            })
            .then(function(data) {
                afficherResultatsRecherche(data.observateurs || [], query);
            })
            .catch(function(error) {
                console.error('Erreur recherche observateurs:', error);
                tbody.innerHTML = '<tr><td colspan="5" class="text-center text-danger">Erreur lors de la recherche</td></tr>';
            });
        }, 300); // Debounce 300ms
    }

    function afficherResultatsRecherche(observateurs, queryOriginal) {
        var tbody = document.getElementById('tbody-observateurs');

        if (!observateurs || observateurs.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Aucun resultat</td></tr>';
            // Afficher l option de creer un nouvel observateur
            if (sectionCreerObservateur && queryOriginal && queryOriginal.length >= 2) {
                document.getElementById('nom-a-creer').textContent = '"' + queryOriginal + '"';
                sectionCreerObservateur.style.display = 'block';
                setEtapeActive(5); // Aucun résultat → guider vers la création
            }
            return;
        }

        // Cacher l option de creation si des resultats existent
        if (sectionCreerObservateur) sectionCreerObservateur.style.display = 'none';
        setEtapeActive(4); // Des résultats trouvés → guider vers la sélection

        tbody.innerHTML = observateurs.map(function(obs) {
            var similarite = '-';
            if (obs.score_similarite !== null) {
                var scorePercent = Math.round(obs.score_similarite * 100);
                var badgeClass = scorePercent >= 80 ? '-subtle text-primary-emphasis' : '';
                similarite = '<span class="badge ' + badgeClass + '">' + scorePercent + '%</span>';
            }

            var type = obs.est_transcription ?
                '<span class="badge -subtle text-primary-emphasis">OCR</span>' :
                '<span class="badge -subtle text-primary-emphasis">Valide</span>';

            return '<tr>' +
                '<td><strong>' + escapeHtml(obs.nom_complet) + '</strong></td>' +
                '<td>' + similarite + '</td>' +
                '<td>' + type + '</td>' +
                '<td>' + obs.nombre_fiches + '</td>' +
                '<td>' +
                '<button type="button" class="btn btn-sm btn-success" onclick="selectionnerObservateur(' +
                obs.id + ', \'' + escapeHtml(obs.nom_complet).replace(/'/g, "\'") + '\', ' + obs.nombre_fiches + ')">' +
                '<i class="fas fa-check"></i></button>' +
                '</td></tr>';
        }).join('');
    }

    // === Valider le nom saisi (bouton Proposer la création) ===
    function validerNomSaisi() {
        var nomSaisi = inputSaisieNom ? inputSaisieNom.value.trim() : '';
        if (nomSaisi.length < 2) {
            alert('Le nom doit contenir au moins 2 caracteres');
            return;
        }

        var tbody = document.getElementById('tbody-observateurs');
        var hasResults = tbody && tbody.querySelectorAll('tr td button').length > 0;

        if (sectionCreerObservateur) {
            document.getElementById('nom-a-creer').textContent = '"' + nomSaisi + '"';

            // Adapter le message selon qu'il existe ou non des résultats similaires
            var avertissement = document.getElementById('avertissement-similaires');
            var titre = document.getElementById('titre-section-creer');
            if (hasResults) {
                if (titre) titre.textContent = 'Créer malgré des résultats similaires ?';
                if (avertissement) avertissement.style.display = 'block';
            } else {
                if (titre) titre.textContent = 'Aucun observateur correspondant trouvé';
                if (avertissement) avertissement.style.display = 'none';
            }

            sectionCreerObservateur.style.display = 'block';
            setEtapeActive(5);
        }
    }

    // === Creer un nouvel observateur ===
    function creerNouvelObservateur() {
        var nomACreer = inputSaisieNom ? inputSaisieNom.value.trim() : '';
        if (nomACreer.length < 2) {
            alert('Le nom doit contenir au moins 2 caracteres');
            return;
        }

        // Desactiver le bouton pendant le traitement
        if (btnCreerObservateur) {
            btnCreerObservateur.disabled = true;
            btnCreerObservateur.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creation...';
        }

        var formData = new FormData();
        formData.append('nom', nomACreer);

        // Recuperer le CSRF token
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken.value);
        }

        fetch('/api/observateurs/creer/', {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success && data.observateur) {
                // Selectionner automatiquement le nouvel observateur
                window.selectionnerObservateur(
                    data.observateur.id,
                    data.observateur.nom_complet,
                    0
                );
            } else {
                alert('Erreur: ' + (data.message || 'Impossible de creer l observateur'));
                if (btnCreerObservateur) {
                    btnCreerObservateur.disabled = false;
                    btnCreerObservateur.innerHTML = '<i class="fas fa-plus"></i> Creer cet observateur';
                }
            }
        })
        .catch(function(error) {
            console.error('Erreur creation observateur:', error);
            alert('Une erreur est survenue lors de la creation');
            if (btnCreerObservateur) {
                btnCreerObservateur.disabled = false;
                btnCreerObservateur.innerHTML = '<i class="fas fa-plus"></i> Creer cet observateur';
            }
        });
    }

    // === Selection et confirmation fusion ===
    window.selectionnerObservateur = function(id, nom, nombreFiches) {
        observateurCible = { id: id, nom: nom, nombreFiches: nombreFiches };

        // Fermer modale recherche
        window.fermerModalObservateur();

        // Afficher modale confirmation
        document.getElementById('message-fusion').innerHTML =
            'Voulez-vous remplacer <strong>' + escapeHtml(observateurActuelNom) +
            '</strong> par <strong>' + escapeHtml(nom) + '</strong> ?';

        // Recuperer le nombre de fiches de l ancien observateur
        fetch('/api/observateurs/similaires/?observateur_id=' + observateurActuelId, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success && data.observateur_actuel) {
                document.getElementById('nombre-fiches-fusion').textContent = data.observateur_actuel.nombre_fiches;
            }
        });

        // Afficher la modale de confirmation
        modalConfirmation.style.display = 'flex';
        modalConfirmation.style.alignItems = 'center';
        modalConfirmation.style.justifyContent = 'center';
        document.body.style.overflow = 'hidden';
    };

    // === Execution de la fusion ===
    function executerFusion() {
        var typeFusion = document.querySelector('input[name="type-fusion"]:checked').value;
        var fusionnerToutes = typeFusion === 'toutes';

        var formData = new FormData();
        formData.append('ancien_observateur_id', observateurActuelId);
        formData.append('nouvel_observateur_id', observateurCible.id);
        formData.append('fiche_id', ficheCouranteId);
        formData.append('fusionner_toutes', fusionnerToutes);

        // Recuperer le CSRF token
        var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfToken) {
            formData.append('csrfmiddlewaretoken', csrfToken.value);
        }

        // Desactiver le bouton pendant le traitement
        var btnConfirmer = document.getElementById('btn-confirmer-fusion');
        var originalText = btnConfirmer.innerHTML;
        btnConfirmer.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Traitement...';
        btnConfirmer.disabled = true;

        fetch('/api/observateurs/fusionner/', {
            method: 'POST',
            headers: { 'X-Requested-With': 'XMLHttpRequest' },
            body: formData
        })
        .then(function(response) {
            return response.json();
        })
        .then(function(data) {
            if (data.success) {
                alert(data.message);
                // Recharger la page pour refleter les changements
                location.reload();
            } else {
                alert('Erreur: ' + data.message);
                btnConfirmer.innerHTML = originalText;
                btnConfirmer.disabled = false;
            }
        })
        .catch(function(error) {
            console.error('Erreur fusion:', error);
            alert('Une erreur est survenue lors de la fusion');
            btnConfirmer.innerHTML = originalText;
            btnConfirmer.disabled = false;
        })
        .finally(function() {
            window.fermerModalConfirmation();
        });
    }

    // === Initialisation des evenements ===
    if (btnRechercher) {
        btnRechercher.addEventListener('click', ouvrirModalObservateur);
    }

    if (btnVoirSuggestions) {
        btnVoirSuggestions.addEventListener('click', ouvrirModalObservateur);
    }

    // Recherche en temps reel pendant la saisie
    if (inputSaisieNom) {
        inputSaisieNom.addEventListener('input', function() {
            setEtapeActive(3);
            rechercherObservateurs(this.value.trim());
        });
    }

    // Bouton Valider
    if (btnValiderNom) {
        btnValiderNom.addEventListener('click', validerNomSaisi);
    }

    // Bouton Creer observateur
    if (btnCreerObservateur) {
        btnCreerObservateur.addEventListener('click', creerNouvelObservateur);
    }

    var btnConfirmerFusion = document.getElementById('btn-confirmer-fusion');
    if (btnConfirmerFusion) {
        btnConfirmerFusion.addEventListener('click', executerFusion);
    }

    // Verification au chargement
    verifierObservateurTranscription();

    console.log('Module Correction Observateur initialisé');
}
