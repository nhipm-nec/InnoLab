#!/usr/bin/env python3
"""
RAG Service for SonarQ Integration
Handles communication with FixChain RAG API for search and add operations
"""

import requests
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from pathlib import Path

@dataclass
class RAGSearchResult:
    """Result from RAG search operation"""
    answer: str
    sources: List[Dict]
    query: str
    success: bool = True
    error_message: str = ""

@dataclass
class RAGAddResult:
    """Result from RAG add operation"""
    success: bool
    document_id: str = ""
    error_message: str = ""
    content_length: int = 0

class RAGService:
    """Service for interacting with FixChain RAG API"""
    
    def __init__(self, base_url: str = "http://localhost:8000/api/v1", timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
        
        # API endpoints
        self.search_endpoint = f"{self.base_url}/rag/reasoning/search"
        self.add_endpoint = f"{self.base_url}/rag/reasoning/add"
        
        # Default headers
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def search_rag_knowledge(self, issues_data: List[Dict], limit: int = 5) -> RAGSearchResult:
        """
        Search RAG knowledge base for similar bug fixes
        
        Args:
            issues_data: List of issues from SonarQube analysis
            limit: Maximum number of results to return
            
        Returns:
            RAGSearchResult with search results or error information
        """
        try:
            # Transform issues_data to search query format
            search_payload = self._transform_issues_to_search_query(issues_data, limit)
            
            if not search_payload.get("query"):
                return RAGSearchResult(
                    answer="No relevant issues found for RAG search.",
                    sources=[],
                    query="",
                    success=False,
                    error_message="No searchable issues found"
                )
            
            self.logger.info(f"Searching RAG with query: {search_payload['query'][:100]}...")
            
            # Make API request
            response = requests.post(
                self.search_endpoint,
                json=search_payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result_data = response.json()
                return RAGSearchResult(
                    answer=result_data.get("answer", ""),
                    sources=result_data.get("sources", []),
                    query=result_data.get("query", ""),
                    success=True
                )
            else:
                error_msg = f"RAG search failed (HTTP {response.status_code}): {response.text[:200]}"
                self.logger.error(error_msg)
                return RAGSearchResult(
                    answer="",
                    sources=[],
                    query="",
                    success=False,
                    error_message=error_msg
                )
                
        except requests.exceptions.RequestException as e:
            error_msg = f"RAG search request failed: {str(e)}"
            self.logger.error(error_msg)
            return RAGSearchResult(
                answer="",
                sources=[],
                query="",
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"RAG search error: {str(e)}"
            self.logger.error(error_msg)
            return RAGSearchResult(
                answer="",
                sources=[],
                query="",
                success=False,
                error_message=error_msg
            )
    
    def add_fix_to_rag(self, fix_context: Dict, issues_data: List[Dict] = None, 
                       raw_response: str = "", fixed_code: str = "") -> RAGAddResult:
        """
        Add bug fix information to RAG knowledge base
        
        Args:
            fix_context: Context about the fix (file_path, success, etc.)
            issues_data: Original issues that were fixed
            raw_response: Raw AI response from the fix process
            fixed_code: The fixed code content
            
        Returns:
            RAGAddResult with operation result
        """
        try:
            # Transform fix information to RAG format
            add_payload = self._transform_fix_to_rag_format(
                fix_context, issues_data, raw_response, fixed_code
            )
            
            self.logger.info(f"Adding fix to RAG: {fix_context.get('file_path', 'unknown')}")
            
            # Make API request
            response = requests.post(
                self.add_endpoint,
                json=add_payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                result_data = response.json()
                return RAGAddResult(
                    success=True,
                    document_id=result_data.get("document_id", ""),
                    content_length=result_data.get("content_length", 0)
                )
            else:
                error_msg = f"RAG add failed (HTTP {response.status_code}): {response.text[:200]}"
                self.logger.error(error_msg)
                return RAGAddResult(
                    success=False,
                    error_message=error_msg
                )
                
        except requests.exceptions.RequestException as e:
            error_msg = f"RAG add request failed: {str(e)}"
            self.logger.error(error_msg)
            return RAGAddResult(
                success=False,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"RAG add error: {str(e)}"
            self.logger.error(error_msg)
            return RAGAddResult(
                success=False,
                error_message=error_msg
            )
    
    def _transform_issues_to_search_query(self, issues_data: List[Dict], limit: int) -> Dict:
        """
        Transform issues data to RAG search query format
        
        Expected output format:
        {
            "query": ["<rule_description1>", "<rule_description2>", "..."],
            "limit": 5,
            "combine_mode": "OR"
        }
        """
        query_list = []
        
        if issues_data:
            for issue in issues_data:
                # Filter for True Bug and Fix action
                classification = issue.get('classification', '').lower()
                action = issue.get('action', '').lower()
                
                if classification == 'true bug' and action == 'fix':
                    rule_description = issue.get('rule_description', '')
                    if rule_description and rule_description.strip():
                        # Remove duplicates while preserving order
                        if rule_description not in query_list:
                            query_list.append(rule_description)
        
        return {
            "query": query_list,
            "limit": limit,
            "combine_mode": "OR"
        }
    
    def _transform_fix_to_rag_format(self, fix_context: Dict, issues_data: List[Dict] = None,
                                   raw_response: str = "", fixed_code: str = "") -> Dict:
        """
        Transform fix information to RAG add format
        
        Expected output format:
        {
            "content": "description",
            "metadata": { /* include ALL relevant key/value pairs */ }
        }
        """
        # Prepare bug context from issues_data
        bug_context = []
        fix_summary = []
        
        if issues_data:
            file_path = fix_context.get('file_path', '')
            for issue in issues_data:
                if issue.get('component', '').endswith(Path(file_path).name):
                    bug_context.append(f"Line {issue.get('line', 'N/A')}: {issue.get('message', 'No message')}")
                    fix_summary.append({
                        "title": issue.get('message', 'Bug fix'),
                        "why": f"Issue type: {issue.get('type', 'Unknown')}, Severity: {issue.get('severity', 'Unknown')}",
                        "change": "Applied AI-generated fix to resolve the issue"
                    })
        
        # Determine code language from file extension
        file_path = fix_context.get('file_path', '')
        file_ext = Path(file_path).suffix.lower() if file_path else ''
        language_map = {
            '.py': 'python',
            '.js': 'javascript', 
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.html': 'html',
            '.css': 'css'
        }
        code_language = language_map.get(file_ext, 'text')
        
        # Build content description
        num_issues = len(fix_summary) if fix_summary else 0
        file_name = Path(file_path).name if file_path else 'unknown file'
        content = f"Bug: Fixed {num_issues} issues in {file_name}"
        
        # Build metadata
        metadata = {
            "bug_title": f"Fixed issues in {file_name}",
            "bug_context": bug_context if bug_context else ["No specific bug context available"],
            "fix_summary": fix_summary if fix_summary else [{
                "title": "General code improvement",
                "why": "Applied AI-generated fixes",
                "change": "Code quality and bug fixes"
            }],
            "fixed_source_present": bool(fixed_code),
            "code_language": code_language,
            "code": fixed_code if fixed_code else ""
        }
        
        # Add additional context from fix_context
        for key, value in fix_context.items():
            if key not in metadata:  # Don't override existing keys
                metadata[key] = value
        
        # Limit raw_ai_response to prevent payload bloat
        if raw_response:
            metadata["raw_ai_response"] = raw_response[:1000]
        
        return {
            "content": content,
            "metadata": metadata
        }
    
    def health_check(self) -> bool:
        """
        Check if RAG service is available
        
        Returns:
            True if service is healthy, False otherwise
        """
        try:
            health_url = f"{self.base_url}/rag/health"
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_rag_context_for_prompt(self, issues_data: List[Dict]) -> str:
        """
        Get RAG context to enhance the fix prompt
        
        Args:
            issues_data: List of issues to search for
            
        Returns:
            Formatted string with RAG context for prompt enhancement
        """
        search_result = self.search_rag_knowledge(issues_data, limit=3)
        
        if not search_result.success or not search_result.sources:
            return "No relevant previous fixes found in knowledge base."
        
        context_parts = ["\n=== RELEVANT PREVIOUS FIXES FROM KNOWLEDGE BASE ==="]
        
        for i, source in enumerate(search_result.sources[:3], 1):
            content = source.get('content', '')[:200]
            similarity = source.get('similarity_score', 0)
            context_parts.append(f"\n{i}. Similar Fix (Similarity: {similarity:.2f}):")
            context_parts.append(f"   {content}...")
            
            # Add metadata if available
            metadata = source.get('metadata', {})
            if metadata.get('code_language'):
                context_parts.append(f"   Language: {metadata['code_language']}")
            if metadata.get('fix_summary'):
                fix_summaries = metadata['fix_summary']
                if isinstance(fix_summaries, list) and fix_summaries:
                    context_parts.append(f"   Fix approach: {fix_summaries[0].get('change', '')}")
        
        context_parts.append("\n=== END OF KNOWLEDGE BASE CONTEXT ===\n")
        
        return "\n".join(context_parts)

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    rag_service = RAGService()
    
    # Test health check
    if rag_service.health_check():
        print("✅ RAG service is healthy")
    else:
        print("❌ RAG service is not available")
    
    # Example search
    sample_issues = [
        {
            "classification": "True Bug",
            "action": "Fix",
            "rule_description": "SQL injection vulnerability in user input",
            "message": "Potential SQL injection",
            "line": 42,
            "component": "src/main/java/Example.java"
        }
    ]
    
    search_result = rag_service.search_rag_knowledge(sample_issues)
    print(f"Search result: {search_result.success}")
    if search_result.success:
        print(f"Answer: {search_result.answer[:100]}...")
        print(f"Sources found: {len(search_result.sources)}")