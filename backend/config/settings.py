"""
Application Configuration Settings
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    
    # Database Configuration
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database')
    COURSES_DATA_PATH = os.path.join(DATABASE_PATH, 'courses_fall25')
    PLANS_DATA_PATH = os.path.join(DATABASE_PATH, 'last_plan.json')
    FIXED_COURSES_PATH = os.path.join(DATABASE_PATH, 'fixed_courses.json')
    
    # Frontend Configuration
    TEMPLATES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'templates')
    STATIC_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'frontend', 'static')
    
    # Optimization Settings
    MAX_CREDITS_PER_SEMESTER = 18
    MIN_CREDITS_PER_SEMESTER = 12
    MAX_SEMESTERS = 12

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 