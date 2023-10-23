import os
import secrets
import zipfile
from flask import Flask, flash, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename

from resume_parser import ResumeParser

# Configurations
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'pdf', 'zip'}  # Now includes ZIP files

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000  # 16MB max limit
app.secret_key = secrets.token_urlsafe(32)

# Initialize the ResumeParser
parser = ResumeParser(os.getenv("OPENAI_API_KEY"))

# Helper function to check if the uploaded file is allowed
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to upload resume (either single or ZIP of multiple)
@app.route("/", methods=['GET', 'POST'])
@app.route("/resume", methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # If it's a ZIP file, extract it
            if filename.endswith('.zip'):
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(app.config['UPLOAD_FOLDER'])
                    for pdf_name in zip_ref.namelist():
                        if pdf_name.lower().endswith('.pdf'):
                            pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], pdf_name)
                            parser.query_resume(pdf_path)  # Process each PDF file
                return "ZIP file extracted and resumes processed."

            # If it's a single PDF file
            else:
                return redirect(url_for('display_resume', name=filename))
    return render_template('index.html')

# Route to display parsed resume
@app.route('/resume/<name>')
def display_resume(name):
    resume_path = os.path.join(app.config["UPLOAD_FOLDER"], name)
    return parser.query_resume(resume_path)  # Parse and return the resume details

# Entry point
if __name__ == "__main__":
    host = os.getenv("RESUME_PARSER_HOST", '127.0.0.1')
    port = os.getenv("RESUME_PARSER_PORT", '8080')
    assert port.isnumeric(), 'port must be an integer'
    port = int(port)
    app.run(host=host, port=port, debug=True)
