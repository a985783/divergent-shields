import subprocess
import os
import sys

def build_pdf():
    work_dir = "paper"
    tex_file = "paper.tex"
    
    print(f"Building PDF from {tex_file} using XeLaTeX...")
    
    # XeLaTeX needs to be run multiple times for citations/references if bibtex is used.
    # paper.tex doesn't seem to use bibtex (references are hardcoded in the file or not shown).
    # Checking paper.tex content: lines 309+ have references manually formatted.
    # So we just need to run xelatex 2-3 times to resolve cross-references (labels).
    
    cmd = ["xelatex", "-interaction=nonstopmode", tex_file]
    
    try:
        # Run 1
        print("Pass 1/2...")
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
        
        # Run 2 (for labels/toc)
        print("Pass 2/2...")
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
        
        print(f"\nSUCCESS: PDF generated at {os.path.join(work_dir, 'paper.pdf')}")
        
    except subprocess.CalledProcessError as e:
        print("\nERROR: Compilation failed.")
        # print first 20 lines of log if available
        log_file = os.path.join(work_dir, "paper.log")
        if os.path.exists(log_file):
            print("--- Log tail ---")
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                print("".join(f.readlines()[-20:]))
        sys.exit(1)

if __name__ == "__main__":
    build_pdf()
