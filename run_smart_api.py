#!/usr/bin/env python3
"""
Run the Smart GovQuery API with automatic Modal app deployment.
"""

import os
import sys
from pathlib import Path

import uvicorn
from dotenv import load_dotenv

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment variables
os.environ["MODAL_TOKEN_ID"] = "ak-82ssY3sBr9rB9tau63rD2n"
os.environ["MODAL_TOKEN_SECRET"] = "as-A4L7Xzb33dybZ9XEhheVAV"
os.environ["MODAL_APP_NAME"] = "govquery-nl2sql-main"

# Import and run the smart API
from smart_api import app

if __name__ == "__main__":
    print("🎯 GovQuery Smart API Server")
    print("=" * 50)
    print("🌐 Server: http://localhost:8000")
    print("📖 API Docs: http://localhost:8000/docs")
    print("🔍 Health: http://localhost:8000/health")
    print("🚀 Features:")
    print("   ✅ Automatic Modal app deployment")
    print("   ✅ Cold start fallback handling")
    print("   ✅ Smart error recovery")
    print("💡 Press Ctrl+C to stop")
    print("=" * 50)
    
    uvicorn.run(
        "smart_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
