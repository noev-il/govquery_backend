#!/usr/bin/env python3
"""
Smart Modal client that automatically handles app deployment and cold starts.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import modal
from pydantic import BaseModel

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.modal_client import ModalNL2SQLClient, NL2SQLRequest, NL2SQLResponse


class SmartModalClient:
    """Smart Modal client with automatic deployment and cold start handling."""
    
    def __init__(self, app_name: str = "govquery-nl2sql-main"):
        self.app_name = app_name
        self.client = ModalNL2SQLClient(app_name)
        self.deployment_attempted = False
        self.last_health_check = 0
        self.health_check_interval = 300  # 5 minutes
        
    def _is_app_running(self) -> bool:
        """Check if the Modal app is currently running."""
        try:
            # Try to get the app
            app = modal.App.lookup(self.app_name, create_if_missing=False)
            return app is not None
        except Exception:
            return False
    
    def _deploy_app(self) -> bool:
        """Deploy the Modal app."""
        if self.deployment_attempted:
            return False
            
        print("🚀 Modal app not found. Deploying...")
        try:
            # Change to deployment directory
            deployment_dir = project_root / "deployment"
            original_dir = os.getcwd()
            os.chdir(deployment_dir)
            
            # Run deployment
            result = subprocess.run([
                sys.executable, "deploy_modal.py"
            ], capture_output=True, text=True, timeout=600)
            
            # Restore original directory
            os.chdir(original_dir)
            
            print(f"Deployment stdout: {result.stdout}")
            print(f"Deployment stderr: {result.stderr}")
            
            if result.returncode == 0:
                print("✅ Modal app deployed successfully!")
                print("⏳ Waiting for app to become available...")
                
                # Wait for app to become available (up to 30 seconds)
                for i in range(30):
                    time.sleep(1)
                    if self._is_app_running():
                        print(f"✅ App is now available! (waited {i+1}s)")
                        self.deployment_attempted = True
                        return True
                    if i % 5 == 0:  # Print every 5 seconds
                        print(f"   Still waiting... ({i+1}s)")
                
                print("⚠️ App deployed but not yet available for queries")
                self.deployment_attempted = True
                return True
            else:
                print(f"❌ Deployment failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("⏰ Deployment timed out")
            return False
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False
    
    def _ensure_app_running(self) -> bool:
        """Ensure the Modal app is running, deploy if necessary."""
        current_time = time.time()
        
        # Skip health check if we checked recently
        if current_time - self.last_health_check < self.health_check_interval:
            return True
            
        self.last_health_check = current_time
        
        if self._is_app_running():
            print("✅ Modal app is running")
            return True
        
        print("⚠️ Modal app not running. Attempting deployment...")
        return self._deploy_app()
    
    def query_with_fallback(self, table_code: str, question: str, force_model: str = None) -> Dict[str, Any]:
        """
        Query with automatic fallback to cold start.
        
        Args:
            table_code: Database table code
            question: Natural language question
            force_model: Model to force (optional)
            
        Returns:
            Query result or error information
        """
        print(f"🔍 Processing query: {question}")
        print(f"📊 Table: {table_code}")
        
        # First, try with existing app
        try:
            print("🎯 Attempting query with existing app...")
            result = self.client.query_simple(table_code, question, force_model)
            
            # Check if we got a valid result
            if result.get("sql") and not result.get("meta", {}).get("error"):
                print("✅ Query successful with existing app!")
                return result
            else:
                print("⚠️ Query failed with existing app, trying cold start...")
                
        except Exception as e:
            print(f"⚠️ Query failed: {e}")
        
        # Fallback: Ensure app is running and try again
        print("🔄 Attempting cold start fallback...")
        if self._ensure_app_running():
            # Retry with multiple attempts (app might need time to become available)
            for attempt in range(3):
                try:
                    print(f"🎯 Retrying query after deployment (attempt {attempt + 1}/3)...")
                    result = self.client.query_simple(table_code, question, force_model)
                    
                    if result.get("sql") and not result.get("meta", {}).get("error"):
                        print("✅ Query successful after cold start!")
                        return result
                    else:
                        print(f"⚠️ Query failed on attempt {attempt + 1}: {result.get('meta', {}).get('error', 'Unknown error')}")
                        if attempt < 2:  # Don't sleep on last attempt
                            print("   Waiting 5 seconds before retry...")
                            time.sleep(5)
                except Exception as e:
                    print(f"⚠️ Query failed on attempt {attempt + 1}: {e}")
                    if attempt < 2:  # Don't sleep on last attempt
                        print("   Waiting 5 seconds before retry...")
                        time.sleep(5)
            
            # If all retries failed
            print("❌ Query still failed after deployment and retries")
            return {
                "model": "error",
                "sql": "",
                "meta": {"error": "Query failed even after app deployment and retries"},
                "table": table_code,
                "question": question
            }
        else:
            print("❌ Could not deploy app")
            return {
                "model": "error",
                "sql": "",
                "meta": {"error": "Could not deploy Modal app"},
                "table": table_code,
                "question": question
            }
    
    def infer_sql_with_fallback(self, query: str, table_codes: List[str] = None, 
                               model_choice: str = "auto", max_tokens: int = 512, 
                               temperature: float = 0.1) -> NL2SQLResponse:
        """
        Infer SQL with automatic fallback handling.
        
        Args:
            query: Natural language query
            table_codes: List of table codes to use
            model_choice: Model choice
            max_tokens: Maximum tokens for generation
            temperature: Sampling temperature
            
        Returns:
            NL2SQLResponse with result or error
        """
        try:
            # Use the first table code or default to B01001
            table_code = table_codes[0] if table_codes else "B01001"
            
            # Try normal inference first (using simple query method)
            result = self.client.query_simple(
                table_code=table_code,
                question=query,
                force_model=model_choice if model_choice != "auto" else None
            )
            
            # Convert result to NL2SQLResponse format
            if result.get("sql") and not result.get("meta", {}).get("error"):
                return NL2SQLResponse(
                    sql_query=result.get("sql", ""),
                    confidence=result.get("meta", {}).get("confidence", 0.0),
                    explanation=result.get("meta", {}).get("explanation", ""),
                    model_used=result.get("model", ""),
                    error=None
                )
            else:
                print(f"⚠️ Normal inference failed: {result.get('meta', {}).get('error', 'Unknown error')}")
                print("🔄 Attempting cold start fallback...")
                
                # Fallback: ensure app is running
                if self._ensure_app_running():
                    # Retry inference
                    result = self.client.query_simple(
                        table_code=table_code,
                        question=query,
                        force_model=model_choice if model_choice != "auto" else None
                    )
                    
                    # Convert result to NL2SQLResponse format
                    if result.get("sql") and not result.get("meta", {}).get("error"):
                        return NL2SQLResponse(
                            sql_query=result.get("sql", ""),
                            confidence=result.get("meta", {}).get("confidence", 0.0),
                            explanation=result.get("meta", {}).get("explanation", ""),
                            model_used=result.get("model", ""),
                            error=None
                        )
                    else:
                        return NL2SQLResponse(
                            sql_query="",
                            error=result.get("meta", {}).get("error", "Query failed after deployment"),
                            confidence=0.0
                        )
                else:
                    return NL2SQLResponse(
                        sql_query="",
                        error="Could not deploy Modal app",
                        confidence=0.0
                    )
                    
        except Exception as e:
            print(f"❌ Inference failed: {e}")
            return NL2SQLResponse(
                sql_query="",
                error=f"Inference failed: {e}",
                confidence=0.0
            )
    
    def load_all_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load all schemas (delegates to base client)."""
        return self.client.load_all_schemas()
    
    def load_schema(self, table_code: str) -> Dict[str, Any]:
        """Load specific schema (delegates to base client)."""
        return self.client.load_schema(table_code)


# Global smart client instance
_smart_client: Optional[SmartModalClient] = None


def get_smart_client() -> SmartModalClient:
    """Get or create global smart Modal client instance."""
    global _smart_client
    if _smart_client is None:
        app_name = os.getenv("MODAL_APP_NAME", "govquery-nl2sql-main")
        _smart_client = SmartModalClient(app_name)
    return _smart_client


def test_smart_client():
    """Test the smart client functionality."""
    print("🧪 Testing Smart Modal Client")
    print("=" * 50)
    
    client = get_smart_client()
    
    # Test schema loading
    print("\n1️⃣ Testing schema loading...")
    try:
        schemas = client.load_all_schemas()
        print(f"✅ Loaded {len(schemas)} schemas")
    except Exception as e:
        print(f"❌ Schema loading failed: {e}")
    
    # Test app status
    print("\n2️⃣ Testing app status...")
    is_running = client._is_app_running()
    print(f"📊 App running: {is_running}")
    
    # Test query with fallback
    print("\n3️⃣ Testing query with fallback...")
    result = client.query_with_fallback(
        "B01001", 
        "What is the total population in Texas?"
    )
    
    print(f"📊 Result: {result.get('model', 'unknown')}")
    if result.get("sql"):
        print(f"🔧 SQL: {result['sql'][:100]}...")
    if result.get("meta", {}).get("error"):
        print(f"❌ Error: {result['meta']['error']}")


if __name__ == "__main__":
    test_smart_client()
