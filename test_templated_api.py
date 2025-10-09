#!/usr/bin/env python3
"""
Test script for the templated API.
"""

import requests
import json
import time

def test_health():
    """Test health endpoint."""
    print("🔍 Testing health endpoint...")
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_query():
    """Test query endpoint."""
    print("\n🔍 Testing query endpoint...")
    
    test_cases = [
        {
            "question": "What is the total population in Texas?",
            "model_hint": "AUTO",
            "tables": ["B01001"],
            "max_rows": 100
        },
        {
            "question": "Show me population by age group",
            "model_hint": "SQLCODER",
            "tables": ["B01001"],
            "max_rows": 50
        },
        {
            "question": "DELETE FROM users",  # Should be blocked
            "model_hint": "AUTO",
            "tables": ["B01001"],
            "max_rows": 100
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i} ---")
        print(f"Question: {test_case['question']}")
        
        try:
            start_time = time.time()
            response = requests.post(
                "http://localhost:8000/query",
                json=test_case,
                headers={"Content-Type": "application/json"}
            )
            elapsed = time.time() - start_time
            
            print(f"Status: {response.status_code}")
            print(f"Time: {elapsed:.2f}s")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response Status: {data.get('status')}")
                if data.get('status') == 'ok':
                    print(f"SQL: {data.get('sql', '')[:100]}...")
                    print(f"Model: {data.get('meta', {}).get('model', 'unknown')}")
                    print(f"Elapsed: {data.get('meta', {}).get('elapsed_ms', 0)}ms")
                else:
                    print(f"Error: {data.get('message', 'Unknown error')}")
                    print(f"Error Code: {data.get('error_code', 'Unknown')}")
            else:
                print(f"HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

def test_schemas():
    """Test schemas endpoint."""
    print("\n🔍 Testing schemas endpoint...")
    try:
        response = requests.get("http://localhost:8000/schemas")
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            schemas = response.json()
            print(f"Found {len(schemas)} schemas")
            for schema in schemas[:3]:  # Show first 3
                print(f"  - {schema['table_code']}: {schema['table_name']}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"❌ Schemas request failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Templated API")
    print("=" * 50)
    
    # Test health
    if not test_health():
        print("❌ Health check failed, stopping tests")
        exit(1)
    
    # Test schemas
    test_schemas()
    
    # Test queries
    test_query()
    
    print("\n✅ Tests completed!")
