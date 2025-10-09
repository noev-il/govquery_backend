#!/usr/bin/env python3
"""
Install requirements for the GovQuery templated API.
"""

import subprocess
import sys
from pathlib import Path

def install_requirements():
    """Install requirements from requirements.txt"""
    requirements_file = Path(__file__).parent / "requirements.txt"
    
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    print("📦 Installing requirements...")
    print("=" * 50)
    
    try:
        # Install requirements
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Requirements installed successfully!")
        print("\nInstalled packages:")
        print(result.stdout)
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Installation failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_installation():
    """Check if key packages are installed correctly."""
    print("\n🔍 Checking installation...")
    
    packages = [
        "modal",
        "fastapi", 
        "uvicorn",
        "pydantic",
        "requests"
    ]
    
    all_good = True
    for package in packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            all_good = False
    
    return all_good

def main():
    """Main installation function."""
    print("🎯 GovQuery Requirements Installer")
    print("=" * 50)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Installation failed. Please check the error messages above.")
        return 1
    
    # Check installation
    if not check_installation():
        print("\n⚠️ Some packages may not be installed correctly.")
        print("Try running: pip install -r requirements.txt")
        return 1
    
    print("\n🎉 All requirements installed successfully!")
    print("\nNext steps:")
    print("1. Run the demo: python launch_demo.py")
    print("2. Or start manually: python templated_api.py")
    print("3. Open frontend: open frontend.html")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
