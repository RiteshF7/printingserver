"""
PDF Processor for Duplex Printing Workflow

This script handles:
1. Splitting odd and even pages from an input PDF
2. Reversing odd pages (so page 1 ends up on top when printed)
3. Rotating even pages by 180 degrees
4. Generating output PDFs ready for duplex printing
"""

from pypdf import PdfReader, PdfWriter
import sys
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch


def clone_page(page):
    """Create a deep copy of a PDF page to avoid modifying the original.
    Preserves rotation and other page attributes."""
    # Get rotation before cloning
    original_rotation = page.get('/Rotate', 0)
    
    temp_writer = PdfWriter()
    temp_writer.add_page(page)
    temp_buffer = io.BytesIO()
    temp_writer.write(temp_buffer)
    temp_buffer.seek(0)
    temp_reader = PdfReader(temp_buffer)
    cloned_page = temp_reader.pages[0]
    
    # Ensure rotation is preserved - if rotation was lost, re-apply it
    cloned_rotation = cloned_page.get('/Rotate', 0)
    if cloned_rotation != original_rotation and original_rotation != 0:
        # Re-apply rotation if it was lost during cloning
        current_rotation = cloned_page.get('/Rotate', 0)
        if current_rotation != original_rotation:
            # Calculate needed rotation
            needed_rotation = (original_rotation - current_rotation) % 360
            if needed_rotation != 0:
                cloned_page.rotate(needed_rotation)
    
    return cloned_page


def create_title_page(filename, page_size=(612, 792), image_path="frontpage.png"):
    """
    Create a PDF page with an image on the left (vertically centered) and filename on the right.
    
    Args:
        filename: Filename to display on the title page
        page_size: Tuple of (width, height) for the page (default: US Letter)
        image_path: Path to the image file to display
    
    Returns:
        PdfReader object with the title page
    """
    from reportlab.lib.utils import ImageReader
    
    width, height = page_size
    
    # Create PDF in memory
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(width, height))
    
    # Remove .pdf extension for display
    display_name = os.path.splitext(filename)[0]
    
    # Load and place image
    image_loaded = False
    image_top_y = 0  # Track top of image for text placement
    
    if os.path.exists(image_path):
        try:
            # Open image
            img = ImageReader(image_path)
            img_width, img_height = img.getSize()
            
            # Scale image to fit nicely (max height: 60% of page, maintain aspect ratio)
            max_img_height = height * 0.6
            scale_factor = min(max_img_height / img_height, 1.0)
            scaled_width = img_width * scale_factor
            scaled_height = img_height * scale_factor
            
            # Position image: center horizontally, vertically with space at bottom
            img_x = (width - scaled_width) / 2  # Center horizontally
            # Position image lower on page to leave space at bottom
            img_y = (height - scaled_height) / 2 - (height * 0.15)  # Lower position with bottom space
            
            # Track top of image for text placement above
            image_top_y = img_y + scaled_height
            
            # Set font for filename first to calculate text height
            font_size = min(36, width / 16)
            can.setFont("Helvetica-Bold", font_size)
            text_width = can.stringWidth(display_name, "Helvetica-Bold", font_size)
            text_height = font_size * 1.2  # Approximate text height
            
            # Position text above the image with spacing
            spacing = 40  # Space between text and image
            text_y = image_top_y + spacing  # Text above image
            text_x = (width - text_width) / 2  # Center text horizontally
            
            # Draw the filename above the image
            can.drawString(text_x, text_y, display_name)
            
            # Draw the image below the text
            can.drawImage(img, img_x, img_y, width=scaled_width, height=scaled_height, preserveAspectRatio=True)
            
            image_loaded = True
            
        except Exception as e:
            print(f"  Warning: Could not load image {image_path}: {e}")
            print(f"  Falling back to text-only title page.")
            image_loaded = False
    else:
        print(f"  Warning: Image file {image_path} not found. Using text-only title page.")
        image_loaded = False
    
    # Set font for filename if image wasn't loaded
    if not image_loaded:
        font_size = min(36, width / 16)
        can.setFont("Helvetica-Bold", font_size)
        can.setFillColorRGB(0, 0, 0)  # Black
        
        # If no image, center text on page
        text_x = width / 2
        text_y = height / 2
        text_width = can.stringWidth(display_name, "Helvetica-Bold", font_size)
        text_x = (width - text_width) / 2  # Center text
        
        # Draw the filename
        can.drawString(text_x, text_y, display_name)
    
    can.save()
    
    # Move to the beginning of the buffer
    packet.seek(0)
    
    # Create PDF reader from the buffer
    title_pdf = PdfReader(packet)
    return title_pdf


def add_title_page_to_pdf(reader, filename, page_size=None, image_path="frontpage.png"):
    """
    Add a title page with image and filename at the beginning of a PDF.
    
    Args:
        reader: PdfReader object of the PDF
        filename: Filename to display on title page
        page_size: Optional page size tuple, auto-detected if None
        image_path: Path to the image file to display on title page
    
    Returns:
        PdfReader object with title page added
    """
    # Get page size from first page if not provided
    if page_size is None and len(reader.pages) > 0:
        page = reader.pages[0]
        mediabox = page.mediabox
        page_size = (float(mediabox.width), float(mediabox.height))
    else:
        page_size = (612, 792)  # Default to US Letter
    
    # Create title page
    title_pdf = create_title_page(filename, page_size, image_path)
    title_page = title_pdf.pages[0]
    
    # Create new PDF with title page + all original pages
    writer = PdfWriter()
    writer.add_page(title_page)
    
    for page in reader.pages:
        writer.add_page(page)
    
    # Write to buffer and read back
    temp_buffer = io.BytesIO()
    writer.write(temp_buffer)
    temp_buffer.seek(0)
    return PdfReader(temp_buffer)


def ensure_even_page_count(reader):
    """
    Ensure PDF has even number of pages by adding a blank page at the end if needed.
    
    Args:
        reader: PdfReader object of the PDF
    
    Returns:
        PdfReader object with even page count
    """
    total_pages = len(reader.pages)
    
    if total_pages % 2 == 0:
        # Already even, return as-is
        return reader
    
    # Need to add a blank page
    # Get page size from first page
    if total_pages > 0:
        page = reader.pages[0]
        mediabox = page.mediabox
        page_size = (float(mediabox.width), float(mediabox.height))
    else:
        page_size = (612, 792)  # Default to US Letter
    
    # Create a blank page using reportlab
    try:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=page_size)
        # Draw nothing - just create an empty page
        can.showPage()
        can.save()
        packet.seek(0)
        blank_pdf = PdfReader(packet)
        
        if len(blank_pdf.pages) > 0:
            blank_page = blank_pdf.pages[0]
        else:
            # Fallback: clone the first page and clear it (less ideal but works)
            blank_page = clone_page(reader.pages[0])
    except Exception as e:
        # Fallback: clone the first page if blank page creation fails
        print(f"  Warning: Could not create blank page, using cloned first page: {e}")
        blank_page = clone_page(reader.pages[0])
    
    # Create new PDF with all original pages + blank page
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.add_page(blank_page)
    
    # Write to buffer and read back
    temp_buffer = io.BytesIO()
    writer.write(temp_buffer)
    temp_buffer.seek(0)
    return PdfReader(temp_buffer)


def split_pdf_into_chunks(pdf_path, chunk_size=20, output_dir="."):
    """
    Split a PDF into multiple PDF files, each containing up to chunk_size pages.
    
    Args:
        pdf_path: Path to the PDF file to split
        chunk_size: Number of pages per chunk (default: 20)
        output_dir: Directory to save output PDFs (default: current directory)
    
    Returns:
        list: List of paths to the created chunk PDFs
    """
    reader = PdfReader(pdf_path)
    total_pages = len(reader.pages)
    
    print(f"\n{'='*60}")
    print(f"Splitting PDF into chunks of {chunk_size} pages each")
    print(f"Total pages: {total_pages}")
    print(f"{'='*60}\n")
    
    chunk_paths = []
    base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    
    num_chunks = (total_pages + chunk_size - 1) // chunk_size  # Ceiling division
    
    for chunk_idx in range(num_chunks):
        start_page = chunk_idx * chunk_size
        end_page = min(start_page + chunk_size, total_pages)
        
        writer = PdfWriter()
        
        for page_num in range(start_page, end_page):
            # Clone page to ensure rotations and other metadata are preserved
            page = clone_page(reader.pages[page_num])
            writer.add_page(page)
        
        chunk_filename = f"{base_name}_part_{chunk_idx + 1}_of_{num_chunks}.pdf"
        chunk_path = os.path.join(output_dir, chunk_filename)
        
        with open(chunk_path, 'wb') as f:
            writer.write(f)
        
        chunk_paths.append(chunk_path)
        print(f"  - Created chunk {chunk_idx + 1}/{num_chunks}: {chunk_filename} (pages {start_page + 1}-{end_page})")
    
    print(f"\n{'='*60}")
    print(f"Created {num_chunks} chunk(s)")
    print(f"{'='*60}\n")
    
    return chunk_paths


def remove_first_last_pages(input_path, output_path=None):
    """
    Remove the first and last page from a PDF.
    
    Args:
        input_path: Path to input PDF file
        output_path: Path for output PDF (if None, creates temp file in memory)
    
    Returns:
        tuple: (PdfReader object with pages removed, original_first_page_num, original_last_page_num)
               or (None, None, None) if PDF has 2 or fewer pages
    """
    reader = PdfReader(input_path)
    total_pages = len(reader.pages)
    
    # Need at least 3 pages to remove first and last
    if total_pages <= 2:
        print(f"  Warning: PDF has only {total_pages} page(s). Cannot remove first and last page.")
        print(f"  Processing all pages as-is.\n")
        return reader, None, None
    
    # Create new PDF with pages 2 to second-to-last (skip first and last)
    writer = PdfWriter()
    for i in range(1, total_pages - 1):  # Skip index 0 (first) and last index
        writer.add_page(reader.pages[i])
    
    # Write to temporary buffer or file
    if output_path:
        with open(output_path, 'wb') as f:
            writer.write(f)
        # Read back from file
        new_reader = PdfReader(output_path)
    else:
        # Use memory buffer
        temp_buffer = io.BytesIO()
        writer.write(temp_buffer)
        temp_buffer.seek(0)
        new_reader = PdfReader(temp_buffer)
    
    original_first = 1
    original_last = total_pages
    
    print(f"  - Removed first page (original page 1) and last page (original page {total_pages})")
    print(f"  - Processing pages 2-{total_pages-1} ({total_pages-2} pages remaining)\n")
    
    return new_reader, original_first, original_last


def add_page_watermark(page, original_page_num, original_filename, is_rotated=False):
    """
    Add a watermark to a PDF page showing original page number and filename.
    
    Args:
        page: pypdf Page object
        original_page_num: Original page number (from the source PDF)
        original_filename: Original filename
        is_rotated: Whether the page is rotated 180 degrees
    
    Returns:
        Page object with watermark
    """
    try:
        # Get page dimensions
        page_mediabox = page.mediabox
        width = float(page_mediabox.width)
        height = float(page_mediabox.height)
        
        # Create a watermark PDF in memory
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        
        # Prepare watermark text
        watermark_text = f"P{original_page_num} | {original_filename}"
        
        # Font size - scale based on page size
        font_size = min(8, width / 100)
        
        # Position: bottom right corner
        # When page is rotated 180°, we need to account for rotation
        # After rotation, what was top-left becomes bottom-right visually
        if is_rotated:
            # For rotated pages, place at top-left in rotated coords (becomes bottom-right visually)
            x = 10
            y = height - 15
            # Left-align since we're at the left edge
            text_width = can.stringWidth(watermark_text, "Helvetica", font_size)
        else:
            # Normal orientation: bottom right
            x = width - 10
            y = 15
            # Right-align by calculating text width
            text_width = can.stringWidth(watermark_text, "Helvetica", font_size)
        
        # Set font and color (light gray, semi-transparent)
        can.setFont("Helvetica", font_size)
        can.setFillColorRGB(0.5, 0.5, 0.5)  # Gray
        can.setFillAlpha(0.7)  # 70% opacity
        
        # Draw text with appropriate alignment
        if is_rotated:
            can.drawString(x, y, watermark_text)
        else:
            can.drawString(x - text_width, y, watermark_text)
        
        can.save()
        
        # Move to the beginning of the StringIO buffer
        packet.seek(0)
        
        # Create a PDF from the watermark
        watermark_pdf = PdfReader(packet)
        watermark_page = watermark_pdf.pages[0]
        
        # Merge watermark with the page
        page.merge_page(watermark_page)
        
        return page
        
    except Exception as e:
        print(f"  Warning: Could not add watermark to page {original_page_num}: {e}")
        return page


def preprocess_pdf(input_path, remove_first_last=True):
    """
    Pre-process a PDF: remove first/last pages, add title page, ensure even count.
    This does NOT split into odd/even or apply rotations.
    
    Args:
        input_path: Path to input PDF file
        remove_first_last: Whether to remove first and last pages (default: True)
    
    Returns:
        tuple: (preprocessed_PdfReader, original_page_map, original_filename, original_total_pages, removed_first, removed_last)
               original_page_map: Maps current page index to original page number (0 for title/blank pages)
    """
    # Get original filename for title page
    original_filename = os.path.basename(input_path)
    
    # Read the input PDF
    original_reader = PdfReader(input_path)
    original_total_pages = len(original_reader.pages)
    
    print(f"Total pages in input PDF: {original_total_pages}")
    
    # Map to track original page numbers
    original_page_map = {}
    removed_first = None
    removed_last = None
    
    # Step 0a: Remove first and last pages if requested
    if remove_first_last:
        print("\nStep 0a: Removing first and last pages...")
        reader, removed_first, removed_last = remove_first_last_pages(input_path)
        if reader is None:
            # PDF had 2 or fewer pages, use original
            reader = original_reader
            total_pages = original_total_pages
            # Map all pages to themselves
            for i in range(total_pages):
                original_page_map[i] = i + 1
        else:
            total_pages = len(reader.pages)
            # Create mapping: new page index -> original page number
            for i in range(total_pages):
                original_page_map[i] = i + 2  # +2 because we removed page 1
        print(f"Pages after removal: {total_pages}")
    else:
        reader = original_reader
        total_pages = original_total_pages
        # Map all pages to themselves
        for i in range(total_pages):
            original_page_map[i] = i + 1
    
    # Step 0b: Add title page at the front
    print("\nStep 0b: Adding title page with image and filename...")
    pages_before_title = total_pages
    # Look for frontpage.png
    image_path = "frontpage.png"
    if not os.path.exists(image_path):
        image_path = os.path.join(os.path.dirname(input_path), "frontpage.png")
        if not os.path.exists(image_path):
            image_path = os.path.join(os.path.dirname(os.path.dirname(input_path)), "frontpage.png")
    if os.path.exists(image_path):
        print(f"  - Using image: {image_path}")
    
    reader = add_title_page_to_pdf(reader, original_filename, image_path=image_path)
    total_pages = len(reader.pages)
    
    # Update page mapping to account for title page (inserted at index 0)
    new_original_page_map = {0: 0}  # Title page maps to 0
    for i in range(1, total_pages):
        old_index = i - 1
        if old_index < pages_before_title:
            if old_index in original_page_map:
                new_original_page_map[i] = original_page_map[old_index]
            else:
                new_original_page_map[i] = old_index + 1
        else:
            new_original_page_map[i] = 0
    original_page_map = new_original_page_map
    
    print(f"Pages after adding title page: {total_pages}")
    
    # Step 0c: Ensure even page count
    print("\nStep 0c: Ensuring even page count...")
    pages_before_even = total_pages
    reader = ensure_even_page_count(reader)
    total_pages = len(reader.pages)
    
    if total_pages > pages_before_even:
        print(f"  - Added blank page to make even count (now {total_pages} pages)")
        # Update mapping for blank page (last page)
        blank_page_index = total_pages - 1
        original_page_map[blank_page_index] = 0
    else:
        print(f"  - Already even ({total_pages} pages)")
    
    return reader, original_page_map, original_filename, original_total_pages, removed_first, removed_last


def process_reader_into_odd_even(reader, original_page_map, original_filename_or_map, output_dir, add_watermarks=True):
    """
    Process a PdfReader into odd and even PDFs for duplex printing.
    
    Args:
        reader: PdfReader object with preprocessed pages
        original_page_map: Dictionary mapping page index to (original_page_num, filename) tuple or just original_page_num
        original_filename_or_map: Either a string filename or the page_map itself (if it contains filename tuples)
        output_dir: Directory to save output PDFs
        add_watermarks: Whether to add watermarks (default: True)
    
    Returns:
        tuple: (odd_pages_path, even_pages_path)
    """
    # Handle both cases: page_map with (page_num, filename) tuples or just page numbers
    # If original_filename_or_map is a string, it's a filename; otherwise it's the page_map
    if isinstance(original_filename_or_map, str):
        # Simple case: single filename for all pages
        get_filename = lambda idx: original_filename_or_map
        get_page_num = lambda idx: original_page_map.get(idx, idx + 1)
    else:
        # Complex case: page_map contains (page_num, filename) tuples
        get_filename = lambda idx: original_page_map.get(idx, (idx + 1, "unknown"))[1] if isinstance(original_page_map.get(idx, (idx + 1, "unknown")), tuple) else "unknown"
        get_page_num = lambda idx: original_page_map.get(idx, (idx + 1, "unknown"))[0] if isinstance(original_page_map.get(idx, (idx + 1, "unknown")), tuple) else original_page_map.get(idx, idx + 1)
    total_pages = len(reader.pages)
    
    # Initialize writers for odd and even pages
    odd_writer = PdfWriter()
    even_writer = PdfWriter()
    
    # Track page order information
    odd_pages_order = []
    even_pages_order = []
    
    # Split pages into odd and even
    print("Step 1: Splitting pages into odd and even...")
    for i in range(total_pages):
        page_num = i + 1  # 1-indexed page number
        original_page_num = get_page_num(i)  # Original page number (0 for title/blank)
        
        if page_num % 2 == 1:  # Odd page (1-indexed)
            odd_pages_order.append((i, original_page_num))
        else:  # Even page
            even_pages_order.append((i, original_page_num))
    
    print(f"  - Odd pages found: {len(odd_pages_order)} pages")
    print(f"  - Even pages found: {len(even_pages_order)} pages\n")
    
    # Step 2: Add odd pages in REVERSE order
    print("Step 2: Adding odd pages in REVERSE order...")
    if add_watermarks:
        print("  (Adding watermarks: original page number and filename)")
    
    for i in range(len(odd_pages_order) - 1, -1, -1):
        page_index, original_page_num = odd_pages_order[i]
        page = clone_page(reader.pages[page_index])
        
        if add_watermarks and original_page_num > 0:
            filename = get_filename(page_index)
            page = add_page_watermark(page, original_page_num, filename, is_rotated=False)
        
        odd_writer.add_page(page)
        if original_page_num > 0:
            print(f"  - Added original page {original_page_num} (position {len(odd_pages_order) - i} in output)")
        elif page_index == 0:
            print(f"  - Added title page (position {len(odd_pages_order) - i} in output)")
        else:
            print(f"  - Added blank page (position {len(odd_pages_order) - i} in output)")
    
    print(f"\n  Final odd pages order: {len(odd_pages_order)} pages\n")
    
    # Step 3: Add even pages in NORMAL order, rotated 180 degrees
    print("Step 3: Adding even pages in NORMAL order, rotated 180°...")
    if add_watermarks:
        print("  (Adding watermarks: original page number and filename)")
    
    for page_index, original_page_num in even_pages_order:
        page = clone_page(reader.pages[page_index])
        
        if original_page_num > 0:
            page.rotate(180)
        
        if add_watermarks and original_page_num > 0:
            filename = get_filename(page_index)
            page = add_page_watermark(page, original_page_num, filename, is_rotated=True)
        
        even_writer.add_page(page)
        if original_page_num > 0:
            print(f"  - Added original page {original_page_num} (rotated 180°)")
        else:
            print(f"  - Added blank/title page (no rotation)")
    
    print(f"\n  Final even pages order: {len(even_pages_order)} pages\n")
    
    # Save output PDFs
    odd_output_path = os.path.join(output_dir, "odd_pages.pdf")
    even_output_path = os.path.join(output_dir, "even_pages_rotated.pdf")
    
    print("Step 4: Saving output PDFs...")
    with open(odd_output_path, 'wb') as f:
        odd_writer.write(f)
    print(f"  - Saved: {odd_output_path}")
    
    with open(even_output_path, 'wb') as f:
        even_writer.write(f)
    print(f"  - Saved: {even_output_path}\n")
    
    return odd_output_path, even_output_path


def process_pdf(input_path, output_dir=".", add_watermarks=True, remove_first_last=True):
    """
    Process PDF for duplex printing workflow.
    
    Args:
        input_path: Path to input PDF file
        output_dir: Directory to save output PDFs (default: current directory)
        add_watermarks: Whether to add watermarks with page numbers and filename (default: True)
        remove_first_last: Whether to remove first and last pages (default: True)
    
    Returns:
        tuple: (odd_pages_path, even_pages_path, page_info)
    """
    print(f"\n{'='*60}")
    print(f"Processing PDF: {input_path}")
    print(f"{'='*60}\n")
    
    # Get original filename for watermark
    original_filename = os.path.basename(input_path)
    
    # Read the input PDF
    original_reader = PdfReader(input_path)
    original_total_pages = len(original_reader.pages)
    
    print(f"Total pages in input PDF: {original_total_pages}")
    
    # Map to track original page numbers (for watermarks)
    # Maps current page index to original page number
    original_page_map = {}
    removed_first = None
    removed_last = None
    
    # Step 0: Remove first and last pages if requested
    if remove_first_last:
        print("\nStep 0a: Removing first and last pages...")
        reader, removed_first, removed_last = remove_first_last_pages(input_path)
        if reader is None:
            # PDF had 2 or fewer pages, use original
            reader = original_reader
            total_pages = original_total_pages
            # Map all pages to themselves
            for i in range(total_pages):
                original_page_map[i] = i + 1
        else:
            total_pages = len(reader.pages)
            # Create mapping: new page index -> original page number
            # Pages 0, 1, 2... in new PDF map to pages 2, 3, 4... in original
            for i in range(total_pages):
                original_page_map[i] = i + 2  # +2 because we removed page 1 (0-indexed = 1)
    else:
        reader = original_reader
        total_pages = original_total_pages
        # Map all pages to themselves
        for i in range(total_pages):
            original_page_map[i] = i + 1
    
    print(f"Pages after removal: {total_pages}")
    
    # Step 0b: Add title page at the front
    print("\nStep 0b: Adding title page with image and filename...")
    pages_before_title = total_pages
    # Look for frontpage.png: try current directory first, then PDF directory
    image_path = "frontpage.png"  # Try current directory first
    if not os.path.exists(image_path):
        image_path = os.path.join(os.path.dirname(input_path), "frontpage.png")
        if not os.path.exists(image_path):
            # Try parent directory of input_path
            image_path = os.path.join(os.path.dirname(os.path.dirname(input_path)), "frontpage.png")
    if os.path.exists(image_path):
        print(f"  - Using image: {image_path}")
    reader = add_title_page_to_pdf(reader, original_filename, image_path=image_path)
    total_pages = len(reader.pages)
    
    # Update page mapping to account for title page (inserted at index 0)
    # All existing pages shift by 1
    new_original_page_map = {0: 0}  # Title page (index 0) maps to 0 (not an original page)
    for i in range(1, total_pages):
        # Original pages now start at index 1
        old_index = i - 1
        if old_index < pages_before_title:
            # Get the original page number from the old mapping
            if old_index in original_page_map:
                new_original_page_map[i] = original_page_map[old_index]
            else:
                new_original_page_map[i] = old_index + 1  # Fallback
        else:
            new_original_page_map[i] = 0  # Blank page
    original_page_map = new_original_page_map
    
    print(f"Pages after adding title page: {total_pages}")
    
    # Step 0c: Ensure even page count
    print("\nStep 0c: Ensuring even page count...")
    pages_before_even = total_pages
    reader = ensure_even_page_count(reader)
    total_pages = len(reader.pages)
    
    if total_pages > pages_before_even:
        print(f"  - Added blank page to make even count (now {total_pages} pages)")
        # Update mapping for blank page (last page)
        blank_page_index = total_pages - 1
        original_page_map[blank_page_index] = 0  # Blank page maps to 0 (not an original page)
    else:
        print(f"  - Already even ({total_pages} pages)")
    
    print(f"Pages to process: {total_pages}\n")
    
    # Process into odd and even PDFs
    odd_output_path, even_output_path = process_reader_into_odd_even(
        reader, original_page_map, original_filename, output_dir, add_watermarks
    )
    
    # Create page info dictionary (using original page numbers)
    all_original_pages = sorted([p for p in original_page_map.values() if p > 0])  # Exclude title/blank pages
    # Calculate odd/even counts (total_pages is even after ensure_even_page_count)
    odd_pages_count = (total_pages + 1) // 2  # Ceiling division for odd pages
    even_pages_count = total_pages // 2  # Floor division for even pages
    
    page_info = {
        'total_pages': total_pages,
        'original_total_pages': original_total_pages,
        'original_sequence': all_original_pages,
        'removed_first_page': removed_first,
        'removed_last_page': removed_last,
        'has_title_page': True,
        'odd_pages_count': odd_pages_count,
        'even_pages_count': even_pages_count,
        'odd_output': odd_output_path,
        'even_output': even_output_path
    }
    
    print(f"{'='*60}")
    print("Processing complete!")
    print(f"{'='*60}\n")
    
    return odd_output_path, even_output_path, page_info


def process_multiple_pdfs(input_paths, output_dir=".", add_watermarks=True, remove_first_last=True):
    """
    Process multiple PDFs for duplex printing workflow.
    
    NEW WORKFLOW:
    1. Pre-process each PDF (remove first/last, add title page, ensure even count)
    2. Merge all pre-processed PDFs into one
    3. Process merged PDF (split odd/even, reverse odd, rotate even)
    4. Combine odd and even pages
    5. Split into chunks
    
    Args:
        input_paths: List of paths to input PDF files
        output_dir: Directory to save output PDFs (default: current directory)
        add_watermarks: Whether to add watermarks with page numbers and filename (default: True)
        remove_first_last: Whether to remove first and last pages from each PDF (default: True)
    
    Returns:
        tuple: (merged_combined_path, merged_combined_path, combined_page_info)
    """
    import tempfile
    import shutil
    
    print(f"\n{'='*60}")
    print(f"Processing {len(input_paths)} PDF files for batch processing")
    print(f"{'='*60}\n")
    
    # Create temporary directory for preprocessed PDFs
    temp_dir = tempfile.mkdtemp(prefix="pdf_batch_")
    
    try:
        combined_page_info = {
            'total_pages': 0,
            'original_sequence': [],
            'files_processed': []
        }
        
        # Step 0: Pre-process each PDF (remove first/last, add title, ensure even)
        preprocessed_readers = []
        merged_page_map = {}  # Maps page index in merged PDF to (original_page_num, filename)
        current_page_index = 0
        
        for file_idx, input_path in enumerate(input_paths):
            print(f"\n{'='*60}")
            print(f"Pre-processing file {file_idx + 1}/{len(input_paths)}: {os.path.basename(input_path)}")
            print(f"{'='*60}\n")
            
            original_filename = os.path.basename(input_path)
            
            # Pre-process PDF (steps 0a, 0b, 0c)
            if remove_first_last:
                print("Step 0a: Removing first and last pages...")
            reader, page_map, filename, original_total, removed_first, removed_last = preprocess_pdf(
                input_path, remove_first_last=remove_first_last
            )
            
            total_pages = len(reader.pages)
            print(f"Pages after pre-processing: {total_pages}\n")
            
            # Update merged page map
            for i in range(total_pages):
                original_page_num = page_map.get(i, i + 1)
                merged_page_map[current_page_index + i] = (original_page_num, filename)
            
            # Track info
            combined_page_info['total_pages'] += total_pages
            combined_page_info['files_processed'].append({
                'filename': filename,
                'total_pages': total_pages,
                'original_total_pages': original_total,
                'removed_first': removed_first,
                'removed_last': removed_last
            })
            
            preprocessed_readers.append(reader)
            current_page_index += total_pages
        
        # Step 0.5: Merge all preprocessed PDFs into one
        print(f"\n{'='*60}")
        print("Merging all preprocessed PDFs...")
        print(f"{'='*60}\n")
        
        merged_writer = PdfWriter()
        for idx, reader in enumerate(preprocessed_readers):
            print(f"  - Adding pages from file {idx + 1} ({len(reader.pages)} pages)")
            for page in reader.pages:
                merged_writer.add_page(clone_page(page))
        
        # Write merged PDF to temporary file
        merged_temp_path = os.path.join(temp_dir, "merged_preprocessed.pdf")
        with open(merged_temp_path, 'wb') as f:
            merged_writer.write(f)
        
        merged_reader = PdfReader(merged_temp_path)
        total_merged_pages = len(merged_reader.pages)
        
        print(f"\nMerged PDF created: {total_merged_pages} pages total\n")
        
        # Step 1-3: Process merged PDF (split odd/even, reverse odd, rotate even)
        print(f"\n{'='*60}")
        print("Processing merged PDF (split odd/even, reverse odd, rotate even)...")
        print(f"{'='*60}\n")
        
        # Process merged PDF into odd and even
        # merged_page_map contains (page_num, filename) tuples
        odd_output_path, even_output_path = process_reader_into_odd_even(
            merged_reader, merged_page_map, merged_page_map, temp_dir, add_watermarks
        )
        
        # Read odd and even PDFs
        odd_reader = PdfReader(odd_output_path)
        even_reader = PdfReader(even_output_path)
        
        # Step 4: Combine odd and even pages into a single PDF
        print(f"\n{'='*60}")
        print("Step 4: Combining odd and even pages into single PDF...")
        print(f"{'='*60}\n")
        
        combined_writer = PdfWriter()
        
        total_odd_pages = len(odd_reader.pages)
        total_even_pages = len(even_reader.pages)
        
        # Add all odd pages first (already in reversed order)
        print("Adding odd pages (reversed order)...")
        page_counter = 0
        for page in odd_reader.pages:
            cloned_page = clone_page(page)
            combined_writer.add_page(cloned_page)
            page_counter += 1
            rotation = cloned_page.get('/Rotate', 0)
            if page_counter <= 3:  # Print first few
                print(f"    Page {page_counter}: Rotation = {rotation}° (should be 0°)")
        
        print(f"  Total odd pages added: {page_counter}\n")
        
        # Then add all even pages (already rotated 180°)
        print("Adding even pages (rotated 180°)...")
        even_start_page = page_counter + 1
        for page in even_reader.pages:
            cloned_page = clone_page(page)
            combined_writer.add_page(cloned_page)
            page_counter += 1
            rotation = cloned_page.get('/Rotate', 0)
            if page_counter - even_start_page < 3:  # Print first few even pages
                status = "OK" if rotation == 180 else "MISSING"
                print(f"    Page {page_counter}: Rotation = {rotation} {status} (should be 180)")
        
        print(f"  Total even pages added: {page_counter - total_odd_pages}\n")
        
        print(f"\n{'='*60}")
        print(f"Batch processing complete! Processed {len(input_paths)} files, {combined_page_info['total_pages']} total pages")
        print(f"{'='*60}\n")
        
        # Save combined PDF
        combined_path = os.path.join(output_dir, "merged_combined.pdf")
        print(f"Saving combined PDF...")
        with open(combined_path, 'wb') as f:
            combined_writer.write(f)
        
        total_combined_pages = len(combined_writer.pages)
        print(f"  - Saved combined PDF: {combined_path} ({total_combined_pages} pages)")
        print(f"    - Odd pages: {total_odd_pages} pages (reversed order)")
        print(f"    - Even pages: {total_even_pages} pages (rotated 180°)\n")
        
        combined_page_info['combined_output'] = combined_path
        combined_page_info['odd_pages_count'] = total_odd_pages
        combined_page_info['even_pages_count'] = total_even_pages
        combined_page_info['total_combined_pages'] = total_combined_pages
        
        # Step 5: Split combined PDF into 20-page chunks
        print(f"\n{'='*60}")
        print("Step 5: Splitting combined PDF into 20-page chunks")
        print(f"{'='*60}\n")
        
        combined_chunks = split_pdf_into_chunks(combined_path, chunk_size=20, output_dir=output_dir)
        combined_page_info['chunks'] = [os.path.relpath(chunk) for chunk in combined_chunks]
        
        return combined_path, combined_path, combined_page_info
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")


def print_pdf(pdf_path, printer_name=None):
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
        # Windows printing using PowerShell or default print verb
        try:
            import subprocess
            if printer_name:
                # Use PowerShell to print with specific printer
                ps_cmd = f'Start-Process -FilePath "{pdf_path}" -Verb Print -ArgumentList "/d:{printer_name}"'
                cmd = ["powershell", "-Command", ps_cmd]
            else:
                # Use default print action
                import os
                os.startfile(pdf_path, "print")
                print(f"Print job sent to default printer!")
                return
        except Exception as e:
            print(f"Error with Windows printing: {e}")
            print("Trying alternative method...")
            # Fallback: try using the print command
            if printer_name:
                cmd = ["print", "/D:", printer_name, pdf_path]
            else:
                cmd = ["print", pdf_path]
    else:
        print(f"Unsupported operating system: {system}")
        return
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Print job sent successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error printing: {e}")
    except FileNotFoundError:
        print("Print command not found. Please install printing utilities.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_processor.py <input_pdf> [output_dir]")
        sys.exit(1)
    
    input_pdf = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "."
    
    if not os.path.exists(input_pdf):
        print(f"Error: File not found: {input_pdf}")
        sys.exit(1)
    
    process_pdf(input_pdf, output_dir)

