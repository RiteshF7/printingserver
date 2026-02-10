"""
Split a PDF into multiple files of N pages each.
"""

import os
import sys
from PyPDF2 import PdfReader, PdfWriter


def split_pdf(input_path, output_dir, pages_per_part=30):
    """
    Split a PDF into parts of specified page count.

    Args:
        input_path (str): Path to input PDF
        output_dir (str): Directory for output PDFs
        pages_per_part (int): Number of pages per output file

    Returns:
        list: Paths to created PDF files
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input PDF not found: {input_path}")

    os.makedirs(output_dir, exist_ok=True)

    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    created = []

    for start in range(0, total_pages, pages_per_part):
        end = min(start + pages_per_part, total_pages)
        part_num = (start // pages_per_part) + 1
        output_name = f"{base_name}_part{part_num:03d}.pdf"
        output_path = os.path.join(output_dir, output_name)

        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])

        with open(output_path, "wb") as f:
            writer.write(f)

        created.append(output_path)
        print(f"  Part {part_num}: pages {start + 1}-{end} -> {output_name}")

    return created


if __name__ == "__main__":
    INPUT_PDF = r"C:\Users\rites\printer\MIH---Merged-PDF.pdf"
    OUTPUT_DIR = r"C:\Users\rites\printer\splitpdf"
    PAGES_PER_PART = 60

    print("Splitting PDF...")
    print(f"Input: {INPUT_PDF}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Pages per part: {PAGES_PER_PART}")
    print()

    try:
        paths = split_pdf(INPUT_PDF, OUTPUT_DIR, PAGES_PER_PART)
        print()
        print(f"Done. Created {len(paths)} file(s) in {OUTPUT_DIR}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
