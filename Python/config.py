import os
from datetime import timedelta
from typing import List, Dict, Any

class Config:
    """Base configuration class."""
    # Server
    PORT = int(os.getenv('PORT', 5000))
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://postgres@localhost:5050/postgres')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_MAX_CONNECTIONS', 20)),
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 5,
        'pool_timeout': int(os.getenv('DB_IDLE_TIMEOUT', 30000)) / 1000  # Convert to seconds
    }

    # Security
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', 86400))
    BCRYPT_ROUNDS = int(os.getenv('BCRYPT_ROUNDS', 12))
    
    # Session Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # File Upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
    
    # Email
    MAIL_SERVER = os.getenv('MAIL_HOST', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_FROM_ADDRESS')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH', './logs/app.log')
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', 900000)) / 1000  # Convert to seconds
    RATELIMIT_MAX_REQUESTS = int(os.getenv('RATE_LIMIT_MAX_REQUESTS', 100))

    @staticmethod
    def validate_config() -> None:
        """Validate required environment variables."""
        required_vars = [
            'DATABASE_URL',
            'SECRET_KEY',
            'MAIL_USERNAME',
            'MAIL_PASSWORD'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Override with more secure settings
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    
    # Stricter rate limiting
    RATELIMIT_MAX_REQUESTS = 50

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
