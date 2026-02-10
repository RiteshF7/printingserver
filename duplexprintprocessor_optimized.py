"""
PDF Duplex Print Processor

Provides utilities for PDF manipulation and a main duplex print processor.
All individual operations (remove pages, rotate, add blank, add numbers)
are available as standalone functions for the web app.
"""

from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
import os
import io


# ---------------------------------------------------------------------------
# Core Utilities
# ---------------------------------------------------------------------------

def _clone_page(page):
    """Clone a PDF page to avoid modifying the original."""
    writer = PdfWriter()
    writer.add_page(page)
    buf = io.BytesIO()
    writer.write(buf)
    buf.seek(0)
    return PdfReader(buf).pages[0]


def _page_number_xy(position, page_width, page_height, font_size):
    """Return (x, y) coordinates for a page number label."""
    margin = 20
    positions = {
        'bottom_right': (page_width - margin - font_size * 2, margin),
        'bottom_left':  (margin, margin),
        'top_right':    (page_width - margin - font_size * 2, page_height - margin - font_size),
        'top_left':     (margin, page_height - margin - font_size),
        'bottom_center': (page_width / 2 - font_size * 1.5, margin),
        'top_center':    (page_width / 2 - font_size * 1.5, page_height - margin - font_size),
    }
    return positions.get(position, positions['bottom_right'])


def _add_page_number(page, number, font_size=12, position='bottom_right'):
    """Overlay a page number on a PDF page (mutates *page* in place)."""
    w = float(page.mediabox.width)
    h = float(page.mediabox.height)

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(w, h))
    x, y = _page_number_xy(position, w, h, font_size)
    c.setFont("Helvetica", font_size)
    c.drawString(x, y, str(number))
    c.save()

    buf.seek(0)
    page.merge_page(PdfReader(buf).pages[0])


def _read_pdf(path):
    """Read a PDF, raising clear errors if the file is missing or empty."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"PDF not found: {path}")
    reader = PdfReader(path)
    if len(reader.pages) == 0:
        raise ValueError("The PDF file is empty")
    return reader


def _write_pdf(writer, path):
    """Write a PdfWriter to disk."""
    with open(path, 'wb') as f:
        writer.write(f)


def _auto_output_path(input_path, suffix):
    """Generate an output path by appending *suffix* before the extension."""
    base, ext = os.path.splitext(input_path)
    return f"{base}_{suffix}{ext}"


# ---------------------------------------------------------------------------
# Individual Operations  (used by the Flask web app)
# ---------------------------------------------------------------------------

def remove_first_last_page(input_path, output_path=None):
    """Remove the first and last pages from a PDF."""
    reader = _read_pdf(input_path)
    total = len(reader.pages)
    if total <= 2:
        raise ValueError(
            f"PDF has only {total} page(s). Need at least 3 to remove first and last."
        )

    output_path = output_path or _auto_output_path(input_path, 'first_last_removed')
    writer = PdfWriter()
    for i in range(1, total - 1):
        writer.add_page(reader.pages[i])
    _write_pdf(writer, output_path)
    return output_path


def rotate_all_pages(input_path, angle, output_path=None):
    """Rotate every page in a PDF by *angle* degrees (90 / 180 / 270)."""
    if angle not in (90, 180, 270):
        raise ValueError("Angle must be 90, 180, or 270 degrees")

    reader = _read_pdf(input_path)
    output_path = output_path or _auto_output_path(input_path, 'rotated')
    writer = PdfWriter()
    for page in reader.pages:
        cloned = _clone_page(page)
        cloned.rotate(angle)
        writer.add_page(cloned)
    _write_pdf(writer, output_path)
    return output_path


def add_blank_page_if_odd(input_path, output_path=None):
    """Append a blank page if the current page count is odd."""
    reader = _read_pdf(input_path)
    output_path = output_path or _auto_output_path(input_path, 'blank_added')
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    if len(reader.pages) % 2 == 1:
        first = reader.pages[0]
        writer.add_blank_page(
            width=float(first.mediabox.width),
            height=float(first.mediabox.height),
        )
    _write_pdf(writer, output_path)
    return output_path


def add_page_numbers(input_path, output_path=None, font_size=12, position='bottom_right'):
    """Add sequential page numbers to every page of a PDF."""
    reader = _read_pdf(input_path)
    output_path = output_path or _auto_output_path(input_path, 'numbered')
    writer = PdfWriter()
    for idx, page in enumerate(reader.pages):
        _add_page_number(page, idx + 1, font_size, position)
        writer.add_page(page)
    _write_pdf(writer, output_path)
    return output_path


# ---------------------------------------------------------------------------
# Main Duplex Print Processor
# ---------------------------------------------------------------------------

def duplex_print_processor_optimized(
    input_pdf_path,
    output_pdf_path=None,
    rotation_angle=180,
    font_size=12,
    remove_first_last=True,
):
    """
    Prepare a PDF for duplex printing in a single pass.

    Steps
    -----
    1. Optionally remove first and last pages.
    2. Add page numbers (sequential, 1-indexed).
    3. Rotate odd-positioned pages (1st, 3rd, 5th …) for the duplex flip.
    4. Append a blank page when the total is odd so every sheet has two sides.

    Parameters
    ----------
    input_pdf_path : str
        Path to the source PDF.
    output_pdf_path : str, optional
        Destination path.  Auto-generated with a ``_duplex_processed_optimized``
        suffix when *None*.
    rotation_angle : int
        Degrees to rotate odd pages (90 / 180 / 270).
    font_size : int
        Font size for the page-number overlay.
    remove_first_last : bool
        Drop the first and last pages before processing.

    Returns
    -------
    str
        Path to the written output PDF.
    """
    reader = _read_pdf(input_pdf_path)

    if rotation_angle not in (90, 180, 270):
        raise ValueError("Rotation angle must be 90, 180, or 270 degrees")

    output_pdf_path = output_pdf_path or _auto_output_path(
        input_pdf_path, 'duplex_processed_optimized'
    )

    total = len(reader.pages)

    # --- Step 1: select pages ------------------------------------------------
    if remove_first_last:
        if total <= 2:
            raise ValueError(
                f"PDF has {total} page(s). Need at least 3 to remove first and last."
            )
        pages = [reader.pages[i] for i in range(1, total - 1)]
    else:
        pages = list(reader.pages)

    page_count = len(pages)
    width = float(pages[0].mediabox.width)
    height = float(pages[0].mediabox.height)

    # --- Step 2-3: number, rotate, write -------------------------------------
    writer = PdfWriter()
    for i, page in enumerate(pages):
        cloned = _clone_page(page)

        # Page number (1-indexed)
        _add_page_number(cloned, i + 1, font_size)

        # Rotate odd-positioned pages (positions 1, 3, 5, … → indices 0, 2, 4, …)
        if i % 2 == 0:
            cloned.rotate(rotation_angle)

        writer.add_page(cloned)

    # --- Step 4: blank page for odd totals -----------------------------------
    if page_count % 2 == 1:
        writer.add_blank_page(width=width, height=height)

    _write_pdf(writer, output_pdf_path)
    return output_pdf_path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print(
            "Usage: python duplexprintprocessor_optimized.py <input_pdf> "
            "[output_pdf] [rotation_angle] [font_size]"
        )
        print("Rotation angle: 90, 180, or 270 (default 180)")
        print("Font size: default 12")
        sys.exit(1)

    _input = sys.argv[1]
    _output = sys.argv[2] if len(sys.argv) > 2 else None

    _angle = 180
    if len(sys.argv) > 3:
        try:
            _angle = int(sys.argv[3])
        except ValueError:
            print("Error: rotation angle must be 90, 180, or 270")
            sys.exit(1)

    _font = 12
    if len(sys.argv) > 4:
        try:
            _font = int(sys.argv[4])
        except ValueError:
            print("Warning: invalid font size, using default 12")

    try:
        result = duplex_print_processor_optimized(_input, _output, _angle, _font)
        print(f"Success! Processed PDF saved to: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
