#!/usr/bin/env python3
"""
Setup script for GovQuery Templated API.
"""

import os
import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    return True

def install_requirements():
    """Install requirements."""
    print("\n📦 Installing requirements...")
    
    try:
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ], check=True)
        print("✅ Requirements installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False

def create_env_file():
    """Create .env file with default values."""
    env_file = Path(".env")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("\n📝 Creating .env file...")
    
    env_content = """# GovQuery Environment Variables
# Replace with your actual Modal credentials
MODAL_TOKEN_ID=your-modal-token-id
MODAL_TOKEN_SECRET=your-modal-token-secret
MODAL_APP_NAME=govquery-nl2sql-main

# Optional: Override default values
# MODAL_APP_NAME=your-custom-app-name
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def test_imports():
    """Test if key imports work."""
    print("\n🧪 Testing imports...")
    
    try:
        import modal
        import fastapi
        import uvicorn
        import pydantic
        import requests
        print("✅ All key imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🎯 GovQuery Templated API Setup")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install requirements
    if not install_requirements():
        return 1
    
    # Create .env file
    if not create_env_file():
        return 1
    
    # Test imports
    if not test_imports():
        return 1
    
    print("\n🎉 Setup completed successfully!")
    print("\n" + "=" * 50)
    print("🚀 Quick Start:")
    print("1. Run demo:     python launch_demo.py")
    print("2. Manual start: python templated_api.py")
    print("3. Open frontend: open frontend.html")
    print("\n📖 Documentation: TEMPLATED_API_README.md")
    print("🧪 Test API:     python test_templated_api.py")
    print("=" * 50)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
