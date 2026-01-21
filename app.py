from flask import Flask, request, send_file, render_template
import os
import tempfile
import zipfile
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from remove_first_last_page import remove_first_last_page
from reverse_odd_pages import reverse_odd_pages
from rotate_pages import rotate_pages
from add_blank_page_if_odd import add_blank_page_if_odd
from duplexprintprocessor import duplex_print_processor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max total size (for multiple files)
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return 'Files are too large. Maximum total size is 500MB. Please upload smaller files.', 413

@app.route('/')
def index():
    return render_template('index.html')

def process_single_pdf(file, feature, angle=180):
    """Process a single PDF file and return the output path."""
    temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    file.save(temp_input.name)
    temp_input.close()
    
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    temp_output.close()
    
    try:
        # Process based on selected feature
        if feature == 'remove_first_last':
            remove_first_last_page(temp_input.name, temp_output.name)
        elif feature == 'reverse_odd':
            reverse_odd_pages(temp_input.name, temp_output.name)
        elif feature == 'rotate':
            rotate_pages(temp_input.name, angle, temp_output.name)
        elif feature == 'add_blank':
            add_blank_page_if_odd(temp_input.name, temp_output.name)
        elif feature == 'duplex':
            duplex_print_processor(temp_input.name, temp_output.name, angle)
        else:
            raise ValueError(f'Unknown feature: {feature}')
        
        # Clean up input temp file
        os.unlink(temp_input.name)
        
        return temp_output.name
    except Exception as e:
        # Clean up on error
        if os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        if os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        raise

@app.route('/process', methods=['POST'])
def process_pdf():
    if 'pdf' not in request.files:
        return 'No file uploaded', 400
    
    # Get all uploaded files (support multiple)
    files = request.files.getlist('pdf')
    
    # Filter out empty files
    files = [f for f in files if f.filename != '']
    
    if not files:
        return 'No file selected', 400
    
    # Validate all files are PDFs
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            return f'Invalid file type: {file.filename}. Please upload PDF files only.', 400
    
    # Get the selected feature
    feature = request.form.get('feature', 'remove_first_last')
    angle = int(request.form.get('angle', 180))
    
    processed_files = []
    temp_files_to_cleanup = []
    
    try:
        # Process each file
        for file in files:
            try:
                output_path = process_single_pdf(file, feature, angle)
                processed_files.append({
                    'path': output_path,
                    'original_name': secure_filename(file.filename)
                })
                temp_files_to_cleanup.append(output_path)
            except Exception as e:
                # Clean up already processed files
                for pf in processed_files:
                    if os.path.exists(pf['path']):
                        os.unlink(pf['path'])
                return f'Error processing {file.filename}: {str(e)}', 500
        
        # If single file, return it directly
        if len(processed_files) == 1:
            return send_file(
                processed_files[0]['path'],
                as_attachment=True,
                download_name=f'processed_{processed_files[0]["original_name"]}',
                mimetype='application/pdf'
            )
        
        # If multiple files, create a zip file
        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        zip_path.close()
        temp_files_to_cleanup.append(zip_path.name)
        
        with zipfile.ZipFile(zip_path.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for pf in processed_files:
                zipf.write(pf['path'], f'processed_{pf["original_name"]}')
        
        # Clean up individual PDF files (they're now in the zip)
        for pf in processed_files:
            if os.path.exists(pf['path']):
                os.unlink(pf['path'])
        
        return send_file(
            zip_path.name,
            as_attachment=True,
            download_name='processed_pdfs.zip',
            mimetype='application/zip'
        )
    
    except ValueError as e:
        # Clean up temp files
        for temp_file in temp_files_to_cleanup:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        return str(e), 400
    except Exception as e:
        # Clean up temp files
        for temp_file in temp_files_to_cleanup:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
        return f'Error processing PDF: {str(e)}', 500

if __name__ == '__main__':
    print('Starting PDF Tools...')
    print('Open your browser and go to: http://localhost:5001')
    print('Press Ctrl+C to stop the server')
    app.run(debug=True, host='0.0.0.0', port=5001)
