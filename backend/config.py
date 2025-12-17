import os
from datetime import timedelta


class Config:
    """应用程序配置类"""

    # Flask Configuration
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    TESTING = os.getenv('TESTING', 'False').lower() == 'true'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///server_manager.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = DEBUG

    # JWT configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=int(os.getenv('JWT_EXPIRATION_HOURS', 24)))

    # Encryption key for passwords (must be 32 bytes)
    # SECURITY: In production, set this via environment variable
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    default_key = 'encryption-key-change-in-production-must-be-32-bytes-long!'
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', default_key)

    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    # Rate Limiting
    RATELIMIT_ENABLED = os.getenv('RATELIMIT_ENABLED', 'True').lower() == 'true'
    RATELIMIT_STORAGE_URL = os.getenv('RATELIMIT_STORAGE_URL', 'memory://')

    # SSH Configuration
    SSH_TIMEOUT = int(os.getenv('SSH_TIMEOUT', 10))

    # Server Check Configuration
    PING_TIMEOUT = int(os.getenv('PING_TIMEOUT', 3))
    PORT_TIMEOUT = int(os.getenv('PORT_TIMEOUT', 5))

    # Concurrent server checking configuration
    # Maximum number of concurrent workers for checking servers
    CHECK_MAX_WORKERS = int(os.getenv('CHECK_MAX_WORKERS', 10))

    # Server Import Configuration
    # In Docker: mount host directory to /app/server_files and set SERVER_FILES_DIR=/app/server_files
    # On host: set SERVER_FILES_DIR to actual path (e.g., /home/Python/服务器)
    SERVER_FILES_DIR = os.getenv('SERVER_FILES_DIR', '/app/server_files')

    # Warn if using default keys in production (not DEBUG and not TESTING)
    # In development mode (DEBUG=True), warnings are suppressed since it's expected
    # to use default keys for local development
    if ENCRYPTION_KEY == default_key and not TESTING and not DEBUG:
        import warnings
        warnings.warn(
            "Using default ENCRYPTION_KEY! "
            "Set ENCRYPTION_KEY environment variable in production.",
            stacklevel=2
        )

    if SECRET_KEY == 'your-secret-key-change-in-production' and not TESTING and not DEBUG:
        import warnings
        warnings.warn(
            "Using default SECRET_KEY! "
            "Set SECRET_KEY environment variable in production.",
            stacklevel=2
        )
