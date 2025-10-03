#!/usr/bin/env python3
"""
Test with a persistent app to avoid cold starts.
"""

import subprocess
import os
import time
import json
from datetime import datetime

# Set up Modal authentication
os.environ["MODAL_TOKEN_ID"] = "ak-82ssY3sBr9rB9tau63rD2n"
os.environ["MODAL_TOKEN_SECRET"] = "as-A4L7Xzb33dybZ9XEhheVAV"

def run_warm_query(table_code, question, model="auto", description=""):
    """Run a query against a persistent app (should be warm)."""
    cmd = [
        "modal", "run", "../core/modal_deployment.py::query",
        "--table-code", table_code,
        "--question", question
    ]
    
    if model != "auto":
        cmd.extend(["--force-model", model])
    
    print(f"\n🔍 {description}")
    print(f"   Table: {table_code}")
    print(f"   Question: {question}")
    print(f"   Model: {model}")
    print("   Starting...")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
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
            
            print(f"   ✅ Success! ({duration:.1f}s)")
            print(f"   Model Used: {model_used}")
            print(f"   SQL: {sql[:100]}{'...' if len(sql) > 100 else ''}")
            
            return {
                "success": True,
                "duration": duration,
                "model_used": model_used,
                "sql": sql,
                "description": description
            }
        else:
            print(f"   ❌ Failed! ({duration:.1f}s)")
            print(f"   Error: {result.stderr}")
            return {
                "success": False,
                "duration": duration,
                "error": result.stderr,
                "description": description
            }
            
    except subprocess.TimeoutExpired:
        print(f"   ⏰ Timeout! (600s)")
        return {
            "success": False,
            "duration": 600,
            "error": "Timeout",
            "description": description
        }
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {
            "success": False,
            "duration": time.time() - start_time,
            "error": str(e),
            "description": description
        }

def test_warm_performance():
    """Test warm app performance."""
    print("🔥 Warm App Performance Test")
    print("=" * 60)
    
    # Test questions
    test_questions = [
        ("B01001", "What is the total population in Texas?"),
        ("B19013", "What is the median household income in California?"),
        ("B15003", "How many people have a bachelor's degree in New York?"),
        ("B23025", "What is the unemployment rate in Florida?"),
        ("B02001", "What is the white population in Texas?"),
    ]
    
    results = []
    
    print("\n🔥 WARM START TEST (Models should be loaded)")
    print("-" * 40)
    
    for i, (table_code, question) in enumerate(test_questions, 1):
        result = run_warm_query(
            table_code, 
            question, 
            "auto",
            f"Warm Query {i}/{len(test_questions)}"
        )
        results.append(result)
        
        # Short wait between queries
        if i < len(test_questions):
            print("   ⏳ Waiting 5 seconds before next query...")
            time.sleep(5)
    
    # Analyze results
    print("\n📊 PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    successful_results = [r for r in results if r["success"]]
    
    if successful_results:
        avg_time = sum(r["duration"] for r in successful_results) / len(successful_results)
        min_time = min(r["duration"] for r in successful_results)
        max_time = max(r["duration"] for r in successful_results)
        
        print(f"🔥 Warm Start Average: {avg_time:.1f}s")
        print(f"   Range: {min_time:.1f}s - {max_time:.1f}s")
        print(f"   Success Rate: {len(successful_results)}/{len(results)} ({len(successful_results)/len(results)*100:.1f}%)")
        
        # Compare to cold start expectations
        cold_avg = 150  # From your test results
        speedup = cold_avg / avg_time if avg_time > 0 else 0
        print(f"⚡ Speedup vs Cold Start: {speedup:.1f}x faster")
        
        if avg_time > 120:
            print("⚠️  Warning: Times are still high - models may not be staying warm")
        elif avg_time < 60:
            print("✅ Excellent: Models are staying warm!")
        else:
            print("✅ Good: Models are reasonably warm")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"warm_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "test_type": "warm_performance",
            "timestamp": timestamp,
            "results": results,
            "summary": {
                "avg_time": avg_time if successful_results else 0,
                "min_time": min_time if successful_results else 0,
                "max_time": max_time if successful_results else 0,
                "success_rate": len(successful_results)/len(results) if results else 0
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")

def main():
    """Main function."""
    print("🎯 GovQuery Warm Performance Test")
    print("=" * 60)
    
    print("\nThis test assumes you have a persistent app running.")
    print("If not, run: python deploy_persistent_fixed.py")
    
    proceed = input("\nProceed with warm test? (y/n): ").strip().lower()
    
    if proceed == 'y':
        test_warm_performance()
    else:
        print("Test cancelled.")

if __name__ == "__main__":
    main()
