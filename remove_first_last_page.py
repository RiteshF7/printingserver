from PyPDF2 import PdfReader, PdfWriter
import os


def remove_first_last_page(input_pdf_path, output_pdf_path=None):
    """
    Remove the first and last pages from a PDF file.
    
    Args:
        input_pdf_path (str): Path to the input PDF file
        output_pdf_path (str, optional): Path for the output PDF file. 
                                         If None, creates a new file with '_first_last_removed' suffix.
    
    Returns:
        str: Path to the output PDF file
    
    Raises:
        FileNotFoundError: If the input PDF file does not exist
        ValueError: If the PDF has 2 or fewer pages
    
    Example:
        >>> remove_first_last_page('document.pdf', 'document_processed.pdf')
        'document_processed.pdf'
    """
    # Validate input file exists
    if not os.path.exists(input_pdf_path):
        raise FileNotFoundError(f"Input PDF file not found: {input_pdf_path}")
    
    # Generate output path if not provided
    if output_pdf_path is None:
        base_name = os.path.splitext(input_pdf_path)[0]
        extension = os.path.splitext(input_pdf_path)[1]
        output_pdf_path = f"{base_name}_first_last_removed{extension}"
    
    # Read the PDF
    reader = PdfReader(input_pdf_path)
    total_pages = len(reader.pages)
    
    if total_pages == 0:
        raise ValueError("The PDF file is empty")
    
    # Check if PDF has at least 3 pages
    if total_pages <= 2:
        raise ValueError(f"PDF has only {total_pages} page(s). Need at least 3 pages to remove first and last.")
    
    # Create writer and add pages except first and last
    writer = PdfWriter()
    for i in range(1, total_pages - 1):  # Skip index 0 (first) and last index
        writer.add_page(reader.pages[i])
    
    # Write to output file
    with open(output_pdf_path, 'wb') as output_file:
        writer.write(output_file)
    
    return output_pdf_path


if __name__ == '__main__':
    # Example usage when run as script
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python remove_first_last_page.py <input_pdf> [output_pdf]")
        print("Example: python remove_first_last_page.py document.pdf document_processed.pdf")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = remove_first_last_page(input_file, output_file)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
