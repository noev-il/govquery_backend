#!/usr/bin/env python3
"""
Setup database schema from JSON schema files.
Creates tables based on the Census schema definitions.
"""

import asyncio
import asyncpg
import json
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

async def setup_database():
    """Set up database schema from JSON files."""
    
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
    
    print("🔌 Connecting to database...")
    conn = await asyncpg.connect(database_url)
    
    try:
        # Load JSON schemas
        schemas_dir = project_root / "schemas"
        schema_files = list(schemas_dir.glob("*.json"))
        
        print(f"📊 Found {len(schema_files)} schema files")
        
        for schema_file in schema_files:
            table_code = schema_file.stem.upper()
            print(f"📋 Processing schema: {table_code}")
            
            with open(schema_file, 'r') as f:
                schema = json.load(f)
            
            # Create table from schema
            await create_table_from_schema(conn, table_code, schema)
            
            # Insert sample data
            await insert_sample_data(conn, table_code, schema)
        
        print("✅ Database schema setup complete!")
        
    finally:
        await conn.close()

async def create_table_from_schema(conn, table_code, schema):
    """Create table from JSON schema."""
    
    # Get table name (lowercase)
    table_name = table_code.lower()
    
    # Build CREATE TABLE statement
    columns = []
    
    # Add primary key columns
    for pk in schema.get("primary_keys", []):
        if pk == "geography_id":
            columns.append(f"{pk} VARCHAR NOT NULL")
        elif pk == "year":
            columns.append(f"{pk} INTEGER NOT NULL")
        else:
            columns.append(f"{pk} VARCHAR NOT NULL")
    
    # Add data columns
    for col in schema.get("columns", []):
        col_name = col["name"]
        col_type = col["type"]
        
        # Skip primary key columns (already added)
        if col_name in schema.get("primary_keys", []):
            continue
            
        columns.append(f"{col_name} {col_type}")
    
    # Create primary key constraint
    primary_keys = ", ".join(schema.get("primary_keys", []))
    primary_key_constraint = f"PRIMARY KEY ({primary_keys})" if primary_keys else ""
    
    # Build CREATE TABLE statement
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        {', '.join(columns)}
        {', ' + primary_key_constraint if primary_key_constraint else ''}
    );
    """
    
    print(f"  Creating table: {table_name}")
    await conn.execute(create_sql)
    
    # Create indexes for common queries
    if "geography_id" in schema.get("primary_keys", []):
        await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_geography ON {table_name} (geography_id);")
    
    if "year" in schema.get("primary_keys", []):
        await conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_year ON {table_name} (year);")

async def insert_sample_data(conn, table_code, schema):
    """Insert sample data from schema."""
    
    table_name = table_code.lower()
    
    # Check if table is empty
    count = await conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
    if count > 0:
        print(f"  Table {table_name} already has data, skipping sample data insertion")
        return
    
    # Get sample row from schema
    sample_row = schema.get("example_row", {})
    if not sample_row:
        print(f"  No sample data for {table_name}")
        return
    
    # Insert sample data
    columns = list(sample_row.keys())
    values = list(sample_row.values())
    placeholders = ", ".join([f"${i+1}" for i in range(len(values))])
    
    insert_sql = f"""
    INSERT INTO {table_name} ({', '.join(columns)})
    VALUES ({placeholders})
    ON CONFLICT DO NOTHING;
    """
    
    print(f"  Inserting sample data for {table_name}")
    await conn.execute(insert_sql, *values)

if __name__ == "__main__":
    asyncio.run(setup_database())
