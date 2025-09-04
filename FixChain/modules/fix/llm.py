from __future__ import annotations
import json
import os
import ast
import subprocess
import tempfile
from typing import Dict, List, Optional
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

from utils.logger import logger
from .base import Fixer


class LLMFixer(Fixer):
<<<<<<< HEAD
    """LLM-based fixer that applies fixes using Gemini AI directly"""
=======
    """Service that applies fixes using local batch_fix.py"""
>>>>>>> 4000c21 (move all logic to FĩChain folder)

    def __init__(self, scan_directory: str):
        self.scan_directory = scan_directory
        
        # Load environment variables
        load_dotenv()
        
        # Initialize Gemini AI
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            logger.error("GEMINI_API_KEY not found - LLMFixer cannot function")
            self.model = None
        else:
            try:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                logger.info("LLMFixer initialized with Gemini 2.0 Flash")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None

<<<<<<< HEAD
    def _validate_python_syntax(self, code: str) -> bool:
        """Validate Python syntax"""
=======
    def fix_bugs(self, list_real_bugs: List[Dict], use_rag: bool = False) -> Dict:
        # Robust input validation and parsing
        if isinstance(list_real_bugs, str):
            try:
                import json
                list_real_bugs = json.loads(list_real_bugs)
                logger.info(f"LLMFixer: Parsed string input to {len(list_real_bugs)} bugs")
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"LLMFixer: Failed to parse list_real_bugs string: {e}")
                return {
                    "success": False,
                    "fixed_count": 0,
                    "error": f"Invalid input format: {str(e)}",
                }
        
        if not isinstance(list_real_bugs, list):
            logger.error(f"LLMFixer: Invalid list_real_bugs type: {type(list_real_bugs)}")
            return {
                "success": False,
                "fixed_count": 0,
                "error": f"Expected list, got {type(list_real_bugs)}",
            }
        
>>>>>>> 4000c21 (move all logic to FĩChain folder)
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False

    def _validate_javascript_syntax(self, code: str) -> bool:
        """Validate JavaScript syntax using Node.js"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            result = subprocess.run(
                ['node', '--check', temp_file],
                capture_output=True,
                text=True
            )
            
            os.unlink(temp_file)
            return result.returncode == 0
            
        except Exception:
            return False

    def _validate_code_syntax(self, file_path: str, code: str) -> bool:
        """Validate code syntax based on file extension"""
        if file_path.endswith('.py'):
            return self._validate_python_syntax(code)
        elif file_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
            return self._validate_javascript_syntax(code)
        else:
            # For other file types, assume valid
            return True

    def _generate_fix_prompt(self, bugs: List[Dict], file_content: str, file_path: str) -> str:
        """Generate prompt for Gemini to fix bugs"""
        
        bug_descriptions = []
        for bug in bugs:
            bug_desc = f"""
Bug Type: {bug.get('type', 'Unknown')}
Severity: {bug.get('severity', 'Unknown')}
Line: {bug.get('line_number', 'Unknown')}
Description: {bug.get('description', 'No description')}
Rule: {bug.get('rule_id', 'Unknown')}
"""
            bug_descriptions.append(bug_desc)
        
        prompt = f"""
You are an expert code security analyst and developer. Fix the following security vulnerabilities in the code.

FILE: {file_path}

BUGS TO FIX:
{chr(10).join(bug_descriptions)}

CURRENT CODE:
```
{file_content}
```

INSTRUCTIONS:
1. Fix ALL the security vulnerabilities listed above
2. Maintain the original code structure and functionality
3. Use secure coding practices
4. Add comments explaining the security fixes
5. Ensure the code remains syntactically correct
6. Do not remove or break existing functionality

Return ONLY the complete fixed code without any explanations or markdown formatting.
"""
        return prompt

    def _fix_file_with_gemini(self, file_path: str, bugs: List[Dict]) -> Dict:
        """Fix a single file using Gemini AI"""
        
        if not self.model:
            return {
                "success": False,
                "error": "Gemini model not available",
                "fixed_content": None
            }
        
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Generate fix prompt
            prompt = self._generate_fix_prompt(bugs, original_content, file_path)
            
            # Get fix from Gemini
            logger.info(f"Requesting fix from Gemini for {file_path}")
            response = self.model.generate_content(prompt)
            fixed_content = response.text.strip()
            
            # Validate syntax
            if not self._validate_code_syntax(file_path, fixed_content):
                logger.error(f"Fixed code has syntax errors: {file_path}")
                return {
                    "success": False,
                    "error": "Fixed code has syntax errors",
                    "fixed_content": None
                }
            
            # Check similarity (basic check)
            similarity = len(set(original_content.split()) & set(fixed_content.split())) / max(len(original_content.split()), len(fixed_content.split()))
            
            if similarity < 0.3:  # Too different, might be hallucination
                logger.warning(f"Fixed code too different from original: {file_path} (similarity: {similarity:.2f})")
                return {
                    "success": False,
                    "error": f"Fixed code too different (similarity: {similarity:.2f})",
                    "fixed_content": None
                }
            
            return {
                "success": True,
                "fixed_content": fixed_content,
                "original_size": len(original_content),
                "fixed_size": len(fixed_content),
                "similarity": similarity,
                "input_tokens": response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
            }
            
        except Exception as e:
            logger.error(f"Error fixing file {file_path}: {e}")
            return {
                "success": False,
                "error": str(e),
                "fixed_content": None
            }

    def fix_bugs(self, list_real_bugs: Dict, use_rag: bool = False) -> Dict:
        """Fix bugs using Gemini AI directly"""
        
        try:
            logger.info(f"Starting LLMFixer for bug data: {type(list_real_bugs)}")
            logger.info(f"DEBUG: Bug data content: {list_real_bugs}")
            
            # Handle different bug data formats
            if isinstance(list_real_bugs, dict):
                # Extract bugs from dict format
                if 'bugs' in list_real_bugs:
                    actual_bugs = list_real_bugs['bugs']
                    logger.info(f"Extracted {len(actual_bugs)} bugs from dict format")
                else:
                    logger.error("Bug data is dict but has no 'bugs' key")
                    return {
                        "success": False,
                        "fixed_count": 0,
                        "failed_count": 0,
                        "error": "Invalid bug data format - dict without 'bugs' key"
                    }
            elif isinstance(list_real_bugs, list):
                actual_bugs = list_real_bugs
                logger.info(f"Using list format with {len(actual_bugs)} bugs")
            else:
                logger.error(f"Unexpected bug data type: {type(list_real_bugs)}")
                return {
                    "success": False,
                    "fixed_count": 0,
                    "failed_count": 0,
                    "error": f"Unexpected bug data type: {type(list_real_bugs)}"
                }
            
<<<<<<< HEAD
            if actual_bugs:
                logger.info(f"DEBUG: First bug type: {type(actual_bugs[0])}")
                logger.info(f"DEBUG: First bug content: {actual_bugs[0]}")
            
            if not self.model:
                return {
                    "success": False,
                    "fixed_count": 0,
                    "failed_count": len(actual_bugs),
                    "error": "Gemini model not available"
                }
            
            if not actual_bugs:
                return {
                    "success": True,
                    "fixed_count": 0,
                    "failed_count": 0,
                    "message": "No bugs to fix"
                }
            
            # Resolve scan directory
            if os.path.isabs(self.scan_directory):
                source_dir = self.scan_directory
            else:
                source_dir = os.path.abspath(os.path.join(os.getcwd(), self.scan_directory))
            
            logger.info(f"Fixing bugs in directory: {source_dir}")
            
            # Group bugs by file
            bugs_by_file = {}
            for i, bug in enumerate(actual_bugs):
                try:
                    logger.info(f"DEBUG: Processing bug {i}: type={type(bug)}")
                    
                    # Handle different bug data formats
                    if isinstance(bug, str):
                        logger.warning(f"Bug {i} is string, skipping: {bug}")
                        continue
                    elif not isinstance(bug, dict):
                        logger.warning(f"Bug {i} is not dict, type: {type(bug)}, skipping")
                        continue
                    
                    # Bearer bugs don't have file_path, need to extract from bug_id or other fields
                    file_path = bug.get('file_path', '')
                    
                    # If no file_path, try to extract from bug_id or other fields
                    if not file_path:
                        bug_id = bug.get('bug_id', '')
                        if 'app.py' in bug_id or 'app_2.py' in bug_id:
                            # Extract filename from bug_id pattern
                            if 'app_2' in bug_id:
                                file_path = 'app_2.py'
                            else:
                                file_path = 'app.py'
=======
            original_dir = os.getcwd()
            # Get FixChain directory for local batch_fix.py
            fixchain_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            batch_fix_dir = os.path.join(fixchain_root, "modules", "fix")
            
            try:
                os.chdir(batch_fix_dir)
                # Create issues file in the project directory
                issues_file_path = os.path.join(source_dir, "list_real_bugs.json")
                try:
                    if os.path.exists(issues_file_path):
                        os.remove(issues_file_path)
                        logger.info(
                            f"Removed existing issues file: {issues_file_path}"
                        )
                    with open(issues_file_path, "w", encoding="utf-8") as f:
                        json.dump(list_real_bugs, f, indent=2, ensure_ascii=False)
                    logger.info(
                        f"Created issues file: {issues_file_path} with {len(list_real_bugs)} bugs"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to create issues file: {str(e)}"
                    )
                    return {
                        "success": False,
                        "fixed_count": 0,
                        "error": f"Failed to create issues file: {str(e)}",
                    }
                
                # Use local batch_fix.py from FixChain
                batch_fix_path = os.path.join(batch_fix_dir, "batch_fix.py")
                fix_cmd = [
                    "python",
                    batch_fix_path,
                    source_dir,
                    "--fix",
                    "--auto",
                    "--issues-file",
                    "list_real_bugs.json",
                ]
                if use_rag:
                    fix_cmd.append("--enable-rag")
                    logger.info("RAG integration enabled for bug fixing")
                logger.info(f"Running command: {' '.join(fix_cmd)}")
                success, output_lines = CLIService.run_command_stream(fix_cmd)
                if success:
                    output_text = "".join(output_lines)
                    try:
                        # Look for the JSON result line that starts with {"success"
                        summary_line = None
                        for line in reversed(output_lines):
                            line = line.strip()
                            if line.startswith('{"success"'):
                                summary_line = line
                                break
                        
                        if summary_line:
                            # Try to find complete JSON by looking for the closing brace
                            if not summary_line.endswith('}'):
                                # JSON might be incomplete, try to reconstruct
                                for i, line in enumerate(reversed(output_lines)):
                                    if line.strip().startswith('{"success"'):
                                        # Collect all lines from this point to find complete JSON
                                        remaining_lines = list(reversed(output_lines))[len(output_lines)-i-1:]
                                        full_json = ''.join(remaining_lines).strip()
                                        # Find the first complete JSON object
                                        brace_count = 0
                                        json_end = -1
                                        for j, char in enumerate(full_json):
                                            if char == '{':
                                                brace_count += 1
                                            elif char == '}':
                                                brace_count -= 1
                                                if brace_count == 0:
                                                    json_end = j + 1
                                                    break
                                        if json_end > 0:
                                            summary_line = full_json[:json_end]
                                        break
                            
                            summary = json.loads(summary_line)
>>>>>>> 4000c21 (move all logic to FĩChain folder)
                        else:
                            # Default to app.py if can't determine
                            file_path = 'app.py'
                        
                        logger.info(f"Extracted file_path '{file_path}' from bug_id: {bug_id}")
                    
                    if not file_path:
                        logger.warning(f"Bug {i} has no file_path: {bug}")
                        continue
                    
                    # Resolve file path
                    if not os.path.isabs(file_path):
                        full_path = os.path.join(source_dir, file_path)
                    else:
                        full_path = file_path
                    
                    full_path = os.path.abspath(full_path)
                    
                    if not os.path.exists(full_path):
                        logger.warning(f"File not found: {full_path}")
                        continue
                    
                    if full_path not in bugs_by_file:
                        bugs_by_file[full_path] = []
                    bugs_by_file[full_path].append(bug)
                    
                except Exception as e:
                    logger.error(f"Error processing bug {i}: {e}, bug data: {bug}")
                    continue
            
            if not bugs_by_file:
                logger.warning("No valid bugs found to process")
                return {
                    "success": False,
                    "fixed_count": 0,
                    "failed_count": len(actual_bugs),
                    "error": "No valid bugs with file paths found"
                }
            
            logger.info(f"DEBUG: Found {len(bugs_by_file)} files to fix")
            
            # Fix each file
            fixed_count = 0
            failed_count = 0
            total_tokens = 0
            total_input_tokens = 0
            total_output_tokens = 0
            
            for file_path, file_bugs in bugs_by_file.items():
                logger.info(f"Fixing {len(file_bugs)} bugs in {file_path}")
                
                result = self._fix_file_with_gemini(file_path, file_bugs)
                
                if result["success"]:
                    # Apply the fix
                    try:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(result["fixed_content"])
                        
                        logger.info(f"Successfully fixed {file_path}")
                        fixed_count += len(file_bugs)
                        
                        # Track token usage
                        total_input_tokens += result.get("input_tokens", 0)
                        total_output_tokens += result.get("output_tokens", 0)
                        
                    except Exception as e:
                        logger.error(f"Failed to write fixed file {file_path}: {e}")
                        failed_count += len(file_bugs)
                else:
                    logger.error(f"Failed to fix {file_path}: {result.get('error', 'Unknown error')}")
                    failed_count += len(file_bugs)
            
            total_tokens = total_input_tokens + total_output_tokens
            
            result = {
                "success": fixed_count > 0,
                "fixed_count": fixed_count,
                "failed_count": failed_count,
                "total_processed": len(actual_bugs),
                "files_processed": len(bugs_by_file),
                "total_tokens": total_tokens,
                "total_input_tokens": total_input_tokens,
                "total_output_tokens": total_output_tokens,
                "message": f"LLMFixer completed: {fixed_count} bugs fixed, {failed_count} failed"
            }
            
            logger.info(f"LLMFixer completed: {fixed_count} fixed, {failed_count} failed")
            return result
            
        except Exception as e:
            logger.error(f"Critical error in LLMFixer.fix_bugs: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "fixed_count": 0,
                "failed_count": 0,
                "error": f"Critical error: {str(e)}"
            }
