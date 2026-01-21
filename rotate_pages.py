from PyPDF2 import PdfReader, PdfWriter
import os
import io


def rotate_pages(input_pdf_path, angle, output_pdf_path=None):
    """
    Rotate all pages in a PDF by the specified angle.
    
    Args:
        input_pdf_path (str): Path to the input PDF file
        angle (int): Rotation angle in degrees (must be a multiple of 90: 90, 180, 270)
        output_pdf_path (str, optional): Path for the output PDF file. 
                                         If None, creates a new file with '_rotated' suffix.
    
    Returns:
        str: Path to the output PDF file
    
    Example:
        >>> rotate_pages('document.pdf', 180, 'document_rotated.pdf')
        'document_rotated.pdf'
    """
    # Validate input file exists
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input PDF file not found: {input_pdf_path}")
    
    # Validate angle
    if angle not in [90, 180, 270]:
        raise ValueError("Angle must be 90, 180, or 270 degrees")
    
    # Generate output path if not provided
    if output_pdf_path is None:
        base_name = os.path.splitext(input_pdf_path)[0]
        extension = os.path.splitext(input_pdf_path)[1]
        output_pdf_path = f"{base_name}_rotated{extension}"
    
    # Read the PDF
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The PDF file is empty")
    
    # Create writer and process all pages
    writer = PdfWriter()
    
    for i in range(total_pages):
        # Clone the page to avoid modifying the original
        original_page = reader.pages[i]
        cloned_page = _clone_page(original_page)
        # Rotate the cloned page
        cloned_page.rotate(angle)
        writer.add_page(cloned_page)
    
    # Write to output file
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


if __name__ == '__main__':
    # Example usage when run as script
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python rotate_pages.py <input_pdf> <angle> [output_pdf]")
        print("Example: python rotate_pages.py document.pdf 180 document_rotated.pdf")
        print("Angle must be 90, 180, or 270 degrees")
        sys.exit(1)
    
    input_file = sys.argv[1]
    try:
        angle = int(sys.argv[2])
    except ValueError:
        print("Error: Angle must be a number (90, 180, or 270)")
        sys.exit(1)
    
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    try:
        result = rotate_pages(input_file, angle, output_file)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
