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
    VERSION: str = "1.0.2"
    
    #Project settings loaded from environment variables.
    # Autres paramètres...
    
    # Modifiez la configuration de la base de données
    db_name: str
    db_user: str
    db_password: str
    db_host: str
    db_port: str = "3306"

    def get_database_config(self) -> dict:
        """Return database configuration in Django format."""
        return {
            "default": {
                "ENGINE": "django.db.backends.mysql",
                "NAME": self.db_name,
                "USER": self.db_user,
                "PASSWORD": self.db_password,
                "HOST": self.db_host,
                "PORT": self.db_port,
            }
        }

    class Config:
        """Pydantic config for environment variables."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
    
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
    
    return Settings(
        DATABASE=database_settings,
        SECRET_KEY=os.environ.get("SECRET_KEY", "django-insecure-^tzqm_vr2-7f#2p10rehlk4pr9!z8z^!3atbbwq@2!%h_$n2f0"),
        DEBUG=os.environ.get("DEBUG", "False").lower() in ("true", "1", "t"),
        USE_DEBUG_TOOLBAR=os.environ.get("USE_DEBUG_TOOLBAR", "False").lower() in ("true", "1", "t"),
        db_name=os.environ.get("DB_NAME", "NidsObservation"),
        db_user=os.environ.get("DB_USER", "jms"),
        db_password=os.environ.get("DB_PASSWORD", "pointeur"),
        db_host=os.environ.get("DB_HOST", "192.168.1.176"),
        db_port=os.environ.get("DB_PORT", "3306"),
        gemini_api_key=os.environ.get("GEMINI_API_KEY", None),
    )