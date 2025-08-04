"""
Flask Application Factory
Creates and configures the Flask application.
"""

import sys
import os
from flask import Flask
from backend.config.settings import Config


def create_app(config_class=Config):
    """
    Application factory function.
    
    Args:
        config_class: Configuration class to use
        
    Returns:
        Configured Flask application
    """
    # Add the project root to Python path
    try:
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        sys.path.append(project_root)
    except NameError:
        # When running with exec() or in certain contexts
        pass
    
    app = Flask(__name__, 
                template_folder='../../frontend/templates',
                static_folder='../../frontend/static')
    app.config.from_object(config_class)
    
    # Register blueprints
    from backend.app.routes.web_routes import web_bp
    from backend.app.routes.api_routes import api_bp
    
    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    
    return app 