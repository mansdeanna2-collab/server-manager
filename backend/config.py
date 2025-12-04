import os
from datetime import timedelta

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///server_manager.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # Encryption key for passwords
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'encryption-key-change-in-production-must-be-32-bytes-long!')
