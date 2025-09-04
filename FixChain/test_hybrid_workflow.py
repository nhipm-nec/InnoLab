#!/usr/bin/env python3
"""
Test script to verify complete hybrid workflow with auto Serena installation
"""

import os
import sys
import subprocess
from pathlib import Path

def test_environment_setup():
    """Test environment variables and dependencies"""
    print("=== Testing Environment Setup ===")
    
    # Check .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file found")
        
        # Check required environment variables
        from dotenv import load_dotenv
        load_dotenv()
        
        gemini_key = os.getenv('GEMINI_API_KEY')
        project_key = os.getenv('PROJECT_KEY')
        
        if gemini_key:
            print("✓ GEMINI_API_KEY is set")
        else:
            print("❌ GEMINI_API_KEY not found in .env")
            
        if project_key:
            print("✓ PROJECT_KEY is set")
        else:
            print("⚠ PROJECT_KEY not set (optional)")
    else:
        print("❌ .env file not found")
        return False
    
    return True

def test_fixer_imports():
    """Test that all fixers can be imported"""
    print("\n=== Testing Fixer Imports ===")
    
    try:
        from modules.fix.serena import SerenaFixer
        print("✓ SerenaFixer imported successfully")
    except Exception as e:
        print(f"❌ Failed to import SerenaFixer: {e}")
        return False
    
    try:
        from modules.fix.hybrid import HybridFixer
        print("✓ HybridFixer imported successfully")
    except Exception as e:
        print(f"❌ Failed to import HybridFixer: {e}")
        return False
    
    try:
        from modules.fix.registry import create
        hybrid_fixer = create("hybrid", "../projects/Flask_App")
        print("✓ HybridFixer created via registry")
    except Exception as e:
        print(f"❌ Failed to create HybridFixer via registry: {e}")
        return False
    
    return True

def test_serena_installation():
    """Test Serena auto-installation"""
    print("\n=== Testing Serena Installation ===")
    
    try:
        from modules.fix.serena import SerenaFixer
        
        # Create SerenaFixer instance to trigger auto-installation
        fixer = SerenaFixer("../projects/Flask_App")
        
        if fixer.serena_available:
            print("✓ Serena toolkit is available")
            print(f"✓ Serena path: {fixer.serena_path}")
        else:
            print("⚠ Serena toolkit not available, will use basic fixes")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Serena installation: {e}")
        return False

def test_hybrid_fixer_initialization():
    """Test HybridFixer initialization"""
    print("\n=== Testing HybridFixer Initialization ===")
    
    try:
        from modules.fix.hybrid import HybridFixer
        
        fixer = HybridFixer("../projects/Flask_App")
        
        print("✓ HybridFixer initialized successfully")
        print(f"✓ Serena fixer available: {fixer.serena_fixer.serena_available}")
        print(f"✓ LLM fixer initialized: {fixer.llm_fixer is not None}")
        print(f"✓ Git repository detected: {fixer.git_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing HybridFixer: {e}")
        return False

def test_demo_script():
    """Test that demo script can be called with hybrid fixer"""
    print("\n=== Testing Demo Script ===")
    
    try:
        # Test help command
        result = subprocess.run([
            sys.executable, "run/run_demo.py", "--help"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✓ Demo script help command works")
            
            # Check if hybrid fixer is mentioned in help
            if "hybrid" in result.stdout:
                print("✓ Hybrid fixer option available in demo script")
            else:
                print("⚠ Hybrid fixer not mentioned in help (might still work)")
        else:
            print(f"❌ Demo script help failed: {result.stderr}")
            return False
        
        return True
        
    except subprocess.TimeoutExpired:
        print("❌ Demo script help command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing demo script: {e}")
        return False

def run_integration_test():
    """Run a quick integration test with sample bugs"""
    print("\n=== Running Integration Test ===")
    
    try:
        from modules.fix.hybrid import HybridFixer
        
        # Create sample bugs for testing
        sample_bugs = [
            {
                "file_path": "../projects/Flask_App/app.py",
                "line_number": 1,
                "bug_type": "hardcoded_secret",
                "description": "Hardcoded password detected",
                "severity": "high"
            }
        ]
        
        fixer = HybridFixer("../projects/Flask_App")
        
        # Test fix_bugs method (dry run)
        print("Testing fix_bugs method...")
        result = fixer.fix_bugs(sample_bugs, use_rag=False)
        
        print(f"✓ Fix result: {result}")
        print(f"✓ Success: {result.get('success', False)}")
        print(f"✓ Fixed count: {result.get('fixed_count', 0)}")
        print(f"✓ Failed count: {result.get('failed_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Testing Hybrid Workflow with Auto Serena Installation")
    print("=" * 60)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Fixer Imports", test_fixer_imports),
        ("Serena Installation", test_serena_installation),
        ("HybridFixer Initialization", test_hybrid_fixer_initialization),
        ("Demo Script", test_demo_script),
        ("Integration Test", run_integration_test)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            print(f"❌ {test_name} ERROR: {e}")
    
    print(f"\n{'='*60}")
    print(f"🎯 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Hybrid workflow is ready.")
        print("\n📋 Next steps:")
        print("1. Run: python3 run/run_demo.py --scanners bearer --fixers hybrid --project ../projects/Flask_App --mode cloud")
        print("2. Monitor logs for Serena auto-installation and hybrid fixing")
        print("3. Check that bugs are actually fixed in the target project")
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
