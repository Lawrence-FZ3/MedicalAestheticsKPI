"""
Documents router — /documents/
Upload, store, parse, download, and send documents to the AI pipeline.
"""
import os
import uuid
import shutil
from datetime import date, datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from backend.auth import verify_token
from backend.audit import log_action
from backend.airtable_client import get_documents_table
from backend.integrations.document_parser import parse_document
from backend.agents.orchestrator import run_pipeline
from backend.config import get_settings

router = APIRouter(prefix="/documents", tags=["Documents"])
settings = get_settings()

UPLOAD_DIR = Path(settings.upload_dir)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".pptx", ".ppt", ".docx", ".doc", ".md", ".markdown", ".txt", ".text"}


@router.post("/upload", summary="Upload and parse a document")
async def upload_document(
    file: UploadFile = File(...),
    category: str = Form("Other"),
    notes: str = Form(""),
    token_data: dict = Depends(verify_token),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{suffix}' not supported.")

    file_bytes = await file.read()
    file_size_kb = round(len(file_bytes) / 1024, 1)

    # Save to disk
    safe_name = f"{uuid.uuid4().hex}{suffix}"
    file_path = UPLOAD_DIR / safe_name
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Parse content
    parsed = parse_document(file_bytes, file.filename)

    # Store metadata + parsed text in Airtable
    table = get_documents_table()
    record = table.create({
        "Document Name": file.filename,
        "Category": category,
        "File Type": suffix.lstrip(".").upper(),
        "File Size KB": file_size_kb,
        "Upload Date": str(date.today()),
        "Uploaded By": token_data.get("sub", "unknown"),
        "File Path": safe_name,
        "Parsed Text": parsed.get("text", "")[:99000],  # Airtable long text limit
        "AI Analysis Run": False,
        "Notes": notes or (parsed.get("error") or ""),
    })

    log_action(
        user=token_data.get("sub", "unknown"),
        action="DOCUMENT_UPLOAD",
        resource="documents",
        resource_id=record["id"],
        detail=f"file={file.filename} category={category} size={file_size_kb}KB",
    )

    return {
        "id": record["id"],
        "filename": file.filename,
        "category": category,
        "file_type": suffix.lstrip(".").upper(),
        "file_size_kb": file_size_kb,
        "parsed_chars": len(parsed.get("text", "")),
        "table_rows": len(parsed.get("tables", [])),
        "parse_error": parsed.get("error"),
        "metadata": parsed.get("metadata", {}),
    }


@router.get("/", summary="List all documents")
def list_documents(
    category: str = None,
    token_data: dict = Depends(verify_token),
):
    table = get_documents_table()
    formula = f"{{Category}}='{category}'" if category else None
    records = table.all(formula=formula, sort=["Upload Date"])
    result = []
    for r in records:
        f = r["fields"]
        result.append({
            "id": r["id"],
            "Document Name": f.get("Document Name", ""),
            "Category": f.get("Category", ""),
            "File Type": f.get("File Type", ""),
            "File Size KB": f.get("File Size KB", 0),
            "Upload Date": f.get("Upload Date", ""),
            "Uploaded By": f.get("Uploaded By", ""),
            "AI Analysis Run": f.get("AI Analysis Run", False),
            "Notes": f.get("Notes", ""),
            "has_parsed_text": bool(f.get("Parsed Text", "")),
        })
    log_action(user=token_data.get("sub", "unknown"), action="DOCUMENTS_LIST", resource="documents", resource_id="all")
    return result


@router.get("/{doc_id}/parsed-text", summary="Get parsed text for a document")
def get_parsed_text(doc_id: str, token_data: dict = Depends(verify_token)):
    table = get_documents_table()
    try:
        record = table.get(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")
    return {
        "id": doc_id,
        "Document Name": record["fields"].get("Document Name", ""),
        "Parsed Text": record["fields"].get("Parsed Text", ""),
    }


@router.get("/{doc_id}/download", summary="Download original file")
def download_document(doc_id: str, token_data: dict = Depends(verify_token)):
    table = get_documents_table()
    try:
        record = table.get(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    safe_name = record["fields"].get("File Path", "")
    file_path = UPLOAD_DIR / safe_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk.")

    original_name = record["fields"].get("Document Name", safe_name)
    log_action(
        user=token_data.get("sub", "unknown"),
        action="DOCUMENT_DOWNLOAD",
        resource="documents",
        resource_id=doc_id,
        detail=f"file={original_name}",
    )
    return FileResponse(path=str(file_path), filename=original_name)


@router.post("/{doc_id}/analyze", summary="Send document to AI pipeline")
def analyze_document(
    doc_id: str,
    background_tasks: BackgroundTasks,
    send_email: bool = True,
    token_data: dict = Depends(verify_token),
):
    """Parse the stored document and run it through the 3-agent AI pipeline."""
    table = get_documents_table()
    try:
        record = table.get(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    fields = record["fields"]
    doc_name = fields.get("Document Name", "Document")
    parsed_text = fields.get("Parsed Text", "")
    category = fields.get("Category", "Other")

    if not parsed_text:
        raise HTTPException(status_code=400, detail="No parsed text available. Re-upload the document.")

    # Re-read file for table data if available
    safe_name = fields.get("File Path", "")
    file_path = UPLOAD_DIR / safe_name
    tables_data = []
    if file_path.exists():
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        parsed = parse_document(file_bytes, doc_name)
        tables_data = parsed.get("tables", [])

    # Build data payload for agents: prefer table rows, fall back to text chunks
    if tables_data:
        data_payload = tables_data[:500]  # cap at 500 rows
        context = f"Category: {category}. Document: {doc_name}. This is structured tabular data extracted from the file."
    else:
        # Split text into chunks as pseudo-records
        lines = [l.strip() for l in parsed_text.split("\n") if l.strip()]
        data_payload = [{"line": l} for l in lines[:300]]
        context = f"Category: {category}. Document: {doc_name}. This is text content extracted from the file. Analyze it for financial insights, key terms, obligations, or patterns."

    def _run_and_flag(doc_id: str, data_payload, context, doc_name, send_email):
        run_pipeline(raw_data=data_payload, data_label=doc_name, context=context, send_email=send_email)
        table.update(doc_id, {"AI Analysis Run": True})

    background_tasks.add_task(_run_and_flag, doc_id, data_payload, context, doc_name, send_email)

    log_action(
        user=token_data.get("sub", "unknown"),
        action="DOCUMENT_AI_ANALYSIS",
        resource="documents",
        resource_id=doc_id,
        detail=f"file={doc_name}",
    )
    return {"status": "started", "message": f"AI pipeline running on '{doc_name}'. Check the AI Agents page for results."}


@router.delete("/{doc_id}", summary="Delete a document")
def delete_document(doc_id: str, token_data: dict = Depends(verify_token)):
    table = get_documents_table()
    try:
        record = table.get(doc_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Document not found")

    safe_name = record["fields"].get("File Path", "")
    file_path = UPLOAD_DIR / safe_name
    if file_path.exists():
        file_path.unlink()

    table.delete(doc_id)
    log_action(
        user=token_data.get("sub", "unknown"),
        action="DOCUMENT_DELETE",
        resource="documents",
        resource_id=doc_id,
        detail=f"file={record['fields'].get('Document Name','')}",
    )
    return {"deleted": doc_id}
