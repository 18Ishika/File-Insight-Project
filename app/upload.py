# app.py
from flask import Flask, request, render_template, redirect, url_for, flash
import os

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

        print("Original shape:", result["original_shape"])
        print("Processed shape:", result["processed_shape"])
        print("Columns:", result["columns"])
        print("Missing values:", result["missing_summary"])
        return redirect(url_for('index'))
    else:
        return "File type not allowed", 400
import pandas as pd
import re

def preprocess_structured_file(file_path, ext):
    # ---------- Load file safely ----------
    if ext == "csv":
        encodings = ["utf-8", "utf-16", "latin1", "cp1252"]
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc, header=0)  # ensure first row is header
                break
            except Exception:
                pass
        if df is None:
            raise ValueError("Unable to read CSV file with supported encodings")
    else:
        df = pd.read_excel(file_path, header=0)

    # Drop fully empty columns immediately
    df = df.dropna(axis=1, how='all')

    # ---------- Clean column names ----------
    df.columns = (
        df.columns
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
    )

    # Drop duplicated column names created after cleaning
    df = df.loc[:, ~df.columns.duplicated()]

    # ---------- Drop duplicate rows ----------
    duplicate_rows = df.duplicated().sum()
    df = df.drop_duplicates()

    # ---------- Handle missing values ----------
    empty_rows = df.isnull().all(axis=1).sum()
    empty_columns = df.isnull().all(axis=0).sum()
    missing_summary = df.isnull().sum().to_dict()
    df = df.dropna(how='any') 

    # ---------- Column types ----------
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    processed_shape = df.shape

    # ---------- Save cleaned file ----------
    if not os.path.exists('processed'):
        os.makedirs('processed')
    filename = os.path.basename(file_path)
    proc_file_path = os.path.join('processed', f'pro_{filename}')
    if ext == "csv":
        df.to_csv(proc_file_path, index=False)
    else:
        df.to_excel(proc_file_path, index=False)

    return {
        "original_shape": df.shape,
        "processed_shape": processed_shape,
        "removed_duplicates": int(duplicate_rows),
        "empty_rows_removed": int(empty_rows),
        "empty_columns": int(empty_columns),
        "missing_summary": missing_summary,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "columns": list(df.columns),
        "cleaned_file_path": proc_file_path
    }

if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True)