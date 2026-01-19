"""
Remove first N and last N pages from a PDF file
"""

from pypdf import PdfReader, PdfWriter
import sys
import os


def remove_first_last_pages(input_path, num_first=1, num_last=1, output_path=None):
    """
    Remove first N and last N pages from a PDF file.
    
    Args:
        input_path: Path to input PDF file
        num_first: Number of pages to remove from the beginning (default: 1)
        num_last: Number of pages to remove from the end (default: 1)
        output_path: Path for output PDF (default: input_name_trimmed.pdf)
    
    Returns:
        str: Path to the output PDF file
    """
    print(f"\n{'='*60}")
    print(f"Removing first {num_first} and last {num_last} pages from: {input_path}")
    print(f"{'='*60}\n")
    
    # Read the input PDF
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    print(f"Total pages in input PDF: {total_pages}")
    
    # Check if we have enough pages
    pages_to_remove = num_first + num_last
    if pages_to_remove >= total_pages:
        print(f"Error: Cannot remove {pages_to_remove} pages from a PDF with only {total_pages} pages.")
        print(f"At least {pages_to_remove + 1} pages are required.\n")
        return None
    
    # Calculate which pages to keep
    start_index = num_first  # Start after first N pages
    end_index = total_pages - num_last  # End before last N pages
    
    print(f"Removing pages 1-{num_first} and pages {total_pages - num_last + 1}-{total_pages}")
    print(f"Keeping pages {num_first + 1}-{total_pages - num_last} ({end_index - start_index} pages)\n")
    
    # Initialize writer
    writer = PdfWriter()
    
    # Add pages in the middle (skip first N and last N)
    for i in range(start_index, end_index):
        writer.add_page(reader.pages[i])
        print(f"  - Kept page {i + 1} (original page {i + 1})")
    
    # Generate output path if not provided
    if output_path is None:
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_dir = os.path.dirname(input_path) or "."
        output_path = os.path.join(output_dir, f"{base_name}_trimmed.pdf")
    
    # Save output PDF
    print(f"\nSaving output PDF...")
    with open(output_path, 'wb') as f:
        writer.write(f)
    print(f"  - Saved: {output_path}\n")
    
    print(f"{'='*60}")
    print("Page removal complete!")
    print(f"{'='*60}\n")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python remove_pages.py <input_pdf> <num_first> <num_last> [output_pdf]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    num_first = int(sys.argv[2])
    num_last = int(sys.argv[3])
    output_pdf = sys.argv[4] if len(sys.argv) > 4 else None
    
    if not os.path.exists(input_pdf):
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)
    
    remove_first_last_pages(input_pdf, num_first, num_last, output_pdf)

