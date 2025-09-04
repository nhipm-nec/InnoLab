import os
import json
import subprocess
from typing import Dict, List
from datetime import datetime

from .base import Fixer
from .serena import SerenaFixer
from .llm import LLMFixer
from utils.logger import logger

class HybridFixer(Fixer):
    """Hybrid fixer that combines Serena precision editing with LLM batch fixing"""
    
    def __init__(self, scan_directory: str):
        super().__init__(scan_directory)
        
        # Initialize both fixers
        self.serena_fixer = SerenaFixer(scan_directory)
        self.llm_fixer = LLMFixer(scan_directory)
        
        # Git integration for auto-commits
        self.git_enabled = self._check_git_repository()
        
    def _check_git_repository(self) -> bool:
        """Check if the scan directory is a git repository"""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', '--git-dir'], 
                cwd=self.scan_directory,
                capture_output=True, 
                text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _create_git_commit(self, fixed_bugs: List[Dict], commit_message: str = None):
        """Create git commit with AI-generated message"""
        if not self.git_enabled:
            logger.info("Git not available, skipping auto-commit")
            return
        
        try:
            # Stage all changes
            subprocess.run(['git', 'add', '.'], cwd=self.scan_directory, check=True)
            
            # Generate commit message if not provided
            if not commit_message:
                commit_message = self._generate_commit_message(fixed_bugs)
            
            # Create commit
            subprocess.run([
                'git', 'commit', '-m', commit_message
            ], cwd=self.scan_directory, check=True)
            
            logger.info(f"Created git commit: {commit_message}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create git commit: {e}")
    
    def _generate_commit_message(self, fixed_bugs: List[Dict]) -> str:
        """Generate AI-powered commit message"""
        try:
            if not fixed_bugs:
                return "fix: automated bug fixes"
            
            # Use Serena's Gemini model to generate commit message
            bug_summary = []
            for bug in fixed_bugs[:5]:  # Limit to first 5 bugs
                bug_type = bug.get('type', 'unknown')
                file_path = bug.get('file_path', 'unknown')
                bug_summary.append(f"- {bug_type} in {file_path}")
            
            prompt = f"""
            Generate a concise git commit message for the following bug fixes:
            
            {chr(10).join(bug_summary)}
            
            Follow conventional commit format (fix:, feat:, refactor:, etc.)
            Keep it under 72 characters.
            Be specific about what was fixed.
            """
            
            response = self.serena_fixer.model.generate_content(prompt)
            commit_message = response.text.strip()
            
            # Ensure it's a single line and reasonable length
            commit_message = commit_message.split('\n')[0][:72]
            
            return commit_message
            
        except Exception as e:
            logger.error(f"Failed to generate commit message: {e}")
            return f"fix: automated bug fixes ({len(fixed_bugs)} issues)"
    
    def fix_bugs(self, list_real_bugs: List[Dict], use_rag: bool = False) -> Dict:
<<<<<<< HEAD
        """Fix bugs using hybrid approach: Serena for simple fixes, LLM for complex ones"""
        
        logger.info(f"HybridFixer: Starting to fix {len(list_real_bugs)} bugs")
=======
        """Fix bugs using hybrid approach: Serena first, then LLM for remaining bugs"""
        
        # Robust input validation and parsing
        if isinstance(list_real_bugs, str):
            try:
                import json
                list_real_bugs = json.loads(list_real_bugs)
                logger.info(f"HybridFixer: Parsed string input to {len(list_real_bugs)} bugs")
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"HybridFixer: Failed to parse list_real_bugs string: {e}")
                return {
                    "success": False,
                    "fixed_count": 0,
                    "error": f"Invalid input format: {str(e)}",
                    "fixer_type": "hybrid"
                }
        
        if not isinstance(list_real_bugs, list):
            logger.error(f"HybridFixer: Invalid list_real_bugs type: {type(list_real_bugs)}")
            return {
                "success": False,
                "fixed_count": 0,
                "error": f"Expected list, got {type(list_real_bugs)}",
                "fixer_type": "hybrid"
            }
        
        try:
            logger.info(f"Starting hybrid fixing for {len(list_real_bugs)} bugs")
        except Exception as e:
            logger.error(f"HybridFixer: Failed to log input length: {e}")
            return {
                "success": False,
                "fixed_count": 0,
                "error": f"Failed to log input length: {str(e)}",
                "fixer_type": "hybrid"
            }
>>>>>>> 4000c21 (move all logic to FĩChain folder)
        
        if not list_real_bugs:
            return {
                "success": True,
                "fixed_count": 0,
                "failed_count": 0,
                "message": "No bugs to fix"
            }
        
        start_time = datetime.now()
        
        # First, try Serena for precision fixes
        logger.info("Phase 1: Attempting Serena precision fixes...")
        serena_result = self.serena_fixer.fix_bugs(list_real_bugs, use_rag)
        
        serena_fixed = serena_result.get('fixed_count', 0)
        serena_failed = serena_result.get('failed_count', 0)
        
        # For bugs that Serena couldn't fix, try LLM approach
        remaining_bugs = []
        if serena_failed > 0:
            # In a real implementation, we'd track which specific bugs failed
            # For now, if Serena fixed some but not all, send all bugs to LLM for comprehensive fixing
            if serena_fixed == 0:
                # Serena fixed nothing, send all bugs to LLM
                remaining_bugs = list_real_bugs
            else:
                # Serena fixed some bugs, but we still send all to LLM for comprehensive coverage
                # LLM will skip already-fixed issues or apply additional fixes
                remaining_bugs = list_real_bugs
        
        llm_fixed = 0
        llm_failed = 0
        llm_result = {}
        
        if remaining_bugs:
            logger.info(f"Phase 2: Attempting LLM fixes for comprehensive coverage...")
            llm_result = self.llm_fixer.fix_bugs(remaining_bugs, use_rag)
            llm_fixed = llm_result.get('fixed_count', 0)
            llm_failed = llm_result.get('failed_count', 0)
        
        # Combine results - avoid double counting
        # Since both fixers work on the same bugs, take the maximum fixes achieved
        total_fixed = max(serena_fixed, llm_fixed, serena_fixed + llm_fixed // 2)
        total_failed = max(0, len(list_real_bugs) - total_fixed)
        
        # Create git commit if fixes were applied - COMMENTED OUT
        # if total_fixed > 0:
        #     fixed_bugs_info = [
        #         {
        #             'type': 'security_issue',
        #             'file_path': 'multiple_files',
        #             'method': 'serena' if i < serena_fixed else 'llm'
        #         }
        #         for i in range(total_fixed)
        #     ]
        #     self._create_git_commit(fixed_bugs_info)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Prepare comprehensive result
        result = {
            "success": total_fixed > 0,
            "fixed_count": total_fixed,
            "failed_count": total_failed,
            "total_processed": len(list_real_bugs),
            "serena_fixes": serena_fixed,
            "llm_fixes": llm_fixed,
            "duration_seconds": duration,
            "message": f"Hybrid fixing completed: {serena_fixed} Serena fixes, {llm_fixed} LLM fixes",
            "serena_result": serena_result,
            "llm_result": llm_result
        }
        
        # Include token usage from LLM if available
        if llm_result.get('total_tokens'):
            result.update({
                'total_tokens': llm_result.get('total_tokens', 0),
                'total_input_tokens': llm_result.get('total_input_tokens', 0),
                'total_output_tokens': llm_result.get('total_output_tokens', 0),
                'average_similarity': llm_result.get('average_similarity', 0),
                'threshold_met_count': llm_result.get('threshold_met_count', 0)
            })
        
        logger.info(f"HybridFixer completed: {total_fixed} total fixes ({serena_fixed} Serena + {llm_fixed} LLM)")
        return result
