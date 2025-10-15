#!/usr/bin/env python3
"""
Test database-level read-only enforcement.
"""

import asyncio
import asyncpg
import os

async def test_db_readonly():
    """Test that database enforces read-only at the connection level."""
    
    # Get database URL
    database_url = os.getenv("DATABASE_URL", "postgresql://govquery:govquery_dev@localhost:5432/census_data")
    
    print("🔒 Testing database-level read-only enforcement...")
    
    try:
        # Connect directly to database
        conn = await asyncpg.connect(database_url)
        print("✅ Connected to database")
        
        # Set read-only mode
        await conn.execute("SET SESSION default_transaction_read_only = on")
        await conn.execute("SET SESSION statement_timeout = '30s'")
        print("✅ Set read-only mode")
        
        # Test SELECT (should work)
        print("\n1️⃣ Testing SELECT query...")
        try:
            result = await conn.fetchval("SELECT COUNT(*) FROM b01001")
            print(f"   ✅ SELECT successful: {result} rows")
        except Exception as e:
            print(f"   ❌ SELECT failed: {e}")
        
        # Test INSERT (should fail at DB level)
        print("\n2️⃣ Testing INSERT query (should fail at DB level)...")
        try:
            await conn.execute("INSERT INTO b01001 VALUES ('test', 2023, 100)")
            print("   ❌ INSERT should have failed but didn't!")
        except Exception as e:
            if "read-only" in str(e).lower() or "cannot execute" in str(e).lower():
                print(f"   ✅ INSERT properly rejected at DB level: {e}")
            else:
                print(f"   ⚠️  INSERT failed but not due to read-only: {e}")
        
        # Test UPDATE (should fail at DB level)
        print("\n3️⃣ Testing UPDATE query (should fail at DB level)...")
        try:
            await conn.execute("UPDATE b01001 SET total_population = 100 WHERE geography_id = 'test'")
            print("   ❌ UPDATE should have failed but didn't!")
        except Exception as e:
            if "read-only" in str(e).lower() or "cannot execute" in str(e).lower():
                print(f"   ✅ UPDATE properly rejected at DB level: {e}")
            else:
                print(f"   ⚠️  UPDATE failed but not due to read-only: {e}")
        
        # Test DELETE (should fail at DB level)
        print("\n4️⃣ Testing DELETE query (should fail at DB level)...")
        try:
            await conn.execute("DELETE FROM b01001 WHERE geography_id = 'test'")
            print("   ❌ DELETE should have failed but didn't!")
        except Exception as e:
            if "read-only" in str(e).lower() or "cannot execute" in str(e).lower():
                print(f"   ✅ DELETE properly rejected at DB level: {e}")
            else:
                print(f"   ⚠️  DELETE failed but not due to read-only: {e}")
        
        await conn.close()
        print("\n✅ Database read-only enforcement test completed")
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_db_readonly())
