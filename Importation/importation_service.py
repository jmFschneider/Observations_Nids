# importation_service.py
import os
import json
import logging
from difflib import SequenceMatcher
from django.db import transaction
from django.conf import settings
from django.utils import timezone

from Observations.models import (
    Utilisateur, Espece, FicheObservation, Localisation,
    Nid, Observation, ResumeObservation, CausesEchec, Remarque
)
from .models import (
    TranscriptionBrute, EspeceCandidate, ObservateurCandidat, ImportationEnCours
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
                # Version simplifiée
                if contenu.startswith('```json') and contenu.endswith('```'):
                    contenu = contenu[7:-3].strip()  # Enlever ```json au début (7 caractères) et ``` à la fin (3 caractères)

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
                # Afficher plus de détails sur l'erreur
                erreur = f"Erreur de format JSON dans {fichier}: {str(e)}. Début du contenu: {contenu[:100] if 'contenu' in locals() else 'Non disponible'}"
                logger.error(erreur)
                resultats['erreurs'].append(erreur)
            except Exception as e:
                erreur = f"Erreur lors de l'importation de {fichier}: {str(e)}"
                logger.error(erreur)
                resultats['erreurs'].append(erreur)

        return resultats

    def extraire_donnees_candidats(self):
        """Extrait les espèces et observateurs candidats des transcriptions brutes"""
        transcriptions = TranscriptionBrute.objects.filter(traite=False)
        especes_ajoutees = 0
        observateurs_ajoutes = 0

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

                # Extraire l'observateur
                if 'informations_generales' in donnees and 'observateur' in donnees['informations_generales']:
                    nom_observateur = donnees['informations_generales']['observateur']
                    if nom_observateur and isinstance(nom_observateur, str):
                        # Vérifier si cet observateur existe déjà comme candidat
                        observateur, created = ObservateurCandidat.objects.get_or_create(
                            nom_complet_transcrit=nom_observateur
                        )
                        if created:
                            observateurs_ajoutes += 1

                            # Tenter une correspondance automatique
                            self._trouver_correspondance_observateur(observateur)

            except Exception as e:
                logger.error(
                    f"Erreur lors de l'extraction des candidats depuis {transcription.fichier_source}: {str(e)}")
                continue

        return {
            'especes_ajoutees': especes_ajoutees,
            'observateurs_ajoutes': observateurs_ajoutes
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

    def _trouver_correspondance_observateur(self, observateur_candidat):
        """Tente de trouver une correspondance pour un observateur candidat"""
        # Créer ou récupérer l'utilisateur
        utilisateur = self.creer_ou_recuperer_utilisateur(observateur_candidat.nom_complet_transcrit)

        # Associer l'utilisateur au candidat
        observateur_candidat.utilisateur_valide = utilisateur
        observateur_candidat.validation_manuelle = True
        observateur_candidat.save()

        return True

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

                # Extraire et vérifier l'observateur
                observateur_candidat = None
                if 'informations_generales' in donnees and 'observateur' in donnees['informations_generales']:
                    nom_observateur = donnees['informations_generales']['observateur']
                    if nom_observateur:
                        observateur_candidat = ObservateurCandidat.objects.filter(
                            nom_complet_transcrit=nom_observateur).first()

                # Créer l'importation en cours
                ImportationEnCours.objects.create(
                    transcription=transcription,
                    espece_candidate=espece_candidate,
                    observateur_candidat=observateur_candidat,
                    statut='en_attente'
                )
                importations_creees += 1

            except Exception as e:
                logger.error(
                    f"Erreur lors de la préparation de l'importation pour {transcription.fichier_source}: {str(e)}")
                continue

        return importations_creees

    # Dans Importation/importation_service.py, ajoutez cette méthode à la classe ImportationService:

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

            logger.info(f"Nouvel utilisateur créé depuis transcription: {utilisateur}")
            return utilisateur

    @transaction.atomic
    def finaliser_importation(self, importation_id):
        """Finalise l'importation d'une transcription en créant les entrées dans les tables principales"""
        try:
            importation = ImportationEnCours.objects.select_for_update().get(id=importation_id)

            # Vérifier si l'espèce et l'observateur sont validés
            if not importation.espece_candidate or not importation.espece_candidate.espece_validee:
                importation.statut = 'erreur'
                importation.save()
                return False, "Espèce non validée"

            if not importation.observateur_candidat or not importation.observateur_candidat.utilisateur_valide:
                importation.statut = 'erreur'
                importation.save()
                return False, "Observateur non validé"

            # Récupérer les données JSON
            donnees = importation.transcription.json_brut

            # Extraire l'année (utiliser l'année actuelle si non disponible)
            annee = timezone.now().year
            if 'informations_generales' in donnees and 'année' in donnees['informations_generales']:
                annee_str = donnees['informations_generales']['année']
                if annee_str and annee_str.isdigit():
                    annee = int(annee_str)

            # Créer la fiche d'observation
            fiche = FicheObservation.objects.create(
                observateur=importation.observateur_candidat.utilisateur_valide,
                espece=importation.espece_candidate.espece_validee,
                annee=annee,
                chemin_image=importation.transcription.fichier_source
            )

            # Enregistrer la référence à la fiche dans l'importation
            importation.fiche_observation = fiche

            # Mettre à jour la localisation
            if 'localisation' in donnees:
                loc = donnees['localisation']
                Localisation.objects.filter(fiche=fiche).update(
                    commune=loc.get('commune') or loc.get('IGN_50000') or 'Non spécifiée',
                    lieu_dit=loc.get('coordonnees_et_ou_lieu_dit') or 'Non spécifiée',
                    departement=loc.get('dep_t') or '00',
                    altitude=loc.get('altitude') or '0',
                    paysage=loc.get('paysage') or 'Non spécifié',
                    alentours=loc.get('alentours') or 'Non spécifié'
                )

            # Mettre à jour les informations du nid
            if 'nid' in donnees:
                nid_data = donnees['nid']
                nid_meme_couple = False
                if nid_data.get('nid_prec_t_meme_c_ple') in ['oui', 'Oui', 'OUI', 'true', 'True', 'TRUE', '1']:
                    nid_meme_couple = True

                # Essayer de convertir la hauteur en entier
                hauteur_nid = 0
                hauteur_str = nid_data.get('haut_nid') or '0'
                try:
                    # Remplacer la virgule par un point si nécessaire
                    hauteur_str = hauteur_str.replace(',', '.')
                    hauteur_nid = int(float(hauteur_str))
                except (ValueError, TypeError):
                    pass

                hauteur_couvert = 0
                couvert_str = nid_data.get('h_c_vert') or '0'
                try:
                    couvert_str = couvert_str.replace(',', '.')
                    hauteur_couvert = int(float(couvert_str))
                except (ValueError, TypeError):
                    pass

                Nid.objects.filter(fiche=fiche).update(
                    nid_prec_t_meme_couple=nid_meme_couple,
                    hauteur_nid=hauteur_nid,
                    hauteur_couvert=hauteur_couvert,
                    details_nid=nid_data.get('nid') or 'Aucun détail'
                )

            # Créer les observations
            if 'tableau_donnees' in donnees and isinstance(donnees['tableau_donnees'], list):
                for obs in donnees['tableau_donnees']:
                    # Essayer de construire une date valide
                    try:
                        jour = int(obs.get('Jour') or 1)
                        mois = int(obs.get('Mois') or 1)
                        heure = int(obs.get('Heure') or 12)
                        minute = 0

                        date_obs = timezone.datetime(annee, mois, jour, heure, minute)

                        # Convertir en format datetime-aware
                        date_obs = timezone.make_aware(date_obs)

                        nombre_oeufs = int(obs.get('Nombre_oeuf') or 0)
                        nombre_poussins = int(obs.get('Nombre_pou') or 0)

                        Observation.objects.create(
                            fiche=fiche,
                            date_observation=date_obs,
                            nombre_oeufs=nombre_oeufs,
                            nombre_poussins=nombre_poussins,
                            observations=obs.get('observations') or ''
                        )
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Impossible de créer l'observation pour la fiche {fiche.num_fiche}: {str(e)}")
                        continue

            # Mettre à jour le résumé de l'observation
            if 'tableau_donnees_2' in donnees:
                resume_data = donnees['tableau_donnees_2']
                nombre_poussins_data = None

                if 'nombre_poussins' in resume_data and resume_data['nombre_poussins']:
                    nombre_poussins_data = resume_data['nombre_poussins'][0] if resume_data['nombre_poussins'] else None

                nombre_poussins_total = 0
                if nombre_poussins_data:
                    # Prendre la valeur 'vol_t' si disponible
                    if 'vol_t' in nombre_poussins_data and nombre_poussins_data['vol_t']:
                        try:
                            nombre_poussins_total = int(nombre_poussins_data['vol_t'])
                        except (ValueError, TypeError):
                            pass

                ResumeObservation.objects.filter(fiche=fiche).update(
                    nombre_poussins=nombre_poussins_total
                )

            # Ajouter causes d'échec si disponibles
            if 'causes_echec' in donnees and donnees['causes_echec'].get('causes_d_echec'):
                CausesEchec.objects.filter(fiche=fiche).update(
                    description=donnees['causes_echec'].get('causes_d_echec')
                )

            # Ajouter une remarque avec le nom du fichier source
            Remarque.objects.create(
                fiche=fiche,
                remarque=f"Importé depuis le fichier {importation.transcription.fichier_source}"
            )

            # Marquer l'importation comme terminée
            importation.statut = 'complete'
            importation.save()

            # Marquer la transcription comme traitée
            importation.transcription.traite = True
            importation.transcription.save()

            return True, f"Fiche d'observation #{fiche.num_fiche} créée avec succès"

        except ImportationEnCours.DoesNotExist:
            return False, "Importation non trouvée"
        except Exception as e:
            logger.error(f"Erreur lors de la finalisation de l'importation {importation_id}: {str(e)}")
            if 'importation' in locals():
                importation.statut = 'erreur'
                importation.save()
            return False, str(e)

    def reinitialiser_importation(self, importation_id=None, fichier_source=None):
        """
        Réinitialise une importation pour permettre de recommencer le processus

        Args:
            importation_id: ID de l'importation à réinitialiser
            fichier_source: Nom du fichier source à réinitialiser (alternative à importation_id)

        Returns:
            dict: Résultat de l'opération avec succès (bool) et message (str)
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
