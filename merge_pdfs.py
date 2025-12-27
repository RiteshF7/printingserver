#!/usr/bin/env python3
"""
PDF Merger Script
Merges all PDF files in the current directory into a single PDF file.
Ensures each PDF has an even number of pages for double-sided printing.
"""

import os
import glob
from pathlib import Path

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
    PYPDF_VERSION = 3
except ImportError:
    try:
        from PyPDF2 import PdfFileWriter, PdfFileReader
        # Compatibility layer for older PyPDF2
        PdfWriter = PdfFileWriter
        PdfReader = PdfFileReader
        HAS_PYPDF = True
        PYPDF_VERSION = 2
    except ImportError:
        print("Error: pypdf or PyPDF2 library is required.")
        print("Install it using: pip install pypdf")
        exit(1)


def create_blank_page(page_width, page_height):
    """
    Create a blank page with the specified dimensions.
    
    Args:
        page_width (float): Width of the page
        page_height (float): Height of the page
    
    Returns:
        Page object: A blank page
    """
    if PYPDF_VERSION >= 3:
        from pypdf import PageObject
        blank_page = PageObject.create_blank_page(width=page_width, height=page_height)
    else:
        from PyPDF2.pdf import PageObject
        blank_page = PageObject.createBlankPage(width=page_width, height=page_height)
    return blank_page


def merge_pdfs(output_filename="merged.pdf"):
    """
    Merge all PDF files in the current directory into a single PDF.
    Ensures each PDF has an even number of pages for double-sided printing.
    
    Args:
        output_filename (str): Name of the output merged PDF file
    """
    # Get current directory
    current_dir = Path(".")
    
    # Find all PDF files in current directory (excluding the output file)
    pdf_files = sorted([f for f in glob.glob("*.pdf") if f != output_filename])
    
    if not pdf_files:
        print("No PDF files found in the current directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to merge:")
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"  {i}. {pdf_file}")
    
    # Create a PDF writer object
    writer = PdfWriter()
    total_pages_added = 0
    blank_pages_added = 0
    
    # Process each PDF file
    for pdf_file in pdf_files:
        try:
            print(f"\nProcessing: {pdf_file}")
            reader = PdfReader(pdf_file)
            num_pages = len(reader.pages)
            
            # Add all pages from this PDF to the writer
            for page_num in range(num_pages):
                writer.add_page(reader.pages[page_num])
                total_pages_added += 1
            
            print(f"  Added {num_pages} page(s)")
            
            # Check if the total pages added so far is odd
            # If odd, add a blank page to make it even
            if total_pages_added % 2 == 1:
                # Get dimensions from the last page added
                last_page = reader.pages[num_pages - 1]
                if PYPDF_VERSION >= 3:
                    page_width = float(last_page.mediabox.width)
                    page_height = float(last_page.mediabox.height)
                else:
                    page_width = float(last_page.mediaBox.getWidth())
                    page_height = float(last_page.mediaBox.getHeight())
                
                # Create and add blank page
                blank_page = create_blank_page(page_width, page_height)
                writer.add_page(blank_page)
                total_pages_added += 1
                blank_pages_added += 1
                print(f"  Added 1 blank page (total pages now: {total_pages_added}, even)")
            else:
                print(f"  Total pages: {total_pages_added} (even, no blank page needed)")
                
        except Exception as e:
            print(f"  Error processing {pdf_file}: {e}")
            continue
    
    # Write the merged PDF to output file
    try:
        print(f"\nWriting merged PDF to: {output_filename}")
        with open(output_filename, "wb") as output_file:
            writer.write(output_file)
        
        # Get file size
        file_size = os.path.getsize(output_filename)
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"\n✓ Successfully merged {len(pdf_files)} PDF file(s) into '{output_filename}'")
        print(f"  Total pages: {total_pages_added} (all even for double-sided printing)")
        if blank_pages_added > 0:
            print(f"  Blank pages added: {blank_pages_added}")
        print(f"  Output file size: {file_size_mb:.2f} MB")
    except Exception as e:
        print(f"\n✗ Error writing output file: {e}")


if __name__ == "__main__":
    import sys
    
    # Allow custom output filename as command line argument
    output_file = sys.argv[1] if len(sys.argv) > 1 else "merged.pdf"
    
    merge_pdfs(output_file)

