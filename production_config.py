"""
Production Configuration for STR Compliance Toolkit

This module contains production-ready configuration settings for deploying the
Short Term Rental Compliance Toolkit in a production environment.
"""

import os
from datetime import timedelta


class ProductionConfig:
    """Production configuration settings"""
    
    # ============= SECURITY SETTINGS =============
    
    # Session Configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET')
    if not SECRET_KEY:
        raise ValueError("SESSION_SECRET environment variable is required for production")
    
    # Session Security
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)  # Session timeout
    
    # CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour CSRF token lifetime
    
    # ============= DATABASE SETTINGS =============
    
    # Database URL (required)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        raise ValueError("DATABASE_URL environment variable is required for production")
    
    # Database Connection Pool Settings
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 20,          # Number of persistent connections
        'pool_recycle': 3600,     # Recycle connections every hour
        'pool_pre_ping': True,    # Verify connections before use
        'pool_timeout': 30,       # Timeout for getting connection
        'max_overflow': 30,       # Additional connections beyond pool_size
    }
    
    # Database Performance
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Disable event system overhead
    SQLALCHEMY_RECORD_QUERIES = False  # Disable query recording in production
    
    # ============= FLASK SETTINGS =============
    
    # Application Environment
    ENV = 'production'
    DEBUG = False
    TESTING = False
    
    # Template and Static File Settings
    TEMPLATES_AUTO_RELOAD = False  # Disable for performance
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year cache for static files
    
    # Request Size Limits
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # ============= LOGGING SETTINGS =============
    
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s [%(name)s] %(message)s'
    LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # Log File Configuration
    LOG_TO_FILE = True
    LOG_FILE_PATH = os.environ.get('LOG_FILE_PATH', '/var/log/str_tracker/app.log')
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB per log file
    LOG_FILE_BACKUP_COUNT = 5  # Keep 5 backup files
    
    # ============= PERFORMANCE SETTINGS =============
    
    # JSON Configuration
    JSON_SORT_KEYS = False  # Slightly faster JSON serialization
    JSONIFY_PRETTYPRINT_REGULAR = False  # Smaller response size
    
    # Response Compression (if using Flask-Compress)
    COMPRESS_MIMETYPES = [
        'text/html', 'text/css', 'text/xml',
        'application/json', 'application/javascript'
    ]
    COMPRESS_LEVEL = 6
    COMPRESS_MIN_SIZE = 500
    
    # ============= ADMIN SETTINGS =============
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
    if not ADMIN_PASSWORD:
        raise ValueError("ADMIN_PASSWORD environment variable is required for production")
    
    # ============= MONITORING SETTINGS =============
    
    # Health Check Configuration
    HEALTH_CHECK_ENABLED = True
    HEALTH_CHECK_DATABASE = True
    HEALTH_CHECK_DISK_SPACE = True
    HEALTH_CHECK_MEMORY = True
    
    # Monitoring Endpoints
    MONITORING_ENDPOINTS = ['/health', '/metrics', '/status']
    
    # ============= RATE LIMITING SETTINGS =============
    
    # API Rate Limits (requests per minute)
    RATE_LIMIT_API = os.environ.get('RATE_LIMIT_API', '100')
    RATE_LIMIT_LOGIN = os.environ.get('RATE_LIMIT_LOGIN', '10')
    RATE_LIMIT_SEARCH = os.environ.get('RATE_LIMIT_SEARCH', '50')
    
    # ============= CACHE SETTINGS =============
    
    # Cache Type (redis recommended for production)
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = 300  # 5 minutes default cache timeout
    
    # Redis Cache Configuration (if using Redis)
    CACHE_REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    # ============= BACKUP SETTINGS =============
    
    # Automated Backup Configuration
    BACKUP_ENABLED = os.environ.get('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_SCHEDULE = os.environ.get('BACKUP_SCHEDULE', '0 2 * * *')  # Daily at 2 AM
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', '30'))
    BACKUP_S3_BUCKET = os.environ.get('BACKUP_S3_BUCKET')  # Optional S3 backup
    
    # ============= SSL/TLS SETTINGS =============
    
    # SSL Configuration
    SSL_REDIRECT = os.environ.get('SSL_REDIRECT', 'true').lower() == 'true'
    SSL_CERT_PATH = os.environ.get('SSL_CERT_PATH')
    SSL_KEY_PATH = os.environ.get('SSL_KEY_PATH')
    
    # Security Headers
    SECURITY_HEADERS = {
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
        'Referrer-Policy': 'strict-origin-when-cross-origin'
    }
    
    # ============= ERROR HANDLING =============
    
    # Error Reporting
    ERROR_404_HELP = False  # Don't show debug info for 404s
    PROPAGATE_EXCEPTIONS = False  # Handle exceptions internally
    
    # Error Logging
    MAIL_ON_ERROR = os.environ.get('MAIL_ON_ERROR', 'false').lower() == 'true'
    ERROR_EMAIL_SUBJECT = 'STR Tracker Application Error'
    ERROR_EMAIL_SENDER = os.environ.get('ERROR_EMAIL_SENDER')
    ERROR_EMAIL_RECIPIENTS = os.environ.get('ERROR_EMAIL_RECIPIENTS', '').split(',')
    
    # SMTP Configuration for Error Emails
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')


class DevelopmentConfig:
    """Development configuration settings"""
    
    # Basic Settings
    ENV = 'development'
    DEBUG = True
    TESTING = False
    
    # Session Configuration
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'dev-secret-key-change-in-production')
    SESSION_COOKIE_SECURE = False  # Allow HTTP in development
    SESSION_COOKIE_HTTPONLY = True
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///str_compliance.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,
        'pool_pre_ping': True,
    }
    
    # Development Features
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    LOG_TO_FILE = False
    
    # CSRF (disabled for easier development)
    WTF_CSRF_ENABLED = False


class TestingConfig:
    """Testing configuration settings"""
    
    # Basic Settings
    ENV = 'testing'
    DEBUG = False
    TESTING = True
    
    # Session Configuration
    SECRET_KEY = 'test-secret-key'
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    
    # Database (in-memory SQLite for tests)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Logging
    LOG_LEVEL = 'ERROR'  # Minimal logging during tests
    LOG_TO_FILE = False


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """Get the appropriate configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default']) 