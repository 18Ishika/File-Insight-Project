import pandas as pd
import re
import os
from ai.describer import describe_data

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
    top5=df.head().to_dict(orient="records")
    summary=describe_data(list(df.columns), top5)
    

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
        "cleaned_file_path": proc_file_path,
        "top5": top5,
        "summary": summary
    }

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4

def generate_pdf_report(result,original_filename):
    name, _ = os.path.splitext(original_filename)
    report_filename = f"report_{name}.pdf"

    output_path = os.path.join("reports", report_filename)

    summary = result["summary"]
    changes = [
        f"Removed {result['removed_duplicates']} duplicate rows.",
        f"Removed {result['empty_rows_removed']} empty rows.",
        f"Removed {result['empty_columns']} empty columns."
    ]
    sample_data = result['top5']
    doc = SimpleDocTemplate(output_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("📊 Data Cleaning Report", styles["Title"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Dataset Summary</b>", styles["Heading2"]))
    elements.append(Paragraph(summary, styles["Normal"]))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("<b>Cleaning Actions</b>", styles["Heading2"]))
    for change in changes:
        elements.append(Paragraph(f"- {change}", styles["Normal"]))

    elements.append(Spacer(1, 12))
    elements.append(Paragraph("<b>Sample Cleaned Data</b>", styles["Heading2"]))

    headers = list(sample_data[0].keys())
    rows = [list(row.values()) for row in sample_data]
    table_data = [headers] + rows
    table = Table(table_data)

    elements.append(table)

    doc.build(elements)
