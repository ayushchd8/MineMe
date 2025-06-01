import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Base configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Database configuration - use .env variable or fallback to SQLite
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///salesforce_sync.db'
    
    # Salesforce OAuth Configuration
    SF_CONSUMER_KEY = os.environ.get('SF_CONSUMER_KEY') or '3MVG9VMBZCsTL9hmxNA4cJ.i0F0z1BiQSl4FtsaFG.mqlZgIIg4CA7Q9ybNLEf55w2zxS_N9kVJtRyZSnvh3.'
    SF_CONSUMER_SECRET = os.environ.get('SF_CONSUMER_SECRET') or '0F2399B4117FDCECAAF6A86320E3BB6F2F644B5E1C61635CDCBE84B09FA69ADB'
    SF_REDIRECT_URI = os.environ.get('SF_REDIRECT_URI') or 'http://localhost:5001/api/auth/callback'
    SF_DOMAIN = os.environ.get('SF_DOMAIN') or 'login'

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
