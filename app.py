# app.py
from flask import Flask, request, render_template, redirect, url_for, flash
import os
from preprocessing.cleaner import preprocess_structured_file , generate_pdf_report

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Set the folder to save uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Allow only certain file types (optional)
ALLOWED_EXTENSIONS = {'csv', 'txt', 'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/')
def index():
    return render_template('index.html')
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if file and allowed_file(file.filename):
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        ext=filename.rsplit('.', 1)[1].lower()
        flash('File successfully uploaded','success')
        result = preprocess_structured_file(file_path, ext)
        generate_pdf_report(result)

        print("Original shape:", result["original_shape"])
        print("Processed shape:", result["processed_shape"])
        print("Columns:", result["columns"])
        print("Missing values:", result["missing_summary"])
        print("Summary:", result["summary"])
        return redirect(url_for('index'))
    else:
        return "File type not allowed", 400
if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)