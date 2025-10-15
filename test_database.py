#!/usr/bin/env python3
"""
Test database functionality without Modal dependencies.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.db_executor import DatabaseExecutor

async def test_database():
    """Test database connection and query execution."""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Fallback to individual components
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "census_data")
        user = os.getenv("POSTGRES_USER", "govquery")
        password = os.getenv("POSTGRES_PASSWORD", "govquery_dev")
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    
    print("🔌 Testing database connection...")
    print(f"📊 Database URL: {database_url}")
    
    executor = DatabaseExecutor(database_url)
    
    try:
        # Connect to database
        await executor.connect()
        print("✅ Database connection established")
        
        # Test connection
        if await executor.test_connection():
            print("✅ Connection test passed")
        else:
            print("❌ Connection test failed")
            return
        
        # Test queries on each table
        test_queries = [
            ("b01001", "SELECT * FROM b01001 LIMIT 3"),
            ("b02001", "SELECT * FROM b02001 LIMIT 3"),
            ("b19013", "SELECT * FROM b19013 LIMIT 3"),
            ("dp02", "SELECT * FROM dp02 LIMIT 3"),
        ]
        
        print("\n🔍 Testing queries on Census tables...")
        for table_name, query in test_queries:
            print(f"\n📋 Testing {table_name}...")
            result = await executor.execute_query(query)
            
            if result["success"]:
                print(f"  ✅ Query successful")
                print(f"  📊 Rows returned: {result['row_count']}")
                print(f"  📊 Columns: {result['columns']}")
                print(f"  ⏱️  Execution time: {result['execution_time_ms']:.2f}ms")
                if result["rows"]:
                    print(f"  📄 Sample data: {result['rows'][0]}")
            else:
                print(f"  ❌ Query failed: {result['error']}")
        
        # Test security features
        print("\n🔒 Testing security features...")
        
        # Test SELECT-only enforcement
        print("  Testing SELECT-only enforcement...")
        result = await executor.execute_query("INSERT INTO b01001 VALUES ('test', 2023, 100)")
        if not result["success"] and ("Forbidden keyword" in result["error"] or "SELECT" in result["error"]):
            print("  ✅ INSERT queries properly rejected")
        else:
            print("  ❌ INSERT queries not properly rejected")
        
        # Test row limit
        print("  Testing row limit enforcement...")
        result = await executor.execute_query("SELECT * FROM b01001", max_rows=2)
        if result["success"] and result["row_count"] <= 2:
            print("  ✅ Row limit properly enforced")
        else:
            print("  ❌ Row limit not properly enforced")
        
        print("\n✅ All database tests completed!")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
    finally:
        await executor.close()
        print("🔌 Database connection closed")

if __name__ == "__main__":
    asyncio.run(test_database())
