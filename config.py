import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str) -> str:
    """
    Lee una variable de entorno y lanza ValueError si está ausente o vacía.
    Se llama durante la construcción de Config para que el servidor
    nunca arranque con claves secretas nulas.
    """
    value = os.getenv(name)
    if not value or not value.strip():
        raise ValueError(
            f"Variable de entorno requerida no configurada: '{name}'. "
            "Revisa tu archivo .env antes de iniciar la aplicación."
        )
    return value


class Config:
    # Base de datos
    SQLALCHEMY_DATABASE_URI = _require_env('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
    }

    # JWT — clave requerida; con None cualquier token sería trivialmente válido
    JWT_SECRET_KEY = _require_env('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_ALGORITHM = 'HS256'

    # Flask
    SECRET_KEY = _require_env('SECRET_KEY')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'

    # Zona horaria de la BD — configurable por entorno
    DB_TIMEZONE = os.getenv('TZ', 'America/Mexico_City')

    # Otros
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB