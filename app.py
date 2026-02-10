"""
Flask Web App for PDF Tools

Provides a web interface for common PDF operations and duplex print processing.
"""

from flask import Flask, request, send_file, render_template
import os
import tempfile
import zipfile
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge
from duplexprintprocessor_optimized import (
    remove_first_last_page,
    rotate_all_pages,
    add_blank_page_if_odd,
    add_page_numbers,
    duplex_print_processor_optimized,
)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return 'Files too large. Maximum total size is 500 MB.', 413


@app.route('/')
def index():
    return render_template('index.html')


# ---- Feature dispatch -------------------------------------------------------

FEATURE_MAP = {
    'remove_first_last': lambda inp, out, angle: remove_first_last_page(inp, out),
    'rotate':            lambda inp, out, angle: rotate_all_pages(inp, angle, out),
    'add_blank':         lambda inp, out, angle: add_blank_page_if_odd(inp, out),
    'add_numbers':       lambda inp, out, angle: add_page_numbers(inp, out),
    'duplex':            lambda inp, out, angle: duplex_print_processor_optimized(
                             inp, out, rotation_angle=angle),
}


def _process_single_pdf(file, feature, angle=180):
    """Save upload to a temp file, process it, return the output temp path."""
    tmp_in = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    file.save(tmp_in.name)
    tmp_in.close()

    tmp_out = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    tmp_out.close()

    try:
        handler = FEATURE_MAP.get(feature)
        if handler is None:
            raise ValueError(f"Unknown feature: {feature}")
        handler(tmp_in.name, tmp_out.name, angle)
        return tmp_out.name
    except Exception:
        # Clean up output on failure
        if os.path.exists(tmp_out.name):
            os.unlink(tmp_out.name)
        raise
    finally:
        # Always clean up the input temp file
        if os.path.exists(tmp_in.name):
            os.unlink(tmp_in.name)


# ---- Route -------------------------------------------------------------------

@app.route('/process', methods=['POST'])
def process_pdf():
    if 'pdf' not in request.files:
        return 'No file uploaded', 400

    files = [f for f in request.files.getlist('pdf') if f.filename]
    if not files:
        return 'No file selected', 400

    for f in files:
        if not f.filename.lower().endswith('.pdf'):
            return f'Invalid file type: {f.filename}. PDF only.', 400

    feature = request.form.get('feature', 'remove_first_last')
    angle = int(request.form.get('angle', 180))

    processed = []          # list of {'path': ..., 'name': ...}
    cleanup_paths = []

    try:
        for f in files:
            try:
                out_path = _process_single_pdf(f, feature, angle)
                processed.append({
                    'path': out_path,
                    'name': secure_filename(f.filename),
                })
                cleanup_paths.append(out_path)
            except Exception as e:
                # Roll back already-processed files
                for p in processed:
                    if os.path.exists(p['path']):
                        os.unlink(p['path'])
                return f'Error processing {f.filename}: {e}', 500

        # Single file → return PDF directly
        if len(processed) == 1:
            return send_file(
                processed[0]['path'],
                as_attachment=True,
                download_name=f"processed_{processed[0]['name']}",
                mimetype='application/pdf',
            )

        # Multiple files → bundle into a ZIP
        zip_tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        zip_tmp.close()
        cleanup_paths.append(zip_tmp.name)

        with zipfile.ZipFile(zip_tmp.name, 'w', zipfile.ZIP_DEFLATED) as zf:
            for p in processed:
                zf.write(p['path'], f"processed_{p['name']}")

        # Clean individual PDFs (now inside the ZIP)
        for p in processed:
            if os.path.exists(p['path']):
                os.unlink(p['path'])

        return send_file(
            zip_tmp.name,
            as_attachment=True,
            download_name='processed_pdfs.zip',
            mimetype='application/zip',
        )

    except ValueError as e:
        _cleanup(cleanup_paths)
        return str(e), 400
    except Exception as e:
        _cleanup(cleanup_paths)
        return f'Error processing PDF: {e}', 500


def _cleanup(paths):
    for p in paths:
        if os.path.exists(p):
            os.unlink(p)


# ---- Main --------------------------------------------------------------------

if __name__ == '__main__':
    print('Starting PDF Tools …')
    print('Open http://localhost:5001')
    print('Press Ctrl+C to stop')
    app.run(debug=True, host='0.0.0.0', port=5001)
