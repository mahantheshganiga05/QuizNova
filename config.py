"""
QuizNova — Configuration
=========================
Configuration classes for different environments.
All secrets loaded from environment variables via python-dotenv.
Never hardcode credentials in this file.
"""

import os
from dotenv import load_dotenv

# Load .env file in development
load_dotenv()


class BaseConfig:
    """
    Shared configuration values for all environments.
    """
    # -------------------------------------------------------------------------
    # Flask Core
    # -------------------------------------------------------------------------
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY') or 'change-me-in-production-use-secrets-token-hex-32'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    _raw_db_url = os.environ.get('DATABASE_URL')
    if _raw_db_url:
        if _raw_db_url.startswith('postgres://'):
            _raw_db_url = _raw_db_url.replace('postgres://', 'postgresql://', 1)
        if 'pg8000' in _raw_db_url:
            _raw_db_url = _raw_db_url.replace('?sslmode=require', '').replace('&sslmode=require', '')

    SQLALCHEMY_DATABASE_URI = _raw_db_url or 'mysql+pymysql://root:@localhost/quiznova'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }

    # -------------------------------------------------------------------------
    # File Uploads
    # -------------------------------------------------------------------------
    MAX_CONTENT_LENGTH = int(os.environ.get('UPLOAD_MAX_MB', 2)) * 1024 * 1024  # Default 2MB
    UPLOAD_FOLDER_PROFILES = os.path.join('static', 'uploads', 'profiles')
    CERTIFICATE_FOLDER = os.path.join('static', 'certificates')
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
    ALLOWED_CSV_EXTENSIONS = {'csv'}

    # -------------------------------------------------------------------------
    # Quiz Configuration
    # -------------------------------------------------------------------------
    QUIZ_MAX_VIOLATIONS = int(os.environ.get('MAX_VIOLATIONS', 3))
    QUIZ_DEFAULT_QUESTIONS = 20
    QUIZ_DEFAULT_TIME_MINUTES = 30
    QUIZ_PASS_THRESHOLD = int(os.environ.get('CERTIFICATE_PASS_THRESHOLD', 60))

    # -------------------------------------------------------------------------
    # Certificate Configuration
    # -------------------------------------------------------------------------
    CERTIFICATE_ENABLED = os.environ.get('CERTIFICATE_ENABLED', '1') == '1'
    CERTIFICATE_INSTRUCTOR_SIGNATURE = os.path.join('static', 'images', 'instructor_signature.png')
    CERTIFICATE_OFFICIAL_SEAL = os.path.join('static', 'images', 'official_seal.png')

    # -------------------------------------------------------------------------
    # Email Configuration (optional in v1)
    # -------------------------------------------------------------------------
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@quiznova.com')
    MAIL_ENABLED = bool(MAIL_USERNAME and MAIL_PASSWORD)

    # -------------------------------------------------------------------------
    # Cloudinary (optional CDN — falls back to local storage)
    # -------------------------------------------------------------------------
    CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
    CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
    CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')
    CLOUDINARY_ENABLED = bool(CLOUDINARY_CLOUD_NAME and CLOUDINARY_API_KEY)

    # -------------------------------------------------------------------------
    # AI API Configuration (stubs — v1 architecture only)
    # -------------------------------------------------------------------------
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    AI_ENABLED = False  # Force-disabled in v1

    # -------------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------------
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour
    SESSION_COOKIE_SECURE = False  # Overridden in ProductionConfig
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400 * 1  # 1 day

    # -------------------------------------------------------------------------
    # Pagination
    # -------------------------------------------------------------------------
    LEADERBOARD_PER_PAGE = 50
    ADMIN_USERS_PER_PAGE = 20
    ADMIN_QUESTIONS_PER_PAGE = 25

    # -------------------------------------------------------------------------
    # Site Metadata
    # -------------------------------------------------------------------------
    SITE_NAME = 'QuizNova'
    SITE_TAGLINE = 'Test Your Knowledge. Ignite Your Potential.'
    SITE_URL = os.environ.get('SITE_URL', 'http://localhost:5000')


class DevelopmentConfig(BaseConfig):
    """Development environment — verbose errors, no HTTPS required."""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = False  # Set True to log all SQL queries
    WTF_CSRF_ENABLED = True


class TestingConfig(BaseConfig):
    """Testing environment — in-memory DB, CSRF disabled."""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    CERTIFICATE_ENABLED = True
    MAIL_ENABLED = True


class ProductionConfig(BaseConfig):
    """Production environment — strict security, no debug."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Requires HTTPS
    WTF_CSRF_ENABLED = True
    SQLALCHEMY_ECHO = False

    @classmethod
    def validate(cls):
        """Validate all required production environment variables are set."""
        required = [
            'FLASK_SECRET_KEY',
            'DATABASE_URL',
        ]
        missing = [key for key in required if not os.environ.get(key)]
        if missing:
            raise EnvironmentError(
                f"Missing required environment variables for production: {', '.join(missing)}"
            )


# =============================================================================
# Configuration Registry
# =============================================================================
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
