#!/usr/bin/env python3
"""
One-time Serena Toolkit Installation Script
Clones Serena from GitHub and installs required dependencies
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run shell command with error handling"""
    print(f"Running: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check, 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def install_serena():
    """Install Serena toolkit"""
    
    # Get InnoLab root directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    innolab_root = os.path.dirname(current_dir)
    projects_dir = os.path.join(innolab_root, "projects")
    serena_dir = os.path.join(projects_dir, "serena")
    marker_file = os.path.join(current_dir, ".serena_installed")
    
    print("=== Serena Toolkit Installation ===")
    print(f"InnoLab root: {innolab_root}")
    print(f"Projects directory: {projects_dir}")
    print(f"Serena target: {serena_dir}")
    
    # Check if already installed
    if os.path.exists(marker_file):
        print("✓ Serena already installed (marker file exists)")
        if os.path.exists(serena_dir):
            print(f"✓ Serena directory found: {serena_dir}")
            return True
        else:
            print("⚠ Marker exists but directory missing, reinstalling...")
            os.remove(marker_file)
    
    # Create projects directory if it doesn't exist
    os.makedirs(projects_dir, exist_ok=True)
    
    # Clone Serena repository
    print("\n1. Cloning Serena repository...")
    if os.path.exists(serena_dir):
        print(f"Directory {serena_dir} already exists, removing...")
        import shutil
        shutil.rmtree(serena_dir)
    
    clone_cmd = "git clone https://github.com/hieuvd341/serena.git"
    if not run_command(clone_cmd, cwd=projects_dir):
        print("❌ Failed to clone Serena repository")
        return False
    
    print("✓ Serena repository cloned successfully")
    
    # Install Python dependencies for Serena
    print("\n2. Installing Serena dependencies...")
    
    # Install tree-sitter and language parsers
    deps = [
        "tree-sitter>=0.20.0",
        "tree-sitter-python>=0.20.0", 
        "tree-sitter-javascript>=0.20.0",
        "tree-sitter-typescript>=0.20.0",
        "tree-sitter-java>=0.20.0",
        "tree-sitter-cpp>=0.20.0",
        "tree-sitter-c>=0.20.0"
    ]
    
    for dep in deps:
        if not run_command(f"pip install {dep}"):
            print(f"⚠ Warning: Failed to install {dep}")
    
    # Install additional requirements if requirements.txt exists
    requirements_file = os.path.join(serena_dir, "requirements.txt")
    if os.path.exists(requirements_file):
        print("Installing from requirements.txt...")
        if not run_command(f"pip install -r {requirements_file}"):
            print("⚠ Warning: Failed to install some requirements")
    
    # Create marker file
    print("\n3. Creating installation marker...")
    with open(marker_file, 'w') as f:
        f.write(f"Serena installed at: {serena_dir}\n")
        f.write(f"Installation date: {subprocess.check_output(['date']).decode().strip()}\n")
    
    print("✓ Installation marker created")
    
    # Verify installation
    print("\n4. Verifying installation...")
    if os.path.exists(os.path.join(serena_dir, "README.md")):
        print("✓ Serena installation verified")
        
        print("\n=== Installation Complete ===")
        print(f"Serena toolkit installed at: {serena_dir}")
        print("You can now use SerenaFixer in FixChain")
        print("\nUsage:")
        print("python3 run/run_demo.py --scanners bearer --fixers hybrid --project ../projects/Flask_App --mode cloud")
        
        return True
    else:
        print("❌ Installation verification failed")
        return False

if __name__ == "__main__":
    success = install_serena()
    sys.exit(0 if success else 1)
