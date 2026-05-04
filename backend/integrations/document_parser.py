"""
Document parser — extracts text and structured data from uploaded files.
Supports: PDF, Excel, PPTX, DOCX, Markdown, plain text.
"""
import io
import json
from pathlib import Path


def parse_document(file_bytes: bytes, filename: str) -> dict:
    """
    Parse any supported file type and return:
      {
        "text": full extracted text (str),
        "tables": list of dicts (for spreadsheet/tabular data),
        "metadata": {page_count, sheet_count, etc.},
        "error": str or None
      }
    """
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            return _parse_pdf(file_bytes)
        elif suffix in (".xlsx", ".xls", ".csv"):
            return _parse_excel(file_bytes, suffix)
        elif suffix in (".pptx", ".ppt"):
            return _parse_pptx(file_bytes)
        elif suffix in (".docx", ".doc"):
            return _parse_docx(file_bytes)
        elif suffix in (".md", ".markdown", ".txt", ".text"):
            return _parse_text(file_bytes)
        else:
            return {"text": "", "tables": [], "metadata": {}, "error": f"Unsupported file type: {suffix}"}
    except Exception as exc:
        return {"text": "", "tables": [], "metadata": {}, "error": str(exc)}


def _parse_pdf(file_bytes: bytes) -> dict:
    import pdfplumber
    text_parts = []
    tables = []
    page_count = 0
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        page_count = len(pdf.pages)
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            if page_text:
                text_parts.append(page_text)
            # Extract tables (great for bank statements)
            for tbl in page.extract_tables():
                if tbl:
                    # First row as headers if it looks like one
                    headers = tbl[0] if tbl[0] else [f"col_{i}" for i in range(len(tbl[0]))]
                    rows = tbl[1:]
                    tables.append([dict(zip(headers, row)) for row in rows if any(row)])
    return {
        "text": "\n\n".join(text_parts),
        "tables": tables,
        "metadata": {"page_count": page_count, "table_count": len(tables)},
        "error": None,
    }


def _parse_excel(file_bytes: bytes, suffix: str) -> dict:
    import pandas as pd
    text_parts = []
    tables = []
    if suffix == ".csv":
        df = pd.read_csv(io.BytesIO(file_bytes))
        sheet_names = ["Sheet1"]
        sheets = {"Sheet1": df}
    else:
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        sheet_names = xl.sheet_names
        sheets = {name: xl.parse(name) for name in sheet_names}

    for sheet_name, df in sheets.items():
        df = df.dropna(how="all").fillna("")
        text_parts.append(f"=== Sheet: {sheet_name} ===\n{df.to_string(index=False)}")
        records = df.to_dict(orient="records")
        if records:
            tables.append({"sheet": sheet_name, "rows": records})

    return {
        "text": "\n\n".join(text_parts),
        "tables": [row for t in tables for row in t["rows"]],  # flatten for AI
        "metadata": {"sheet_count": len(sheet_names), "sheets": sheet_names},
        "error": None,
    }


def _parse_pptx(file_bytes: bytes) -> dict:
    from pptx import Presentation
    prs = Presentation(io.BytesIO(file_bytes))
    text_parts = []
    for i, slide in enumerate(prs.slides, 1):
        slide_texts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                slide_texts.append(shape.text.strip())
        if slide_texts:
            text_parts.append(f"--- Slide {i} ---\n" + "\n".join(slide_texts))
    return {
        "text": "\n\n".join(text_parts),
        "tables": [],
        "metadata": {"slide_count": len(prs.slides)},
        "error": None,
    }


def _parse_docx(file_bytes: bytes) -> dict:
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    tables = []
    for tbl in doc.tables:
        rows = []
        headers = [cell.text.strip() for cell in tbl.rows[0].cells] if tbl.rows else []
        for row in tbl.rows[1:]:
            rows.append(dict(zip(headers, [cell.text.strip() for cell in row.cells])))
        if rows:
            tables.append(rows)
    return {
        "text": "\n".join(paragraphs),
        "tables": [row for t in tables for row in t],
        "metadata": {"paragraph_count": len(paragraphs), "table_count": len(tables)},
        "error": None,
    }


def _parse_text(file_bytes: bytes) -> dict:
    text = file_bytes.decode("utf-8", errors="replace")
    return {
        "text": text,
        "tables": [],
        "metadata": {"char_count": len(text), "line_count": text.count("\n")},
        "error": None,
    }
