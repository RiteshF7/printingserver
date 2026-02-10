"""
Batch PDF Processor

Processes all PDF files in the input directory for duplex printing
and saves outputs to the output directory.
"""

import os
import glob
import argparse
from duplexprintprocessor_optimized import duplex_print_processor_optimized

# Default configuration
INPUT_DIR = r"C:\Users\rites\printer\input"
OUTPUT_DIR = r"C:\Users\rites\printer\output"
DEFAULT_ROTATION = 180
DEFAULT_FONT_SIZE = 12


def get_pdf_files(directory):
    """Return sorted list of PDF file paths in *directory*."""
    return sorted(glob.glob(os.path.join(directory, "*.pdf")))


def process_pdf(input_path, output_dir, rotation_angle, font_size, remove_first_last):
    """Process a single PDF and return (success, result_or_error)."""
    try:
        base = os.path.splitext(os.path.basename(input_path))[0]
        ext = os.path.splitext(input_path)[1]
        output_path = os.path.join(output_dir, f"{base}_duplex_processed_optimized{ext}")

        result = duplex_print_processor_optimized(
            input_pdf_path=input_path,
            output_pdf_path=output_path,
            rotation_angle=rotation_angle,
            font_size=font_size,
            remove_first_last=remove_first_last,
        )
        return True, result
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(
        description="Batch process PDF files for duplex printing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python batch_process_pdfs.py                    # Remove first/last pages (default)\n"
            "  python batch_process_pdfs.py --keep-all-pages   # Keep all pages\n"
        ),
    )
    parser.add_argument(
        "--keep-all-pages", "--no-remove",
        action="store_true",
        dest="keep_all_pages",
        help="Keep all pages (do not remove first and last page)",
    )
    parser.add_argument(
        "--rotation-angle",
        type=int,
        default=DEFAULT_ROTATION,
        choices=[90, 180, 270],
        help=f"Rotation angle for odd pages (default: {DEFAULT_ROTATION})",
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=DEFAULT_FONT_SIZE,
        help=f"Font size for page numbers (default: {DEFAULT_FONT_SIZE})",
    )
    args = parser.parse_args()

    remove_first_last = not args.keep_all_pages

    print("=" * 60)
    print("Batch PDF Processor")
    print("=" * 60)
    print(f"  Input directory : {INPUT_DIR}")
    print(f"  Output directory: {OUTPUT_DIR}")
    print(f"  Rotation angle  : {args.rotation_angle}°")
    print(f"  Font size       : {args.font_size}")
    print(f"  Remove first/last: {remove_first_last}")
    print("=" * 60 + "\n")

    # Validate directories
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory does not exist: {INPUT_DIR}")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdf_files = get_pdf_files(INPUT_DIR)
    if not pdf_files:
        print(f"No PDF files found in: {INPUT_DIR}")
        return

    print(f"Found {len(pdf_files)} PDF file(s) to process.\n")

    success_count = 0
    error_count = 0

    for i, pdf_path in enumerate(pdf_files, 1):
        name = os.path.basename(pdf_path)
        print(f"[{i}/{len(pdf_files)}] {name}")

        ok, result = process_pdf(
            pdf_path, OUTPUT_DIR, args.rotation_angle, args.font_size, remove_first_last
        )

        if ok:
            print(f"  -> OK: {os.path.basename(result)}")
            success_count += 1
        else:
            print(f"  -> ERROR: {result}")
            error_count += 1

    print("\n" + "=" * 60)
    print("Done!")
    print(f"  Processed: {len(pdf_files)}  |  OK: {success_count}  |  Errors: {error_count}")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
