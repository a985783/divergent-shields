import markdown
import os
import subprocess
import re

def generate_pdf():
    input_file = "paper/paper.md"
    html_file = "paper/paper.html"
    output_file = "paper/paper.pdf"
    
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
        
    # Pre-process image paths
    # Markdown images: ![Alt](path)
    # Correct path for HTML context relative to paper/ directory or absolute
    # paper.md has paths like /paper/figures/... assuming root is project root.
    # We need to make them absolute for cupsfilter/html to find them easily.
    cwd = os.getcwd()
    
    def repl_img(match):
        alt = match.group(1)
        path = match.group(2)
        if path.startswith('/'):
            # Assume it's project root relative, e.g. /paper/figures/x.png
            # Remove leading slash and prepend cwd
            abs_path = os.path.join(cwd, path.lstrip('/'))
        else:
            # Assume relative to paper/ directory
            abs_path = os.path.join(cwd, "paper", path)
        return f'![{alt}]({abs_path})'
        
    text = re.sub(r'!\[(.*?)\]\((.*?)\)', repl_img, text)
    
    # Extensions
    extensions = ['extra', 'tables', 'toc']
    
    html_content = markdown.markdown(text, extensions=extensions)
    
    # Add SSRN Academic CSS
    styled_html = f"""
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                margin: 1in;
                size: A4;
                @bottom-center {{
                    content: counter(page);
                    font-family: "Times New Roman", Times, serif;
                    font-size: 10pt;
                }}
            }}
            body {{
                font-family: "Times New Roman", Times, serif;
                line-height: 1.5;
                font-size: 12pt;
                max-width: 100%;
                margin: 0 auto;
                padding: 0;
                text-align: justify;
                color: #000;
            }}
            /* Title Page Adjustments */
            h1:first-of-type {{
                text-align: center;
                font-size: 16pt;
                margin-top: 0;
                margin-bottom: 24pt;
                font-weight: bold;
                text-transform: uppercase;
            }}
            /* Author/Affiliation/Date metadata (usually first few paragraphs) */
            p:nth-of-type(1), p:nth-of-type(2), p:nth-of-type(3), p:nth-of-type(4) {{
                text-align: center;
                margin-bottom: 6pt;
            }}
            
            /* Section Headings */
            h1, h2, h3 {{
                color: #000;
                font-family: "Times New Roman", Times, serif;
            }}
            h2 {{
                font-size: 12pt;
                font-weight: bold;
                text-transform: uppercase;
                margin-top: 24pt;
                border-bottom: none;
            }}
            h3 {{
                font-size: 12pt;
                font-style: italic;
                font-weight: bold;
                margin-top: 18pt;
            }}
            
            /* Abstract formatting if detected (heuristic) */
            strong {{
                font-weight: bold;
            }}
            
            /* Tables and Figures */
            img {{
                max-width: 80%;
                height: auto;
                display: block;
                margin: 24pt auto;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 24pt 0;
                font-size: 10pt;
            }}
            th {{
                border-top: 1px solid #000;
                border-bottom: 1px solid #000;
                padding: 6px;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                border-bottom: 1px solid #ddd;
                padding: 6px;
                text-align: left;
            }}
            tr:last-child td {{
                border-bottom: 1px solid #000;
            }}
            
            /* Blockquotes */
            blockquote {{
                border-left: none;
                margin: 1.5em 2em;
                font-style: italic;
            }}
            
            /* Code */
            code {{
                font-family: "Courier New", Courier, monospace;
                font-size: 10pt;
                background: none;
            }}
            pre {{
                background: #f4f4f4;
                padding: 10px;
                border: 1px solid #ddd;
                overflow-x: auto;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(styled_html)
        
    print(f"HTML generated: {html_file}")
    print("Converting to PDF via Playwright...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # Launch browser (chromium is usually fine)
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Go to the HTML file
            # Playwright needs an absolute URL, e.g. file:///...
            abs_html_path = os.path.abspath(html_file)
            page.goto(f"file://{abs_html_path}")
            
            # Generate PDF
            # Matching the CSS @page or reasonable defaults
            page.pdf(
                path=output_file,
                format="A4",
                print_background=True,
                margin={
                    "top": "40px",
                    "bottom": "40px",
                    "left": "40px",
                    "right": "40px"
                }
            )
            browser.close()
            
        print(f"PDF generated successfully: {output_file}")
            
    except ImportError:
        print("Error: playwright is not installed. Please install it with 'pip install playwright' and 'playwright install'.")
    except Exception as e:
        print(f"Error generating PDF: {e}")

if __name__ == "__main__":
    generate_pdf()
