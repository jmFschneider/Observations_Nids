"""
Script pour nettoyer complètement Redis des données Celery.
À utiliser quand la purge normale ne fonctionne pas.

Usage:
    python clean_redis_celery.py
"""

import redis

# Connexion à Redis
r = redis.Redis(host='127.0.0.1', port=6379, db=0, decode_responses=True)

print("=" * 60)
print("  NETTOYAGE COMPLET DE REDIS - DONNÉES CELERY")
print("=" * 60)

# Lister toutes les clés Celery
print("\n🔍 Recherche des clés Celery dans Redis...")

celery_keys: list[str] = []
patterns = ['celery*', '*task-meta*', '_kombu*', 'unacked*']

for pattern in patterns:
    keys = r.keys(pattern)
    if isinstance(keys, list):
        celery_keys.extend(keys)

if not celery_keys:
    print("✅ Aucune clé Celery trouvée dans Redis")
else:
    print(f"\n📦 {len(celery_keys)} clé(s) Celery trouvée(s):")
    for key in celery_keys[:20]:  # Limiter l'affichage
        key_type = r.type(key)
        print(f"  - {key} (type: {key_type})")

    if len(celery_keys) > 20:
        print(f"  ... et {len(celery_keys) - 20} autres clés")

    # Demander confirmation
    print("\n⚠️  ATTENTION: Cette opération va supprimer TOUTES ces clés!")
    response = input("Voulez-vous continuer ? (oui/non): ")

    if response.lower() in ['oui', 'o', 'yes', 'y']:
        print("\n🗑️  Suppression des clés...")
        deleted = 0
        for key in celery_keys:
            r.delete(key)
            deleted += 1
        print(f"✅ {deleted} clé(s) supprimée(s)")
    else:
        print("❌ Opération annulée")

print("\n✅ Terminé !")
