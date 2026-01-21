from PyPDF2 import PdfWriter
import sys


def create_blank_pdf(num_pages=100, output_path='blank_pages.pdf', width=612, height=792):
    """
    Create a PDF with specified number of blank pages using pypdf.
    
    Args:
        num_pages (int): Number of blank pages to create (default: 100)
        output_path (str): Path for the output PDF file (default: 'blank_pages.pdf')
        width (float): Width of each page in points (default: 612, which is US Letter width)
        height (float): Height of each page in points (default: 792, which is US Letter height)
    
    Returns:
        str: Path to the created PDF file
    
    Example:
        >>> create_blank_pdf(100, 'my_blank_pages.pdf')
        'my_blank_pages.pdf'
    """
    # Create a PDF writer
    writer = PdfWriter()
    
    # Add blank pages
    for i in range(num_pages):
        writer.add_blank_page(width=width, height=height)
    
    # Write to output file
    with open(output_path, 'wb') as output_file:
        writer.write(output_file)
    
    print(f"Successfully created PDF with {num_pages} blank pages: {output_path}")
    return output_path


if __name__ == '__main__':
    # Default values
    num_pages = 100
    output_path = 'blank_pages.pdf'
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            num_pages = int(sys.argv[1])
        except ValueError:
            print(f"Error: '{sys.argv[1]}' is not a valid number of pages.")
            print("Usage: python create_blank_pdf.py [num_pages] [output_path]")
            sys.exit(1)
    
    if len(sys.argv) > 2:
        output_path = sys.argv[2]
    
    try:
        result = create_blank_pdf(num_pages, output_path)
        print(f"PDF created successfully: {result}")
    except Exception as e:
        print(f"Error creating PDF: {e}")
        sys.exit(1)
