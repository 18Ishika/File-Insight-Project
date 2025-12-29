import pandas as pd
import os
from ai.describer import describe_data

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors


# ===================== DATA PREPROCESSING =====================

def preprocess_structured_file(file_path, ext):
    # ---------- Load file ----------
    if ext == "csv":
        encodings = ["utf-8", "utf-16", "latin1", "cp1252"]
        df = None
        for enc in encodings:
            try:
                df = pd.read_csv(file_path, encoding=enc)
                break
            except Exception:
                pass
        if df is None:
            raise ValueError("Unable to read CSV with supported encodings")
    else:
        df = pd.read_excel(file_path)

    original_shape = df.shape

    # ---------- Clean ----------
    df = df.dropna(axis=1, how="all")

    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^\w]+", "_", regex=True)
    )
    df = df.loc[:, ~df.columns.duplicated()]

    duplicate_rows = df.duplicated().sum()
    df = df.drop_duplicates()

    empty_rows = df.isnull().all(axis=1).sum()
    empty_columns = df.isnull().all(axis=0).sum()
    missing_summary = df.isnull().sum().to_dict()

    df = df.dropna(how="any")

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

    processed_shape = df.shape
    top5 = df.head().to_dict(orient="records")
    summary = describe_data(list(df.columns), top5)

    # ---------- Save cleaned ----------
    os.makedirs("processed", exist_ok=True)
    filename = os.path.basename(file_path)
    cleaned_path = os.path.join("processed", f"pro_{filename}")

    if ext == "csv":
        df.to_csv(cleaned_path, index=False)
    else:
        df.to_excel(cleaned_path, index=False)

    return {
        "original_shape": original_shape,
        "processed_shape": processed_shape,
        "removed_duplicates": int(duplicate_rows),
        "empty_rows_removed": int(empty_rows),
        "empty_columns": int(empty_columns),
        "missing_summary": missing_summary,
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
        "columns": list(df.columns),
        "top5": top5,
        "summary": summary,
        "cleaned_file_path": cleaned_path,
    }


# ===================== PDF REPORT =====================

def generate_pdf_report(result, original_filename):
    os.makedirs("reports", exist_ok=True)

    name, _ = os.path.splitext(original_filename)
    output_path = os.path.join("reports", f"report_{name}.pdf")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        name="Cell",
        fontSize=8,
        leading=10,
        wordWrap="CJK",
    )

    elements = []

    # ---------- Title ----------
    elements.append(Paragraph("Data Cleaning Report", styles["Title"]))
    elements.append(Spacer(1, 14))

    # ---------- Overview ----------
    elements.append(Paragraph("Dataset Overview", styles["Heading2"]))

    overview_table = Table(
        [
            ["Metric", "Value"],
            ["Original Shape", str(result["original_shape"])],
            ["Processed Shape", str(result["processed_shape"])],
            ["Duplicate Rows Removed", result["removed_duplicates"]],
            ["Rows with Missing Values Removed", result["empty_rows_removed"]],
            ["Empty Columns Removed", result["empty_columns"]],
        ],
        colWidths=[220, 220],
    )

    overview_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
    ]))

    elements.append(overview_table)
    elements.append(Spacer(1, 16))

    # ---------- AI Summary ----------
    elements.append(Paragraph("AI Summary", styles["Heading2"]))
    elements.append(Paragraph(result["summary"], styles["Normal"]))
    elements.append(Spacer(1, 16))

    # ---------- Columns ----------
    elements.append(Paragraph("Column Breakdown", styles["Heading2"]))

    col_table = Table(
        [
            ["Type", "Columns"],
            ["Numeric", ", ".join(result["numeric_columns"]) or "None"],
            ["Categorical", ", ".join(result["categorical_columns"]) or "None"],
        ],
        colWidths=[140, 300],
    )

    col_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))

    elements.append(col_table)
    elements.append(Spacer(1, 16))

    # ---------- Sample Data ----------
    elements.append(Paragraph("Sample Cleaned Data (Top 5 Rows)", styles["Heading2"]))

    sample_data = result["top5"]

    if sample_data:
        headers = list(sample_data[0].keys())

        table_data = [
            [Paragraph(h, styles["Normal"]) for h in headers]
        ]

        for row in sample_data:
            table_data.append([
                Paragraph(str(v), cell_style) for v in row.values()
            ])

        page_width = A4[0] - doc.leftMargin - doc.rightMargin
        col_width = page_width / len(headers)

        sample_table = Table(
            table_data,
            colWidths=[col_width] * len(headers),
            repeatRows=1,
        )

        sample_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
        ]))

        elements.append(sample_table)
    else:
        elements.append(Paragraph("No data available after cleaning.", styles["Normal"]))

    doc.build(elements)
    return output_path
