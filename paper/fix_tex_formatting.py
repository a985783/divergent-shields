import re
import os

def fix_tex_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace **text** with \textbf{text}
    # We use a non-greedy match.
    content = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', content)

    # 2. Replace *text* with \textit{text}, but avoid * at start of line (bullets)
    # This is tricky because * is used for multiplication in math or loose asterisks.
    # We'll match *text* where * is not preceded by \ (to avoid matching \* or \textbullet)
    # and not followed by space.
    # However, given the file uses * for bullets, we should handle bullets first or be careful.
    
    # Let's handle list items first.
    # Lines starting with "* " or "\textbullet " should be list items.
    # We can try to wrap them in itemize, but simpler is to ensure they use a consistent bullet char.
    # SSRN/LaTeX standard: \begin{itemize} \item ... \end{itemize}
    # But doing that programmatically without robust parsing is error-prone (nested lists etc).
    # Safe fallback: replace `* ` at line start with `\textbullet\ ` and ensure breaks.
    
    # normalize bullets
    lines = content.split('\n')
    new_lines = []
    in_list = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Detect bullet point
        is_bullet = False
        if stripped.startswith('* '):
            line = line.replace('* ', '\\item ', 1)
            is_bullet = True
        elif stripped.startswith('\\textbullet'):
            # replace \textbullet with \item
            # handle cases like "\textbullet\ **Mechanism**"
            line = re.sub(r'^\s*\\textbullet\s*(\\ )?', r'\\item ', line)
            is_bullet = True
            
        if is_bullet:
            if not in_list:
                new_lines.append('\\begin{itemize}')
                in_list = True
        else:
            if in_list and stripped == '':
                # Empty line ends the list
                new_lines.append('\\end{itemize}')
                in_list = False
            elif in_list and not is_bullet and stripped != '':
                # Non-empty line that isn't a bullet... 
                # Could be continuation of previous item?
                # Or a new paragraph?
                # If it's indented, it's continuation.
                # If it's strictly mostly text, assume continuation?
                # Let's assume blank line is the delimiter for safety.
                pass
        
        new_lines.append(line)
    
    if in_list:
        new_lines.append('\\end{itemize}')
        
    content = '\n'.join(new_lines)

    # Now handle *italic* (if any left that aren't math)
    # We'll skip this to avoid breaking math or other things unless specific patterns found.
    # The abstract uses *Excepción Ibérica*.
    content = re.sub(r'([^\\])\*(.*?)\*', r'\1\\textit{\2}', content)
    
    # Fix [0.2cm] to just be newline or ensure spacing is clean
    # Actually \\[0.2cm] is fine in lists, but maybe redundant if we use itemize.
    # Let's remove \\[0.2cm] if inside itemize (optional) or leave it.
    # Leaving it is safer.
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Fixed formatting in {file_path}")

if __name__ == "__main__":
    fix_tex_file("paper/paper.tex")
