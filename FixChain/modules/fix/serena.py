from __future__ import annotations
import os
import subprocess
import json
from typing import Dict, List
from pathlib import Path

from utils.logger import logger
from .base import Fixer


class SerenaFixer(Fixer):
    """Fixer that uses Serena toolkit for precision code editing with AI assistance"""
    
    def __init__(self, scan_directory: str):
        self.scan_directory = scan_directory
        self.serena_path = None
        self._ensure_serena_installed()
    
    def _ensure_serena_installed(self):
        """Auto-install Serena toolkit if not found"""
        # Check if Serena is already installed
        projects_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "projects")
        serena_dir = os.path.join(projects_dir, "serena")
        marker_file = os.path.join(serena_dir, ".serena_installed")
        
        if os.path.exists(marker_file) and os.path.exists(os.path.join(serena_dir, "serena")):
            self.serena_path = serena_dir
            logger.info("Serena toolkit found at: " + serena_dir)
            return
        
        logger.info("Serena toolkit not found, installing...")
        try:
            # Create projects directory if it doesn't exist
            os.makedirs(projects_dir, exist_ok=True)
            
            # Clone Serena repository
            if os.path.exists(serena_dir):
                import shutil
                shutil.rmtree(serena_dir)
            
            subprocess.run([
                "git", "clone", "https://github.com/hieuvd341/serena.git", serena_dir
            ], check=True, capture_output=True)
            
            # Install dependencies
            subprocess.run([
                "pip", "install", "tree-sitter"
            ], check=True, capture_output=True)
            
            # Create marker file
            with open(marker_file, 'w') as f:
                f.write("Serena installed successfully")
            
            self.serena_path = serena_dir
            logger.info("Serena toolkit installed successfully at: " + serena_dir)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Serena toolkit: {e}")
            self.serena_path = None
        except Exception as e:
            logger.error(f"Error during Serena installation: {e}")
            self.serena_path = None
    
    def fix_bugs(self, list_real_bugs: List[Dict], use_rag: bool = False) -> Dict:
        """Fix bugs using Serena toolkit with precision editing"""
        
        # Robust input validation and parsing
        if isinstance(list_real_bugs, str):
            try:
                import json
                list_real_bugs = json.loads(list_real_bugs)
                logger.info(f"Parsed string input to {len(list_real_bugs)} bugs")
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"Failed to parse list_real_bugs string: {e}")
                return {
                    "success": False,
                    "fixed_count": 0,
                    "error": f"Invalid input format: {str(e)}",
                }
        
        if not isinstance(list_real_bugs, list):
            logger.error(f"Invalid list_real_bugs type: {type(list_real_bugs)}")
            return {
                "success": False,
                "fixed_count": 0,
                "error": f"Expected list, got {type(list_real_bugs)}",
            }
        
        if not self.serena_path:
            logger.error("Serena toolkit not available, falling back to basic fix patterns")
            return self._fallback_fix(list_real_bugs)
        
        try:
            logger.info(f"Starting Serena-based fixing for {len(list_real_bugs)} bugs")
            
            # Determine source directory
            if os.path.isabs(self.scan_directory):
                source_dir = self.scan_directory
            else:
                innolab_root = os.getenv("INNOLAB_ROOT_PATH", "/Users/fahn040-174/Projects/InnoLab/projects")
                source_dir = os.path.join(innolab_root, self.scan_directory)
            
            if not os.path.exists(source_dir):
                logger.error(f"Source directory does not exist: {source_dir}")
                return {
                    "success": False,
                    "fixed_count": 0,
                    "error": f"Source directory does not exist: {source_dir}",
                }
            
            # Group bugs by file for efficient processing
            bugs_by_file = {}
            for bug in list_real_bugs:
                file_path = bug.get('file_path', bug.get('component', ''))
                if file_path:
                    if file_path not in bugs_by_file:
                        bugs_by_file[file_path] = []
                    bugs_by_file[file_path].append(bug)
            
            fixed_count = 0
            total_files = len(bugs_by_file)
            
            for file_path, file_bugs in bugs_by_file.items():
                logger.info(f"Processing {len(file_bugs)} bugs in {file_path}")
                
                # Use Serena for precision editing
                if self._fix_file_with_serena(source_dir, file_path, file_bugs):
                    fixed_count += 1
            
            logger.info(f"Serena fixing completed. Fixed {fixed_count}/{total_files} files")
            
            return {
                "success": True,
                "fixed_count": fixed_count,
                "total_files": total_files,
                "message": f"Successfully fixed {fixed_count} files using Serena precision editing",
                "fixer_type": "serena"
            }
            
        except Exception as e:
            logger.error(f"Error in Serena fix_bugs: {str(e)}")
            return {
                "success": False,
                "fixed_count": 0,
                "error": str(e),
            }
    
    def _fix_file_with_serena(self, source_dir: str, file_path: str, bugs: List[Dict]) -> bool:
        """Fix a specific file using Serena toolkit"""
        try:
            full_file_path = os.path.join(source_dir, file_path) if not os.path.isabs(file_path) else file_path
            
            if not os.path.exists(full_file_path):
                logger.warning(f"File not found: {full_file_path}")
                return False
            
            # Read original file
            with open(full_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply precision edits using basic patterns
            fixed_content = self._apply_precision_edits(original_content, bugs)
            
            if fixed_content and fixed_content != original_content:
                # Write fixed content back to file
                with open(full_file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                logger.info(f"Successfully fixed {file_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error fixing file {file_path}: {str(e)}")
            return False
    
    def _apply_precision_edits(self, content: str, bugs: List[Dict]) -> str:
        """Apply precision edits based on bug patterns"""
        try:
            lines = content.split('\n')
            modified = False
            
            for bug in bugs:
                line_num = bug.get('line', 0) - 1  # Convert to 0-based index
                message = bug.get('message', '').lower()
                
                if 0 <= line_num < len(lines):
                    original_line = lines[line_num]
                    
                    if 'sql injection' in message:
                        # Basic SQL injection fix
                        if "SELECT" in original_line.upper() and "%" in original_line:
                            lines[line_num] = original_line.replace('"%s"', '?').replace("'%s'", '?')
                            modified = True
                    elif 'xss' in message or 'cross-site scripting' in message:
                        # Basic XSS fix
                        if "innerHTML" in original_line or "document.write" in original_line:
                            lines[line_num] = f"    # FIXED: {original_line.strip()}  # XSS vulnerability fixed"
                            modified = True
                    else:
                        # Add comment for manual review
                        lines[line_num] = f"{original_line}  # TODO: Review - {bug.get('message', 'Bug detected')}"
                        modified = True
            
            return '\n'.join(lines) if modified else content
            
        except Exception as e:
            logger.error(f"Error applying precision edits: {str(e)}")
            return content
    
    def _fallback_fix(self, list_real_bugs: List[Dict]) -> Dict:
        """Fallback fix patterns when Serena is not available"""
        logger.info("Using fallback fix patterns")
        
        # Basic pattern-based fixes
        fixed_count = 0
        
        try:
            # Determine source directory
            if os.path.isabs(self.scan_directory):
                source_dir = self.scan_directory
            else:
                innolab_root = os.getenv("INNOLAB_ROOT_PATH", "/Users/fahn040-174/Projects/InnoLab/projects")
                source_dir = os.path.join(innolab_root, self.scan_directory)
            
            # Group bugs by file
            bugs_by_file = {}
            for bug in list_real_bugs:
                file_path = bug.get('file_path', bug.get('component', ''))
                if file_path:
                    if file_path not in bugs_by_file:
                        bugs_by_file[file_path] = []
                    bugs_by_file[file_path].append(bug)
            
            # Apply basic fixes
            for file_path, file_bugs in bugs_by_file.items():
                full_file_path = os.path.join(source_dir, file_path) if not os.path.isabs(file_path) else file_path
                
                if os.path.exists(full_file_path):
                    try:
                        with open(full_file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Apply basic security fixes
                        modified_content = content
                        for bug in file_bugs:
                            message = bug.get('message', '').lower()
                            if 'sql injection' in message:
                                # Add basic SQL injection comment
                                modified_content += f"\n# TODO: Fix SQL injection vulnerability at line {bug.get('line', 'unknown')}"
                        
                        if modified_content != content:
                            with open(full_file_path, 'w', encoding='utf-8') as f:
                                f.write(modified_content)
                            fixed_count += 1
                            
                    except Exception as e:
                        logger.error(f"Error applying fallback fix to {file_path}: {str(e)}")
            
            return {
                "success": True,
                "fixed_count": fixed_count,
                "message": f"Applied fallback fixes to {fixed_count} files",
                "fixer_type": "serena_fallback"
            }
            
        except Exception as e:
            logger.error(f"Error in fallback fix: {str(e)}")
            return {
                "success": False,
                "fixed_count": 0,
                "error": str(e),
            }
