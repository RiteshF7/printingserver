#!/usr/bin/env python3
"""
Print-Ready PDF Batcher

Workflow (per requirements):
  - Iterate PDFs in input dir
  - For each PDF:
      - Remove first and last page
      - Insert a generated title page (filename, 36pt, centered) as new page 1
      - If resulting page count is odd, append a blank page
  - Global merge into a master sequence (in-memory)
  - Split into 20-page batches (last may be smaller)
  - For each batch:
      - Fronts: pages 1,3,5,... (odd-numbered) reversed
      - Backs: pages 2,4,6,... (even-numbered) rotated 180°
      - Output: Reversed fronts first, then rotated backs
"""

from __future__ import annotations

import argparse
import io
import re
from pathlib import Path
from typing import Iterable, List, Sequence, Tuple

from pypdf import PdfReader, PdfWriter
from pypdf._page import PageObject

from reportlab.pdfgen import canvas


def _page_size(page: PageObject) -> Tuple[float, float]:
    return float(page.mediabox.width), float(page.mediabox.height)


def _create_blank_page(width: float, height: float) -> PageObject:
    return PageObject.create_blank_page(width=width, height=height)


def _make_title_page_bytes(
    title: str,
    width: float,
    height: float,
    font_name: str = "Helvetica-Bold",
    font_size: int = 36,
) -> bytes:
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(width, height))
    c.setFont(font_name, font_size)
    c.drawCentredString(width / 2.0, height / 2.0, title)
    c.showPage()
    c.save()
    return buf.getvalue()


def _is_probably_output_pdf(path: Path) -> bool:
    # Avoid accidentally re-processing previously generated output files.
    name = path.name
    if re.fullmatch(r"Batch_\d+\.pdf", name, flags=re.IGNORECASE):
        return True
    if name.lower() in {"master_sequence.pdf", "merged.pdf", "merged_for_printing.pdf"}:
        return True
    return False


def _iter_input_pdfs(input_dir: Path) -> List[Path]:
    pdfs = []
    for p in sorted(input_dir.iterdir()):
        if p.is_file() and p.suffix.lower() == ".pdf" and not _is_probably_output_pdf(p):
            pdfs.append(p)
    return pdfs


def process_single_pdf(path: Path) -> Tuple[List[PageObject], str]:
    """
    Returns (pages, warning). warning is "" when ok.
    """
    try:
        reader = PdfReader(str(path))
    except Exception as e:  # pragma: no cover
        return ([], f"ERROR: failed to read '{path.name}': {e}")

    n = len(reader.pages)
    if n < 3:
        return ([], f"SKIP: '{path.name}' has only {n} page(s); cannot remove first+last safely.")

    content_pages = list(reader.pages[1:-1])
    if not content_pages:
        return ([], f"SKIP: '{path.name}' became empty after removing first+last pages.")

    width, height = _page_size(content_pages[0])
    title_text = path.stem
    title_pdf = _make_title_page_bytes(title_text, width, height)
    title_reader = PdfReader(io.BytesIO(title_pdf))
    title_page = title_reader.pages[0]

    out_pages: List[PageObject] = [title_page]
    out_pages.extend(content_pages)

    # Even-count padding at the per-file level.
    if len(out_pages) % 2 == 1:
        out_pages.append(_create_blank_page(width, height))

    return (out_pages, "")


def batch_duplex_optimize(pages: Sequence[PageObject]) -> List[PageObject]:
    """
    Given a batch (in normal reading order), return pages reordered for manual duplexing:
      - reversed odd pages (1,3,5,...) first
      - then even pages (2,4,6,...) rotated 180°
    """
    fronts = list(pages[0::2])
    backs = list(pages[1::2])

    fronts.reverse()
    for p in backs:
        # pypdf rotates in-place and returns the page.
        p.rotate(180)

    return fronts + backs


def write_pdf(pages: Iterable[PageObject], output_path: Path) -> None:
    writer = PdfWriter()
    for p in pages:
        writer.add_page(p)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as f:
        writer.write(f)


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Process PDFs into duplex-optimized 20-page batches.")
    ap.add_argument(
        "--input-dir",
        default=".",
        help="Directory containing source PDFs (default: current directory).",
    )
    ap.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write Batch_*.pdf into (default: current directory).",
    )
    ap.add_argument("--batch-size", type=int, default=20, help="Pages per batch (default: 20).")
    args = ap.parse_args(argv)

    input_dir = Path(args.input_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    batch_size = int(args.batch_size)
    if batch_size <= 0:
        raise SystemExit("--batch-size must be > 0")

    pdfs = _iter_input_pdfs(input_dir)
    if not pdfs:
        print(f"No input PDFs found in: {input_dir}")
        return 0

    print(f"Found {len(pdfs)} PDF(s) in {input_dir}:")
    for p in pdfs:
        print(f"  - {p.name}")

    master_pages: List[PageObject] = []
    skipped = 0

    for p in pdfs:
        pages, warning = process_single_pdf(p)
        if warning:
            print(warning)
        if not pages:
            skipped += 1
            continue
        master_pages.extend(pages)
        print(f"OK: '{p.name}' -> {len(pages)} page(s) after title/trim/pad.")

    if not master_pages:
        print("No pages produced (all inputs skipped/failed).")
        return 1

    print(f"\nMaster sequence pages: {len(master_pages)} (from {len(pdfs) - skipped} file(s))")

    batch_paths: List[Path] = []
    batch_count = 0
    for i in range(0, len(master_pages), batch_size):
        batch_count += 1
        batch = master_pages[i : i + batch_size]
        optimized = batch_duplex_optimize(batch)
        out_path = output_dir / f"Batch_{batch_count}.pdf"
        write_pdf(optimized, out_path)
        batch_paths.append(out_path)
        print(f"Wrote {out_path} ({len(optimized)} page(s))")

    print(f"\nDone. Wrote {len(batch_paths)} batch file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

