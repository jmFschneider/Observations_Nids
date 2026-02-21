# Optimisation OCR — Axes 3 et 4

> **Date** : Février 2026
> **Branche** : `optim/OCR_axe1`
> **Fichiers modifiés** : `ocr/tasks.py`, `ocr/views.py`, `ocr/urls.py`,
> `observations_nids/celery.py`, `docker/docker-compose.yml`,
> `ocr/templates/ocr/selection_images.html`, `ocr/templates/ocr/home.html`
> **Fichier créé** : `ocr/templates/ocr/historique.html`

---

## Axe 3 — Rate Limiting Distribué

### Contexte

Chaque worker Celery instanciait un `RateLimiter` en mémoire locale. Avec
`--concurrency=2` en production, le quota Gemini (60 RPM) n'était pas respecté
globalement : chaque processus maintenait son propre compteur indépendant.

### 3.1 — `RedisRateLimiter` (`ocr/tasks.py`)

La classe `RateLimiter` est remplacée par `RedisRateLimiter`, qui coordonne les
requêtes entre tous les workers via Redis.

**Mécanisme** : fenêtre fixe par minute avec `INCR` atomique.

```
Clé Redis : ocr:rate_limiter:{minute_bucket}
TTL       : 70 secondes
Limite    : 60 INCR par fenêtre
```

À chaque appel à `wait_if_needed()` :
1. `INCR` atomique sur la clé de la minute courante
2. Si `count <= 60` → slot accordé, on procède
3. Si `count > 60` → attente jusqu'à la prochaine fenêtre (max 5 s par itération)

**Fallback** : si Redis est inaccessible à l'initialisation, la classe bascule
en mode local (comportement identique à l'ancien `RateLimiter`) avec un warning
visible dans les logs du worker.

**Gestion des erreurs Redis ponctuelles** : une exception `RedisError` dans
`wait_if_needed()` génère un warning et laisse passer la requête sans bloquer la
tâche.

**Import ajouté** : `import redis` (paquet déjà présent via la dépendance Celery).
**Type hint** : `cast(int, self._redis.incr(key))` pour satisfaire mypy (le stub
redis-py expose `Awaitable[Any] | Any` même sur le client synchrone).

### 3.2 — Queue dédiée `ocr`

**`ocr/tasks.py`** : ajout de `queue='ocr'` sur le décorateur `@shared_task`.

**`observations_nids/celery.py`** : activation de `task_routes` (bloc commenté
remplacé) :

```python
task_routes={
    'ocr.process_images_production': {'queue': 'ocr'},
}
```

**`docker/docker-compose.yml`** : le worker Docker écoute désormais les deux
queues pour ne pas perdre les tâches générales (ingest, etc.) ni les tâches OCR :

```
celery -A observations_nids worker --loglevel=info --concurrency=2 -Q celery,ocr
```

La queue par défaut Celery s’appelle `celery` (pas `default`) ; les tâches sans
route (ex. `ingest.process_json_batch`) partent donc en `celery`. Il faut
toujours utiliser `-Q celery,ocr` et non `-Q default,ocr`.

**Monitoring** : la clé Redis du rate limiter est observable en direct :

```bash
redis-cli KEYS "ocr:rate_limiter:*"
redis-cli GET ocr:rate_limiter:<bucket>
```

---

## Axe 4 — Expérience Utilisateur et Observabilité

### 4.1 — Logs de progression en temps réel

**`ocr/views.py`** : `verifier_progression` retourne désormais le champ `logs`
dans le payload JSON quand le statut est `PROGRESS` :

```python
'logs': info.get('logs', []),
```

Les logs sont accumulés dans `ocr/tasks.py` par la fonction `log_progress()`
(inchangée) et stockés dans le meta Celery sous la clé `logs` (liste de dicts
`{timestamp, message, level}`).

**`ocr/templates/ocr/selection_images.html`** :

- Bloc CSS `{% block extra_css %}` avec les classes `.ocr-log-content` et
  `.ocr-log-entry` (thème sombre, bordure colorée selon le niveau).
- Zone `#log-container` (masquée initialement) qui s'affiche au premier log.
- Bouton "Effacer" le journal sans interrompre la tâche.
- Fonction JS `updateLogs(logs)` : ajout incrémental des nouveaux logs avec
  auto-scroll vers le bas. `escapeHtml()` protège contre les injections XSS.

### 4.2 — Historique des transcriptions OCR

**`ocr/views.py`** : nouvelle vue `historique_ocr`.

```python
qs = TranscriptionOCR.objects.select_related('fiche')
if statut in ('succes', 'erreur', 'en_cours'):
    qs = qs.filter(statut=statut)
paginator = Paginator(qs, 25)
```

Filtre par statut via paramètre GET `?statut=`. Pagination à 25 lignes.
`select_related('fiche')` évite le N+1 sur le lien vers `FicheObservation`.

**`ocr/urls.py`** : route `historique/` → `historique_ocr`, nom `ocr:historique_ocr`.

**`ocr/templates/ocr/historique.html`** (nouveau fichier) :

- Tableau : date, chemin image, badge statut coloré, durée, lien fiche (#N),
  bouton téléchargement JSON.
- Filtres statut en groupe de boutons Bootstrap (Tous / Succès / Erreurs / En cours).
- Pagination avec fenêtre ±3 pages autour de la page courante.
- Tooltip Bootstrap sur le message d'erreur des lignes en échec.

**`ocr/templates/ocr/home.html`** : bouton "Historique" ajouté dans la zone
d'actions principale, pointant vers `ocr:historique_ocr`.

### 4.3 — Page de résultats post-batch

Le `confirm()` JavaScript de `selection_images.html` est remplacé par la
fonction `showResults(data)` qui injecte un bloc Bootstrap dans `#results-container`.

Ce bloc affiche :
- Trois compteurs : **Réussis** (vert) / **Ignorés** (orange) / **Erreurs** (rouge)
- La liste des fichiers en erreur avec leur message si non vide
- Un bouton "Importer les JSON" vers `ingest:accueil_importation`

En cas d'erreur Celery (`status === 'FAILURE'`), la barre de progression passe
en rouge et le bouton de lancement est réactivé pour permettre un nouvel essai.

### 4.4 — Sélection du modèle Gemini

**Annulé (YAGNI)** : un seul modèle est disponible en production
(`gemini-3-flash-preview`). Un sélecteur serait vide de sens. L'ajout d'options
se fera lorsque de nouveaux modèles seront qualifiés pour le pipeline.
