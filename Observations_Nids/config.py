"""
Configuration module for Observations_Nids project.
Uses Pydantic for settings validation and python-dotenv for environment variables.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Dans config.py, modifiez la classe DatabaseSettings et la fonction get_settings
class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    engine: str = "django.db.backends.mysql"
    name: str
    user: str
    password: str
    host: str
    port: str = "3306"

class CelerySettings(BaseSettings):
    broker_url: str = "redis://127.0.0.1:6379/0"
    result_backend: str = "redis://127.0.0.1:6379/0"
    task_serializer: str = "json"
    accept_content: list = ["json"]
    result_serializer: str = "json"
    timezone: str = "Europe/Paris"
    task_track_started: bool = True
    task_time_limit: int = 30 * 60  # 30 minutes
    worker_hijack_root_logger: bool = False
    # Configuration spécifique à Windows pour Celery
    if os.name == 'nt':
        CELERY_WORKER_CONCURRENCY: int = 1
        CELERY_WORKER_POOL: str = 'solo'

    class Config:
        env_prefix = "CELERY_"  # Chercher les variables préfixées par CELERY_
        extra = "ignore"  # Ignore extra fields not defined in the model

class Settings(BaseSettings):
    """
    Project settings loaded from environment variables.

    This class uses Pydantic to validate settings and provide default values.
    Environment variables are loaded using python-dotenv.
    """
    # Core Django settings
    SECRET_KEY: str
    DEBUG: bool = False
    ALLOWED_HOSTS: List[str] = Field(default_factory=lambda: ["localhost", "127.0.0.1"])

    gemini_api_key: Optional[str] = None

    # Celery settings (nouveau)
    celery: CelerySettings = Field(default_factory=CelerySettings)

    # Database settings
    DATABASE: DatabaseSettings

    # Custom settings
    USE_DEBUG_TOOLBAR: bool = False
    SESSION_COOKIE_AGE: int = 3600
    SESSION_EXPIRE_AT_BROWSER_CLOSE: bool = True

    # Media and static settings
    MEDIA_ROOT: str = str(BASE_DIR / "media")
    STATIC_ROOT: str = str(BASE_DIR / "static")

    # Version
    VERSION: str = "1.1.0"

    def get_database_config(self) -> dict:
        """Return database configuration in Django format."""
        return {
            "default": {
                "ENGINE": self.DATABASE.engine,
                "NAME": self.DATABASE.name,
                "USER": self.DATABASE.user,
                "PASSWORD": self.DATABASE.password,
                "HOST": self.DATABASE.host,
                "PORT": self.DATABASE.port,
            }
        }

    class Config:
        """Pydantic config for environment variables."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        extra = "ignore"  # Ignore extra fields not defined in the model

    @validator("ALLOWED_HOSTS", pre=True)
    def validate_allowed_hosts(cls, v):
        """Valider et nettoyer les valeurs de ALLOWED_HOSTS."""
        if isinstance(v, str):
            # Si c'est une chaîne, la diviser par des virgules
            hosts = [host.strip() for host in v.split(",") if host.strip()]
            return hosts if hosts else ["localhost", "127.0.0.1"]
        elif isinstance(v, list):
            # Si c'est déjà une liste, nettoyer chaque élément
            return [str(host).strip() for host in v if str(host).strip()]
        return ["localhost", "127.0.0.1"]

def get_settings() -> Settings:
    """
    Get settings from environment variables.

    This function creates a Settings instance with values from environment variables.
    For database settings, it uses the DB_* environment variables.
    """
    database_settings = DatabaseSettings(
        name=os.environ.get("DB_NAME", "NidsObservation"),
        user=os.environ.get("DB_USER", "jms"),
        password=os.environ.get("DB_PASSWORD", "pointeur"),
        host=os.environ.get("DB_HOST", "192.168.1.176"),
        port=os.environ.get("DB_PORT", "3306"),
    )

    celery_settings = CelerySettings()
    #     broker_url=os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0"),
    #     result_backend=os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0"),
    #     # Les autres paramètres ont des valeurs par défaut dans la classe
    # )

    return Settings(
        DATABASE=database_settings,
        SECRET_KEY=os.environ.get("SECRET_KEY", "django-insecure-^tzqm_vr2-7f#2p10rehlk4pr9!z8z^!3atbbwq@2!%h_$n2f0"),
        DEBUG=os.environ.get("DEBUG", "False").lower() in ("true", "1", "t"),
        USE_DEBUG_TOOLBAR=os.environ.get("USE_DEBUG_TOOLBAR", "False").lower() in ("true", "1", "t"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", None),
        # Ajouter les paramètres Celery
        celery=celery_settings,
    )
