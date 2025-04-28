# importation_service.py
import os
import json
import logging
from difflib import SequenceMatcher

from django.db import transaction
from django.conf import settings
from django.utils import timezone

# Importer le modèle Utilisateur depuis Administration
from Administration.models import Utilisateur
from Observations.models import (
    Espece, FicheObservation, Localisation,
    Nid, Observation, ResumeObservation, CausesEchec, Remarque
)
from .models import (
    TranscriptionBrute, EspeceCandidate, ImportationEnCours
)

logger = logging.getLogger(__name__)


class ImportationService:
    """Service pour gérer l'importation des données JSON transcrites vers la base de données"""

    def __init__(self):
        self.seuil_similarite = 0.8  # Seuil à partir duquel on considère une correspondance probable

    def importer_fichiers_json(self, repertoire):
        """Importe tous les fichiers JSON d'un répertoire vers la table TranscriptionBrute"""
        chemin_complet = os.path.join(settings.MEDIA_ROOT, 'transcription_results', repertoire)
        resultats = {
            'total': 0,
            'reussis': 0,
            'ignores': 0,
            'erreurs': []
        }

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
                with open(chemin_fichier, 'r', encoding='utf-8') as f:
                    contenu = f.read()

                # Supprimer les marqueurs Markdown si présents
                if contenu.startswith('```json') and contenu.endswith('```'):
                    contenu = contenu[7:-3].strip()

                # Parser le JSON nettoyé
                contenu_json = json.loads(contenu)

                # Créer l'entrée dans TranscriptionBrute
                TranscriptionBrute.objects.create(
                    fichier_source=fichier,
                    json_brut=contenu_json
                )
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

                # Extraire l'espèce
                if 'informations_generales' in donnees and 'espece' in donnees['informations_generales']:
                    nom_espece = donnees['informations_generales']['espece']
                    if nom_espece and isinstance(nom_espece, str):
                        # Vérifier si cette espèce existe déjà comme candidate
                        espece, created = EspeceCandidate.objects.get_or_create(
                            nom_transcrit=nom_espece
                        )
                        if created:
                            especes_ajoutees += 1

                            # Tenter une correspondance automatique
                            self._trouver_correspondance_espece(espece)

                # Extraire et créer/récupérer l'observateur directement
                if 'informations_generales' in donnees and 'observateur' in donnees['informations_generales']:
                    nom_observateur = donnees['informations_generales']['observateur']
                    if nom_observateur and isinstance(nom_observateur, str):
                        # Créer ou récupérer l'utilisateur automatiquement
                        utilisateur = self.creer_ou_recuperer_utilisateur(nom_observateur)
                        if utilisateur and getattr(utilisateur, '_created', False):
                            utilisateurs_crees += 1

            except Exception as e:
                logger.error(
                    f"Erreur lors de l'extraction des candidats depuis {transcription.fichier_source}: {str(e)}")
                continue

        return {
            'especes_ajoutees': especes_ajoutees,
            'utilisateurs_crees': utilisateurs_crees
        }

    def _trouver_correspondance_espece(self, espece_candidate):
        """Tente de trouver une correspondance pour une espèce candidate"""
        especes_existantes = Espece.objects.filter(valide_par_admin=True)
        meilleure_correspondance = None
        meilleur_score = 0

        for espece_existante in especes_existantes:
            score = SequenceMatcher(None, espece_candidate.nom_transcrit.lower(),
                                    espece_existante.nom.lower()).ratio()

            if score > meilleur_score and score >= self.seuil_similarite:
                meilleur_score = score
                meilleure_correspondance = espece_existante

        if meilleure_correspondance:
            espece_candidate.espece_validee = meilleure_correspondance
            espece_candidate.save()
            return True

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

        # Vérifier si l'utilisateur existe déjà avec ce nom et prénom
        try:
            utilisateur = Utilisateur.objects.get(
                first_name__iexact=prenom,
                last_name__iexact=nom,
                est_transcription=True
            )
            return utilisateur
        except Utilisateur.DoesNotExist:
            # Créer un nouvel utilisateur
            utilisateur = Utilisateur.objects.create(
                username=username,
                email=email,
                first_name=prenom,
                last_name=nom,
                est_transcription=True,
                est_valide=True,  # Automatically validate transcription users
                role='observateur'
            )
            # Définir un mot de passe aléatoire
            password = Utilisateur.objects.make_random_password()
            utilisateur.set_password(password)
            utilisateur.save()

            # Marquer l'utilisateur comme nouvellement créé pour les statistiques
            utilisateur._created = True

            logger.info(f"Nouvel utilisateur créé depuis transcription: {utilisateur}")
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
                if 'informations_generales' in donnees and 'espece' in donnees['informations_generales']:
                    nom_espece = donnees['informations_generales']['espece']
                    if nom_espece:
                        espece_candidate = EspeceCandidate.objects.filter(nom_transcrit=nom_espece).first()

                # Extraire et créer/récupérer l'observateur directement
                utilisateur = None
                if 'informations_generales' in donnees and 'observateur' in donnees['informations_generales']:
                    nom_observateur = donnees['informations_generales']['observateur']
                    # if nom_observateur:
                    utilisateur = self.creer_ou_recuperer_utilisateur(nom_observateur)

                # Créer l'importation en cours
                ImportationEnCours.objects.create(
                    transcription=transcription,
                    espece_candidate=espece_candidate,
                    observateur=utilisateur,  # Utiliser directement l'utilisateur au lieu d'un candidat
                    statut='en_attente'
                )
                importations_creees += 1

            except Exception as e:
                logger.error(
                    f"Erreur lors de la préparation de l'importation pour {transcription.fichier_source}: {str(e)}")
                continue

        return importations_creees

    @transaction.atomic
    def finaliser_importation(self, importation_id):
        try:
            importation = ImportationEnCours.objects.select_for_update().get(id=importation_id)

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

            nom_fichier_json = importation.transcription.fichier_source  # Exemple : Image_1_result.json
            nom_image = nom_fichier_json.replace('_result.json', '.jpg')  # Exemple : Image_1.jpg
            chemin_image = os.path.join('Rep1', nom_image)  # Pour un usage via MEDIA_URL

            # Création de la fiche d'observation (les objets liés seront créés automatiquement
            # par la méthode save() du modèle FicheObservation)
            fiche = FicheObservation.objects.create(
                observateur=importation.observateur,
                espece=importation.espece_candidate.espece_validee,
                annee=annee,
                chemin_image=chemin_image,
                chemin_json=nom_fichier_json,
                transcription=True
            )
            importation.fiche_observation = fiche

            # Mise à jour de l'objet Localisation qui existe déjà
            if 'localisation' in donnees:
                loc = donnees['localisation']
                localisation = Localisation.objects.get(fiche=fiche)
                localisation.commune = loc.get('commune') or loc.get('IGN_50000') or 'Non spécifiée'
                localisation.lieu_dit = loc.get('coordonnees_et_ou_lieu_dit') or 'Non spécifiée'
                localisation.departement = loc.get('dep_t') or '00'
                localisation.altitude = loc.get('altitude') or '0'
                localisation.paysage = loc.get('paysage') or 'Non spécifié'
                localisation.alentours = loc.get('alentours') or 'Non spécifié'
                localisation.save()

            # Mise à jour de l'objet Nid qui existe déjà
            if 'nid' in donnees:
                nid_data = donnees['nid']

                def safe_float_to_int(val):
                    try:
                        return int(float(str(val).replace(',', '.')))
                    except:
                        return 0

                nid = Nid.objects.get(fiche=fiche)
                nid.nid_prec_t_meme_couple = bool(nid_data.get('nid_prec_t_meme_c_ple'))
                nid.hauteur_nid = safe_float_to_int(nid_data.get('haut_nid'))
                nid.hauteur_couvert = safe_float_to_int(nid_data.get('h_c_vert'))
                nid.details_nid = nid_data.get('nid') or 'Aucun détail'
                nid.save()

            # Création des observations
            if 'tableau_donnees' in donnees and isinstance(donnees['tableau_donnees'], list):
                for obs in donnees['tableau_donnees']:
                    try:
                        jour = int(obs.get('Jour') or 1)
                        mois = int(obs.get('Mois') or 1)
                        heure = int(str(obs.get('Heure') or 12).replace('e', ''))
                        date_obs = timezone.make_aware(timezone.datetime(annee, mois, jour, heure, 0))

                        Observation.objects.create(
                            fiche=fiche,
                            date_observation=date_obs,
                            nombre_oeufs=int(obs.get('Nombre_oeuf') or 0),
                            nombre_poussins=int(obs.get('Nombre_pou') or 0),
                            observations=obs.get('observations') or ''
                        )
                    except Exception as e:
                        logger.warning(f"Observation ignorée (fiche {fiche.num_fiche}) : {str(e)}")

            # Mise à jour de l'objet ResumeObservation qui existe déjà
            if 'tableau_donnees_2' in donnees:
                resume_data = donnees['tableau_donnees_2']

                def safe_int(value):
                    try:
                        return int(value)
                    except:
                        return None

                resume = ResumeObservation.objects.get(fiche=fiche)
                resume.premier_oeuf_pondu_jour = safe_int(resume_data.get('1er_o_pondu', {}).get('jour'))
                resume.premier_oeuf_pondu_mois = safe_int(resume_data.get('1er_o_pondu', {}).get('Mois'))
                resume.premier_poussin_eclos_jour = safe_int(resume_data.get('1er_p_eclos', {}).get('jour'))
                resume.premier_poussin_eclos_mois = safe_int(resume_data.get('1er_p_eclos', {}).get('Mois'))
                resume.premier_poussin_volant_jour = safe_int(resume_data.get('1er_p_volant', {}).get('jour'))
                resume.premier_poussin_volant_mois = safe_int(resume_data.get('1er_p_volant', {}).get('Mois'))
                resume.nombre_oeufs_pondus = safe_int(resume_data.get('nombre_oeufs', {}).get('pondus')) or 0
                resume.nombre_oeufs_eclos = safe_int(resume_data.get('nombre_oeufs', {}).get('eclos')) or 0
                resume.nombre_oeufs_non_eclos = safe_int(resume_data.get('nombre_oeufs', {}).get('n_ecl')) or 0
                resume.nombre_poussins = safe_int(resume_data.get('nombre_poussins', {}).get('vol_t')) or 0
                resume.save()

            # Mise à jour de l'objet CausesEchec qui existe déjà
            if 'causes_echec' in donnees:
                causes_echec = CausesEchec.objects.get(fiche=fiche)
                causes_echec.description = donnees['causes_echec'].get('causes_d_echec') or ''
                causes_echec.save()

            # Ajout d'une remarque si elle existe
            if "remarque" in donnees and donnees["remarque"]:
                Remarque.objects.create(
                    fiche=fiche,
                    remarque=donnees["remarque"]
                )

            importation.statut = 'complete'
            importation.transcription.traite = True
            importation.save()
            importation.transcription.save()

            return True, f"Fiche d'observation #{fiche.num_fiche} créée avec succès"

        except ImportationEnCours.DoesNotExist:
            return False, "Importation non trouvée"
        except Exception as e:
            logger.error(f"Erreur lors de l'importation {importation_id}: {str(e)}")
            if 'importation' in locals():
                importation.statut = 'erreur'
                importation.save()
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
                return {"success": False, "message": "Aucun identifiant fourni pour la réinitialisation"}

            # Suppression de la fiche d'observation si elle existe
            if importation and importation.fiche_observation:
                fiche_id = importation.fiche_observation.num_fiche
                importation.fiche_observation.delete()
                logger.info(f"Fiche d'observation #{fiche_id} supprimée")

            # Marquer la transcription comme non traitée
            transcription.traite = False
            transcription.save()

            # Supprimer l'importation en cours
            if importation:
                importation.delete()
                logger.info(f"Importation pour {transcription.fichier_source} réinitialisée")

            return {
                "success": True,
                "message": f"L'importation de {transcription.fichier_source} a été réinitialisée avec succès"
            }

        except (ImportationEnCours.DoesNotExist, TranscriptionBrute.DoesNotExist) as e:
            logger.error(f"Erreur lors de la réinitialisation: {str(e)}")
            return {"success": False, "message": f"Importation ou transcription non trouvée: {str(e)}"}
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la réinitialisation: {str(e)}")
            return {"success": False, "message": f"Erreur lors de la réinitialisation: {str(e)}"}