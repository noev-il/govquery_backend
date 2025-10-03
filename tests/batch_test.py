#!/usr/bin/env python3
"""
Simple batch testing for GovQuery.
Run multiple questions in sequence.
"""

import subprocess
import os
import time

# Set up Modal authentication
os.environ["MODAL_TOKEN_ID"] = "ak-82ssY3sBr9rB9tau63rD2n"
os.environ["MODAL_TOKEN_SECRET"] = "as-A4L7Xzb33dybZ9XEhheVAV"

# Test questions
TEST_QUESTIONS = [
    # Population Demographics
    ("B01001", "What is the total population in Texas?"),
    ("B01001", "How many males are there in California?"),
    ("B01001", "What is the female population in New York?"),
    ("B01001", "How many people are under 18 in Florida?"),
    
    # Income & Economics
    ("B19013", "What is the median household income in Texas?"),
    ("B19013", "What is the median household income in California?"),
    ("B19001", "How many households have income over $100,000 in New York?"),
    
    # Education
    ("B15003", "How many people have a bachelor's degree in Texas?"),
    ("B15003", "What is the education level distribution in California?"),
    
    # Employment
    ("B23025", "What is the unemployment rate in Texas?"),
    ("B23025", "How many people are employed in California?"),
    
    # Race & Ethnicity
    ("B02001", "What is the white population in Texas?"),
    ("B02001", "How many African Americans are there in California?"),
    ("B02001", "What is the Hispanic population in New York?"),
]

def run_query(table_code, question, model="auto"):
    """Run a single query."""
    cmd = [
        "modal", "run", "../core/modal_deployment.py::query",
        "--table-code", table_code,
        "--question", question
    ]
    
    if model != "auto":
        cmd.extend(["--force-model", model])
    
    print(f"\n🔍 Testing: {question}")
    print(f"   Table: {table_code}, Model: {model}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, timeout=600)
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"✅ Success! ({duration:.1f}s)")
        else:
            print(f"❌ Failed! ({duration:.1f}s)")
            
    except subprocess.TimeoutExpired:
        print(f"⏰ Timeout! (600s)")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run batch tests."""
    print("🚀 GovQuery Batch Testing")
    print("=" * 50)
    print(f"Running {len(TEST_QUESTIONS)} test questions...")
    
    start_time = time.time()
    success_count = 0
    
    for i, (table_code, question) in enumerate(TEST_QUESTIONS, 1):
        print(f"\n[{i}/{len(TEST_QUESTIONS)}]")
        run_query(table_code, question)
        success_count += 1  # Assuming success for now
        
        # Small delay between requests
        time.sleep(3)
    
    total_time = time.time() - start_time
    print(f"\n🎉 Batch test completed!")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Average per query: {total_time/len(TEST_QUESTIONS):.1f}s")

if __name__ == "__main__":
    main()
