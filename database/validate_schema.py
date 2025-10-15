#!/usr/bin/env python3
"""
Schema validation script for Census database.
Compares database structure against JSON schemas and generates validation report.
"""

import asyncio
import asyncpg
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class SchemaValidator:
    """Validates database schema against JSON schema definitions."""
    
    def __init__(self, connection_url: str):
        self.connection_url = connection_url
        self.conn = None
        
        # Expected Census tables from schemas
        self.expected_tables = {
            'b01001', 'b02001', 'b14001', 'b14002', 'b15003', 
            'b19001', 'b19013', 'b20005', 'b23006', 'b23025', 
            'b24010', 'dp02'
        }
        
        # Load JSON schemas
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict]:
        """Load JSON schemas from schemas directory."""
        schemas = {}
        schemas_dir = project_root / "schemas"
        
        for schema_file in schemas_dir.glob("*.json"):
            table_code = schema_file.stem.upper()
            try:
                with open(schema_file, 'r') as f:
                    schemas[table_code] = json.load(f)
            except Exception as e:
                print(f"⚠️ Failed to load schema {schema_file}: {e}")
        
        return schemas
    
    async def connect(self):
        """Connect to database."""
        self.conn = await asyncpg.connect(self.connection_url)
    
    async def close(self):
        """Close database connection."""
        if self.conn:
            await self.conn.close()
    
    async def get_database_tables(self) -> List[str]:
        """Get list of tables in database."""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name;
        """
        rows = await self.conn.fetch(query)
        return [row['table_name'] for row in rows]
    
    async def get_table_columns(self, table_name: str) -> List[Dict[str, Any]]:
        """Get column information for a table."""
        query = """
        SELECT 
            column_name,
            data_type,
            is_nullable,
            column_default,
            character_maximum_length
        FROM information_schema.columns 
        WHERE table_name = $1 
        AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        rows = await self.conn.fetch(query, table_name)
        return [dict(row) for row in rows]
    
    async def get_table_row_count(self, table_name: str) -> int:
        """Get row count for a table."""
        try:
            result = await self.conn.fetchval(f"SELECT COUNT(*) FROM {table_name}")
            return result
        except Exception as e:
            print(f"⚠️ Failed to get row count for {table_name}: {e}")
            return 0
    
    async def get_sample_data(self, table_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        try:
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            rows = await self.conn.fetch(query)
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"⚠️ Failed to get sample data for {table_name}: {e}")
            return []
    
    def compare_schemas(self, db_columns: List[Dict], json_schema: Dict) -> Dict[str, Any]:
        """Compare database columns with JSON schema."""
        json_columns = {col['name'].lower(): col for col in json_schema.get('columns', [])}
        db_columns_dict = {col['column_name'].lower(): col for col in db_columns}
        
        comparison = {
            'missing_in_db': [],
            'missing_in_schema': [],
            'type_mismatches': [],
            'matches': []
        }
        
        # Check for columns missing in database
        for col_name, col_info in json_columns.items():
            if col_name not in db_columns_dict:
                comparison['missing_in_db'].append(col_name)
            else:
                comparison['matches'].append(col_name)
        
        # Check for columns missing in schema
        for col_name in db_columns_dict:
            if col_name not in json_columns:
                comparison['missing_in_schema'].append(col_name)
        
        # Check for type mismatches (simplified)
        for col_name in comparison['matches']:
            db_col = db_columns_dict[col_name]
            json_col = json_columns[col_name]
            
            # Simple type comparison (can be enhanced)
            db_type = db_col['data_type'].upper()
            json_type = json_col.get('type', '').upper()
            
            if json_type and db_type != json_type:
                comparison['type_mismatches'].append({
                    'column': col_name,
                    'db_type': db_type,
                    'schema_type': json_type
                })
        
        return comparison
    
    async def validate_all(self) -> Dict[str, Any]:
        """Run complete validation."""
        print("🔍 Starting database schema validation...")
        
        # Get database tables
        db_tables = await self.get_database_tables()
        print(f"📊 Found {len(db_tables)} tables in database")
        
        validation_results = {
            'database_tables': db_tables,
            'expected_tables': list(self.expected_tables),
            'missing_tables': [],
            'extra_tables': [],
            'table_validations': {},
            'summary': {
                'total_tables': len(db_tables),
                'expected_tables_found': 0,
                'schema_matches': 0,
                'schema_mismatches': 0,
                'missing_tables_count': 0
            }
        }
        
        # Check for missing/extra tables
        db_tables_set = set(db_tables)
        validation_results['missing_tables'] = list(self.expected_tables - db_tables_set)
        validation_results['extra_tables'] = list(db_tables_set - self.expected_tables)
        
        validation_results['summary']['missing_tables_count'] = len(validation_results['missing_tables'])
        validation_results['summary']['expected_tables_found'] = len(self.expected_tables - set(validation_results['missing_tables']))
        
        # Validate each expected table
        for table_name in self.expected_tables:
            if table_name in db_tables:
                print(f"✅ Validating table: {table_name}")
                
                # Get table information
                columns = await self.get_table_columns(table_name)
                row_count = await self.get_table_row_count(table_name)
                sample_data = await self.get_sample_data(table_name)
                
                # Compare with JSON schema
                json_schema = self.schemas.get(table_name, {})
                schema_comparison = self.compare_schemas(columns, json_schema)
                
                table_validation = {
                    'exists': True,
                    'row_count': row_count,
                    'column_count': len(columns),
                    'columns': columns,
                    'sample_data': sample_data,
                    'schema_comparison': schema_comparison,
                    'json_schema': json_schema
                }
                
                # Determine if schema matches
                if (not schema_comparison['missing_in_db'] and 
                    not schema_comparison['type_mismatches']):
                    table_validation['schema_match'] = True
                    validation_results['summary']['schema_matches'] += 1
                else:
                    table_validation['schema_match'] = False
                    validation_results['summary']['schema_mismatches'] += 1
                
                validation_results['table_validations'][table_name] = table_validation
            else:
                print(f"❌ Missing table: {table_name}")
                validation_results['table_validations'][table_name] = {
                    'exists': False,
                    'row_count': 0,
                    'column_count': 0,
                    'schema_match': False
                }
        
        return validation_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate human-readable validation report."""
        report = []
        report.append("=" * 80)
        report.append("CENSUS DATABASE SCHEMA VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Summary
        summary = results['summary']
        report.append("📊 SUMMARY")
        report.append(f"Total tables in database: {summary['total_tables']}")
        report.append(f"Expected tables found: {summary['expected_tables_found']}/{len(self.expected_tables)}")
        report.append(f"Schema matches: {summary['schema_matches']}")
        report.append(f"Schema mismatches: {summary['schema_mismatches']}")
        report.append(f"Missing tables: {summary['missing_tables_count']}")
        report.append("")
        
        # Missing tables
        if results['missing_tables']:
            report.append("❌ MISSING TABLES")
            for table in results['missing_tables']:
                report.append(f"  - {table}")
            report.append("")
        
        # Extra tables
        if results['extra_tables']:
            report.append("ℹ️ EXTRA TABLES (not in expected schemas)")
            for table in results['extra_tables']:
                report.append(f"  - {table}")
            report.append("")
        
        # Table validations
        report.append("🔍 TABLE VALIDATIONS")
        for table_name, validation in results['table_validations'].items():
            if validation['exists']:
                status = "✅" if validation['schema_match'] else "⚠️"
                report.append(f"{status} {table_name}")
                report.append(f"    Rows: {validation['row_count']:,}")
                report.append(f"    Columns: {validation['column_count']}")
                
                if not validation['schema_match']:
                    comparison = validation['schema_comparison']
                    if comparison['missing_in_db']:
                        report.append(f"    Missing columns: {', '.join(comparison['missing_in_db'])}")
                    if comparison['type_mismatches']:
                        report.append(f"    Type mismatches: {len(comparison['type_mismatches'])}")
            else:
                report.append(f"❌ {table_name} - NOT FOUND")
            report.append("")
        
        return "\n".join(report)


async def main():
    """Main validation function."""
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
    
    validator = SchemaValidator(database_url)
    
    try:
        await validator.connect()
        print("🔌 Connected to database")
        
        results = await validator.validate_all()
        
        # Generate and print report
        report = validator.generate_report(results)
        print(report)
        
        # Save results to file
        results_file = Path(__file__).parent / "validation_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📄 Detailed results saved to: {results_file}")
        
        # Return exit code based on validation
        if results['summary']['missing_tables_count'] > 0:
            print("❌ Validation failed: Missing tables")
            return 1
        elif results['summary']['schema_mismatches'] > 0:
            print("⚠️ Validation completed with warnings: Schema mismatches")
            return 0
        else:
            print("✅ Validation passed: All tables and schemas match")
            return 0
            
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1
    finally:
        await validator.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
