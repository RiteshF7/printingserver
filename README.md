## Print-Ready PDF Batcher (manual duplex, 20-page batches)

This directory contains a standalone script implementing:
- Per-PDF cleanup: remove first+last pages, insert a generated title page, then pad to an even page count.
- Global merge into a master sequence.
- Split into batches of 20 pages.
- Per-batch manual duplex optimization:
  - odd pages (1,3,5,...) reversed (fronts)
  - even pages (2,4,6,...) rotated 180° (backs)

### Install

From repo root:

```bash
python -m pip install -r print_ready_pdf_batcher/requirements.txt
```

### Run

Process PDFs in the repo root, but write outputs into this directory:

```bash
python print_ready_pdf_batcher/print_ready_pdf_batcher.py --input-dir . --output-dir print_ready_pdf_batcher/output
```

Outputs are named `Batch_1.pdf`, `Batch_2.pdf`, ...

### Notes

- Files with fewer than 3 pages are skipped (cannot safely remove first+last).
- To avoid re-processing outputs, files named `Batch_*.pdf` (and a few common merged names) are ignored as inputs.

