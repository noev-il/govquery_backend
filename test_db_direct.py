#!/usr/bin/env python3
"""
Test database-level read-only enforcement by bypassing SQL validation.
"""

import asyncio
import asyncpg
import os

async def test_db_direct():
    """Test database read-only enforcement directly."""
    
    database_url = os.getenv("DATABASE_URL", "postgresql://govquery:govquery_dev@localhost:5432/census_data")
    
    print("🔒 Testing database read-only enforcement directly...")
    
    try:
        # Connect using the same settings as DatabaseExecutor
        conn = await asyncpg.connect(database_url)
        
        # Apply the same security settings as DatabaseExecutor
        try:
            await conn.execute("SET ROLE read_only")
        except Exception:
            print("   ⚠️  read_only role not found, using default permissions")
        
        await conn.execute("SET SESSION default_transaction_read_only = on")
        await conn.execute("SET SESSION statement_timeout = '30s'")
        await conn.execute("SET SESSION idle_in_transaction_session_timeout = '30s'")
        
        print("   ✅ Applied read-only security settings")
        
        # Test SELECT (should work)
        print("\n1️⃣ Testing SELECT...")
        try:
            result = await conn.fetchval("SELECT COUNT(*) FROM b01001")
            print(f"   ✅ SELECT successful: {result} rows")
        except Exception as e:
            print(f"   ❌ SELECT failed: {e}")
        
        # Test INSERT (should fail at DB level)
        print("\n2️⃣ Testing INSERT...")
        try:
            await conn.execute("INSERT INTO b01001 VALUES ('test', 2023, 100)")
            print("   ❌ INSERT should have failed!")
        except Exception as e:
            if "read-only" in str(e).lower() or "cannot execute" in str(e).lower():
                print(f"   ✅ INSERT properly rejected: {e}")
            else:
                print(f"   ⚠️  INSERT failed for other reason: {e}")
        
        # Test UPDATE (should fail at DB level)
        print("\n3️⃣ Testing UPDATE...")
        try:
            await conn.execute("UPDATE b01001 SET total_population = 100 WHERE geography_id = 'test'")
            print("   ❌ UPDATE should have failed!")
        except Exception as e:
            if "read-only" in str(e).lower() or "cannot execute" in str(e).lower():
                print(f"   ✅ UPDATE properly rejected: {e}")
            else:
                print(f"   ⚠️  UPDATE failed for other reason: {e}")
        
        await conn.close()
        print("\n✅ Database read-only test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_db_direct())
