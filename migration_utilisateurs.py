# migration_utilisateurs.py

"""
Script pour migrer les utilisateurs de l'application Observations vers l'application Administration.

À exécuter en tant que script Django (python manage.py shell < migration_utilisateurs.py)
"""

import sys
import logging
from django.db import transaction

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("migration_utilisateurs.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

try:
    # Importation des modèles anciens et nouveaux
    from Observations.models import Utilisateur as AncienUtilisateur
    from Administration.models import Utilisateur as NouvelUtilisateur

    logger.info("Début de la migration des utilisateurs")

    # Obtenir tous les utilisateurs existants
    anciens_utilisateurs = AncienUtilisateur.objects.all()
    logger.info(f"Nombre d'utilisateurs à migrer : {anciens_utilisateurs.count()}")

    # Démarrer une transaction pour assurer l'intégrité des données
    with transaction.atomic():
        for ancien in anciens_utilisateurs:
            try:
                # Créer un nouvel utilisateur avec les mêmes données
                nouveau = NouvelUtilisateur(
                    id=ancien.id,  # Conserver le même ID pour maintenir les relations
                    username=ancien.username,
                    password=ancien.password,  # Le hash de mot de passe est copié tel quel
                    email=ancien.email,
                    first_name=ancien.first_name,
                    last_name=ancien.last_name,
                    is_active=ancien.is_active,
                    is_staff=ancien.is_staff,
                    is_superuser=ancien.is_superuser,
                    date_joined=ancien.date_joined,
                    role=ancien.role,
                    est_valide=ancien.est_valide,
                    est_transcription=ancien.est_transcription
                )
                nouveau.save()
                logger.info(f"Utilisateur migré avec succès : {ancien.username}")
            except Exception as e:
                logger.error(f"Erreur lors de la migration de l'utilisateur {ancien.username}: {str(e)}")
                raise  # Annuler la transaction en cas d'erreur

    logger.info("Migration des utilisateurs terminée avec succès")

except ImportError as e:
    logger.error(f"Erreur d'importation: {str(e)}")
    logger.error("Assurez-vous que ce script est exécuté après avoir créé les modèles dans les deux applications")
    sys.exit(1)
except Exception as e:
    logger.error(f"Erreur inattendue: {str(e)}")
    sys.exit(1)