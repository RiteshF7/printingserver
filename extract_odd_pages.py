"""
Extract odd pages from a PDF file and optionally print them
"""

from pypdf import PdfReader, PdfWriter
import sys
import os


def extract_odd_pages(input_path, output_path=None, print_pdf=False):
    """
    Extract odd pages (1-indexed: 1, 3, 5, ...) from a PDF file.
    
    Args:
        input_path: Path to input PDF file
        output_path: Path for output PDF (default: input_name_odd_pages.pdf)
        print_pdf: Whether to print the PDF after extraction (default: False)
    
    Returns:
        str: Path to the output PDF file
    """
    print(f"\n{'='*60}")
    print(f"Extracting odd pages from: {input_path}")
    print(f"{'='*60}\n")
    
    # Read the input PDF
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    print(f"Total pages in input PDF: {total_pages}")
    
    # Initialize writer
    writer = PdfWriter()
    odd_pages = []
    
    # Extract odd pages (1-indexed: 1, 3, 5, ...)
    for i in range(0, total_pages, 2):  # Step by 2: 0, 2, 4, ... (which are pages 1, 3, 5, ...)
        page = reader.pages[i]
        writer.add_page(page)
        odd_pages.append(i + 1)
        print(f"  - Added page {i + 1} (odd page)")
    
    # Generate output path if not provided
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(output_dir, f"{base_name}_odd_pages.pdf")
    
    # Save output PDF
    print(f"\nSaving output PDF...")
    with open(output_path, 'wb') as f:
        writer.write(f)
    print(f"  - Saved: {output_path}")
    print(f"  - Extracted {len(odd_pages)} odd page(s): pages {odd_pages}\n")
    
    # Print if requested
    if print_pdf:
        print_pdf_file(output_path)
    
    print(f"{'='*60}")
    print("Extraction complete!")
    print(f"{'='*60}\n")
    
    return output_path


def print_pdf_file(pdf_path, printer_name=None):
    """
    Print a PDF file using system print command.
    
    Args:
        pdf_path: Path to PDF file to print
        printer_name: Optional printer name (if None, uses default printer)
    """
    import subprocess
    import platform
    
    print(f"\nPrinting: {pdf_path}")
    
    system = platform.system()
    
    if system == "Linux":
        if printer_name:
            cmd = ["lp", "-d", printer_name, pdf_path]
        else:
            cmd = ["lp", pdf_path]
    elif system == "Darwin":  # macOS
        if printer_name:
            cmd = ["lpr", "-P", printer_name, pdf_path]
        else:
            cmd = ["lpr", pdf_path]
    elif system == "Windows":
        # Windows printing using default print verb
        try:
            import os
            # Convert to absolute path
            abs_path = os.path.abspath(pdf_path)
            os.startfile(abs_path, "print")
            print(f"Print job sent to default printer!")
            return
        except Exception as e:
            print(f"Error with Windows printing: {e}")
            print("Trying alternative method...")
            # Fallback: try using PowerShell
            try:
                import os
                abs_path = os.path.abspath(pdf_path)
                ps_cmd = f'Start-Process -FilePath "{abs_path}" -Verb Print'
                cmd = ["powershell", "-Command", ps_cmd]
                subprocess.run(cmd, check=True)
                print(f"Print job sent successfully!")
            except Exception as e2:
                print(f"Error printing: {e2}")
    else:
        print(f"Unsupported operating system: {system}")
        return


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_odd_pages.py <input_pdf> [output_pdf] [--print]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_pdf = None
    print_pdf = False
    
    # Parse arguments
    for arg in sys.argv[2:]:
        if arg == "--print" or arg == "-p":
            print_pdf = True
        else:
            output_pdf = arg
    
    if not os.path.exists(input_pdf):
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)
    
    extract_odd_pages(input_pdf, output_pdf, print_pdf)

