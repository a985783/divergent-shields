#!/usr/bin/env python3
"""
Fix hardcoded paths in Python files
Replace absolute paths with dynamic project root-based paths
"""

import os
import re

def fix_file(file_path):
    """Fix hardcoded paths in a single file"""
    print(f"Fixing {file_path}...")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace hardcoded path with dynamic root calculation
    old_path = "/Users/cuiqingsong/Documents/第三论文尝试"
    
    # Check if file contains the old path
    if old_path not in content:
        print(f"No hardcoded path found in {file_path}")
        return False
    
    # Add project root calculation code at the beginning of imports section
    root_code = '''
# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if __name__ == "__main__" else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
'''
    
    # For scripts in root directory (run_all.py)
    if os.path.basename(file_path) == "run_all.py" or os.path.dirname(file_path) == os.path.abspath('.'):
        root_code = '''
# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.abspath('.')
'''
    
    # For files in scripts/ directory
    if 'scripts' in file_path:
        root_code = '''
# Get project root directory dynamically
import os
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
'''
    
    # Replace hardcoded paths with dynamic paths
    # Data path
    content = content.replace(
        'DATA_PATH = "/Users/cuiqingsong/Documents/第三论文尝试/data/processed/merged_data.csv"',
        'DATA_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "merged_data.csv")'
    )
    
    # Figures directory
    content = content.replace(
        'FIGURES_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/paper/figures"',
        'FIGURES_DIR = os.path.join(PROJECT_ROOT, "paper", "figures")'
    )
    
    # Results directory
    content = content.replace(
        'RESULTS_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/paper/tables"',
        'RESULTS_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")'
    )
    
    # Tables directory (for 01_descriptive.py)
    content = content.replace(
        'TABLES_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/paper/tables"',
        'TABLES_DIR = os.path.join(PROJECT_ROOT, "paper", "tables")'
    )
    
    # Raw data directory (for scripts)
    content = content.replace(
        'RAW_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/data/raw"',
        'RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")'
    )
    
    # Processed directory (for process_data.py)
    content = content.replace(
        'PROCESSED_DIR = "/Users/cuiqingsong/Documents/第三论文尝试/data/processed"',
        'PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")'
    )
    
    # SCM results path (for 10_fiscal_cost_estimation.py)
    content = content.replace(
        'SCM_RESULTS_PATH = "/Users/cuiqingsong/Documents/第三论文尝试/paper/tables/scm_enhanced_ES_HICP_Total.csv"',
        'SCM_RESULTS_PATH = os.path.join(PROJECT_ROOT, "paper", "tables", "scm_enhanced_ES_HICP_Total.csv")'
    )
    
    # LP results path (for 10_fiscal_cost_estimation.py)
    content = content.replace(
        'LP_RESULTS_PATH = "/Users/cuiqingsong/Documents/第三论文尝试/paper/tables/lp_enhanced_PL.csv"',
        'LP_RESULTS_PATH = os.path.join(PROJECT_ROOT, "paper", "tables", "lp_enhanced_PL.csv")'
    )
    
    # Add root calculation code after the initial comments and before other imports
    # Find the first import line
    import_match = re.search(r'^import|^from', content, re.MULTILINE)
    if import_match:
        insert_pos = import_match.start()
        content = content[:insert_pos] + root_code + content[insert_pos:]
    else:
        # If no imports, add at the beginning
        content = root_code + content
    
    # Ensure directories are created (add os.makedirs if not present)
    dir_checks = '''
# Ensure directories exist
os.makedirs(FIGURES_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)
'''
    
    if 'os.makedirs' not in content:
        # Find the end of config section to insert dir checks
        config_end = content.find('def ')
        if config_end != -1:
            content = content[:config_end] + dir_checks + content[config_end:]
    
    # Write the fixed content back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Successfully fixed {file_path}")
    return True

def main():
    project_root = os.path.abspath('.')
    print(f"Project root: {project_root}")
    
    # Files to fix
    files_to_fix = []
    
    # Analysis scripts
    analysis_dir = os.path.join(project_root, 'analysis')
    for filename in os.listdir(analysis_dir):
        if filename.endswith('.py'):
            files_to_fix.append(os.path.join(analysis_dir, filename))
    
    # Scripts
    scripts_dir = os.path.join(project_root, 'scripts')
    for filename in os.listdir(scripts_dir):
        if filename.endswith('.py'):
            files_to_fix.append(os.path.join(scripts_dir, filename))
    
    # Root level files
    if os.path.exists('run_all.py'):
        files_to_fix.append('run_all.py')
    
    # Fix each file
    fixed_files = []
    for file_path in files_to_fix:
        if os.path.isfile(file_path):
            try:
                if fix_file(file_path):
                    fixed_files.append(file_path)
            except Exception as e:
                print(f"Error fixing {file_path}: {e}")
    
    print(f"\nFixed {len(fixed_files)} files")
    for file in fixed_files:
        print(f"  {file}")

if __name__ == "__main__":
    main()
