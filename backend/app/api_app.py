"""
API Application
Clean API application using the application factory pattern.
"""

from backend.app import create_app
from backend.config.settings import Config

app = create_app(Config)

# Override template folder for API-only app
app.template_folder = None
app.static_folder = None

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001) 