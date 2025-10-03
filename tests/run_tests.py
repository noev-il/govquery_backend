#!/usr/bin/env python3
"""
Test runner for GovQuery mass testing.
"""

import os
import sys
import time

def main():
    """Run different types of tests."""
    print("🎯 GovQuery Test Runner")
    print("=" * 50)
    
    print("\nAvailable test types:")
    print("1. Quick Test (5 questions)")
    print("2. Batch Test (15 questions)")
    print("3. Mass Test (comprehensive)")
    print("4. Parallel Test (3 workers)")
    print("5. Model Comparison")
    
    choice = input("\nSelect test type (1-5): ").strip()
    
    if choice == "1":
        print("\n🚀 Running Quick Test...")
        os.system("python batch_test.py")
        
    elif choice == "2":
        print("\n🚀 Running Batch Test...")
        os.system("python batch_test.py")
        
    elif choice == "3":
        print("\n🚀 Running Mass Test...")
        os.system("python mass_test.py")
        
    elif choice == "4":
        print("\n🚀 Running Parallel Test...")
        os.system("python parallel_test.py")
        
    elif choice == "5":
        print("\n🚀 Running Model Comparison...")
        # Run a simple model comparison
        questions = [
            ("B01001", "What is the total population in Texas?"),
            ("B19013", "What is the median household income in California?"),
        ]
        
        for model in ["auto", "t5", "sqlcoder"]:
            print(f"\n🔬 Testing {model.upper()} model:")
            for table, question in questions:
                cmd = f'modal run modal_deployment.py::query --table-code {table} --question "{question}" --force-model {model}'
                print(f"   {question}")
                os.system(cmd)
                time.sleep(2)
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
