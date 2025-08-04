#!/usr/bin/env python3
"""
Setup script for Course Planner Application
"""

import os
import sys
import shutil
from pathlib import Path

def create_env_file():
    """Create .env file from template if it doesn't exist"""
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if not env_file.exists() and env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit .env file with your actual API keys and configuration")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("❌ env.example file not found")

def create_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'frontend/static/css',
        'frontend/static/js',
        'database/migrations',
        'docs'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ Created necessary directories")

def check_dependencies():
    """Check if required dependencies are available"""
    try:
        import flask
        print("✅ Flask is installed")
    except ImportError:
        print("❌ Flask is not installed. Run: pip install -r backend/requirements.txt")
    
    try:
        import gurobipy
        print("✅ Gurobi is installed")
    except ImportError:
        print("❌ Gurobi is not installed. Please install Gurobi and gurobipy")
    
    try:
        import openai
        print("✅ OpenAI is installed")
    except ImportError:
        print("❌ OpenAI is not installed. Run: pip install openai")

def main():
    """Main setup function"""
    print("🚀 Setting up Course Planner Application...")
    print()
    
    create_directories()
    print()
    
    create_env_file()
    print()
    
    check_dependencies()
    print()
    
    print("📋 Next steps:")
    print("1. Edit .env file with your API keys")
    print("2. Install missing dependencies if any")
    print("3. Run: python app.py")
    print()
    print("🎉 Setup complete!")

if __name__ == '__main__':
    main() 