import subprocess
import os
import sys

def generate_pdf():
    tex_file = "paper_cn.tex"
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.exists(os.path.join(script_dir, tex_file)):
        work_dir = script_dir
    else:
        work_dir = "."
    
    print(f"Building PDF from {tex_file} using XeLaTeX for Chinese support...")
    
    cmd = ["xelatex", "-interaction=nonstopmode", tex_file]
    
    try:
        print("Compiling (Pass 1/2)...")
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
        
        print("Compiling (Pass 2/2)...")
        subprocess.run(cmd, cwd=work_dir, check=True, capture_output=True)
        
        pdf_path = os.path.join(work_dir, "paper_cn.pdf")
        if os.path.exists(pdf_path):
            print(f"\nSUCCESS: Chinese PDF generated at {pdf_path}")
        else:
            print(f"\nERROR: PDF file not found at {pdf_path}")
            sys.exit(1)
        
    except subprocess.CalledProcessError as e:
        print("\nERROR: PDF generation failed.")
        log_file = os.path.join(work_dir, "paper_cn.log")
        if os.path.exists(log_file):
            print("--- Log tail ---")
            try:
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    print("".join(f.readlines()[-30:]))
            except:
                print("(Could not read log file)")
        else:
            print("STDERR:")
            print(e.stderr.decode('utf-8', errors='replace'))
        sys.exit(1)

if __name__ == "__main__":
    generate_pdf()
