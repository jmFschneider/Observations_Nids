// Fonction qui calcule la distance de Levenshtein entre deux chaînes
function levenshteinDistance(str1, str2) {
    if (str1.length === 0) return str2.length;
    if (str2.length === 0) return str1.length;

    const matrix = [];

    // Initialisation de la matrice
    for (let i = 0; i <= str2.length; i++) {
        matrix[i] = [i];
    }
    for (let j = 0; j <= str1.length; j++) {
        matrix[0][j] = j;
    }

    // Remplissage de la matrice
    for (let i = 1; i <= str2.length; i++) {
        for (let j = 1; j <= str1.length; j++) {
            const cost = str1[j - 1] === str2[i - 1] ? 0 : 1;
            matrix[i][j] = Math.min(
                matrix[i - 1][j] + 1,      // suppression
                matrix[i][j - 1] + 1,      // insertion
                matrix[i - 1][j - 1] + cost // substitution
            );
        }
    }

    return matrix[str2.length][str1.length];
}

// Calcule le pourcentage de similarité entre deux chaînes
function similarityPercentage(str1, str2) {
    const maxLength = Math.max(str1.length, str2.length);
    if (maxLength === 0) return 100; // Les deux chaînes sont vides

    const distance = levenshteinDistance(str1, str2);
    return Math.round(((maxLength - distance) / maxLength) * 100);
}

// Normalisation des chaînes pour la comparaison
function normalizeString(str) {
    return str.toLowerCase()
        .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // Enlever les accents
        .replace(/[^\w\s]/gi, ''); // Enlever la ponctuation
}

// Fonction qui trouve les meilleures correspondances d'espèces
function findBestMatches(transcribedName, options, threshold = 70, maxResults = 5) {
    const normalizedTranscribed = normalizeString(transcribedName);

    // Calcul des scores pour toutes les options
    const scores = [];
    for (let i = 0; i < options.length; i++) {
        const optionText = options[i].text;
        const normalizedOption = normalizeString(optionText);

        const similarity = similarityPercentage(normalizedTranscribed, normalizedOption);

        scores.push({
            index: i,
            value: options[i].value,
            text: optionText,
            similarity: similarity
        });
    }

    // Tri par score de similarité (décroissant)
    scores.sort((a, b) => b.similarity - a.similarity);

    // Retourner uniquement les correspondances au-dessus du seuil
    return scores.filter(score => score.similarity >= threshold).slice(0, maxResults);
}

// Fonction principale d'initialisation
function initSpeciesMatcher() {
    const transcribedInput = document.getElementById('nom_espece1');
    const speciesSelect = document.getElementById('espece_validee1');

    // Créer ou récupérer le conteneur pour afficher les résultats
    let resultsContainer = document.getElementById('species-match-results');
    if (!resultsContainer) {
        resultsContainer = document.createElement('div');
        resultsContainer.id = 'species-match-results';
        resultsContainer.className = 'mt-3 p-2 border rounded';
        speciesSelect.parentNode.insertBefore(resultsContainer, speciesSelect.nextSibling);
    }

    // Fonction pour mettre à jour les résultats
    function updateResults() {
        const transcribedName = transcribedInput.value.trim();
        if (!transcribedName) {
            resultsContainer.innerHTML = '<p class="text-muted">Veuillez entrer un nom d\'espèce transcrit</p>';
            return;
        }

        const options = Array.from(speciesSelect.options).slice(1); // Ignorer l'option "-- Sélectionnez une espèce --"
        const matches = findBestMatches(transcribedName, options);

        if (matches.length === 0) {
            resultsContainer.innerHTML = '<p class="text-danger">Aucune correspondance trouvée</p>';
            return;
        }

        // Si correspondance exacte (100%), sélectionner automatiquement
        if (matches[0].similarity === 100) {
            speciesSelect.value = matches[0].value;
            resultsContainer.innerHTML = `
                <p class="text-success">
                    <strong>Correspondance exacte!</strong> "${matches[0].text}" a été sélectionnée automatiquement.
                </p>
            `;
            return;
        }

        // Afficher les meilleures correspondances
        let html = '<p><strong>Meilleures correspondances:</strong></p><ul>';

        matches.forEach(match => {
            html += `
                <li>
                    <a href="#" class="select-species" data-value="${match.value}">
                        ${match.text} (${match.similarity}%)
                    </a>
                </li>
            `;
        });

        html += '</ul>';
        resultsContainer.innerHTML = html;

        // Ajouter des gestionnaires d'événements pour la sélection
        const links = resultsContainer.querySelectorAll('.select-species');
        links.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const value = this.getAttribute('data-value');
                speciesSelect.value = value;

                // Mettre à jour l'affichage
                resultsContainer.innerHTML = `
                    <p class="text-success">
                        <strong>${this.textContent}</strong> a été sélectionné.
                    </p>
                `;
            });
        });
    }

    // Événement de mise à jour lorsque l'entrée change
    transcribedInput.addEventListener('input', updateResults);

    // Exécuter une première fois pour initialiser
    updateResults();
}

// Exécuter la fonction d'initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', initSpeciesMatcher);