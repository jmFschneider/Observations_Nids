"""
Health check endpoint pour Docker et monitoring
"""

from django.db import connection
from django.http import JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET


@never_cache
@require_GET
def health_check(request):
    """
    Endpoint de health check pour Docker et load balancers.
    Vérifie que l'application et la base de données sont opérationnelles.

    Returns:
        JsonResponse avec status 200 si tout va bien, 503 sinon
    """
    try:
        # Vérifier la connexion à la base de données
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

        return JsonResponse(
            {
                "status": "healthy",
                "database": "connected",
            },
            status=200,
        )
    except Exception as e:
        return JsonResponse(
            {
                "status": "unhealthy",
                "error": str(e),
            },
            status=503,
        )
