#!/usr/bin/env python3
"""
Enhanced Batch Fix Script - FixChain Version
Moved from SonarQ to FixChain for better architecture
"""

import google.generativeai as genai
import os
import sys
import json
import ast
import shutil
import subprocess
import argparse
from pathlib import Path
import logging
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import tempfile
import fnmatch

# Import RAG service from FixChain structure
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from service.rag_service import RAGService

@dataclass
class FixResult:
    success: bool
    file_path: str
    original_size: int
    fixed_size: int
    issues_found: List[str]
    validation_errors: List[str]
    backup_path: Optional[str] = None
    processing_time: float = 0.0
    similarity_ratio: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    meets_threshold: bool = True

class CodeValidator:
    """Validate code quality and syntax"""
    
    @staticmethod
    def validate_python_syntax(code: str) -> Tuple[bool, List[str]]:
        """Validate Python syntax"""
        errors = []
        try:
            ast.parse(code)
            return True, errors
        except SyntaxError as e:
            errors.append(f"Syntax Error: {e.msg} at line {e.lineno}")
            return False, errors
        except Exception as e:
            errors.append(f"Parse Error: {str(e)}")
            return False, errors
    
    @staticmethod
    def validate_javascript_syntax(code: str) -> Tuple[bool, List[str]]:
        """Basic JavaScript validation using Node.js if available"""
        errors = []
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                f.flush()
                
                result = subprocess.run(
                    ['node', '--check', f.name], 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                
                os.unlink(f.name)
                
                if result.returncode != 0:
                    errors.append(f"JS Syntax Error: {result.stderr}")
                    return False, errors
                
                return True, errors
                
        except subprocess.TimeoutExpired:
            errors.append("Validation timeout")
            return False, errors
        except FileNotFoundError:
            return True, ["Node.js not available for validation"]
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    @staticmethod
    def validate_html_syntax(code: str) -> Tuple[bool, List[str]]:
        """Basic HTML validation"""
        errors = []
        try:
            if '<html' in code.lower() and '</html>' not in code.lower():
                errors.append("Missing closing </html> tag")
            if '<head' in code.lower() and '</head>' not in code.lower():
                errors.append("Missing closing </head> tag")
            if '<body' in code.lower() and '</body>' not in code.lower():
                errors.append("Missing closing </body> tag")
            
            return len(errors) == 0, errors
        except Exception as e:
            errors.append(f"HTML validation error: {str(e)}")
            return False, errors
    
    @staticmethod
    def validate_css_syntax(code: str) -> Tuple[bool, List[str]]:
        """Basic CSS validation"""
        errors = []
        try:
            open_braces = code.count('{')
            close_braces = code.count('}')
            if open_braces != close_braces:
                errors.append(f"Mismatched braces: {open_braces} open, {close_braces} close")
            
            return len(errors) == 0, errors
        except Exception as e:
            errors.append(f"CSS validation error: {str(e)}")
            return False, errors
    
    @staticmethod
    def check_code_quality(original: str, fixed: str) -> Dict[str, any]:
        """Compare code quality metrics"""
        return {
            'size_change': len(fixed) - len(original),
            'line_change': len(fixed.split('\n')) - len(original.split('\n')),
            'similarity_ratio': CodeValidator._similarity_ratio(original, fixed)
        }
    
    @staticmethod
    def _similarity_ratio(str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings"""
        from difflib import SequenceMatcher
        return SequenceMatcher(None, str1, str2).ratio()

    def _load_prompt_template(self, template_type: str, custom_prompt: str = None):
        """Load prompt template from files or use custom prompt"""
        try:
            # Setup Jinja2 environment for template loading - updated path
            prompt_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompt')
            
            if os.path.exists(prompt_dir):
                env = Environment(loader=FileSystemLoader(prompt_dir))
                
                template_files = {
                    'fix': 'fix.j2',
                    'analyze': 'analyze.j2',
                    'custom': 'custom.j2'
                }
                
                if custom_prompt:
                    template_file = template_files.get('custom', 'custom.j2')
                    if os.path.exists(os.path.join(prompt_dir, template_file)):
                        template = env.get_template(template_file)
                        return template, {'custom_prompt': custom_prompt}
                    else:
                        template_content = f"""
{custom_prompt}

Code cần sửa:
{{{{ original_code }}}}

Chỉ trả về code đã sửa, không cần markdown formatting hay giải thích.
"""
                        class SimpleTemplate:
                            def __init__(self, content):
                                self.content = content
                            def render(self, **kwargs):
                                result = self.content
                                for key, value in kwargs.items():
                                    result = result.replace(f'{{{{ {key} }}}}', str(value))
                                return result
                        
                        return SimpleTemplate(template_content), {}
                else:
                    template_file = template_files.get(template_type, 'fix.j2')
                    if os.path.exists(os.path.join(prompt_dir, template_file)):
                        template = env.get_template(template_file)
                        return template, {}
                    else:
                        return None, {}
            else:
                return None, {}
        
        except Exception as e:
            print(f"Warning: Could not load template from prompt directory: {e}")
            return None, {}
