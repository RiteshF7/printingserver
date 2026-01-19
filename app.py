"""
Flask web application for PDF duplex printing workflow
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import json
import tempfile
import threading
import time
from pdf_processor import process_pdf, process_multiple_pdfs, print_pdf, clone_page
from printer_reverse import reverse_page, manual_reverse_instructions
from pypdf import PdfReader, PdfWriter
import logging

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create uploads directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'output'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle PDF file upload and process it"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'error': 'File must be a PDF'}), 400
        
        # Save uploaded file
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        # Get options from form data
        remove_first_last = request.form.get('remove_first_last', 'true').lower() == 'true'
        add_watermarks = request.form.get('add_watermarks', 'true').lower() == 'true'
        
        # Process the PDF
        odd_path, even_path, page_info = process_pdf(filepath, OUTPUT_FOLDER, add_watermarks=add_watermarks, remove_first_last=remove_first_last)
        
        # Convert paths to relative for web access
        page_info['odd_output'] = os.path.relpath(odd_path)
        page_info['even_output'] = os.path.relpath(even_path)
        
        return jsonify({
            'success': True,
            'message': 'PDF processed successfully',
            'page_info': page_info
        })
    
    except Exception as e:
        logger.error(f"Error processing PDF: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/print', methods=['POST'])
def print_pdf_endpoint():
    """Handle print requests"""
    try:
        data = request.json
        phase = data.get('phase')  # 'phase1' or 'phase2'
        pdf_path = data.get('pdf_path')
        printer_name = data.get('printer_name')
        
        if not phase or not pdf_path:
            return jsonify({'error': 'Missing phase or pdf_path'}), 400
        
        # Construct full path
        full_path = os.path.join(OUTPUT_FOLDER, os.path.basename(pdf_path))
        
        if not os.path.exists(full_path):
            return jsonify({'error': 'PDF file not found'}), 404
        
        # Print the PDF
        print_pdf(full_path, printer_name)
        
        return jsonify({
            'success': True,
            'message': f'Print job sent for {phase}'
        })
    
    except Exception as e:
        logger.error(f"Error printing PDF: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/reverse', methods=['POST'])
def reverse_page_endpoint():
    """Handle page reverse/retract requests"""
    try:
        data = request.json
        printer_name = data.get('printer_name')
        copies = data.get('copies', 1)
        
        # Attempt to reverse the page
        success = reverse_page(printer_name, copies)
        
        return jsonify({
            'success': success,
            'message': 'Reverse command sent' if success else 'Manual reverse required - see instructions'
        })
    
    except Exception as e:
        logger.error(f"Error reversing page: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/upload-multiple', methods=['POST'])
def upload_multiple_files():
    """Handle multiple PDF file uploads, process them, and merge results"""
    try:
        if 'files[]' not in request.files:
            return jsonify({'error': 'No files provided'}), 400
        
        files = request.files.getlist('files[]')
        
        if not files or files[0].filename == '':
            return jsonify({'error': 'No files selected'}), 400
        
        # Validate and save all PDFs
        saved_paths = []
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'error': f'File {file.filename} is not a PDF'}), 400
            
            # Save uploaded file
            filepath = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(filepath)
            saved_paths.append(filepath)
        
        # Get options from form data
        remove_first_last = request.form.get('remove_first_last', 'true').lower() == 'true'
        add_watermarks = request.form.get('add_watermarks', 'true').lower() == 'true'
        
        # Process all PDFs and merge them
        odd_path, even_path, page_info = process_multiple_pdfs(saved_paths, OUTPUT_FOLDER, add_watermarks=add_watermarks, remove_first_last=remove_first_last)
        
        # Convert paths to relative for web access
        page_info['odd_output'] = os.path.relpath(odd_path)
        page_info['even_output'] = os.path.relpath(even_path)
        
        return jsonify({
            'success': True,
            'message': f'{len(saved_paths)} PDF(s) processed and merged successfully',
            'page_info': page_info
        })
    
    except Exception as e:
        logger.error(f"Error processing multiple PDFs: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    """Download generated PDF files"""
    filepath = os.path.join(OUTPUT_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    return jsonify({'error': 'File not found'}), 404


@app.route('/list-pdfs', methods=['GET'])
def list_pdfs():
    """List all PDF files in the output folder"""
    try:
        pdf_files = []
        if os.path.exists(OUTPUT_FOLDER):
            for filename in os.listdir(OUTPUT_FOLDER):
                if filename.lower().endswith('.pdf'):
                    filepath = os.path.join(OUTPUT_FOLDER, filename)
                    file_size = os.path.getsize(filepath)
                    pdf_files.append({
                        'filename': filename,
                        'size': file_size,
                        'size_mb': round(file_size / (1024 * 1024), 2)
                    })
        
        # Sort by filename
        pdf_files.sort(key=lambda x: x['filename'])
        
        return jsonify({
            'success': True,
            'pdfs': pdf_files
        })
    except Exception as e:
        logger.error(f"Error listing PDFs: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/get-pdf-info', methods=['POST'])
def get_pdf_info():
    """Get information about a PDF file (page count, etc.)"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': 'No filename provided'}), 400
        
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'File not found'}), 404
        
        reader = PdfReader(filepath)
        total_pages = len(reader.pages)
        
        # Check if it's a processed PDF (has odd/even structure)
        # For now, we'll assume any PDF can be split into odd/even
        odd_pages = (total_pages + 1) // 2
        even_pages = total_pages // 2
        
        return jsonify({
            'success': True,
            'filename': filename,
            'total_pages': total_pages,
            'odd_pages': odd_pages,
            'even_pages': even_pages
        })
    except Exception as e:
        logger.error(f"Error getting PDF info: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@app.route('/print-odd-even', methods=['POST'])
def print_odd_even():
    """Print odd or even pages from a selected PDF"""
    try:
        data = request.json
        filename = data.get('filename')
        page_type = data.get('page_type')  # 'odd' or 'even'
        printer_name = data.get('printer_name')
        
        if not filename or not page_type:
            return jsonify({'error': 'Missing filename or page_type'}), 400
        
        if page_type not in ['odd', 'even']:
            return jsonify({'error': 'page_type must be "odd" or "even"'}), 400
        
        filepath = os.path.join(OUTPUT_FOLDER, filename)
        if not os.path.exists(filepath):
            return jsonify({'error': 'PDF file not found'}), 404
        
        # Read the PDF
        reader = PdfReader(filepath)
        total_pages = len(reader.pages)
        
        # Create a temporary PDF with only odd or even pages
        writer = PdfWriter()
        
        if page_type == 'odd':
            # Add odd pages (1-indexed: 1, 3, 5, ...)
            for i in range(0, total_pages, 2):
                writer.add_page(reader.pages[i])
        else:  # even
            # Add even pages (1-indexed: 2, 4, 6, ...)
            for i in range(1, total_pages, 2):
                page = reader.pages[i]
                # Clone and rotate 180° for even pages
                cloned_page = clone_page(page)
                cloned_page.rotate(180)
                writer.add_page(cloned_page)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', dir=OUTPUT_FOLDER)
        temp_path = temp_file.name
        temp_file.close()
        
        with open(temp_path, 'wb') as f:
            writer.write(f)
        
        # Print the temporary file
        print_pdf(temp_path, printer_name)
        
        # Clean up temp file after a delay (in production, use background task)
        def cleanup_temp():
            time.sleep(5)  # Wait 5 seconds
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
        
        threading.Thread(target=cleanup_temp, daemon=True).start()
        
        return jsonify({
            'success': True,
            'message': f'Print job sent for {page_type} pages',
            'pages_printed': len(writer.pages)
        })
    
    except Exception as e:
        logger.error(f"Error printing odd/even pages: {str(e)}", exc_info=True)
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import sys
    # Allow port to be specified via command line or environment variable
    port = 5001  # Default to 5001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}. Using default port 5001.")
    elif os.environ.get('PORT'):
        try:
            port = int(os.environ.get('PORT'))
        except ValueError:
            print(f"Invalid PORT environment variable. Using default port 5001.")
    
    print(f"Starting Flask server on port {port}...")
    app.run(debug=True, host='0.0.0.0', port=port)

