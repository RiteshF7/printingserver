from remove_first_last_page import remove_first_last_page
from add_blank_page_if_odd import add_blank_page_if_odd
from add_page_numbers import add_page_numbers
from reverse_odd_pages import reverse_odd_pages
from rotate_odd_pages import rotate_odd_pages
import os
import tempfile


def duplex_print_processor(input_pdf_path, output_pdf_path=None, rotation_angle=180):
    """
    Process a PDF for duplex printing by:
    1. Removing first and last page
    2. Adding blank page if total pages is odd
    3. Adding page numbers to bottom right
    4. Reversing odd pages
    5. Rotating odd pages
    
    Args:
        input_pdf_path (str): Path to the input PDF file
        output_pdf_path (str, optional): Path for the output PDF file. 
                                         If None, creates a new file with '_duplex_processed' suffix.
        rotation_angle (int, optional): Rotation angle for odd pages (default: 180 degrees).
                                        Must be 90, 180, or 270.
    
    Returns:
        str: Path to the output PDF file
    
    Raises:
        FileNotFoundError: If the input PDF file does not exist
        ValueError: If the PDF has 2 or fewer pages, or if rotation angle is invalid
    
    Example:
        >>> duplex_print_processor('document.pdf', 'document_processed.pdf')
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
        output_pdf_path = f"{base_name}_duplex_processed{extension}"
    
    # Use temporary files to chain operations
    temp_files = []
    
    try:

        
        # Step 1: Remove first and last page
        temp1 = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp1.close()
        temp_files.append(temp1.name)
        remove_first_last_page(input_pdf_path, temp1.name)
        
        # Step 2: Add blank page if odd
        temp2 = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp2.close()
        temp_files.append(temp2.name)
        add_blank_page_if_odd(temp1.name, temp2.name)
        
        # Step 3: Add page numbers to bottom right
        temp3 = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp3.close()
        temp_files.append(temp3.name)
        add_page_numbers(temp2.name, temp3.name)
        
        # Step 4: Reverse odd pages
        temp4 = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp4.close()
        temp_files.append(temp4.name)
        reverse_odd_pages(temp3.name, temp4.name)
        
        # Step 5: Rotate odd pages
        rotate_odd_pages(temp4.name, rotation_angle, output_pdf_path)
        
        # Clean up temporary files
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        
        return output_pdf_path
    
    except Exception as e:
        # Clean up temporary files on error
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        raise


if __name__ == '__main__':
    # Example usage when run as script
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python duplexprintprocessor.py <input_pdf> [output_pdf] [rotation_angle]")
        print("Example: python duplexprintprocessor.py document.pdf document_processed.pdf 180")
        print("Rotation angle must be 90, 180, or 270 degrees (default: 180)")
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
    
    try:
        result = duplex_print_processor(input_file, output_file, rotation_angle)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
