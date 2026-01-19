from flask import Flask, request, send_file, render_template
import os
import tempfile
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from remove_first_last_page import remove_first_last_page
from reverse_odd_pages import reverse_odd_pages
from rotate_pages import rotate_pages
from add_blank_page_if_odd import add_blank_page_if_odd
from duplexprintprocessor import duplex_print_processor

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return 'File is too large. Maximum file size is 100MB. Please upload a smaller file.', 413

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_pdf():
    if 'pdf' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['pdf']
    if file.filename == '':
        return 'No file selected', 400
    
    if not file.filename.lower().endswith('.pdf'):
        return 'Please upload a PDF file', 400
    
    # Get the selected feature
    feature = request.form.get('feature', 'remove_first_last')
    
    temp_input = None
    temp_output = None
    
    try:
        # Save uploaded file temporarily
        temp_input = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        file.save(temp_input.name)
        temp_input.close()
        
        # Process PDF using the extracted function
        temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_output.close()
        
        # Process based on selected feature
        if feature == 'remove_first_last':
            remove_first_last_page(temp_input.name, temp_output.name)
        elif feature == 'reverse_odd':
            reverse_odd_pages(temp_input.name, temp_output.name)
        elif feature == 'rotate':
            angle = int(request.form.get('angle', 180))
            rotate_pages(temp_input.name, angle, temp_output.name)
        elif feature == 'add_blank':
            add_blank_page_if_odd(temp_input.name, temp_output.name)
        elif feature == 'duplex':
            angle = int(request.form.get('angle', 180))
            duplex_print_processor(temp_input.name, temp_output.name, angle)
        else:
            raise ValueError(f'Unknown feature: {feature}')
        
        # Clean up input temp file
        os.unlink(temp_input.name)
        temp_input = None
        
        # Send file to user
        return send_file(
            temp_output.name,
            as_attachment=True,
            download_name=f'processed_{secure_filename(file.filename)}',
            mimetype='application/pdf'
        )
    
    except ValueError as e:
        # Clean up temp files if they exist
        if temp_input and os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        if temp_output and os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        return str(e), 400
    except Exception as e:
        # Clean up temp files if they exist
        if temp_input and os.path.exists(temp_input.name):
            os.unlink(temp_input.name)
        if temp_output and os.path.exists(temp_output.name):
            os.unlink(temp_output.name)
        return f'Error processing PDF: {str(e)}', 500

if __name__ == '__main__':
    print('Starting PDF Tools...')
    print('Open your browser and go to: http://localhost:5001')
    print('Press Ctrl+C to stop the server')
    app.run(debug=True, host='0.0.0.0', port=5001)
