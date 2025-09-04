#!/usr/bin/env python3
"""
Test script for Serena integration in FixChain
"""

import os
import sys
import subprocess
from pathlib import Path

def test_serena_integration():
    """Test the Serena integration setup"""
    print("🧪 Testing Serena Integration in FixChain")
    print("=" * 50)
    
    # Check if required environment variables are set
    required_env_vars = ['GEMINI_API_KEY', 'PROJECT_KEY']
    missing_vars = []
    
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment variables check passed")
    
    # Test import of new modules
    try:
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from modules.fix.serena import SerenaFixer
        from modules.fix.hybrid import HybridFixer
        print("✅ Serena and Hybrid fixers imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import fixers: {e}")
        return False
    
    # Test fixer registry
    try:
        from modules.fix import registry
        
        # Test creating fixers
        test_dir = "/tmp/test_scan"
        os.makedirs(test_dir, exist_ok=True)
        
        serena_fixer = registry.create("serena", test_dir)
        hybrid_fixer = registry.create("hybrid", test_dir)
        llm_fixer = registry.create("llm", test_dir)
        
        print("✅ All fixers created successfully")
        print(f"   - SerenaFixer: {type(serena_fixer).__name__}")
        print(f"   - HybridFixer: {type(hybrid_fixer).__name__}")
        print(f"   - LLMFixer: {type(llm_fixer).__name__}")
        
    except Exception as e:
        print(f"❌ Failed to create fixers: {e}")
        return False
    
    # Test demo script with new parameters
    try:
        demo_path = os.path.join(os.path.dirname(__file__), "run", "run_demo.py")
        result = subprocess.run([
            "python3", demo_path, "--help"
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0 and "hybrid" in result.stdout:
            print("✅ Updated demo script help shows hybrid fixer option")
        else:
            print("⚠️  Demo script help may not be updated properly")
            
    except Exception as e:
        print(f"⚠️  Could not test demo script: {e}")
    
    print("\n🎉 Serena integration test completed!")
    print("\nNext steps:")
    print("1. Install additional dependencies: pip install -r requirements_serena.txt")
    print("2. Run with Serena: python3 run/run_demo.py --scanners bearer --fixers serena --project ../projects/Flask_App")
    print("3. Run with Hybrid: python3 run/run_demo.py --scanners bearer --fixers hybrid --project ../projects/Flask_App")
    
    return True

if __name__ == "__main__":
    test_serena_integration()
