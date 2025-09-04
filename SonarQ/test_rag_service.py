#!/usr/bin/env python3
"""
Test script for RAG Service integration
"""

import os
import sys
import json
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rag_service import RAGService, RAGSearchResult, RAGAddResult
from dotenv import load_dotenv

def test_rag_service():
    """Test RAG service functionality"""
    print("Testing RAG Service...")
    print("=" * 50)
    
    # Initialize RAG service
    rag_service = RAGService()
    
    # Test health check
    print("\n1. Testing health check...")
    is_healthy = rag_service.health_check()
    print(f"   RAG service health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
    
    if not is_healthy:
        print("   ⚠️ RAG service is not available. Please check the API endpoint.")
        return
    
    # Test data for search
    test_issues_data = [
        {
            "key": "TEST-001",
            "rule": "python:S1481",
            "severity": "MINOR",
            "component": "test_file.py",
            "line": 10,
            "message": "Remove this unused local variable",
            "type": "CODE_SMELL",
            "classification": "True Bug",
            "action": "Fix",
            "rule_description": "Unused local variables should be removed"
        },
        {
            "key": "TEST-002",
            "rule": "python:S1134",
            "severity": "INFO",
            "component": "test_file.py",
            "line": 15,
            "message": "Take the required action to fix the issue indicated by this comment",
            "type": "CODE_SMELL",
            "classification": "True Bug",
            "action": "Fix",
            "rule_description": "Track uses of 'FIXME' tags"
        }
    ]
    
    # Test search functionality
    print("\n2. Testing RAG search...")
    search_result = rag_service.search_rag_knowledge(test_issues_data, limit=5)
    
    if search_result.success:
        print(f"   ✅ Search successful! Found {len(search_result.sources)} results")
        if search_result.sources:
            for i, source in enumerate(search_result.sources[:2], 1):
                print(f"   📄 Result {i}: {source.get('content', 'No content')[:100]}...")
        else:
            print("   📭 No results found (this is normal for a new RAG system)")
    else:
        print(f"   ❌ Search failed: {search_result.error_message}")
    
    # Test get RAG context
    print("\n3. Testing RAG context generation...")
    rag_context = rag_service.get_rag_context_for_prompt(test_issues_data)
    
    if rag_context:
        print(f"   ✅ RAG context generated ({len(rag_context)} characters)")
        print(f"   📝 Context preview: {rag_context[:200]}...")
    else:
        print("   📭 No RAG context available (normal for new system)")
    
    # Test add functionality
    print("\n4. Testing RAG add functionality...")
    
    # Sample fix context
    fix_context = {
        'file_path': '/test/sample.py',
        'original_size': 150,
        'fixed_size': 140,
        'similarity_ratio': 0.95,
        'input_tokens': 500,
        'output_tokens': 200,
        'total_tokens': 700,
        'processing_time': 2.5,
        'meets_threshold': True,
        'validation_errors': [],
        'issues_found': ['Unused variable removed']
    }
    
    # Sample AI response
    ai_response = """
## 1. Bug Context
- Found unused local variable 'temp_var' at line 10
- Classification: True Positive (code smell)

## 2. Fix Summary
- Removed unused variable 'temp_var'
- Why: Variable was declared but never used, causing code smell
- Change: Deleted line 10 containing the unused variable declaration

## 3. Fixed Source Code
# Original code had unused variable, now removed
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
"""
    
    # Sample fixed code
    fixed_code = """
def process_data(data):
    result = []
    for item in data:
        result.append(item * 2)
    return result
"""
    
    add_result = rag_service.add_fix_to_rag(fix_context, test_issues_data, ai_response, fixed_code)
    
    if add_result.success:
        print(f"   ✅ Successfully added fix to RAG!")
        print(f"   📄 Document ID: {add_result.document_id}")
    else:
        print(f"   ❌ Failed to add to RAG: {add_result.error_message}")
    
    print("\n" + "=" * 50)
    print("RAG Service test completed!")
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"   Health Check: {'✅' if is_healthy else '❌'}")
    print(f"   Search: {'✅' if search_result.success else '❌'}")
    print(f"   Context: {'✅' if rag_context else '📭'}")
    print(f"   Add: {'✅' if add_result.success else '❌'}")

if __name__ == "__main__":
    # Load environment variables
    load_dotenv()
    test_rag_service()