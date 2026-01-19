from PyPDF2 import PdfReader, PdfWriter
import os


def add_blank_page_if_odd(input_pdf_path, output_pdf_path=None):
    """
    Add a blank page at the end of the PDF if the total number of pages is odd.
    If the page count is even, the PDF is copied as-is.
    
    Args:
        input_pdf_path (str): Path to the input PDF file
        output_pdf_path (str, optional): Path for the output PDF file. 
                                         If None, creates a new file with '_blank_page_added' suffix.
    
    Returns:
        str: Path to the output PDF file
    
    Example:
        >>> add_blank_page_if_odd('document.pdf', 'document_processed.pdf')
        'document_processed.pdf'
    """
    # Validate input file exists
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input PDF file not found: {input_pdf_path}")
    
    # Generate output path if not provided
    if output_pdf_path is None:
        base_name = os.path.splitext(input_pdf_path)[0]
        extension = os.path.splitext(input_pdf_path)[1]
        output_pdf_path = f"{base_name}_blank_page_added{extension}"
    
    # Read the PDF
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The PDF file is empty")
    
    # Create writer and copy all pages
    writer = PdfWriter()
    
    for i in range(total_pages):
        writer.add_page(reader.pages[i])
    
    # Add blank page if total pages is odd
    if total_pages % 2 == 1:
        # Get dimensions from the first page to match the size
        first_page = reader.pages[0]
        width = float(first_page.mediabox.width)
        height = float(first_page.mediabox.height)
        
        # Add a blank page with the same dimensions
        writer.add_blank_page(width=width, height=height)
    
    # Write to output file
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    return output_pdf_path


if __name__ == '__main__':
    # Example usage when run as script
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python add_blank_page_if_odd.py <input_pdf> [output_pdf]")
        print("Example: python add_blank_page_if_odd.py document.pdf document_processed.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = add_blank_page_if_odd(input_file, output_file)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
