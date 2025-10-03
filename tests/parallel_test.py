#!/usr/bin/env python3
"""
Parallel testing for GovQuery using multiple processes.
Note: This is more complex due to Modal's architecture.
"""

import subprocess
import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Tuple, Dict, Any

# Set up Modal authentication
os.environ["MODAL_TOKEN_ID"] = "ak-82ssY3sBr9rB9tau63rD2n"
os.environ["MODAL_TOKEN_SECRET"] = "as-A4L7Xzb33dybZ9XEhheVAV"

# Test questions for parallel execution
PARALLEL_QUESTIONS = [
    ("B01001", "What is the total population in Texas?"),
    ("B01001", "How many males are there in California?"),
    ("B19013", "What is the median household income in New York?"),
    ("B15003", "How many people have a bachelor's degree in Florida?"),
    ("B23025", "What is the unemployment rate in Illinois?"),
    ("B02001", "What is the white population in Georgia?"),
]

def run_single_query_parallel(args: Tuple[str, str, str]) -> Dict[str, Any]:
    """Run a single query in parallel."""
    table_code, question, model = args
    
    cmd = [
        "modal", "run", "../core/modal_deployment.py::query",
        "--table-code", table_code,
        "--question", question
    ]
    
    if model != "auto":
        cmd.extend(["--force-model", model])
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            # Parse output
            output_lines = result.stdout.split('\n')
            sql = ""
            model_used = ""
            
            for line in output_lines:
                if line.startswith("SQL:"):
                    sql = line.replace("SQL:", "").strip()
                elif line.startswith("Model:"):
                    model_used = line.replace("Model:", "").strip()
            
            return {
                "success": True,
                "table_code": table_code,
                "question": question,
                "model_requested": model,
                "model_used": model_used,
                "sql": sql,
                "duration": duration,
                "error": None
            }
        else:
            return {
                "success": False,
                "table_code": table_code,
                "question": question,
                "model_requested": model,
                "duration": duration,
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "table_code": table_code,
            "question": question,
            "model_requested": model,
            "duration": 600,
            "error": "Timeout"
        }
    except Exception as e:
        return {
            "success": False,
            "table_code": table_code,
            "question": question,
            "model_requested": model,
            "duration": time.time() - start_time,
            "error": str(e)
        }

def run_parallel_tests(max_workers: int = 3) -> List[Dict[str, Any]]:
    """Run tests in parallel."""
    print(f"🚀 Running Parallel Tests (max {max_workers} workers)")
    print("=" * 50)
    
    # Prepare arguments for parallel execution
    test_args = [(table, question, "auto") for table, question in PARALLEL_QUESTIONS]
    
    results = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_args = {
            executor.submit(run_single_query_parallel, args): args 
            for args in test_args
        }
        
        # Process completed tasks
        for i, future in enumerate(as_completed(future_to_args), 1):
            args = future_to_args[future]
            table_code, question, model = args
            
            print(f"\n[{i}/{len(test_args)}] Completed:")
            print(f"   Table: {table_code}")
            print(f"   Question: {question}")
            
            try:
                result = future.result()
                results.append(result)
                
                if result["success"]:
                    print(f"   ✅ Success! ({result['duration']:.1f}s)")
                    print(f"   Model: {result['model_used']}")
                    print(f"   SQL: {result['sql'][:80]}{'...' if len(result['sql']) > 80 else ''}")
                else:
                    print(f"   ❌ Failed: {result['error']}")
                    
            except Exception as e:
                print(f"   ❌ Exception: {e}")
                results.append({
                    "success": False,
                    "table_code": table_code,
                    "question": question,
                    "model_requested": model,
                    "duration": 0,
                    "error": str(e)
                })
    
    total_time = time.time() - start_time
    success_count = sum(1 for r in results if r["success"])
    
    print(f"\n📊 Parallel Test Results:")
    print(f"   Total time: {total_time:.1f}s")
    print(f"   Success rate: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
    print(f"   Average per query: {total_time/len(results):.1f}s")
    
    return results

def main():
    """Main function."""
    print("🎯 GovQuery Parallel Testing")
    print("=" * 50)
    
    print(f"Testing {len(PARALLEL_QUESTIONS)} questions in parallel...")
    
    # Run parallel tests
    results = run_parallel_tests(max_workers=3)
    
    # Save results
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"parallel_test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")

if __name__ == "__main__":
    main()
