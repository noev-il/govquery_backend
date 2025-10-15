#!/usr/bin/env python3
"""
Test SQL validation functionality.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from core.db_executor import DatabaseExecutor

def test_validation():
    """Test SQL validation without database connection."""
    
    # Create executor without connecting
    executor = DatabaseExecutor("dummy://url")
    
    # Test cases
    test_cases = [
        ("SELECT * FROM b01001", True, "Valid SELECT query"),
        ("INSERT INTO b01001 VALUES ('test', 2023, 100)", False, "INSERT should be rejected"),
        ("UPDATE b01001 SET total_population = 100", False, "UPDATE should be rejected"),
        ("DELETE FROM b01001", False, "DELETE should be rejected"),
        ("SELECT * FROM b01001; DROP TABLE b01001", False, "Multiple statements should be rejected"),
        ("select * from b01001", True, "Case insensitive SELECT should work"),
    ]
    
    print("🔍 Testing SQL validation...")
    
    for sql, expected_valid, description in test_cases:
        is_valid, error_msg = executor._validate_sql(sql)
        
        if is_valid == expected_valid:
            status = "✅"
        else:
            status = "❌"
        
        print(f"{status} {description}")
        print(f"   SQL: {sql}")
        print(f"   Expected: {'Valid' if expected_valid else 'Invalid'}")
        print(f"   Got: {'Valid' if is_valid else 'Invalid'}")
        if not is_valid and error_msg:
            print(f"   Error: {error_msg}")
        print()

if __name__ == "__main__":
    test_validation()
