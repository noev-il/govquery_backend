#!/usr/bin/env python3
"""
Test security layers: SQL validation + Database read-only enforcement
"""

import asyncio
import httpx
import asyncpg
import os

async def test_security_layers():
    """Test both security layers working together."""
    
    print("🔒 SECURITY LAYERS TEST")
    print("=" * 40)
    
    # Layer 1: SQL Validation (Application Level)
    print("\n1️⃣ LAYER 1: SQL Validation (Application Level)")
    print("   Testing mutations caught by SQL validation...")
    
    mutations = [
        ("INSERT", "INSERT INTO b01001 VALUES ('test', 2023, 100)"),
        ("UPDATE", "UPDATE b01001 SET total_population = 100"),
        ("DELETE", "DELETE FROM b01001 WHERE geography_id = 'test'")
    ]
    
    validation_passes = 0
    for mutation_type, sql in mutations:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/execute",
                    json={"sql": sql},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if not data["success"] and "Forbidden keyword" in data["error"]:
                        validation_passes += 1
                        print(f"   ✅ {mutation_type}: Caught by SQL validation")
                    else:
                        print(f"   ❌ {mutation_type}: Not caught by validation")
                else:
                    print(f"   ❌ {mutation_type}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {mutation_type}: ERROR - {e}")
    
    print(f"   📊 SQL Validation: {validation_passes}/3 mutations caught")
    
    # Layer 2: Database Read-Only (Database Level)
    print("\n2️⃣ LAYER 2: Database Read-Only (Database Level)")
    print("   Testing mutations caught by database read-only...")
    
    database_url = os.getenv("DATABASE_URL", "postgresql://govquery:govquery_dev@localhost:5432/census_data")
    
    try:
        conn = await asyncpg.connect(database_url)
        
        # Apply same security settings as DatabaseExecutor
        await conn.execute("SET SESSION default_transaction_read_only = on")
        await conn.execute("SET SESSION statement_timeout = '30s'")
        
        db_passes = 0
        for mutation_type, sql in mutations:
            try:
                await conn.execute(sql)
                print(f"   ❌ {mutation_type}: Should have been blocked!")
            except Exception as e:
                if "read-only" in str(e).lower() or "cannot execute" in str(e).lower():
                    db_passes += 1
                    print(f"   ✅ {mutation_type}: Caught by database read-only")
                else:
                    print(f"   ⚠️  {mutation_type}: Blocked for other reason: {e}")
        
        await conn.close()
        print(f"   📊 Database Read-Only: {db_passes}/3 mutations caught")
        
    except Exception as e:
        print(f"   ❌ Database test failed: {e}")
        db_passes = 0
    
    # Summary
    print("\n" + "=" * 40)
    print("🏁 SECURITY LAYERS SUMMARY")
    print("=" * 40)
    print(f"✅ SQL Validation (Layer 1): {validation_passes}/3")
    print(f"✅ Database Read-Only (Layer 2): {db_passes}/3")
    print(f"✅ Defense in Depth: {'ACTIVE' if validation_passes >= 2 and db_passes >= 2 else 'INACTIVE'}")
    
    if validation_passes >= 2 and db_passes >= 2:
        print("🎉 SECURITY: ✅ EXCELLENT - Both layers working")
        return True
    else:
        print("🚫 SECURITY: ❌ ISSUES - Layers need improvement")
        return False

if __name__ == "__main__":
    asyncio.run(test_security_layers())
