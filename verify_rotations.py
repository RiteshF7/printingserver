#!/usr/bin/env python3
"""Quick script to verify rotations in generated PDF"""

from pypdf import PdfReader
import sys

pdf_path = sys.argv[1] if len(sys.argv) > 1 else 'output/merged_combined.pdf'

try:
    r = PdfReader(pdf_path)
    print(f"Total pages: {len(r.pages)}")
    print("\nVerifying rotations:")
    print("="*60)
    
    # Check first 5 odd pages (should be 0)
    print("\nFirst 5 odd pages (should have 0 rotation):")
    for i in range(min(5, len(r.pages))):
        rot = r.pages[i].get('/Rotate', 0)
        status = "OK" if rot == 0 else f"MISSING (found {rot})"
        print(f"  Page {i+1}: Rotation = {rot} - {status}")
    
    # Check first 5 even pages (should be 180)
    odd_count = len(r.pages) // 2
    print(f"\nFirst 5 even pages (starting at page {odd_count + 1}, should have 180 rotation):")
    for i in range(odd_count, min(odd_count + 5, len(r.pages))):
        rot = r.pages[i].get('/Rotate', 0)
        status = "OK" if rot == 180 else f"MISSING (found {rot})"
        print(f"  Page {i+1}: Rotation = {rot} - {status}")
    
    print("\n" + "="*60)
    
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

