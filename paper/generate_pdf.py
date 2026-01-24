import subprocess
import os
import sys

def generate_pdf():
    # Use paper.tex as the source of truth for high-quality formatting
    tex_file = "paper.tex"
    
    # Ensure we are in the correct directory (paper/)
    # If script is run from project root, we might need to adjust or chdir
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming the script is in paper/, we verify
    if os.path.exists(os.path.join(script_dir, tex_file)):
        work_dir = script_dir
    else:
        # Fallback if run from elsewhere and file is local
        work_dir = "."
    
    print(f"Building PDF from {tex_file} using XeLaTeX for SSRN formatting...")
    
    cmd = ["xelatex", "-interaction=nonstopmode", tex_file]
    
    try:
        # Pass 1: Initial compile
        print("Compiling (Pass 1/2)...")
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
        
        # Pass 2: Resolve references and layout
        print("Compiling (Pass 2/2)...")
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
        
        pdf_path = os.path.join(work_dir, "paper.pdf")
        print(f"\nSUCCESS: Formatted PDF generated at {pdf_path}")
        
    except subprocess.CalledProcessError as e:
        print("\nERROR: PDF generation failed.")
        log_file = os.path.join(work_dir, "paper.log")
        if os.path.exists(log_file):
            print("--- Log tail ---")
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    print("".join(f.readlines()[-20:]))
            except:
                print("(Could not read log file)")
        sys.exit(1)

if __name__ == "__main__":
    generate_pdf()
