#!/usr/bin/env python3
"""
Test to demonstrate the difference between warm and cold app queries.
"""

import subprocess
import os
import time
import json
from datetime import datetime

# Set up Modal authentication
os.environ["MODAL_TOKEN_ID"] = "ak-82ssY3sBr9rB9tau63rD2n"
os.environ["MODAL_TOKEN_SECRET"] = "as-A4L7Xzb33dybZ9XEhheVAV"

def run_query_with_timing(table_code, question, model="auto", description=""):
    """Run a query and measure timing."""
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

def test_warm_vs_cold():
    """Test warm vs cold app performance."""
    print("🧪 Warm vs Cold App Performance Test")
    print("=" * 60)
    
    # Test questions
    test_questions = [
        ("B01001", "What is the total population in Texas?"),
        ("B19013", "What is the median household income in California?"),
        ("B15003", "How many people have a bachelor's degree in New York?"),
    ]
    
    results = []
    
    # Cold start test (first run)
    print("\n❄️ COLD START TEST (Models not loaded)")
    print("-" * 40)
    
    for i, (table_code, question) in enumerate(test_questions, 1):
        result = run_query_with_timing(
            table_code, 
            question, 
            "auto",
            f"Cold Start {i}/3"
        )
        results.append(result)
        
        # Wait a bit between cold start queries
        if i < len(test_questions):
            print("   ⏳ Waiting 30 seconds before next cold query...")
            time.sleep(30)
    
    # Warm start test (subsequent runs)
    print("\n🔥 WARM START TEST (Models already loaded)")
    print("-" * 40)
    
    for i, (table_code, question) in enumerate(test_questions, 1):
        result = run_query_with_timing(
            table_code, 
            question, 
            "auto",
            f"Warm Start {i}/3"
        )
        results.append(result)
        
        # Shorter wait between warm queries
        if i < len(test_questions):
            print("   ⏳ Waiting 10 seconds before next warm query...")
            time.sleep(10)
    
    # Analyze results
    print("\n📊 PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    cold_results = [r for r in results if "Cold" in r["description"]]
    warm_results = [r for r in results if "Warm" in r["description"]]
    
    if cold_results:
        cold_avg = sum(r["duration"] for r in cold_results if r["success"]) / len([r for r in cold_results if r["success"]])
        print(f"❄️ Cold Start Average: {cold_avg:.1f}s")
        print(f"   Range: {min(r['duration'] for r in cold_results if r['success']):.1f}s - {max(r['duration'] for r in cold_results if r['success']):.1f}s")
    
    if warm_results:
        warm_avg = sum(r["duration"] for r in warm_results if r["success"]) / len([r for r in warm_results if r["success"]])
        print(f"🔥 Warm Start Average: {warm_avg:.1f}s")
        print(f"   Range: {min(r['duration'] for r in warm_results if r['success']):.1f}s - {max(r['duration'] for r in warm_results if r['success']):.1f}s")
    
    if cold_results and warm_results:
        speedup = cold_avg / warm_avg if warm_avg > 0 else 0
        print(f"⚡ Speedup: {speedup:.1f}x faster when warm")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"warm_cold_test_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump({
            "test_type": "warm_vs_cold",
            "timestamp": timestamp,
            "cold_results": cold_results,
            "warm_results": warm_results,
            "summary": {
                "cold_avg": cold_avg if cold_results else 0,
                "warm_avg": warm_avg if warm_results else 0,
                "speedup": speedup if cold_results and warm_results else 0
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")

def test_model_loading_breakdown():
    """Test to show model loading breakdown."""
    print("\n🔬 MODEL LOADING BREAKDOWN TEST")
    print("=" * 60)
    
    # Run a single query and analyze the output for loading times
    result = run_query_with_timing(
        "B01001",
        "What is the total population in Texas?",
        "auto",
        "Model Loading Analysis"
    )
    
    print("\n📋 Expected Loading Breakdown:")
    print("   🔄 Model Download: ~1-2 minutes")
    print("   🧠 T5 Model Loading: ~1-2 minutes")
    print("   🧠 SQLCoder Model Loading: ~1-2 minutes")
    print("   ⚙️  Tokenizer Setup: ~30 seconds")
    print("   🎯 SQL Generation: ~10-30 seconds")
    print("   📤 Response: ~5 seconds")

def main():
    """Main function."""
    print("🎯 GovQuery Warm vs Cold Performance Test")
    print("=" * 60)
    
    print("\nThis test will demonstrate the performance difference between:")
    print("❄️ Cold Start: First query (models need to load)")
    print("🔥 Warm Start: Subsequent queries (models already loaded)")
    
    print("\n⚠️  Note: This test will take 10-15 minutes to complete")
    print("   Cold start queries take 2-5 minutes each")
    print("   Warm start queries take 30-90 seconds each")
    
    proceed = input("\nProceed with test? (y/n): ").strip().lower()
    
    if proceed == 'y':
        test_warm_vs_cold()
        test_model_loading_breakdown()
    else:
        print("Test cancelled.")

if __name__ == "__main__":
    main()
