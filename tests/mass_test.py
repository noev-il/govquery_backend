#!/usr/bin/env python3
"""
Mass testing system for GovQuery.
Tests multiple questions across different tables and models.
"""

import subprocess
import os
import time
import json
from datetime import datetime
from typing import List, Dict, Any

# Set up Modal authentication
# Modal credentials should be set via environment variables
# Set these before running: export MODAL_TOKEN_ID="your-id" MODAL_TOKEN_SECRET="your-secret"
if not os.environ.get("MODAL_TOKEN_ID") or not os.environ.get("MODAL_TOKEN_SECRET"):
    raise ValueError("MODAL_TOKEN_ID and MODAL_TOKEN_SECRET must be set as environment variables")

# Test question sets
TEST_QUESTIONS = {
    "population_demographics": [
        ("B01001", "What is the total population in Texas?"),
        ("B01001", "How many males are there in California?"),
        ("B01001", "What is the female population in New York?"),
        ("B01001", "How many people are under 18 in Florida?"),
        ("B01001", "What is the population 65 and over in Illinois?"),
    ],
    
    "income_economics": [
        ("B19013", "What is the median household income in Texas?"),
        ("B19013", "What is the median household income in California?"),
        ("B19013", "What is the median household income in New York?"),
        ("B19001", "How many households have income over $100,000 in Texas?"),
        ("B19001", "What is the income distribution in California?"),
    ],
    
    "education": [
        ("B15003", "How many people have a bachelor's degree in Texas?"),
        ("B15003", "What is the education level distribution in California?"),
        ("B15003", "How many people have a high school diploma in New York?"),
        ("B15003", "What percentage of people have a graduate degree in Florida?"),
    ],
    
    "employment": [
        ("B23025", "What is the unemployment rate in Texas?"),
        ("B23025", "How many people are employed in California?"),
        ("B23025", "What is the labor force participation in New York?"),
        ("B23025", "How many people are not in the labor force in Florida?"),
    ],
    
    "race_ethnicity": [
        ("B02001", "What is the white population in Texas?"),
        ("B02001", "How many African Americans are there in California?"),
        ("B02001", "What is the Hispanic population in New York?"),
        ("B02001", "How many Asians are there in Florida?"),
    ],
    
    "housing": [
        ("B19001", "What is the median home value in Texas?"),
        ("B19001", "How many owner-occupied homes are there in California?"),
        ("B19001", "What is the median rent in New York?"),
        ("B19001", "How many renter-occupied homes are there in Florida?"),
    ]
}

# Model variations to test
MODELS_TO_TEST = ["auto", "t5", "sqlcoder"]

def run_single_query(table_code: str, question: str, model: str = None) -> Dict[str, Any]:
    """Run a single query and return results."""
    cmd = [
        "modal", "run", "../core/modal_deployment.py::query",
        "--table-code", table_code,
        "--question", question
    ]
    
    if model and model != "auto":
        cmd.extend(["--force-model", model])
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if result.returncode == 0:
            # Parse the output to extract results
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
                "model_used": None,
                "sql": None,
                "duration": duration,
                "error": result.stderr
            }
            
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "table_code": table_code,
            "question": question,
            "model_requested": model,
            "model_used": None,
            "sql": None,
            "duration": 600,
            "error": "Timeout after 10 minutes"
        }
    except Exception as e:
        return {
            "success": False,
            "table_code": table_code,
            "question": question,
            "model_requested": model,
            "model_used": None,
            "sql": None,
            "duration": time.time() - start_time,
            "error": str(e)
        }

def run_category_tests(category: str, questions: List[tuple], models: List[str] = None) -> List[Dict[str, Any]]:
    """Run tests for a specific category."""
    if models is None:
        models = ["auto"]
    
    results = []
    total_tests = len(questions) * len(models)
    current_test = 0
    
    print(f"\n🧪 Testing {category} ({total_tests} tests)")
    print("=" * 60)
    
    for table_code, question in questions:
        for model in models:
            current_test += 1
            print(f"\n[{current_test}/{total_tests}] {category} - {model.upper()}")
            print(f"Table: {table_code}")
            print(f"Question: {question}")
            print("Running...")
            
            result = run_single_query(table_code, question, model)
            results.append(result)
            
            if result["success"]:
                print(f"✅ Success! ({result['duration']:.1f}s)")
                print(f"   Model: {result['model_used']}")
                print(f"   SQL: {result['sql'][:100]}{'...' if len(result['sql']) > 100 else ''}")
            else:
                print(f"❌ Failed: {result['error']}")
            
            # Small delay between requests
            time.sleep(2)
    
    return results

def run_quick_test() -> List[Dict[str, Any]]:
    """Run a quick test with a subset of questions."""
    print("🚀 Running Quick Mass Test")
    print("=" * 50)
    
    # Select a few questions from each category
    quick_questions = []
    for category, questions in TEST_QUESTIONS.items():
        quick_questions.extend(questions[:2])  # Take first 2 from each category
    
    return run_category_tests("Quick Test", quick_questions, ["auto"])

def run_full_test() -> Dict[str, List[Dict[str, Any]]]:
    """Run full test suite across all categories and models."""
    print("🚀 Running Full Mass Test Suite")
    print("=" * 50)
    
    all_results = {}
    
    for category, questions in TEST_QUESTIONS.items():
        results = run_category_tests(category, questions, MODELS_TO_TEST)
        all_results[category] = results
    
    return all_results

def run_model_comparison() -> Dict[str, List[Dict[str, Any]]]:
    """Run model comparison tests."""
    print("🚀 Running Model Comparison Test")
    print("=" * 50)
    
    # Select a few representative questions
    comparison_questions = [
        ("B01001", "What is the total population in Texas?"),
        ("B19013", "What is the median household income in California?"),
        ("B15003", "How many people have a bachelor's degree in New York?"),
        ("B23025", "What is the unemployment rate in Florida?"),
    ]
    
    results = {}
    for model in MODELS_TO_TEST:
        print(f"\n🔬 Testing {model.upper()} model")
        model_results = run_category_tests(f"{model.upper()} Model", comparison_questions, [model])
        results[model] = model_results
    
    return results

def save_results(results: Dict[str, Any], filename: str = None):
    """Save test results to JSON file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Results saved to: {filename}")

def print_summary(results: Dict[str, Any]):
    """Print test summary."""
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    total_tests = 0
    total_success = 0
    total_duration = 0
    
    for category, category_results in results.items():
        if isinstance(category_results, list):
            category_tests = len(category_results)
            category_success = sum(1 for r in category_results if r["success"])
            category_duration = sum(r["duration"] for r in category_results)
            
            total_tests += category_tests
            total_success += category_success
            total_duration += category_duration
            
            success_rate = (category_success / category_tests) * 100 if category_tests > 0 else 0
            
            print(f"{category:20} | {category_success:3}/{category_tests:3} ({success_rate:5.1f}%) | {category_duration:6.1f}s")
    
    overall_success_rate = (total_success / total_tests) * 100 if total_tests > 0 else 0
    avg_duration = total_duration / total_tests if total_tests > 0 else 0
    
    print("-" * 50)
    print(f"{'TOTAL':20} | {total_success:3}/{total_tests:3} ({overall_success_rate:5.1f}%) | {total_duration:6.1f}s")
    print(f"{'AVERAGE':20} | {'':8} | {avg_duration:6.1f}s per test")

def main():
    """Main function to run mass tests."""
    print("🎯 GovQuery Mass Testing System")
    print("=" * 50)
    
    print("\nSelect test type:")
    print("1. Quick Test (12 questions, auto model)")
    print("2. Full Test (all categories, all models)")
    print("3. Model Comparison (4 questions, all models)")
    print("4. Custom Test")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        results = run_quick_test()
        save_results({"quick_test": results})
        print_summary({"quick_test": results})
        
    elif choice == "2":
        results = run_full_test()
        save_results(results)
        print_summary(results)
        
    elif choice == "3":
        results = run_model_comparison()
        save_results(results)
        print_summary(results)
        
    elif choice == "4":
        print("\nCustom test options:")
        print("Available categories:", list(TEST_QUESTIONS.keys()))
        print("Available models:", MODELS_TO_TEST)
        
        category = input("Enter category (or 'all'): ").strip()
        model = input("Enter model (or 'all'): ").strip()
        
        if category == "all":
            questions = []
            for cat_questions in TEST_QUESTIONS.values():
                questions.extend(cat_questions)
            category = "custom_all"
        else:
            questions = TEST_QUESTIONS.get(category, [])
        
        if model == "all":
            models = MODELS_TO_TEST
        else:
            models = [model]
        
        if questions:
            results = run_category_tests(category, questions, models)
            save_results({category: results})
            print_summary({category: results})
        else:
            print("❌ Invalid category or no questions found")
    
    else:
        print("❌ Invalid choice")

if __name__ == "__main__":
    main()
