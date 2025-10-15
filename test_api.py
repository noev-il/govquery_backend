#!/usr/bin/env python3
"""
Test the /execute API endpoint without Modal dependencies.
"""

import asyncio
import httpx
import json
import time

async def test_api():
    """Test the /execute API endpoint."""
    
    # Start the API server in background (we'll need to do this manually)
    print("🚀 Testing API endpoint...")
    print("📝 Note: Make sure the API server is running on port 8000")
    print("   You can start it with: MODAL_TOKEN_ID=test MODAL_TOKEN_SECRET=test python run_smart_api.py")
    print()
    
    # Test queries
    test_queries = [
        {
            "name": "Basic SELECT query",
            "sql": "SELECT * FROM b01001 LIMIT 3",
            "expected_columns": ["geography_id", "year", "total_population"]
        },
        {
            "name": "Aggregate query",
            "sql": "SELECT COUNT(*) as total_rows FROM b01001",
            "expected_columns": ["total_rows"]
        },
        {
            "name": "Invalid INSERT query (should fail)",
            "sql": "INSERT INTO b01001 VALUES ('test', 2023, 100)",
            "should_fail": True
        },
        {
            "name": "Query with row limit",
            "sql": "SELECT * FROM b02001",
            "max_rows": 2,
            "expected_max_rows": 2
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for i, test in enumerate(test_queries, 1):
            print(f"🧪 Test {i}: {test['name']}")
            
            try:
                # Prepare request
                request_data = {
                    "sql": test["sql"]
                }
                if "max_rows" in test:
                    request_data["max_rows"] = test["max_rows"]
                
                # Make request
                response = await client.post(
                    "http://localhost:8000/execute",
                    json=request_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    if result["success"]:
                        print(f"  ✅ Query successful")
                        print(f"  📊 Rows returned: {result['row_count']}")
                        print(f"  📊 Columns: {result['columns']}")
                        print(f"  ⏱️  Execution time: {result['execution_time_ms']:.2f}ms")
                        
                        # Check expected columns
                        if "expected_columns" in test:
                            for col in test["expected_columns"]:
                                if col in result["columns"]:
                                    print(f"  ✅ Expected column '{col}' found")
                                else:
                                    print(f"  ❌ Expected column '{col}' not found")
                        
                        # Check row limit
                        if "expected_max_rows" in test:
                            if result["row_count"] <= test["expected_max_rows"]:
                                print(f"  ✅ Row limit properly enforced ({result['row_count']} <= {test['expected_max_rows']})")
                            else:
                                print(f"  ❌ Row limit not enforced ({result['row_count']} > {test['expected_max_rows']})")
                        
                        if result["rows"] and len(result["rows"]) > 0:
                            print(f"  📄 Sample data: {result['rows'][0]}")
                    
                    else:
                        if test.get("should_fail", False):
                            print(f"  ✅ Query properly rejected: {result['error']}")
                        else:
                            print(f"  ❌ Query failed unexpectedly: {result['error']}")
                
                else:
                    print(f"  ❌ HTTP error {response.status_code}: {response.text}")
                
            except httpx.ConnectError:
                print(f"  ❌ Connection failed - is the API server running?")
                break
            except Exception as e:
                print(f"  ❌ Test failed: {e}")
            
            print()
    
    print("🏁 API testing completed!")

if __name__ == "__main__":
    asyncio.run(test_api())
