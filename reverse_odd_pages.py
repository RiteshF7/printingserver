from PyPDF2 import PdfReader, PdfWriter
import os
import io


def reverse_odd_pages(input_pdf_path, output_pdf_path=None):
    """
    Reverse the order of odd-numbered pages (1-indexed: pages 1, 3, 5, 7, ...).
    Even pages remain in their original positions.
    
    Args:
        input_pdf_path (str): Path to the input PDF file
        output_pdf_path (str, optional): Path for the output PDF file. 
                                         If None, creates a new file with '_reversed_odd' suffix.
    
    Returns:
        str: Path to the output PDF file
    
    Example:
        >>> reverse_odd_pages('document.pdf', 'document_processed.pdf')
        'document_processed.pdf'
    """
    # Validate input file exists
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input PDF file not found: {input_pdf_path}")
    
    # Generate output path if not provided
    if output_pdf_path is None:
        base_name = os.path.splitext(input_pdf_path)[0]
        extension = os.path.splitext(input_pdf_path)[1]
        output_pdf_path = f"{base_name}_reversed_odd{extension}"
    
    # Read the PDF
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The PDF file is empty")
    
    # Extract odd page indices (1-indexed: pages 1, 3, 5, 7, ... which are indices 0, 2, 4, 6, ...)
    odd_page_indices = list(range(0, total_pages, 2))
    
    # Reverse the order of odd page indices
    odd_page_indices_reversed = list(reversed(odd_page_indices))
    
    # Create writer and rebuild PDF
    writer = PdfWriter()
    
    for i in range(total_pages):
        if i % 2 == 0:  # Odd page (1-indexed: 1, 3, 5, ... are indices 0, 2, 4, ...)
            # Get the original page index from the reversed list
            original_index = odd_page_indices_reversed[i // 2]
            # Clone the page to avoid modifying the original
            original_page = reader.pages[original_index]
            cloned_page = _clone_page(original_page)
            writer.add_page(cloned_page)
        else:  # Even page (2-indexed: 2, 4, 6, ... are indices 1, 3, 5, ...)
            # Keep even pages as they are
            writer.add_page(reader.pages[i])
    
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
    
    if len(sys.argv) < 2:
        print("Usage: python reverse_odd_pages.py <input_pdf> [output_pdf]")
        print("Example: python reverse_odd_pages.py document.pdf document_processed.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = reverse_odd_pages(input_file, output_file)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
