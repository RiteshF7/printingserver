from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import os
import io


def duplex_print_processor_optimized(input_pdf_path, output_pdf_path=None, rotation_angle=180, font_size=12):
    """
    Optimized single-loop processor for duplex printing that performs all operations in one pass:
    1. Removing first and last page
    2. Adding blank page if total pages is odd
    3. Adding page numbers to bottom right (intermediate positions)
    4. Reversing odd pages
    5. Rotating odd pages
    
    Args:
        input_pdf_path (str): Path to the input PDF file
        output_pdf_path (str, optional): Path for the output PDF file. 
                                         If None, creates a new file with '_duplex_processed_optimized' suffix.
        rotation_angle (int, optional): Rotation angle for odd pages (default: 180 degrees).
                                        Must be 90, 180, or 270.
        font_size (int, optional): Font size for page numbers. Default is 12.
    
    Returns:
        str: Path to the output PDF file
    
    Raises:
        FileNotFoundError: If the input PDF file does not exist
        ValueError: If the PDF has 2 or fewer pages, or if rotation angle is invalid
    
    Example:
        >>> duplex_print_processor_optimized('document.pdf', 'document_processed.pdf')
        'document_processed.pdf'
    """
    # Validate input file exists
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input PDF file not found: {input_pdf_path}")
    
    # Validate rotation angle
    if rotation_angle not in [90, 180, 270]:
        raise ValueError("Rotation angle must be 90, 180, or 270 degrees")
    
    # Generate output path if not provided
    if output_pdf_path is None:
        base_name = os.path.splitext(input_pdf_path)[0]
        extension = os.path.splitext(input_pdf_path)[1]
        output_pdf_path = f"{base_name}_duplex_processed_optimized{extension}"
    
    # Read the PDF once
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The PDF file is empty")
    
    # Validate: must have at least 3 pages to remove first and last
    if total_pages <= 2:
        raise ValueError(f"PDF has only {total_pages} page(s). Need at least 3 pages to remove first and last.")
    
    # Step 1: Calculate pages to keep (remove first and last)
    # Keep pages at indices 1 to total_pages-2 (0-indexed)
    kept_pages = []
    for i in range(1, total_pages - 1):
        kept_pages.append(reader.pages[i])
    
    kept_page_count = len(kept_pages)
    
    # Step 2: Determine if blank page is needed
    needs_blank_page = (kept_page_count % 2 == 1)
    
    # Get page dimensions from first kept page (for blank page if needed)
    page_width = float(kept_pages[0].mediabox.width) if kept_pages else 0
    page_height = float(kept_pages[0].mediabox.height) if kept_pages else 0
    
    # Step 3: Pre-process - separate odd and even pages, reverse odd pages
    # Track pages with their intermediate positions (1-indexed)
    odd_pages_with_pos = []  # (page, intermediate_position) for odd pages
    even_pages_with_pos = []  # (page, intermediate_position) for even pages
    
    for i in range(kept_page_count):
        intermediate_position = i + 1  # 1-indexed intermediate position
        if i % 2 == 0:  # Odd page (1-indexed)
            odd_pages_with_pos.append((kept_pages[i], intermediate_position))
        else:  # Even page (1-indexed)
            even_pages_with_pos.append((kept_pages[i], intermediate_position))
    
    # Reverse odd pages list (but keep their intermediate positions)
    reversed_odd_pages_with_pos = list(reversed(odd_pages_with_pos))
    
    # Step 4: Single loop - process all pages
    writer = PdfWriter()
    
    # Calculate final page count (before adding blank page)
    final_page_count = kept_page_count
    
    for i in range(final_page_count):
        if i % 2 == 0:  # Odd page position (1-indexed: 1, 3, 5, ...)
            # Get page from reversed odd pages list
            page_index = i // 2
            original_page, intermediate_page_num = reversed_odd_pages_with_pos[page_index]
            
            # Clone the page
            cloned_page = _clone_page(original_page)
            
            # Add page number (intermediate position, before reversal)
            _add_page_number(cloned_page, intermediate_page_num, font_size)
            
            # Rotate the page
            cloned_page.rotate(rotation_angle)
            
            # Add to writer
            writer.add_page(cloned_page)
        else:  # Even page position (1-indexed: 2, 4, 6, ...)
            # Get page from even pages list
            page_index = i // 2
            original_page, intermediate_page_num = even_pages_with_pos[page_index]
            
            # Clone the page
            cloned_page = _clone_page(original_page)
            
            # Add page number (intermediate position)
            _add_page_number(cloned_page, intermediate_page_num, font_size)
            
            # Add to writer (no rotation for even pages)
            writer.add_page(cloned_page)
    
    # Step 5: Add blank page if needed (unnumbered)
    if needs_blank_page:
        writer.add_blank_page(width=page_width, height=page_height)
    
    # Step 6: Write final PDF once
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    return output_pdf_path


def _clone_page(page):
    """
    Clone a PDF page to avoid modifying the original.
    
    Args:
        page: PyPDF2 page object
    
    Returns:
        Cloned page object
    """
    temp_writer = PdfWriter()
    temp_writer.add_page(page)
    page_buffer = io.BytesIO()
    temp_writer.write(page_buffer)
    page_buffer.seek(0)
    temp_reader = PdfReader(page_buffer)
    return temp_reader.pages[0]


def _add_page_number(page, page_number, font_size=12, position='bottom_right'):
    """
    Add a page number to a PDF page in the bottom right corner.
    
    Args:
        page: PyPDF2 page object
        page_number (int): Page number to display
        font_size (int): Font size for page number
        position (str): Position of page number (default: 'bottom_right')
    """
    # Get page dimensions
    page_width = float(page.mediabox.width)
    page_height = float(page.mediabox.height)
    
    # Create a text overlay with page number
    overlay_buffer = io.BytesIO()
    overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
    
    # Calculate position
    x, y = _calculate_page_number_position(position, page_width, page_height, font_size)
    
    # Draw page number
    overlay_canvas.setFont("Helvetica", font_size)
    overlay_canvas.drawString(x, y, str(page_number))
    overlay_canvas.save()
    
    # Merge overlay with original page
    overlay_buffer.seek(0)
    overlay_reader = PdfReader(overlay_buffer)
    overlay_page = overlay_reader.pages[0]
    
    # Merge the pages
    page.merge_page(overlay_page)


def _calculate_page_number_position(position, page_width, page_height, font_size):
    """
    Calculate x, y coordinates for page number based on position option.
    
    Args:
        position (str): Position option
        page_width (float): Width of the page
        page_height (float): Height of the page
        font_size (int): Font size (for margin calculation)
    
    Returns:
        tuple: (x, y) coordinates
    """
    margin = 20  # Margin from edge
    
    if position == 'bottom_right':
        x = page_width - margin - (font_size * 2)  # Approximate width for page numbers
        y = margin
    elif position == 'bottom_left':
        x = margin
        y = margin
    elif position == 'top_right':
        x = page_width - margin - (font_size * 2)
        y = page_height - margin - font_size
    elif position == 'top_left':
        x = margin
        y = page_height - margin - font_size
    elif position == 'bottom_center':
        x = (page_width / 2) - (font_size * 1.5)
        y = margin
    elif position == 'top_center':
        x = (page_width / 2) - (font_size * 1.5)
        y = page_height - margin - font_size
    else:
        # Default to bottom_right
        x = page_width - margin - (font_size * 2)
        y = margin
    
    return x, y


if __name__ == '__main__':
    # Example usage when run as script
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python duplexprintprocessor_optimized.py <input_pdf> [output_pdf] [rotation_angle] [font_size]")
        print("Example: python duplexprintprocessor_optimized.py document.pdf document_processed.pdf 180")
        print("Rotation angle must be 90, 180, or 270 degrees (default: 180)")
        print("Font size for page numbers (default: 12)")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    rotation_angle = 180  # Default rotation angle
    if len(sys.argv) > 3:
        try:
            rotation_angle = int(sys.argv[3])
        except ValueError:
            print("Error: Rotation angle must be a number (90, 180, or 270)")
            sys.exit(1)
    
    font_size = 12  # Default font size
    if len(sys.argv) > 4:
        try:
            font_size = int(sys.argv[4])
        except ValueError:
            print("Warning: Invalid font size, using default 12")
    
    try:
        result = duplex_print_processor_optimized(input_file, output_file, rotation_angle, font_size)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
