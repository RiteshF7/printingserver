"""
Create test PDFs with numbered blank pages for verifying duplex logic.
"""

from reportlab.pdfgen import canvas


def create_test_pdf(num_pages, output_path):
    """Create a PDF with *num_pages* blank pages, each labeled with its page number."""
    c = canvas.Canvas(output_path, pagesize=(612, 792))  # US Letter
    for i in range(1, num_pages + 1):
        # Large centered page number
        c.setFont("Helvetica-Bold", 72)
        c.drawCentredString(306, 420, str(i))
        # Small label at bottom-left
        c.setFont("Helvetica", 14)
        c.drawString(30, 20, f"Page {i} of {num_pages}")
        c.showPage()
    c.save()
    print(f"Created {output_path}  ({num_pages} pages)")


if __name__ == "__main__":
    create_test_pdf(9, r"C:\Users\rites\printer\input\test_9_pages.pdf")
    create_test_pdf(10, r"C:\Users\rites\printer\input\test_10_pages.pdf")
