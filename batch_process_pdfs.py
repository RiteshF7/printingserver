"""
Batch PDF Processor
Processes all PDF files in the input directory using duplexprintprocessor_optimized
and saves outputs to the output directory.
"""

import os
import glob
from duplexprintprocessor_optimized import duplex_print_processor_optimized

# Configuration
INPUT_DIR = r"C:\Users\rites\printer\input"
OUTPUT_DIR = r"C:\Users\rites\printer\output"
ROTATION_ANGLE = 180  # Default rotation angle
FONT_SIZE = 12  # Default font size for page numbers


def ensure_output_directory():
    """Create output directory if it doesn't exist."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created output directory: {OUTPUT_DIR}")


def get_pdf_files(input_dir):
    """Get all PDF files from the input directory."""
    pdf_pattern = os.path.join(input_dir, "*.pdf")
    pdf_files = glob.glob(pdf_pattern)
    return sorted(pdf_files)


def process_pdf(input_path, output_dir, rotation_angle=180, font_size=12):
    """
    Process a single PDF file and save to output directory.
    
    Args:
        input_path (str): Path to input PDF file
        output_dir (str): Directory to save output PDF
        rotation_angle (int): Rotation angle for odd pages
        font_size (int): Font size for page numbers
    
    Returns:
        tuple: (success: bool, output_path: str or error_message: str)
    """
    try:
        # Get base filename
        base_name = os.path.basename(input_path)
        name_without_ext = os.path.splitext(base_name)[0]
        extension = os.path.splitext(base_name)[1]
        
        # Create output path
        output_filename = f"{name_without_ext}_duplex_processed_optimized{extension}"
        output_path = os.path.join(output_dir, output_filename)
        
        # Process the PDF
        result_path = duplex_print_processor_optimized(
            input_pdf_path=input_path,
            output_pdf_path=output_path,
            rotation_angle=rotation_angle,
            font_size=font_size
        )
        
        return True, result_path
    
    except FileNotFoundError as e:
        return False, f"File not found: {str(e)}"
    except ValueError as e:
        return False, f"Value error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"


def main():
    """Main function to batch process all PDFs."""
    print("=" * 60)
    print("Batch PDF Processor")
    print("=" * 60)
    print(f"Input directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Rotation angle: {ROTATION_ANGLE} degrees")
    print(f"Font size: {FONT_SIZE}")
    print("=" * 60)
    print()
    
    # Ensure output directory exists
    ensure_output_directory()
    
    # Check if input directory exists
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory does not exist: {INPUT_DIR}")
        print("Please create the directory and add PDF files to process.")
        return
    
    # Get all PDF files
    pdf_files = get_pdf_files(INPUT_DIR)
    
    if not pdf_files:
        print(f"No PDF files found in: {INPUT_DIR}")
        print("Please add PDF files to the input directory.")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s) to process.\n")
    
    # Process each PDF
    success_count = 0
    error_count = 0
    
    for i, pdf_file in enumerate(pdf_files, 1):
        filename = os.path.basename(pdf_file)
        print(f"[{i}/{len(pdf_files)}] Processing: {filename}")
        
        success, result = process_pdf(
            pdf_file,
            OUTPUT_DIR,
            ROTATION_ANGLE,
            FONT_SIZE
        )
        
        if success:
            output_filename = os.path.basename(result)
            print(f"  ✓ Success! Saved to: {output_filename}")
            success_count += 1
        else:
            print(f"  ✗ Error: {result}")
            error_count += 1
        
        print()
    
    # Summary
    print("=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Total files processed: {len(pdf_files)}")
    print(f"Successful: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Output directory: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
