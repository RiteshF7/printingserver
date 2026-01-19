from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import os
import io


def add_page_numbers(input_pdf_path, output_pdf_path=None, font_size=12, position='bottom_right'):
    """
    Add page numbers to each page of a PDF in the bottom right corner.
    
    Args:
        input_pdf_path (str): Path to the input PDF file
        output_pdf_path (str, optional): Path for the output PDF file. 
                                         If None, creates a new file with '_numbered' suffix.
        font_size (int, optional): Font size for page numbers. Default is 12.
        position (str, optional): Position of page numbers. Options: 'bottom_right', 'bottom_left', 
                                 'top_right', 'top_left', 'bottom_center', 'top_center'. 
                                 Default is 'bottom_right'.
    
    Returns:
        str: Path to the output PDF file
    
    Example:
        >>> add_page_numbers('document.pdf', 'document_numbered.pdf')
        'document_numbered.pdf'
    """
    # Validate input file exists
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input PDF file not found: {input_pdf_path}")
    
    # Generate output path if not provided
    if output_pdf_path is None:
        base_name = os.path.splitext(input_pdf_path)[0]
        extension = os.path.splitext(input_pdf_path)[1]
        output_pdf_path = f"{base_name}_numbered{extension}"
    
    # Read the PDF
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The PDF file is empty")
    
    # Create writer
    writer = PdfWriter()
    
    # Process each page
    for page_num in range(total_pages):
        page = reader.pages[page_num]
        
        # Get page dimensions
        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        
        # Create a text overlay with page number
        overlay_buffer = io.BytesIO()
        overlay_canvas = canvas.Canvas(overlay_buffer, pagesize=(page_width, page_height))
        
        # Calculate position based on option
        x, y = _calculate_position(position, page_width, page_height, font_size)
        
        # Draw page number (1-indexed)
        overlay_canvas.setFont("Helvetica", font_size)
        overlay_canvas.drawString(x, y, str(page_num + 1))
        overlay_canvas.save()
        
        # Merge overlay with original page
        overlay_buffer.seek(0)
        overlay_reader = PdfReader(overlay_buffer)
        overlay_page = overlay_reader.pages[0]
        
        # Merge the pages
        page.merge_page(overlay_page)
        writer.add_page(page)
    
    # Write to output file
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    return output_pdf_path


def _calculate_position(position, page_width, page_height, font_size):
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
        print("Usage: python add_page_numbers.py <input_pdf> [output_pdf] [font_size] [position]")
        print("Example: python add_page_numbers.py document.pdf document_numbered.pdf")
        print("Example: python add_page_numbers.py document.pdf document_numbered.pdf 14 bottom_right")
        print("Position options: bottom_right, bottom_left, top_right, top_left, bottom_center, top_center")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    font_size = 12
    if len(sys.argv) > 3:
        try:
            font_size = int(sys.argv[3])
        except ValueError:
            print("Warning: Invalid font size, using default 12")
    
    position = 'bottom_right'
    if len(sys.argv) > 4:
        position = sys.argv[4]
    
    try:
        result = add_page_numbers(input_file, output_file, font_size, position)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
