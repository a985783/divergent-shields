#!/usr/bin/env python3
"""
Master Run Script for Energy Crisis Policy Evaluation
Reproduces all results from data processing to robustness checks

Usage:
    python run_all.py          # Run all analyses
    python run_all.py --fast   # Run only main analyses (skip robustness)
    python run_all.py --step   # Run step-by-step with prompts
"""

import subprocess
import sys
import os
import argparse
from datetime import datetime

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print formatted header"""
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")

def print_success(message):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_warning(message):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def print_error(message):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def run_script(script_path, description, timeout=300):
    """Run a Python script and handle errors"""
    print(f"Running: {description}")
    print(f"Script: {script_path}")
    
    if not os.path.exists(script_path):
        print_error(f"Script not found: {script_path}")
        return False
    
    try:
        # Run script and capture output
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            print_success(f"Completed: {description}")
            
            # Print key output lines
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                key_lines = [line for line in lines if any(keyword in line.lower() for keyword in ['completed', 'saved', 'results', 'summary'])]
                if key_lines:
                    for line in key_lines[-3:]:  # Last 3 key lines
                        print(f"  {line}")
            
            return True
        else:
            print_error(f"Failed: {description}")
            if result.stderr:
                error_lines = result.stderr.strip().split('\n')[-5:]  # Last 5 error lines
                for line in error_lines:
                    print(f"  {line}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"Timeout: {description} (>{timeout}s)")
        return False
    except Exception as e:
        print_error(f"Error: {description} - {str(e)}")
        return False

def check_data_files():
    """Check if required data files exist"""
    print_header("CHECKING DATA FILES")
    
    required_files = [
        "data/processed/merged_data.csv",
        "data/raw/prc_hicp_midx.tsv.gz"
    ]
    
    all_exist = True
    for file_path in required_files:
        if os.path.exists(file_path):
            print_success(f"Found: {file_path}")
        else:
            print_error(f"Missing: {file_path}")
            all_exist = False
    
    if not all_exist:
        print_warning("Some data files are missing. You may need to run data fetching scripts first.")
    
    return all_exist

def main():
    parser = argparse.ArgumentParser(description='Run all analyses for energy crisis policy evaluation')
    parser.add_argument('--fast', action='store_true', help='Skip robustness checks for faster execution')
    parser.add_argument('--step', action='store_true', help='Run step-by-step with user confirmation')
    args = parser.parse_args()
    
    # Record start time
    start_time = datetime.now()
    
    print_header("ENERGY CRISIS POLICY EVALUATION - FULL ANALYSIS")
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version.split()[0]}")
    print(f"Working directory: {os.getcwd()}")
    
    # Check data files
    if not check_data_files():
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)
    
    if args.step:
        input("\nPress Enter to start analysis...")
    
    # Analysis pipeline
    scripts = [
        {
            'path': 'analysis/01_descriptive.py',
            'desc': '1. Descriptive Analysis',
            'required': True
        },
        {
            'path': 'analysis/02_local_projections_enhanced.py',
            'desc': '2. Local Projections (Enhanced)',
            'required': True
        },
        {
            'path': 'analysis/03_synthetic_control_spain_enhanced.py',
            'desc': '3. Synthetic Control Method (Enhanced)',
            'required': True
        },
        {
            'path': 'analysis/04_scm_placebo_tests.py',
            'desc': '4. Placebo Tests',
            'required': True
        },
        {
            'path': 'analysis/10_fiscal_cost_estimation.py',
            'desc': '5. Fiscal Cost Estimation',
            'required': True
        }
    ]
    
    # Add optional robustness checks
    if not args.fast:
        scripts.append({
            'path': 'analysis/05_robustness_checks.py',
            'desc': '5. Robustness Checks (Donor Pools, Time Periods)',
            'required': False
        })
    
    # Run scripts
    results = []
    for i, script in enumerate(scripts, 1):
        print_header(f"STEP {i}: {script['desc']}")
        
        if args.step and i > 1:
            input("\nPress Enter to continue...")
        
        success = run_script(script['path'], script['desc'])
        results.append({
            'step': i,
            'script': script['path'],
            'description': script['desc'],
            'success': success,
            'required': script['required']
        })
        
        # Stop on error if required script
        if not success and script['required']:
            print_error("Required script failed. Stopping pipeline.")
            break
    
    # Summary
    print_header("ANALYSIS PIPELINE SUMMARY")
    
    successful = sum(1 for r in results if r['success'])
    total = len(results)
    required_success = sum(1 for r in results if r['success'] and r['required'])
    required_total = sum(1 for r in results if r['required'])
    
    print(f"Total scripts: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {total - successful}")
    print(f"Required scripts: {required_success}/{required_total}")
    
    # Print detailed results
    print(f"\n{Colors.BOLD}Detailed Results:{Colors.ENDC}")
    for r in results:
        status = f"{Colors.OKGREEN}✓ SUCCESS{Colors.ENDC}" if r['success'] else f"{Colors.FAIL}✗ FAILED{Colors.ENDC}"
        req = "[REQ]" if r['required'] else "[OPT]"
        print(f"  {r['step']}. {r['description']} {req}: {status}")
    
    # Check outputs
    print(f"\n{Colors.BOLD}Generated Outputs:{Colors.ENDC}")
    
    output_dirs = ['paper/tables', 'paper/figures']
    for dir_path in output_dirs:
        if os.path.exists(dir_path):
            files = os.listdir(dir_path)
            print(f"  {dir_path}/: {len(files)} files")
        else:
            print_error(f"  {dir_path}/: Directory not found")
    
    # Timing
    end_time = datetime.now()
    duration = end_time - start_time
    
    print(f"\n{Colors.BOLD}Timing:{Colors.ENDC}")
    print(f"  Start: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  End: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Duration: {duration}")
    
    # Final status
    if required_success == required_total:
        print_success("\n🎉 All required analyses completed successfully!")
        print("\nNext steps:")
        print("  1. Review generated tables in paper/tables/")
        print("  2. Review generated figures in paper/figures/")
        print("  3. Update paper.md with new results")
        print("  4. Prepare response to reviewers")
        sys.exit(0)
    else:
        print_error("\n❌ Some required analyses failed.")
        print("\nTroubleshooting:")
        print("  - Check error messages above")
        print("  - Verify data files exist")
        print("  - Check Python dependencies: pip install -r requirements.txt")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        sys.exit(1)
