#!/usr/bin/env python3
"""
Test the GovQuery API endpoints.
"""

import requests
import json
import time

def test_api():
    """Test the API endpoints."""
    print("🌐 Testing GovQuery API...")
    print("=" * 50)
    
    # Test the health endpoint
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Health endpoint working")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("💡 Make sure to start the API server first: python api.py")
        return
    
    # Test the query endpoint
    test_queries = [
        {
            "table_code": "B01001",
            "question": "What is the total population in Texas?",
            "force_model": None
        },
        {
            "table_code": "B01001", 
            "question": "How many females are there in California?",
            "force_model": "t5"
        },
        {
            "table_code": "B19013",
            "question": "What is the median household income in New York?",
            "force_model": "sqlcoder"
        }
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📊 Test {i}: {query['question']}")
        print(f"   Table: {query['table_code']}")
        if query['force_model']:
            print(f"   Model: {query['force_model']}")
        
        try:
            response = requests.post(
                "http://localhost:8000/query",
                json=query,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"   Model: {result.get('model', 'N/A')}")
                print(f"   SQL: {result.get('sql', 'N/A')}")
                if result.get('meta'):
                    print(f"   Meta: {result['meta']}")
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")
        
        # Small delay between requests
        time.sleep(1)
    
    print("\n🎉 API testing complete!")

if __name__ == "__main__":
    test_api()
