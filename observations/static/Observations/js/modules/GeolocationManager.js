/**
 * Gestion de la géolocalisation GPS
 * Gère le clic sur le bouton "Ma position" pour récupérer les coordonnées
 * et pré-remplir les champs latitude/longitude.
 */
export default function initGeolocation() {
    'use strict';

    const getGpsBtn = document.getElementById('get-gps-btn');
    if (getGpsBtn) {
        getGpsBtn.addEventListener('click', function() {
            if (!navigator.geolocation) {
                alert('La géolocalisation n\'est pas supportée par votre navigateur');
                return;
            }

            // Afficher un indicateur de chargement
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Localisation...';
            this.disabled = true;

            navigator.geolocation.getCurrentPosition(
                // Succès
                function(position) {
                    const lat = position.coords.latitude.toFixed(6);
                    const lon = position.coords.longitude.toFixed(6);

                    // Remplir les champs
                    const latInput = document.getElementById('id_latitude');
                    const lonInput = document.getElementById('id_longitude');

                    if (latInput && lonInput) {
                        latInput.value = lat;
                        lonInput.value = lon;

                        // Afficher automatiquement les communes à proximité
                        const communeInput = document.getElementById('id_commune');
                        if (communeInput) {
                            // Si le champ est vide, on affiche un message encourageant à taper
                            if (!communeInput.value.trim()) {
                                alert(`Position GPS récupérée:\nLatitude: ${lat}\nLongitude: ${lon}\n\nVous pouvez maintenant taper dans le champ "Commune".\nLes résultats seront automatiquement filtrés dans un rayon de 10 km.`);
                                // Mettre le focus sur le champ commune
                                communeInput.focus();
                            } else {
                                // Si le champ contient déjà du texte, relancer la recherche
                                alert(`Position GPS récupérée:\nLatitude: ${lat}\nLongitude: ${lon}\n\nMise à jour de la liste des communes (rayon 10 km)...`);
                                const event = new Event('input', { bubbles: true });
                                communeInput.dispatchEvent(event);
                            }
                        } else {
                            alert(`Position GPS récupérée:\nLatitude: ${lat}\nLongitude: ${lon}`);
                        }
                    }

                    // Restaurer le bouton
                    getGpsBtn.innerHTML = originalText;
                    getGpsBtn.disabled = false;
                },
                // Erreur
                function(error) {
                    let message = 'Erreur lors de la récupération de la position';
                    switch(error.code) {
                        case error.PERMISSION_DENIED:
                            message = 'Permission refusée pour accéder à votre position';
                            break;
                        case error.POSITION_UNAVAILABLE:
                            message = 'Position non disponible';
                            break;
                        case error.TIMEOUT:
                            message = 'Délai d\'attente dépassé';
                            break;
                    }
                    alert(message);

                    // Restaurer le bouton
                    getGpsBtn.innerHTML = originalText;
                    getGpsBtn.disabled = false;
                }
            );
        });
        
        console.log('Module Géolocalisation initialisé');
    }
}
