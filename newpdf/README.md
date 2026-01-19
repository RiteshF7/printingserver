# PDF Page Remover

Simple tool to remove the first and last page from a PDF file.

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python app.py
```

2. Open your browser and go to: http://localhost:5000

3. Select a PDF file (drag & drop or click to choose)

4. Click "Remove First & Last Page" button

5. The processed PDF will automatically download

## Requirements

- Python 3.7+
- PyPDF2
- Flask

## Note

The PDF must have at least 3 pages to remove the first and last page.
