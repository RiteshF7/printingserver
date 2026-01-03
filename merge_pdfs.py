"""
Merge all PDF files in a folder into one PDF file
"""

from pypdf import PdfReader, PdfWriter
import os
import sys


def merge_pdfs_in_folder(folder_path, output_path=None):
    """
    Merge all PDF files in a folder into one PDF file.
    
    Args:
        folder_path: Path to folder containing PDF files
        output_path: Path for merged PDF (default: folder_path/merged.pdf)
    
    Returns:
        str: Path to the merged PDF file
    """
    print(f"\n{'='*60}")
    print(f"Merging PDFs from: {folder_path}")
    print(f"{'='*60}\n")
    
    # Get all PDF files in the folder
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]
    pdf_files.sort()  # Sort alphabetically
    
    if not pdf_files:
        print(f"Error: No PDF files found in {folder_path}")
        return None
    
    print(f"Found {len(pdf_files)} PDF file(s):")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    print()
    
    # Initialize writer
    writer = PdfWriter()
    total_pages = 0
    
    # Read and merge all PDFs
    print("Merging PDFs...")
    for pdf_file in pdf_files:
        pdf_path = os.path.join(folder_path, pdf_file)
        try:
            reader = PdfReader(pdf_path)
            num_pages = len(reader.pages)
            total_pages += num_pages
            
            for page in reader.pages:
                writer.add_page(page)
            
            print(f"  - Added {num_pages} page(s) from: {pdf_file}")
        except Exception as e:
            print(f"  - Error reading {pdf_file}: {e}")
            continue
    
    # Generate output path if not provided
    if output_path is None:
        output_path = os.path.join(folder_path, "merged.pdf")
    
    # Save merged PDF
    print(f"\nSaving merged PDF...")
    with open(output_path, 'wb') as f:
        writer.write(f)
    print(f"  - Saved: {output_path}")
    print(f"  - Total pages: {total_pages}\n")
    
    print(f"{'='*60}")
    print("Merge complete!")
    print(f"{'='*60}\n")
    
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python merge_pdfs.py <folder_path> [output_pdf]")
        sys.exit(1)
    
    folder_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder not found: {folder_path}")
        sys.exit(1)
    
    if not os.path.isdir(folder_path):
        print(f"Error: Not a directory: {folder_path}")
        sys.exit(1)
    
    merge_pdfs_in_folder(folder_path, output_path)


