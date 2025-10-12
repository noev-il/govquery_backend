#!/usr/bin/env python3
"""
Launch script for the GovQuery templated API demo.
Starts the backend server and opens the frontend in a browser.
"""

import os
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    try:
        import uvicorn
        import fastapi
        import requests
        print("✅ All dependencies found")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install with: pip install uvicorn fastapi requests")
        return False

def start_backend():
    """Start the templated API backend."""
    print("🚀 Starting GovQuery Templated API...")
    
    # Modal credentials should be set via environment variables
    # Set these before running: export MODAL_TOKEN_ID="your-id" MODAL_TOKEN_SECRET="your-secret"
    if not os.environ.get("MODAL_TOKEN_ID") or not os.environ.get("MODAL_TOKEN_SECRET"):
        raise ValueError("MODAL_TOKEN_ID and MODAL_TOKEN_SECRET must be set as environment variables")
    os.environ["MODAL_APP_NAME"] = "govquery-nl2sql-main"
    
    try:
        # Start the server
        subprocess.run([
            sys.executable, "templated_api.py"
        ], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Server failed to start: {e}")
        return False
    
    return True

def open_frontend():
    """Open the frontend in a browser."""
    frontend_path = Path(__file__).parent / "frontend.html"
    frontend_url = f"file://{frontend_path.absolute()}"
    
    print(f"🌐 Opening frontend: {frontend_url}")
    webbrowser.open(frontend_url)

def wait_for_server(max_wait=30):
    """Wait for the server to be ready."""
    import requests
    
    print("⏳ Waiting for server to start...")
    for i in range(max_wait):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ Server is ready!")
                return True
        except:
            pass
        
        time.sleep(1)
        if i % 5 == 0 and i > 0:
            print(f"   Still waiting... ({i}s)")
    
    print("❌ Server failed to start within 30 seconds")
    return False

def main():
    """Main launch function."""
    print("🎯 GovQuery Templated API Demo Launcher")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Start backend in background
    print("\n1️⃣ Starting backend server...")
    # Ensure Modal credentials are available in environment
    if not os.environ.get("MODAL_TOKEN_ID") or not os.environ.get("MODAL_TOKEN_SECRET"):
        raise ValueError("MODAL_TOKEN_ID and MODAL_TOKEN_SECRET must be set as environment variables")
    
    backend_process = subprocess.Popen([
        sys.executable, "templated_api.py"
    ], env={
        **os.environ,
        "MODAL_APP_NAME": "govquery-nl2sql-main"
    })
    
    try:
        # Wait for server to be ready
        if not wait_for_server():
            backend_process.terminate()
            return 1
        
        # Open frontend
        print("\n2️⃣ Opening frontend...")
        open_frontend()
        
        print("\n🎉 Demo is ready!")
        print("📖 Backend API: http://localhost:8000")
        print("🌐 Frontend: Check your browser")
        print("💡 Press Ctrl+C to stop the server")
        
        # Keep running until interrupted
        backend_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Stopping demo...")
        backend_process.terminate()
        backend_process.wait()
        print("✅ Demo stopped")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
