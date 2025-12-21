/**
 * Module de préparation d'images pour OCR
 * Port JavaScript du code Python pdf_Conversion.py
 */

// État global
let fichesQueue = [];
let currentIndex = 0;
let stats = {
    traitees: 0,
    erreurs: 0,
    total: 0
};

// Images en cours de traitement
let currentRectoImg = null;
let currentVersoImg = null;
let rectoRotation = 0;
let versoRotation = 0;

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', function() {
    const folderInput = document.getElementById('folderInput');
    if (folderInput) {
        folderInput.addEventListener('change', handleFolderSelection);
    }
});

/**
 * Gestion de la sélection du dossier
 */
function handleFolderSelection(event) {
    const files = Array.from(event.target.files);

    if (files.length === 0) {
        alert('Aucun fichier sélectionné');
        return;
    }

    // Détecter les paires recto/verso
    const paires = detecterPairesRectoVerso(files);

    if (paires.length === 0) {
        alert('Aucune paire recto/verso détectée. Les fichiers doivent contenir "recto" et "verso" dans leur nom.');
        return;
    }

    // Initialiser la queue
    fichesQueue = paires;
    currentIndex = 0;
    stats.total = paires.length;
    stats.traitees = 0;
    stats.erreurs = 0;

    // Afficher les stats
    afficherStats(paires);

    // Afficher la section de traitement
    document.getElementById('processingCard').style.display = 'block';
    document.getElementById('progressSection').style.display = 'block';

    // Charger la première fiche
    chargerFiche(0);
}

/**
 * Détecte les paires recto/verso dans la liste de fichiers
 */
function detecterPairesRectoVerso(files) {
    const paires = [];
    const rectos = files.filter(f => f.name.toLowerCase().includes('recto'));

    rectos.forEach(recto => {
        // Extraire le numéro de fiche (ex: "001" dans "001_recto.jpg")
        const match = recto.name.match(/(\d+)/);
        if (!match) return;

        const numero = match[0];

        // Chercher le verso correspondant
        const verso = files.find(f =>
            f.name.includes(numero) &&
            f.name.toLowerCase().includes('verso')
        );

        if (verso) {
            paires.push({
                numero: numero,
                recto: recto,
                verso: verso
            });
        }
    });

    // Trier par numéro
    paires.sort((a, b) => parseInt(a.numero) - parseInt(b.numero));

    return paires;
}

/**
 * Affiche les statistiques de fichiers détectés
 */
function afficherStats(paires) {
    const statsDiv = document.getElementById('fileStats');
    const statsList = document.getElementById('fileStatsList');

    statsList.innerHTML = `
        <li><strong>${paires.length}</strong> paires recto/verso détectées</li>
        <li>Fiches : ${paires.map(p => p.numero).join(', ')}</li>
    `;

    statsDiv.style.display = 'block';

    // Mettre à jour la progression
    mettreAJourProgression();
}

/**
 * Charge une fiche pour traitement
 */
function chargerFiche(index) {
    if (index >= fichesQueue.length) {
        // Terminé !
        afficherResume();
        return;
    }

    const fiche = fichesQueue[index];
    currentIndex = index;

    // Réinitialiser les rotations
    rectoRotation = 0;
    versoRotation = 0;

    // Afficher l'info de la fiche courante
    document.getElementById('currentFicheInfo').textContent =
        `Fiche ${index + 1}/${fichesQueue.length} - N° ${fiche.numero}`;

    // Charger les images
    chargerImage(fiche.recto, 'recto');
    chargerImage(fiche.verso, 'verso');
}

/**
 * Charge une image dans un canvas
 */
function chargerImage(file, type) {
    const reader = new FileReader();

    reader.onload = function(e) {
        const img = new Image();
        img.onload = function() {
            if (type === 'recto') {
                currentRectoImg = img;
                afficherImageSurCanvas(img, 'rectoCanvas', 0);
            } else {
                currentVersoImg = img;
                afficherImageSurCanvas(img, 'versoCanvas', 0);
            }

            // Si les deux images sont chargées, générer la fusion
            if (currentRectoImg && currentVersoImg) {
                genererFusion();
            }
        };
        img.src = e.target.result;
    };

    reader.readAsDataURL(file);
}

/**
 * Affiche une image sur un canvas avec rotation
 */
function afficherImageSurCanvas(img, canvasId, rotation) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');

    // Dimensions selon la rotation
    const isRotated = (rotation === 90 || rotation === 270 || rotation === -90);
    canvas.width = isRotated ? img.height : img.width;
    canvas.height = isRotated ? img.width : img.height;

    // Appliquer la rotation
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();

    if (rotation !== 0) {
        // Centrer la rotation
        ctx.translate(canvas.width / 2, canvas.height / 2);
        ctx.rotate(rotation * Math.PI / 180);
        ctx.translate(-img.width / 2, -img.height / 2);
    }

    ctx.drawImage(img, 0, 0);
    ctx.restore();
}

/**
 * Applique une rotation à une image
 */
function rotateImage(type, angle) {
    if (type === 'recto') {
        rectoRotation = (rectoRotation + angle) % 360;
        if (rectoRotation < 0) rectoRotation += 360;
        afficherImageSurCanvas(currentRectoImg, 'rectoCanvas', rectoRotation);
    } else {
        versoRotation = (versoRotation + angle) % 360;
        if (versoRotation < 0) versoRotation += 360;
        afficherImageSurCanvas(currentVersoImg, 'versoCanvas', versoRotation);
    }

    // Régénérer la fusion
    genererFusion();
}

/**
 * Génère l'image fusionnée (recto + partie gauche du verso)
 * Port de la fonction combine_recto_verso() du Python
 */
function genererFusion() {
    if (!currentRectoImg || !currentVersoImg) return;

    const fusionCanvas = document.getElementById('fusionCanvas');
    const ctx = fusionCanvas.getContext('2d');

    // Obtenir les images avec rotation appliquée
    const rectoCanvas = document.getElementById('rectoCanvas');
    const versoCanvas = document.getElementById('versoCanvas');

    const rectoWidth = rectoCanvas.width;
    const rectoHeight = rectoCanvas.height;
    const versoWidth = versoCanvas.width;
    const versoHeight = versoCanvas.height;

    // Recadrer le verso : 5.5/10 de la largeur (comme dans le code Python)
    const cropWidth = Math.floor(versoWidth * 5.5 / 10);

    // Canvas final : largeur = recto, hauteur = recto + verso
    fusionCanvas.width = rectoWidth;
    fusionCanvas.height = rectoHeight + versoHeight;

    // Fond blanc
    ctx.fillStyle = '#FFFFFF';
    ctx.fillRect(0, 0, fusionCanvas.width, fusionCanvas.height);

    // Dessiner recto en haut
    ctx.drawImage(rectoCanvas, 0, 0);

    // Dessiner verso recadré en bas
    const copyWidth = Math.min(cropWidth, rectoWidth);
    ctx.drawImage(
        versoCanvas,
        0, 0, copyWidth, versoHeight,  // Source (partie gauche du verso)
        0, rectoHeight, copyWidth, versoHeight  // Destination (en bas du canvas)
    );
}

/**
 * Valide la fiche courante et passe à la suivante
 */
async function validerFiche() {
    const fusionCanvas = document.getElementById('fusionCanvas');
    const notes = document.getElementById('notesInput').value;
    const fiche = fichesQueue[currentIndex];

    try {
        // Convertir le canvas en blob
        const blob = await new Promise(resolve => {
            fusionCanvas.toBlob(resolve, 'image/jpeg', 0.92);
        });

        // Préparer les données
        const formData = new FormData();
        formData.append('fichier_fusionne', blob, `fiche_${fiche.numero}_prepared.jpg`);
        formData.append('fichier_recto', fiche.recto.webkitRelativePath || fiche.recto.name);
        formData.append('fichier_verso', fiche.verso.webkitRelativePath || fiche.verso.name);
        formData.append('notes', notes);

        // Créer l'objet operations
        const operations = {
            rotation_recto: rectoRotation,
            rotation_verso: versoRotation,
            crop_verso_width: '55%',
            timestamp: new Date().toISOString()
        };
        formData.append('operations', JSON.stringify(operations));

        // Envoyer au serveur
        const response = await fetch(window.location.href, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (data.success) {
            stats.traitees++;
            console.log(`✓ Fiche ${fiche.numero} traitée (ID: ${data.preparation_id})`);
        } else {
            stats.erreurs++;
            console.error(`✗ Erreur fiche ${fiche.numero}: ${data.error}`);
            alert(`Erreur : ${data.error}`);
        }

    } catch (error) {
        stats.erreurs++;
        console.error('Erreur lors de l\'upload:', error);
        alert(`Erreur lors de l'upload : ${error.message}`);
    }

    // Mettre à jour la progression
    mettreAJourProgression();

    // Réinitialiser les notes
    document.getElementById('notesInput').value = '';

    // Passer à la suivante
    chargerFiche(currentIndex + 1);
}

/**
 * Ignore la fiche courante et passe à la suivante
 */
function ignorerFiche() {
    if (confirm('Êtes-vous sûr de vouloir ignorer cette fiche ?')) {
        chargerFiche(currentIndex + 1);
    }
}

/**
 * Met à jour la barre de progression
 */
function mettreAJourProgression() {
    const pourcentage = Math.floor((stats.traitees / stats.total) * 100);

    const progressBar = document.getElementById('progressBar');
    progressBar.style.width = pourcentage + '%';
    progressBar.textContent = pourcentage + '%';

    document.getElementById('countTraitees').textContent = stats.traitees;
    document.getElementById('countErreurs').textContent = stats.erreurs;
    document.getElementById('countRestantes').textContent = stats.total - stats.traitees - stats.erreurs;
}

/**
 * Affiche le résumé final
 */
function afficherResume() {
    const message = `
        🎉 Traitement terminé !

        ✓ ${stats.traitees} fiches traitées avec succès
        ${stats.erreurs > 0 ? `✗ ${stats.erreurs} erreurs` : ''}

        Total : ${stats.total} fiches
    `;

    alert(message);

    // Recharger la page pour recommencer
    if (confirm('Voulez-vous traiter d\'autres fiches ?')) {
        location.reload();
    }
}

/**
 * Récupère le cookie CSRF
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
