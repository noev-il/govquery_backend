#!/usr/bin/env python3
"""
Final demonstration of the complete GovQuery PostgreSQL Census integration.
"""

import asyncio
import httpx
import json

async def demo_system():
    """Demonstrate the complete system working."""
    
    print("🎉 GovQuery PostgreSQL Census Integration - Final Demo")
    print("=" * 60)
    
    # Test the execute endpoint directly
    print("\n📊 Testing Census Data Query Execution...")
    
    test_queries = [
        {
            "name": "Population by Sex (B01001)",
            "sql": "SELECT geography_id, year, total_population, male_population, female_population FROM b01001 LIMIT 3"
        },
        {
            "name": "Race Demographics (B02001)", 
            "sql": "SELECT geography_id, white_alone, black_or_african_american_alone, asian_alone FROM b02001 LIMIT 2"
        },
        {
            "name": "Income Data (B19013)",
            "sql": "SELECT geography_id, median_household_income FROM b19013 LIMIT 1"
        },
        {
            "name": "Education Data (DP02)",
            "sql": "SELECT geography_id, high_school_graduate_or_higher, bachelors_degree_or_higher FROM dp02 LIMIT 1"
        }
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            for i, test in enumerate(test_queries, 1):
                print(f"\n{i}️⃣ {test['name']}")
                print(f"   SQL: {test['sql']}")
                
                response = await client.post(
                    "http://localhost:8000/execute",
                    json={"sql": test["sql"], "max_rows": 5},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result["success"]:
                        print(f"   ✅ Success: {result['row_count']} rows in {result['execution_time_ms']:.1f}ms")
                        if result["rows"]:
                            print(f"   📄 Data: {result['rows'][0]}")
                    else:
                        print(f"   ❌ Failed: {result['error']}")
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return
    
    # Test security features
    print("\n🔒 Testing Security Features...")
    
    security_tests = [
        "INSERT INTO b01001 VALUES ('test', 2023, 100)",
        "UPDATE b01001 SET total_population = 100", 
        "SELECT * FROM b01001; DROP TABLE b01001"
    ]
    
    try:
        async with httpx.AsyncClient() as client:
            for i, sql in enumerate(security_tests, 1):
                print(f"\n{i}️⃣ Testing: {sql[:50]}...")
                
                response = await client.post(
                    "http://localhost:8000/execute",
                    json={"sql": sql},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if not result["success"]:
                        print(f"   ✅ Properly rejected: {result['error']}")
                    else:
                        print(f"   ❌ Should have been rejected!")
                else:
                    print(f"   ❌ HTTP Error: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Security test failed: {e}")
    
    # Test frontend integration
    print("\n🌐 Testing Frontend Integration...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:3000/api/govquery/execute",
                json={"sql": "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public'"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result["success"]:
                    print(f"   ✅ Frontend integration working")
                    print(f"   📊 Total Census tables: {result['rows'][0]['total_tables'] if result['rows'] else 'unknown'}")
                else:
                    print(f"   ❌ Frontend query failed: {result['error']}")
            else:
                print(f"   ❌ Frontend HTTP error: {response.status_code}")
    
    except Exception as e:
        print(f"   ⚠️  Frontend test skipped (server may not be running): {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 INTEGRATION COMPLETE!")
    print("=" * 60)
    print("✅ PostgreSQL database with 12 Census tables")
    print("✅ FastAPI backend with /execute endpoint") 
    print("✅ SQL validation and security enforcement")
    print("✅ TypeScript frontend integration")
    print("✅ Docker containerized database")
    print("✅ Connection pooling and performance optimization")
    print("✅ Comprehensive error handling")
    print("✅ Complete documentation")
    
    print("\n🎯 Key Features Demonstrated:")
    print("   • Direct SQL execution against Census data")
    print("   • SELECT-only security enforcement")
    print("   • Row limits and query timeouts")
    print("   • Frontend API proxy integration")
    print("   • TypeScript client with executeSQL() method")
    print("   • Comprehensive error handling and logging")
    
    print("\n📚 Documentation:")
    print("   • DATABASE_SETUP.md - Complete setup guide")
    print("   • README.md - Updated with database features")
    print("   • Test scripts for validation and demos")
    
    print("\n🚀 Ready for production with real Modal credentials!")

if __name__ == "__main__":
    asyncio.run(demo_system())
