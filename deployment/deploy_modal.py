#!/usr/bin/env python3
"""
Deployment script for GovQuery Modal functions.
This script deploys your T5 and SQLCoder models to Modal.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False


def main():
    """Deploy the Modal functions."""
    print("🚀 Deploying GovQuery NL2SQL models to Modal...")
    
    # Check if modal is installed
    if not run_command("modal --version", "Checking Modal CLI installation"):
        print("❌ Modal CLI not found. Please install it with: pip install modal")
        return 1
    
    # Deploy the app using Modal CLI
    if not run_command("modal deploy ../core/modal_deployment.py", "Deploying Modal app"):
        print("❌ Deployment failed")
        return 1
    
    print("✅ Modal functions deployed successfully!")
    print("\n📋 Next steps:")
    print("1. Test the deployment with: python example_usage.py")
    print("2. Start the API server with: python api.py")
    
    return 0


if __name__ == "__main__":
    exit(main())
