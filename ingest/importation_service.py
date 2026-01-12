# importation_service.py
import datetime
import json
import logging
import os
from difflib import SequenceMatcher

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.crypto import get_random_string

from accounts.models import Utilisateur
from geo.models import Localisation
from geo.utils.geocoding import get_geocodeur
from observations.models import (
    CausesEchec,
    FicheObservation,
    Nid,
    Observation,
    Remarque,
    ResumeObservation,
)
from taxonomy.models import Espece

from .models import EspeceCandidate, ImportationEnCours, TranscriptionBrute

logger = logging.getLogger(__name__)


class ImportationService:
    """Service pour gérer l'importation des données JSON transcrites vers la base de données"""

    def __init__(self):
        self.seuil_similarite = (
            0.8  # Seuil à partir duquel on considère une correspondance probable
        )
        self.geocodeur = get_geocodeur()  # Réutiliser l'instance singleton

        # Cache pour optimiser les recherches d'espèces
        self._especes_cache = None
        self._especes_index = None  # Index par première lettre

        # Cache pour optimiser la recherche de fichiers (évite os.walk répétitifs)
        self._fichiers_cache = None

    def _initialiser_cache_especes(self):
        """Construit le cache des espèces indexé par première lettre pour optimiser le matching"""
        if self._especes_cache is not None:
            return  # Cache déjà initialisé

        logger.info("Initialisation du cache des espèces...")
        self._especes_cache = list(Espece.objects.filter(valide_par_admin=True))
        self._especes_index = {}

        # Créer un index par première lettre pour accélérer la recherche
        for espece in self._especes_cache:
            premiere_lettre = espece.nom[0].lower() if espece.nom else ''
            if premiere_lettre not in self._especes_index:
                self._especes_index[premiere_lettre] = []
            self._especes_index[premiere_lettre].append(espece)

        logger.info(
            f"Cache espèces initialisé: {len(self._especes_cache)} espèces, "
            f"{len(self._especes_index)} lettres indexées"
        )

    def _initialiser_cache_fichiers(self):
        """Construit le cache des chemins de fichiers JSON pour éviter os.walk() répétitif"""
        if self._fichiers_cache is not None:
            return  # Cache déjà initialisé

        logger.info("Initialisation du cache des fichiers JSON...")
        self._fichiers_cache = {}

        base_dir = os.path.join(settings.MEDIA_ROOT, 'transcription_results')
        if not os.path.exists(base_dir):
            logger.warning(f"Répertoire {base_dir} introuvable")
            return

        # Parcourir récursivement une seule fois
        fichiers_trouves = 0
        for root, _dirs, files in os.walk(base_dir):
            for fichier in files:
                if fichier.endswith('_result.json'):
                    # Chemin complet du JSON
                    json_absolu = os.path.join(root, fichier)
                    # Chemin relatif à MEDIA_ROOT
                    chemin_json_relatif = os.path.relpath(json_absolu, settings.MEDIA_ROOT)

                    # Déduire le chemin de l'image depuis le chemin du JSON
                    nom_image = fichier.replace('_result.json', '.jpg')
                    parts = chemin_json_relatif.split(os.sep)

                    if len(parts) >= 5 and parts[0] == 'transcription_results':
                        # Reconstruire le chemin image : jpeg/TRI_ANCIEN/FUSION_FULL/nom_image
                        chemin_image_relatif = os.path.join(parts[1], parts[2], parts[3], nom_image)
                    else:
                        chemin_image_relatif = nom_image

                    # Normaliser les chemins avec des slashes
                    self._fichiers_cache[fichier] = {
                        'chemin_json': chemin_json_relatif.replace(os.sep, '/'),
                        'chemin_image': chemin_image_relatif.replace(os.sep, '/'),
                    }
                    fichiers_trouves += 1

        logger.info(f"Cache fichiers initialisé: {fichiers_trouves} fichiers JSON indexés")

    def importer_fichiers_json(self, repertoire):
        """Importe tous les fichiers JSON d'un répertoire vers la table TranscriptionBrute"""
        chemin_complet = os.path.join(settings.MEDIA_ROOT, 'transcription_results', repertoire)
        resultats = {'total': 0, 'reussis': 0, 'ignores': 0, 'erreurs': []}

        if not os.path.exists(chemin_complet):
            logger.error(f"Le répertoire {chemin_complet} n'existe pas")
            return resultats

        for fichier in os.listdir(chemin_complet):
            if not fichier.endswith('_result.json'):
                continue

            resultats['total'] += 1
            chemin_fichier = os.path.join(chemin_complet, fichier)

            try:
                # Vérifier si le fichier a déjà été importé
                if TranscriptionBrute.objects.filter(fichier_source=fichier).exists():
                    resultats['ignores'] += 1
                    continue

                # Lire le contenu du fichier
                with open(chemin_fichier, encoding='utf-8') as f:
                    contenu = f.read()

                # Supprimer les marqueurs Markdown si présents
                if contenu.startswith('```json') and contenu.endswith('```'):
                    contenu = contenu[7:-3].strip()

                # Parser le JSON nettoyé
                contenu_json = json.loads(contenu)

                # Créer l'entrée dans TranscriptionBrute
                TranscriptionBrute.objects.create(fichier_source=fichier, json_brut=contenu_json)
                resultats['reussis'] += 1
                logger.info(f"Fichier importé avec succès: {fichier}")

            except json.JSONDecodeError as e:
                erreur = f"Erreur de format JSON dans {fichier}: {str(e)}. Début du contenu: {contenu[:100] if 'contenu' in locals() else 'Non disponible'}"
                logger.error(erreur)
                resultats['erreurs'].append(erreur)
            except Exception as e:
                erreur = f"Erreur lors de l'importation de {fichier}: {str(e)}"
                logger.error(erreur)
                resultats['erreurs'].append(erreur)

        return resultats

    def extraire_donnees_candidats(self):
        """Extrait les espèces et crée automatiquement les utilisateurs à partir des transcriptions brutes"""
        transcriptions = TranscriptionBrute.objects.filter(traite=False)
        especes_ajoutees = 0
        utilisateurs_crees = 0

        for transcription in transcriptions:
            try:
                donnees = transcription.json_brut

                # Extraire l'espèce et le code GONM
                if 'informations_generales' in donnees:
                    info_gen = donnees['informations_generales']
                    nom_espece = info_gen.get('espece', '')
                    code_gonm = info_gen.get('n_espece', '')

                    if nom_espece and isinstance(nom_espece, str):
                        # Vérifier si cette espèce existe déjà comme candidate
                        espece, created = EspeceCandidate.objects.get_or_create(
                            nom_transcrit=nom_espece,
                            defaults={
                                'code_gonm_transcrit': code_gonm
                                if isinstance(code_gonm, str)
                                else ''
                            },
                        )

                        # Si l'espèce existait déjà mais sans code GONM, le mettre à jour
                        if (
                            not created
                            and code_gonm
                            and isinstance(code_gonm, str)
                            and not espece.code_gonm_transcrit
                        ):
                            espece.code_gonm_transcrit = code_gonm
                            espece.save()

                        if created:
                            especes_ajoutees += 1

                            # Tenter une correspondance automatique
                            self._trouver_correspondance_espece(espece)

                    elif code_gonm and isinstance(code_gonm, str):
                        # Cas particulier : nom absent mais code GONM présent
                        # Chercher directement l'espèce par son code
                        try:
                            espece_bdd = Espece.objects.get(
                                code_gonm__iexact=code_gonm, valide_par_admin=True
                            )

                            # Créer EspeceCandidate avec le nom officiel de la BDD
                            espece, created = EspeceCandidate.objects.get_or_create(
                                nom_transcrit=espece_bdd.nom,
                                defaults={'code_gonm_transcrit': code_gonm},
                            )

                            if created:
                                especes_ajoutees += 1
                                # Valider automatiquement (100% confiance sur code GONM)
                                espece.espece_validee = espece_bdd
                                espece.score_similarite = 100.0
                                espece.save()
                                logger.info(
                                    f"Espèce identifiée par code GONM '{code_gonm}': {espece_bdd.nom}"
                                )

                        except Espece.DoesNotExist:
                            logger.warning(
                                f"Code GONM '{code_gonm}' introuvable en BDD "
                                f"(fichier {transcription.fichier_source}, pas de nom d'espèce fourni)"
                            )
                        except Espece.MultipleObjectsReturned:
                            logger.error(
                                f"Plusieurs espèces avec code GONM '{code_gonm}' "
                                f"(fichier {transcription.fichier_source})"
                            )

                # Extraire et créer/récupérer l'observateur directement
                if (
                    'informations_generales' in donnees
                    and 'observateur' in donnees['informations_generales']
                ):
                    nom_observateur = donnees['informations_generales']['observateur']
                    if nom_observateur and isinstance(nom_observateur, str):
                        # Créer ou récupérer l'utilisateur automatiquement
                        utilisateur = self.creer_ou_recuperer_utilisateur(nom_observateur)
                        if utilisateur and getattr(utilisateur, '_created', False):
                            utilisateurs_crees += 1

                # NOTE: Le géocodage des communes est maintenant fait uniquement dans finaliser_importation()
                # pour éviter de géocoder 2 fois la même commune

            except Exception as e:
                logger.error(
                    f"Erreur lors de l'extraction des candidats depuis {transcription.fichier_source}: {str(e)}"
                )
                continue

        return {
            'especes_ajoutees': especes_ajoutees,
            'utilisateurs_crees': utilisateurs_crees,
        }

    def _trouver_correspondance_espece(self, espece_candidate):
        """
        Tente de trouver une correspondance pour une espèce candidate avec logique en cascade:
        1. Priorité au matching par nom (fuzzy)
        2. Fallback sur code GONM si le nom échoue
        3. Détection d'incohérences entre nom et code
        """
        # Initialiser le cache si nécessaire
        self._initialiser_cache_especes()

        espece_trouvee = None
        methode_matching = None

        # PRIORITÉ 1 : Essayer le matching par nom (comportement actuel)
        # Optimisation : ne comparer qu'avec les espèces ayant la même première lettre
        premiere_lettre = (
            espece_candidate.nom_transcrit[0].lower() if espece_candidate.nom_transcrit else ''
        )
        especes_candidates = self._especes_index.get(premiere_lettre, [])

        # Si aucune espèce avec cette première lettre, chercher dans toutes les espèces
        if not especes_candidates:
            especes_candidates = self._especes_cache

        meilleure_correspondance = None
        meilleur_score = 0

        for espece_existante in especes_candidates:
            score = SequenceMatcher(
                None, espece_candidate.nom_transcrit.lower(), espece_existante.nom.lower()
            ).ratio()

            if score > meilleur_score and score >= self.seuil_similarite:
                meilleur_score = score
                meilleure_correspondance = espece_existante

        if meilleure_correspondance:
            espece_trouvee = meilleure_correspondance
            methode_matching = 'nom'
            logger.info(
                f"Espèce '{espece_candidate.nom_transcrit}' identifiée par nom: "
                f"'{espece_trouvee.nom}' (score: {meilleur_score:.0%})"
            )

        # PRIORITÉ 2 : Fallback sur code GONM si le nom a échoué
        if not espece_trouvee and espece_candidate.code_gonm_transcrit:
            try:
                espece_par_code = Espece.objects.get(
                    code_gonm__iexact=espece_candidate.code_gonm_transcrit, valide_par_admin=True
                )
                espece_trouvee = espece_par_code
                methode_matching = 'code_gonm'
                logger.info(
                    f"Espèce '{espece_candidate.nom_transcrit}' identifiée par code GONM "
                    f"'{espece_candidate.code_gonm_transcrit}': '{espece_trouvee.nom}'"
                )
            except Espece.DoesNotExist:
                logger.warning(
                    f"Code GONM '{espece_candidate.code_gonm_transcrit}' introuvable pour "
                    f"'{espece_candidate.nom_transcrit}'"
                )
            except Espece.MultipleObjectsReturned:
                logger.error(
                    f"Plusieurs espèces avec le code GONM '{espece_candidate.code_gonm_transcrit}' - "
                    f"intervention manuelle requise"
                )

        # Vérifier cohérence nom/code si les deux sont présents
        if (
            espece_trouvee
            and methode_matching == 'nom'
            and espece_candidate.code_gonm_transcrit
            and espece_trouvee.code_gonm
            and espece_trouvee.code_gonm.upper() != espece_candidate.code_gonm_transcrit.upper()
        ):
            logger.warning(
                f"INCOHÉRENCE détectée pour '{espece_candidate.nom_transcrit}': "
                f"nom→'{espece_trouvee.nom}' (code:{espece_trouvee.code_gonm}) "
                f"mais JSON indique code '{espece_candidate.code_gonm_transcrit}'"
            )

        # Sauvegarder le résultat
        if espece_trouvee:
            espece_candidate.espece_validee = espece_trouvee
            espece_candidate.score_similarite = (
                meilleur_score * 100 if methode_matching == 'nom' else 100.0
            )
            espece_candidate.save()
            return True

        # PRIORITÉ 3 : Échec d'identification
        logger.warning(
            f"Impossible d'identifier '{espece_candidate.nom_transcrit}' "
            f"(code GONM: '{espece_candidate.code_gonm_transcrit or 'absent'}')"
        )
        return False

    def creer_ou_recuperer_utilisateur(self, nom_observateur):
        """Crée ou récupère un utilisateur à partir d'un nom d'observateur manuscrit"""
        if not nom_observateur or nom_observateur.strip() == '':
            prenom = "Obs"
            nom = "Observateur"
        else:
            # Séparer le nom complet en prénom et nom
            parts = nom_observateur.strip().split()

            if len(parts) >= 2:
                prenom = parts[0]
                nom = ' '.join(parts[1:])
            else:
                # Un seul mot, on le duplique
                prenom = parts[0]
                nom = parts[0]

        # Normaliser les valeurs (supprimer caractères spéciaux, etc.)
        prenom = ''.join(c for c in prenom if c.isalnum() or c.isspace()).strip()
        nom = ''.join(c for c in nom if c.isalnum() or c.isspace()).strip()

        # Si après nettoyage on a des chaînes vides, revenir aux valeurs par défaut
        if not prenom or not nom:
            prenom = "Obs"
            nom = "Observateur"

        # Construire username et email
        base_username = f"{prenom.lower()}.{nom.lower()}"
        email = f"{prenom.lower()}.{nom.lower()}@transcription.trans"

        # Créer un username unique
        username = base_username
        counter = 1

        while Utilisateur.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1

        # Vérifier si l'utilisateur existe déjà avec ce nom et prénom (sans filtrer par est_transcription)
        # Cela permet de récupérer les utilisateurs existants même s'ils n'étaient pas marqués comme transcription
        utilisateur = Utilisateur.objects.filter(
            first_name__iexact=prenom, last_name__iexact=nom
        ).first()

        if utilisateur:
            # Utilisateur trouvé - s'assurer qu'il est marqué comme transcription
            if not utilisateur.est_transcription:
                utilisateur.est_transcription = True
                utilisateur.save()
                logger.info(
                    f"Utilisateur existant marqué comme transcription: {utilisateur} (ID: {utilisateur.id})"
                )
            return utilisateur

        # Utilisateur non trouvé - créer un nouveau
        try:
            utilisateur = Utilisateur.objects.create(
                username=username,
                email=email,
                first_name=prenom,
                last_name=nom,
                est_transcription=True,
                est_valide=True,  # Automatically validate transcription users
                role='observateur',
            )
            # Définir un mot de passe aléatoire
            password = get_random_string(12)  # Utilisateur.objects.make_random_password()
            utilisateur.set_password(password)
            utilisateur.save()

            # Marquer l'utilisateur comme nouvellement créé pour les statistiques
            utilisateur._created = True

            logger.info(f"Nouvel utilisateur créé depuis transcription: {utilisateur}")
            return utilisateur

        except Exception as e:
            # En cas d'erreur (ex: email déjà existant), chercher par email
            logger.warning(
                f"Erreur lors de la création de l'utilisateur {prenom} {nom}: {str(e)}. "
                f"Tentative de récupération par email."
            )
            utilisateur_par_email = Utilisateur.objects.filter(email=email).first()
            if utilisateur_par_email:
                if not utilisateur_par_email.est_transcription:
                    utilisateur_par_email.est_transcription = True
                    utilisateur_par_email.save()
                logger.info(f"Utilisateur récupéré par email: {utilisateur_par_email}")
                return utilisateur_par_email
            else:
                # Dernière tentative: créer avec un email unique
                email_unique = (
                    f"{prenom.lower()}.{nom.lower()}.{get_random_string(4)}@transcription.trans"
                )
                utilisateur = Utilisateur.objects.create(
                    username=username,
                    email=email_unique,
                    first_name=prenom,
                    last_name=nom,
                    est_transcription=True,
                    est_valide=True,
                    role='observateur',
                )
                password = get_random_string(12)
                utilisateur.set_password(password)
                utilisateur.save()
                utilisateur._created = True
                logger.info(
                    f"Utilisateur créé avec email unique: {utilisateur} (email: {email_unique})"
                )
                return utilisateur

    def preparer_importations(self):
        """Prépare les importations pour les transcriptions qui ont des candidats validés"""
        transcriptions = TranscriptionBrute.objects.filter(traite=False)
        importations_creees = 0

        for transcription in transcriptions:
            try:
                # Vérifier si une importation existe déjà
                if ImportationEnCours.objects.filter(transcription=transcription).exists():
                    continue

                donnees = transcription.json_brut

                # Extraire et vérifier l'espèce
                espece_candidate = None
                if (
                    'informations_generales' in donnees
                    and 'espece' in donnees['informations_generales']
                ):
                    nom_espece = donnees['informations_generales']['espece']
                    if nom_espece:
                        espece_candidate = EspeceCandidate.objects.filter(
                            nom_transcrit=nom_espece
                        ).first()

                # Extraire et créer/récupérer l'observateur directement
                utilisateur = None
                if (
                    'informations_generales' in donnees
                    and 'observateur' in donnees['informations_generales']
                ):
                    nom_observateur = donnees['informations_generales']['observateur']
                    # if nom_observateur:
                    utilisateur = self.creer_ou_recuperer_utilisateur(nom_observateur)

                # Créer l'importation en cours
                ImportationEnCours.objects.create(
                    transcription=transcription,
                    espece_candidate=espece_candidate,
                    observateur=utilisateur,  # Utiliser directement l'utilisateur au lieu d'un candidat
                    statut='en_attente',
                )
                importations_creees += 1

            except Exception as e:
                logger.error(
                    f"Erreur lors de la préparation de l'importation pour {transcription.fichier_source}: {str(e)}"
                )
                continue

        return importations_creees

    @transaction.atomic
    def finaliser_importation(self, importation_id):
        def safe_int(val, default=None):
            if val is None or str(val).strip().lower() in ["", "null", "none"]:
                return default
            try:
                return int(float(str(val).replace(",", ".")))
            except (ValueError, TypeError):
                return default

        try:
            logger.info(f"[DEBUT] Finalisation de l'importation {importation_id}")
            # Optimisation: précharger les relations pour éviter les requêtes N+1
            importation = (
                ImportationEnCours.objects.select_for_update()
                .select_related(
                    "transcription",
                    "espece_candidate",
                    "espece_candidate__espece_validee",
                    "observateur",
                )
                .get(id=importation_id)
            )

            logger.info(f"Importation récupérée. Statut actuel: {importation.statut}")

            # Vérifier que l'importation n'est pas déjà terminée
            if importation.statut == 'complete':
                logger.warning(f"Importation {importation_id} déjà finalisée")
                return False, "Cette importation a déjà été finalisée"

            if not importation.espece_candidate or not importation.espece_candidate.espece_validee:
                importation.statut = 'erreur'
                importation.save()
                return False, "Espèce non validée"

            if not importation.observateur:
                importation.statut = 'erreur'
                importation.save()
                return False, "Observateur non trouvé"

            donnees = importation.transcription.json_brut

            annee = timezone.now().year
            if 'informations_generales' in donnees:
                annee_str = donnees['informations_generales'].get('annee')
                if annee_str and str(annee_str).isdigit():
                    annee = int(annee_str)

            nom_fichier_json = (
                importation.transcription.fichier_source
            )  # Exemple : Image_1_result.json

            # Utiliser le cache de fichiers pour éviter os.walk() répétitif
            self._initialiser_cache_fichiers()

            # Récupérer les chemins depuis le cache
            if nom_fichier_json in self._fichiers_cache:
                chemins = self._fichiers_cache[nom_fichier_json]
                chemin_json = chemins['chemin_json']
                chemin_image = chemins['chemin_image']
            else:
                # Fallback si fichier non trouvé dans le cache
                nom_image = nom_fichier_json.replace('_result.json', '.jpg')
                chemin_json = nom_fichier_json
                chemin_image = nom_image
                logger.warning(
                    f"Fichier {nom_fichier_json} non trouvé dans le cache, utilisation des chemins par défaut"
                )

            # Création de la fiche d'observation (les objets liés seront créés automatiquement
            # par la méthode save() du modèle FicheObservation)
            fiche = FicheObservation.objects.create(
                observateur=importation.observateur,
                espece=importation.espece_candidate.espece_validee,
                annee=annee,
                chemin_image=chemin_image,
                chemin_json=chemin_json,
                transcription=True,
            )
            importation.fiche_observation = fiche

            # Mettre à jour l'état de correction à "en cours de correction"
            # car la fiche issue d'une transcription OCR nécessite une correction manuelle
            etat_correction = fiche.etat_correction
            etat_correction.statut = 'en_cours'
            etat_correction.save()

            # Mise à jour de l'objet Localisation (créé automatiquement ou récupéré)
            if 'localisation' in donnees:
                loc = donnees['localisation']
                localisation, _ = Localisation.objects.get_or_create(fiche=fiche)

                # Récupérer les données brutes
                nom_commune = loc.get('commune') or loc.get('IGN_50000') or 'Non spécifiée'
                departement = loc.get('dep_t') or '00'

                # Géocoder la commune pour obtenir les coordonnées
                altitude_depuis_geo = None
                if nom_commune != 'Non spécifiée':
                    try:
                        resultat_geo = self.geocodeur.geocoder_commune(nom_commune, departement)
                        if resultat_geo:
                            # Utiliser le nom officiel et les coordonnées trouvées
                            localisation.commune = resultat_geo.get(
                                'adresse_complete', nom_commune
                            ).split(',')[0]
                            localisation.latitude = str(resultat_geo['lat'])
                            localisation.longitude = str(resultat_geo['lon'])
                            localisation.coordonnees = resultat_geo['coordonnees_gps']
                            localisation.source_coordonnees = resultat_geo['source']
                            localisation.precision_gps = resultat_geo.get('precision_metres', 5000)
                            if 'code_insee' in resultat_geo:
                                localisation.code_insee = resultat_geo['code_insee']
                            # Récupérer l'altitude si disponible
                            if 'altitude' in resultat_geo and resultat_geo['altitude'] is not None:
                                altitude_depuis_geo = resultat_geo['altitude']
                            logger.info(
                                f"Fiche {fiche.num_fiche}: Commune géocodée '{nom_commune}' -> "
                                f"{localisation.commune} (source: {resultat_geo['source']})"
                            )
                        else:
                            # Pas trouvé, garder le nom brut
                            localisation.commune = nom_commune
                            logger.warning(
                                f"Fiche {fiche.num_fiche}: Commune '{nom_commune}' non trouvée, coordonnées non mises à jour"
                            )
                    except Exception as e:
                        # En cas d'erreur, garder le nom brut
                        localisation.commune = nom_commune
                        logger.error(
                            f"Fiche {fiche.num_fiche}: Erreur géocodage '{nom_commune}': {str(e)}"
                        )
                else:
                    localisation.commune = nom_commune

                localisation.lieu_dit = loc.get('coordonnees_et_ou_lieu_dit') or 'Non spécifiée'
                localisation.departement = departement
                # Utiliser l'altitude du géocodage si disponible, sinon celle du JSON, sinon 0
                if altitude_depuis_geo is not None:
                    localisation.altitude = altitude_depuis_geo
                else:
                    altitude_json = loc.get('altitude')
                    if altitude_json:
                        try:
                            localisation.altitude = int(altitude_json)
                        except (ValueError, TypeError):
                            localisation.altitude = 0
                    else:
                        localisation.altitude = 0
                localisation.paysage = loc.get('paysage') or 'Non spécifié'
                localisation.alentours = loc.get('alentours') or 'Non spécifié'
                localisation.save()

            # Mise à jour de l'objet Nid (créé automatiquement ou récupéré)
            if 'nid' in donnees:
                nid_data = donnees['nid']

                nid, _ = Nid.objects.get_or_create(fiche=fiche)
                nid.nid_prec_t_meme_couple = bool(nid_data.get('nid_prec_t_meme_c_ple'))
                nid.hauteur_nid = safe_int(nid_data.get('haut_nid'))
                nid.hauteur_couvert = safe_int(nid_data.get('h_c_vert'))
                nid.details_nid = nid_data.get('nid') or 'Aucun détail'
                nid.save()

            # Création des observations en lot (bulk_create pour performance)
            if 'tableau_donnees' in donnees and isinstance(donnees['tableau_donnees'], list):
                observations_a_creer = []
                for obs in donnees['tableau_donnees']:
                    try:
                        jour = int(obs.get('Jour') or 1)
                        mois = int(obs.get('Mois') or 1)

                        heure_brute = obs.get('Heure')
                        heure_connue = True
                        if (
                            heure_brute is None
                            or str(heure_brute).strip() == ""
                            or str(heure_brute).lower() == "null"
                        ):
                            heure = 0
                            heure_connue = False
                        else:
                            try:
                                heure = int(str(heure_brute).replace('e', ''))
                            except (ValueError, TypeError):
                                heure = 0
                                heure_connue = False

                        date_obs = timezone.make_aware(
                            datetime.datetime(annee, mois, jour, heure, 0)
                        )

                        observations_a_creer.append(
                            Observation(
                                fiche=fiche,
                                date_observation=date_obs,
                                heure_connue=heure_connue,
                                nombre_oeufs=safe_int(obs.get('Nombre_oeuf')),
                                nombre_poussins=safe_int(obs.get('Nombre_pou')),
                                observations=obs.get('observations') or '',
                            )
                        )
                    except Exception as e:
                        logger.warning(f"Observation ignorée (fiche {fiche.num_fiche}) : {str(e)}")

                # Créer toutes les observations en une seule requête
                if observations_a_creer:
                    Observation.objects.bulk_create(observations_a_creer)

            # Mise à jour de l'objet ResumeObservation (créé automatiquement ou récupéré)
            if 'tableau_donnees_2' in donnees:
                resume_data = donnees['tableau_donnees_2']

                resume, _ = ResumeObservation.objects.get_or_create(fiche=fiche)

                # Récupération des valeurs (None si pas renseigné, pas 0)
                # Sécurisation de l'accès aux dictionnaires imbriqués
                nombre_oeufs_dict = resume_data.get('nombre_oeufs') or {}
                nombre_poussins_dict = resume_data.get('nombre_poussins') or {}

                nombre_oeufs_pondus = safe_int(nombre_oeufs_dict.get('pondus'))
                nombre_oeufs_eclos = safe_int(nombre_oeufs_dict.get('eclos'))
                nombre_oeufs_non_eclos = safe_int(nombre_oeufs_dict.get('n_ecl'))
                nombre_poussins = safe_int(nombre_poussins_dict.get('vol_t'))

                # Log des valeurs pour debugging
                logger.info(
                    f"Fiche {fiche.num_fiche} - Valeurs résumé: pondus={nombre_oeufs_pondus}, "
                    f"éclos={nombre_oeufs_eclos}, non_éclos={nombre_oeufs_non_eclos}, poussins={nombre_poussins}"
                )

                # Validation et correction automatique des contraintes
                # Si on a des poussins mais pas d'œufs éclos renseignés, on déduit le minimum d'œufs éclos
                if (
                    nombre_poussins
                    and nombre_poussins > 0
                    and (nombre_oeufs_eclos is None or nombre_oeufs_eclos == 0)
                ):
                    nombre_oeufs_eclos = nombre_poussins
                    logger.warning(
                        f"Fiche {fiche.num_fiche}: Correction automatique - œufs éclos ajusté à {nombre_oeufs_eclos} pour cohérence avec {nombre_poussins} poussins"
                    )

                # Si on a plus de poussins que d'œufs éclos, ajuster les œufs éclos
                if nombre_poussins and nombre_oeufs_eclos and nombre_poussins > nombre_oeufs_eclos:
                    nombre_oeufs_eclos = nombre_poussins
                    logger.warning(
                        f"Fiche {fiche.num_fiche}: Correction automatique - œufs éclos ajusté à {nombre_oeufs_eclos} pour respecter la contrainte"
                    )

                # Si on a des œufs éclos mais pas d'œufs pondus renseignés, ajuster
                if (
                    nombre_oeufs_eclos
                    and nombre_oeufs_eclos > 0
                    and (nombre_oeufs_pondus is None or nombre_oeufs_eclos > nombre_oeufs_pondus)
                ):
                    nombre_oeufs_pondus = nombre_oeufs_eclos + (nombre_oeufs_non_eclos or 0)
                    logger.warning(
                        f"Fiche {fiche.num_fiche}: Correction automatique - œufs pondus ajusté à {nombre_oeufs_pondus} pour cohérence"
                    )

                # Attribution des valeurs validées
                # Sécurisation de l'accès aux dictionnaires imbriqués
                premier_oeuf_dict = resume_data.get('1er_o_pondu') or {}
                premier_poussin_eclos_dict = resume_data.get('1er_p_eclos') or {}
                premier_poussin_volant_dict = resume_data.get('1er_p_volant') or {}

                resume.premier_oeuf_pondu_jour = safe_int(premier_oeuf_dict.get('jour'))
                resume.premier_oeuf_pondu_mois = safe_int(premier_oeuf_dict.get('Mois'))
                resume.premier_poussin_eclos_jour = safe_int(premier_poussin_eclos_dict.get('jour'))
                resume.premier_poussin_eclos_mois = safe_int(premier_poussin_eclos_dict.get('Mois'))
                resume.premier_poussin_volant_jour = safe_int(premier_poussin_volant_dict.get('jour'))
                resume.premier_poussin_volant_mois = safe_int(premier_poussin_volant_dict.get('Mois'))
                resume.nombre_oeufs_pondus = nombre_oeufs_pondus
                resume.nombre_oeufs_eclos = nombre_oeufs_eclos
                resume.nombre_oeufs_non_eclos = nombre_oeufs_non_eclos
                resume.nombre_poussins = nombre_poussins

                resume.save()
                logger.info(f"Fiche {fiche.num_fiche}: Résumé sauvegardé avec succès")

            # Mise à jour de l'objet CausesEchec (créé automatiquement ou récupéré)
            if 'causes_echec' in donnees:
                causes_echec, _ = CausesEchec.objects.get_or_create(fiche=fiche)
                causes_echec.description = donnees['causes_echec'].get('causes_d_echec') or ''
                causes_echec.save()

            # Ajout d'une remarque si présente dans les données
            if 'remarque' in donnees and donnees['remarque']:
                Remarque.objects.create(fiche=fiche, remarque=donnees['remarque'])

            # Marquer l'importation comme terminée
            logger.info(f"Mise à jour du statut de l'importation {importation_id} vers 'complete'")
            importation.statut = 'complete'
            importation.save()
            logger.info(f"Statut sauvegardé. Valeur après save: {importation.statut}")

            # Vérification immédiate en base
            importation.refresh_from_db()
            logger.info(f"Statut après refresh_from_db: {importation.statut}")

            # Marquer la transcription comme traitée
            importation.transcription.traite = True
            importation.transcription.save()

            logger.info(f"Importation finalisée avec succès pour la fiche {fiche.num_fiche}")
            return True, f"Fiche {fiche.num_fiche} créée avec succès"

        except Exception as e:
            logger.error(
                f"Erreur lors de la finalisation de l'importation {importation_id}: {str(e)}"
            )
            return False, str(e)

    def reinitialiser_importation(self, importation_id=None, fichier_source=None):
        """
        Réinitialise une importation pour permettre de recommencer le processus
        """
        try:
            # Si un ID d'importation est fourni, on l'utilise
            if importation_id:
                importation = ImportationEnCours.objects.get(id=importation_id)
                transcription = importation.transcription

            # Sinon, on recherche par le nom du fichier
            elif fichier_source:
                transcription = TranscriptionBrute.objects.get(fichier_source=fichier_source)
                try:
                    importation = ImportationEnCours.objects.get(transcription=transcription)
                except ImportationEnCours.DoesNotExist:
                    importation = None
            else:
                return {
                    "success": False,
                    "message": "Aucun identifiant fourni pour la réinitialisation",
                }

            # Sauvegarder le nom du fichier pour le message
            fichier_nom = transcription.fichier_source

            # Suppression de la fiche d'observation si elle existe
            if importation and importation.fiche_observation:
                fiche_id = importation.fiche_observation.num_fiche
                importation.fiche_observation.delete()
                logger.info(f"Fiche d'observation #{fiche_id} supprimée")

            # Supprimer l'importation en cours
            if importation:
                importation.delete()
                logger.info(f"ImportationEnCours pour {fichier_nom} supprimée")

            # Marquer la transcription comme non traitée pour permettre la re-préparation
            transcription.traite = False
            transcription.save()
            logger.info(f"TranscriptionBrute pour {fichier_nom} marquée comme non traitée")

            return {
                "success": True,
                "message": f"L'importation de {fichier_nom} a été réinitialisée avec succès.",
            }

        except (ImportationEnCours.DoesNotExist, TranscriptionBrute.DoesNotExist) as e:
            logger.error(f"Erreur lors de la réinitialisation: {str(e)}")
            return {
                "success": False,
                "message": f"importation ou transcription non trouvée: {str(e)}",
            }
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la réinitialisation: {str(e)}")
            return {"success": False, "message": f"Erreur lors de la réinitialisation: {str(e)}"}
