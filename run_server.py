#!/usr/bin/env python3
"""
Script to run the Course Planner servers with proper path setup
"""

import sys
import os
import argparse

def main():
    parser = argparse.ArgumentParser(description='Run Course Planner servers')
    parser.add_argument('--server', choices=['main', 'api'], default='main',
                       help='Which server to run (main or api)')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host to bind to')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to bind to')
    parser.add_argument('--debug', action='store_true',
                       help='Run in debug mode')
    
    args = parser.parse_args()
    
    # Add the current directory to Python path
    sys.path.insert(0, os.path.dirname(__file__))
    
    if args.server == 'main':
        from backend.app.main_app import app
        print("🚀 Starting main Course Planner server...")
    else:
        from backend.app.api_app import app
        print("🚀 Starting API Course Planner server...")
    
    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug
    )

if __name__ == '__main__':
    main() 