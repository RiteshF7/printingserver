"""
Extract first N pages from a PDF file
"""

from pypdf import PdfReader, PdfWriter
import sys
import os


def extract_pages(input_path, num_pages, output_path=None):
    """
    Extract first N pages from a PDF file.
    
    Args:
        input_path: Path to input PDF file
        num_pages: Number of pages to extract from the beginning
        output_path: Path for output PDF (default: input_name_first_N_pages.pdf)
    
    Returns:
        str: Path to the output PDF file
    """
    print(f"\n{'='*60}")
    print(f"Extracting first {num_pages} pages from: {input_path}")
    print(f"{'='*60}\n")
    
    # Read the input PDF
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    print(f"Total pages in input PDF: {total_pages}")
    
    # Check if we have enough pages
    if num_pages > total_pages:
        print(f"Warning: Requested {num_pages} pages, but PDF only has {total_pages} pages.")
        print(f"Extracting all {total_pages} pages instead.\n")
        num_pages = total_pages
    else:
        print(f"Extracting first {num_pages} pages...\n")
    
    # Initialize writer
    writer = PdfWriter()
    
    # Add first N pages
    for i in range(num_pages):
        writer.add_page(reader.pages[i])
        print(f"  - Added page {i + 1}")
    
    # Generate output path if not provided
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(output_dir, f"{base_name}_first_{num_pages}_pages.pdf")
    
    # Save output PDF
    print(f"\nSaving output PDF...")
    with open(output_path, 'wb') as f:
        writer.write(f)
    print(f"  - Saved: {output_path}\n")
    
    print(f"{'='*60}")
    print("Extraction complete!")
    print(f"{'='*60}\n")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python extract_pages.py <input_pdf> <num_pages> [output_pdf]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    num_pages = int(sys.argv[2])
    output_pdf = sys.argv[3] if len(sys.argv) > 3 else None
    
    if not os.path.exists(input_pdf):
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)
    
    extract_pages(input_pdf, num_pages, output_pdf)



