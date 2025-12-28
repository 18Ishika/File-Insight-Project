from flask import Flask, request, render_template, redirect, url_for, flash, send_file
import os
from preprocessing.cleaner import preprocess_structured_file, generate_pdf_report

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
REPORT_FOLDER = 'reports'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx'}

# ----------------------------------------
# Utility
# ----------------------------------------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ----------------------------------------
# Routes
# ----------------------------------------
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("No file part", "error")
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash("No file selected", "error")
        return redirect(url_for('index'))

    if not allowed_file(file.filename):
        flash("File type not allowed", "error")
        return redirect(url_for('index'))

    # Save uploaded file
    filename = file.filename
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    ext = filename.rsplit('.', 1)[1].lower()

    # Process + generate report
    result = preprocess_structured_file(file_path, ext)
    pdf_path = generate_pdf_report(result, filename)

    report_filename = os.path.basename(pdf_path)

    flash("File processed successfully", "success")

    return render_template(
        "index.html",
        report_filename=report_filename
    )


@app.route('/download-report/<filename>')
def download_report(filename):
    path = os.path.join(REPORT_FOLDER, filename)
    return send_file(path, as_attachment=True)


# ----------------------------------------
# App start
# ----------------------------------------
if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(REPORT_FOLDER, exist_ok=True)
    app.run(debug=True)
