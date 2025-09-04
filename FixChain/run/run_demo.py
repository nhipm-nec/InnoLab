#!/usr/bin/env python3
"""
Demo script to run ExecutionService with or without RAG
This bypasses MongoDB dependency for testing
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import List, Dict
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.dify_lib import DifyMode
from utils.logger import logger
from modules.scan import registry as scan_registry
from modules.fix import registry as fix_registry
from modules.analysis_service import AnalysisService

try:
    # Check if RAG functionality is available
    # For demo purposes, RAG is available but simplified
    RAG_AVAILABLE = True
except Exception as e:
    logger.warning(f"Error checking RAG availability: {e}")
    RAG_AVAILABLE = False

# Load environment variables from root directory
root_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
load_dotenv(root_env_path)

class ExecutionServiceNoMongo:
    """ExecutionService without MongoDB dependency"""

    def __init__(self, scan_directory=None, scanners=None, fixers=None):
        # Load environment variables
        self.dify_cloud_api_key = os.getenv('DIFY_CLOUD_API_KEY')
        self.dify_local_api_key = os.getenv('DIFY_LOCAL_API_KEY')
        self.sonar_host = os.getenv('SONAR_HOST', 'http://localhost:9000')
        self.sonar_token = os.getenv('SONAR_TOKEN')

        # Configuration from environment variables
        self.max_iterations = int(os.getenv('MAX_ITERATIONS', '5'))
        self.project_key = os.getenv('PROJECT_KEY')
        self.source_code_path = os.getenv('SOURCE_CODE_PATH')
        # Priority: parameter > environment variable > default
        self.scan_directory = scan_directory or os.getenv('SCAN_DIRECTORY', 'projects/demo_project')

        # Scanner configuration - allow comma separated string or list
        if isinstance(scanners, str):
            self.scan_modes = [m.strip().lower() for m in scanners.split(',') if m.strip()]
        elif scanners:
            self.scan_modes = [m.lower() for m in scanners]
        else:
            self.scan_modes = ['sonar']

        # Fixer configuration - allow comma separated string or list
        if isinstance(fixers, str):
            self.fix_modes = [m.strip().lower() for m in fixers.split(',') if m.strip()]
        elif fixers:
            self.fix_modes = [m.lower() for m in fixers]
        else:
            self.fix_modes = ['hybrid']  # Default to hybrid fixer

        # Execution tracking
        self.execution_count = 0
        self.current_source_file = 'code.py'  # Track current source file to scan

        # Log configuration
        logger.info(f"ExecutionServiceNoMongo initialized with:")
        logger.info(f"  Max iterations: {self.max_iterations}")
        logger.info(f"  Project key: {self.project_key}")
        logger.info(f"  Source code path: {self.source_code_path}")
        logger.info(f"  Scan directory: {self.scan_directory}")
        logger.info(f"  Scan mode: {self.scan_modes}")
        logger.info(f"  Fix mode: {self.fix_modes}")
        logger.info(f"  RAG available: {RAG_AVAILABLE}")

        # Initialize services
        self.analysis_service = AnalysisService(
            self.dify_cloud_api_key, self.dify_local_api_key
        )
        self.scanners: List = []
        # Arguments for built-in scanners
        scanner_args = {
            'bearer': {
                'project_key': self.project_key,
                'scan_directory': self.scan_directory,
            },
            'sonar': {
                'project_key': self.project_key,
                'scan_directory': self.scan_directory,
                'sonar_token': self.sonar_token,
            },
            'sonarq': {
                'project_key': self.project_key,
                'scan_directory': self.scan_directory,
                'sonar_token': self.sonar_token,
            },
        }
        
        for mode in self.scan_modes:
            registry_name = 'sonarq' if mode == 'sonar' else mode
            args = scanner_args.get(mode) or scanner_args.get(registry_name, {})
            self.scanners.append(scan_registry.create(registry_name, **args))

        self.fixers: List = []
        for mode in self.fix_modes:
            self.fixers.append(fix_registry.create(mode, self.scan_directory))
    
    def insert_rag_default(self) -> bool:
        """Insert default RAG data for bug fixing"""
        logger.info("Inserting default RAG data...")
        try:
            # Get dataset path from environment
            dataset_path = os.getenv('RAG_DATASET_PATH')
            if not dataset_path:
                logger.error("RAG_DATASET_PATH must be set in environment")
                return False
            
            # Check if dataset file exists
            if not os.path.exists(dataset_path):
                logger.error(f"Dataset file not found: {dataset_path}")
                return False
            
            # For demo without MongoDB, we'll just validate the dataset file
            # In full implementation with MongoDB, use this approach:
            # from modules.execution import ExecutionService
            # execution_service = ExecutionService()
            # return execution_service.insert_dataset_to_rag(dataset_path)
            
            # For now, just return True since we're not using MongoDB
            logger.info(f"Dataset file validated: {dataset_path}")
            return True
            
            
        except Exception as e:
            logger.error(f"Error inserting RAG data: {str(e)}")
            return False

    
    def read_source_code(self, file_path: str = None) -> str:
        """Read source code from scan directory"""
        try:
            if file_path is None:
                # Read all Python files in scan directory
                source_files = []
                
                # Determine the correct scan path similar to Bearer scanner logic
                innolab_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                sonar_dir = os.path.join(innolab_root, "SonarQ")
                
                if self.scan_directory and self.scan_directory != "projects/demo_project":
                    if self.scan_directory == "SonarQ":
                        # Special case for SonarQ - use projects/SonarQ
                        scan_path = os.path.join(innolab_root, "projects", "SonarQ")
                    elif os.path.isabs(self.scan_directory):
                        scan_path = self.scan_directory
                    else:
                        # Try relative to innolab_root first
                        scan_path = os.path.abspath(os.path.join(innolab_root, self.scan_directory))
                        if not os.path.exists(scan_path):
                            # Then try relative to sonar_dir
                            scan_path = os.path.abspath(os.path.join(sonar_dir, self.scan_directory))
                            if not os.path.exists(scan_path):
                                # Finally try as direct path under innolab_root
                                scan_path = os.path.abspath(os.path.join(innolab_root, os.path.basename(self.scan_directory)))
                else:
                    # Default to demo_project directory
                    scan_path = os.path.join(innolab_root, "projects", "demo_project")
                    if not os.path.exists(scan_path):
                        # Fallback to source_bug directory if demo_project doesn't exist
                        scan_path = os.path.join(sonar_dir, "source_bug")
                
                if not os.path.exists(scan_path):
                    logger.error(f"Scan directory not found: {scan_path}")
                    return ""
                
                logger.info(f"Reading source code from directory: {scan_path}")
                
                for root, dirs, files in os.walk(scan_path):
                    for file in files:
                        if file.endswith(('.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.h')):
                            file_full_path = os.path.join(root, file)
                            try:
                                with open(file_full_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                                    relative_path = os.path.relpath(file_full_path, scan_path)
                                    source_files.append(f"// File: {relative_path}\n{content}\n\n")
                            except Exception as e:
                                logger.warning(f"Could not read file {file_full_path}: {e}")
                                continue
                
                return ''.join(source_files)
            else:
                # Read specific file
                full_path = os.path.join(self.scan_directory, file_path)
                with open(full_path, 'r', encoding='utf-8') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error reading source code: {str(e)}")
            return ""

    def log_execution_result(self, result: Dict):
        """Log execution result (simplified version without MongoDB)"""
        logger.info("=== EXECUTION RESULT ===")
        logger.info(f"Mode: {result.get('mode')}")
        logger.info(f"Project: {result.get('project_key')}")
        logger.info(f"Total bugs fixed: {result.get('total_bugs_fixed')}")
        logger.info(f"Total iterations: {len(result.get('iterations', []))}")
        logger.info(f"Start time: {result.get('start_time')}")
        logger.info(f"End time: {result.get('end_time')}")
        
        for i, iteration in enumerate(result.get('iterations', []), 1):
            logger.info(f"Iteration {i}: {iteration.get('bugs_found')} bugs found, {iteration.get('fix_result', {}).get('fixed_count', 0)} fixed")
    
    def run_execution(self, use_rag: bool = False, mode: DifyMode = DifyMode.CLOUD) -> Dict:
        """Run execution with proper scan → fix → rescan loop"""
        start_time = datetime.now()
        logger.info(f"Starting execution {'with' if use_rag else 'without'} RAG (mode: {mode})")
        
        iterations = []
        total_bugs_fixed = 0
        
        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"\n=== ITERATION {iteration}/{self.max_iterations} ===")

            # Scan for bugs using all configured scanners
            bugs = []
            for scan_mode, scanner in zip(self.scan_modes, self.scanners):
                scanner_bugs = scanner.scan()
                logger.info(f"{scan_mode.upper()} scanner found {len(scanner_bugs)} bugs")
                bugs.extend(scanner_bugs)

            # Analyze bug counts
            bug_counts = self.analysis_service.count_bug_types(bugs)
            bugs_type_bug = bug_counts.get('BUG', 0)
            bugs_type_code_smell = bug_counts.get('CODE_SMELL', 0)
            bugs_found = bug_counts.get('TOTAL', 0)

            logger.info(
                f"Iteration {iteration}: Found {bugs_found} open bugs ({bugs_type_bug} BUG, {bugs_type_code_smell} CODE_SMELL) across scanners: {', '.join(self.scan_modes).upper()}"
            )

            # Create iteration result
            iteration_result = {
                "iteration": iteration,
                "bugs_found": bugs_found,
                "bugs_type_bug": bugs_type_bug,
                "bugs_type_code_smell": bugs_type_code_smell,
                "timestamp": datetime.now().isoformat()
            }
            
            # Check if no bugs found - early exit
            if bugs_found == 0:
                logger.info("No bugs found - execution completed successfully")
                iteration_result["fix_result"] = {
                    "success": True,
                    "fixed_count": 0,
                    "failed_count": 0,
                    "bugs_remain": 0,
                    "bugs_type_bug": 0,
                    "bugs_type_code_smell": 0,
                    "message": "No bugs found"
                }
                iterations.append(iteration_result)
                break
            
            # Read source code for analysis
            source_code = self.read_source_code()
            
            # Analysis bugs with Dify
            analysis_result = self.analysis_service.analyze_bugs_with_dify(
                bugs, use_rag=use_rag, mode=mode, source_code=source_code
            )
            list_real_bugs = analysis_result.get("list_bugs")

            # Parse list_real_bugs if it's a string
            if isinstance(list_real_bugs, str):
                try:
                    list_real_bugs = json.loads(list_real_bugs)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.error(f"Failed to parse list_real_bugs as JSON: {str(e)}")
                    list_real_bugs = []
            elif list_real_bugs is None:
                list_real_bugs = []

            # Save analysis result for reporting
            iteration_result["analysis_result"] = analysis_result

            # If no real bugs to fix after analysis, continue to next iteration
            if not list_real_bugs or len(list_real_bugs) == 0:
                logger.info("No real bugs to fix after analysis - continuing to next iteration")
                iteration_result["fix_result"] = {
                    "success": True,
                    "fixed_count": 0,
                    "failed_count": 0,
                    "bugs_remain": bugs_found,
                    "bugs_type_bug": bugs_type_bug,
                    "bugs_type_code_smell": bugs_type_code_smell,
                    "message": "No real bugs identified for fixing after analysis"
                }
                iterations.append(iteration_result)
                continue

            # Fix bugs using configured fixers
            fix_results = []
            iteration_fixed_count = 0
            
            for fixer in self.fixers:
                logger.info(f"Applying fixer: {fixer.__class__.__name__}")
                fix_result_raw = fixer.fix_bugs(list_real_bugs, use_rag=use_rag)

                # Ensure fix result is parsed from final JSON line if returned as text
                if isinstance(fix_result_raw, str):
                    try:
                        fix_result = json.loads(fix_result_raw.splitlines()[-1])
                    except json.JSONDecodeError:
                        logger.error("Failed to parse fix result JSON")
                        fix_result = {"success": False, "fixed_count": 0, "error": "Invalid JSON output"}
                else:
                    fix_result = fix_result_raw

                fix_results.append(fix_result)

                # Update counters based on fix result
                if fix_result.get("success", False):
                    fixed_count = fix_result.get("fixed_count", 0)
                    iteration_fixed_count += fixed_count
                    total_bugs_fixed += fixed_count
                    logger.info(f"Fixer {fixer.__class__.__name__} fixed {fixed_count} bugs")
                else:
                    logger.error(f"Fix failed: {fix_result.get('error', 'Unknown error')}")

            # Store fix results in iteration (keep last result for compatibility)
            iteration_result["fix_results"] = fix_results
            if fix_results:
                iteration_result["fix_result"] = fix_results[-1]

            # Re-scan to verify fixes
            rescan_bugs = []
            for scanner in self.scanners:
                rescan_bugs.extend(scanner.scan())
            rescan_bug_counts = self.analysis_service.count_bug_types(rescan_bugs)
            iteration_result["rescan_bugs_found"] = rescan_bug_counts.get('TOTAL', 0)
            iteration_result["rescan_bugs_type_bug"] = rescan_bug_counts.get('BUG', 0)
            iteration_result["rescan_bugs_type_code_smell"] = rescan_bug_counts.get('CODE_SMELL', 0)
            
            bugs_reduced = bugs_found - len(rescan_bugs)
            logger.info(f"Rescan found {len(rescan_bugs)} open bugs ({rescan_bug_counts['BUG']} BUG, {rescan_bug_counts['CODE_SMELL']} CODE_SMELL)")
            logger.info(f"Bugs reduced: {bugs_reduced} (from {bugs_found} to {len(rescan_bugs)})")

            iterations.append(iteration_result)

            # Stop if no bugs remain after rescan
            if len(rescan_bugs) == 0:
                logger.info(f"Iteration {iteration} completed: all bugs resolved after rescan")
                break

            # Stop if no progress was made (no bugs fixed)
            if iteration_fixed_count == 0:
                logger.info(f"Iteration {iteration}: No bugs were fixed, stopping to avoid infinite loop")
                # Don't break immediately, allow one more iteration to see if different bugs are found

            # Log iteration result
            logger.info(f"Iteration {iteration} completed: {len(rescan_bugs)} bugs remain after rescan")
        
        end_time = datetime.now()
        
        # Prepare final result
        mode_str = mode.value if hasattr(mode, 'value') else str(mode)
        if use_rag:
            mode_str = f"{mode_str}_with_rag"
        
        result = {
            "mode": mode_str,
            "project_key": self.project_key,
            "total_bugs_fixed": total_bugs_fixed,
            "iterations": iterations,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds()
        }
        
        if use_rag:
            result["rag_enabled"] = True
        
        # Log final result
        self.log_execution_result(result)
        
        return result

def main():
    """Main function to run the demo"""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='ExecutionService Demo - Bug fixing with Dify AI')
    parser.add_argument('--insert_rag', action='store_true',
                       help='Run with RAG support (insert default RAG data and use RAG for bug fixing)')
    parser.add_argument('--mode', choices=['cloud', 'local'], default='cloud',
                       help='Dify mode to use (default: cloud)')
    parser.add_argument('--project', type=str, default='projects/demo_project',
                       help='Path to project directory to scan (default: projects/demo_project)')
    parser.add_argument('--scanners', type=str, default='sonar',
                       help='Comma-separated scanners to use for bug detection (default: sonar)')
    parser.add_argument('--fixers', type=str, default='hybrid',
                       help='Comma-separated fixers to apply (default: hybrid)')
    
    args = parser.parse_args()
    
    print("🚀 Running ExecutionService Demo")
    print("This demo runs the bug fixing process without MongoDB dependency")
    print(f"RAG functionality: {'Available' if RAG_AVAILABLE else 'Not Available'}")
    print(f"Scanners: {args.scanners}")
    print(f"Fixers: {args.fixers}")
    print(f"Project directory: {args.project}")
    print("-" * 60)
    
    # Determine execution mode based on command line arguments
    if args.insert_rag:
        if not RAG_AVAILABLE:
            print("\n⚠️  Warning: --insert_rag specified but RAG functionality is not available")
            print("Falling back to execution without RAG")
            use_rag = False
        else:
            print("\n🔍 Running with RAG support (--insert_rag specified)")
            use_rag = True
    else:
        # Default to running without RAG (no interactive mode)
        print("\nRunning with default mode: without RAG")
        use_rag = False
    
    try:
        # Initialize service with selected project and modules
        service = ExecutionServiceNoMongo(
            scan_directory=args.project,
            scanners=args.scanners,
            fixers=args.fixers,
        )
        
        # Determine Dify mode
        dify_mode = DifyMode.CLOUD if args.mode == 'cloud' else DifyMode.LOCAL
        
        # Run execution based on user choice
        if use_rag:
            print(f"\nRunning with RAG support (mode: {args.mode}, scanners: {args.scanners})...")
        else:
            print(f"\nRunning without RAG (mode: {args.mode}, scanners: {args.scanners})...")
        
        result = service.run_execution(use_rag=use_rag, mode=dify_mode)
        
        # Display results
        print("\n" + "="*50)
        print("📊 EXECUTION RESULTS")
        print("="*50)
        print(f"Mode: {result.get('mode')}")
        print(f"Project: {result.get('project_key')}")
        print(f"Total bugs fixed: {result.get('total_bugs_fixed')}")
        print(f"Total iterations: {len(result.get('iterations', []))}")
        print(f"Duration: {result.get('duration_seconds'):.2f} seconds")
        
        for i, iteration in enumerate(result.get('iterations', []), 1):
            
            print(f"\n  Iteration {i}:")
            print(f"    🐞 Bugs found: {iteration.get('bugs_found')}")
            print(f"        + Type Bug: {iteration.get('bugs_type_bug')}")
            bugs_ignored = iteration.get('bugs_type_code_smell', 0)
            print(f"        + Type Code-smell: {bugs_ignored}")
   
            bugs_to_fix = iteration.get('analysis_result', {}).get('bugs_to_fix', 0)
            print(f"    🔧 Bugs to fix: {bugs_to_fix}")
            rescan_found = iteration.get('rescan_bugs_found', 0)
            rescan_bug_type = iteration.get('rescan_bugs_type_bug', 0)
            rescan_code_smell = iteration.get('rescan_bugs_type_code_smell', 0)
            print(f"    🔄 Bugs after rescan: {rescan_found} ({rescan_bug_type} BUG, {rescan_code_smell} CODE_SMELL)")
            print(f"    🚫 Bugs Ignored: {bugs_ignored}")
       

            # print(f"    Bugs remain: {iteration.get('fix_result', {}).get('bugs_remain', 0)}")
            fix_results = iteration.get('fix_results', [])
            fix_result = fix_results[-1] if fix_results else iteration.get('fix_result', {})
            
            # Hiển thị thông tin token usage nếu có
            if fix_result.get('total_tokens', 0) > 0:
                print(f"    💰 Token Usage:")
                print(f"        + Input tokens: {fix_result.get('total_input_tokens', 0):,}")
                print(f"        + Output tokens: {fix_result.get('total_output_tokens', 0):,}")
                print(f"        + Total tokens: {fix_result.get('total_tokens', 0):,}")
                print(f"        + Average similarity: {fix_result.get('average_similarity', 0):.3f}")
                print(f"        + Threshold met: {fix_result.get('threshold_met_count', 0)}")
            
            # print(f"    Bugs fixed: {fix_result.get('fixed_count', 0)}")
            # print(f"    Bugs failed: {fix_result.get('failed_count', 0)}")
            if fix_result.get('message'):
                print(f"    Message: {fix_result.get('message')}")
        
        print(f"\n⏰ Start time: {result.get('start_time')}")
        print(f"⏰ End time: {result.get('end_time')}")
        print("\n✅ Demo completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error during execution: {str(e)}")
        logger.error(f"Demo failed: {str(e)}")

if __name__ == "__main__":
    main()
