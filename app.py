#!/usr/bin/env python3
"""
Course Planner Application
Main entry point for the Flask application
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.server import app

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 