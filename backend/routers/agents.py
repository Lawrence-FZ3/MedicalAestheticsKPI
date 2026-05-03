"""
AI Agent Pipeline router — /agents/
Triggers the 3-agent pipeline on demand with arbitrary data sources.
"""
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Any
from backend.auth import verify_token
from backend.audit import log_action
from backend.agents.orchestrator import run_pipeline

router = APIRouter(prefix="/agents", tags=["AI Agents"])


class PipelineRequest(BaseModel):
    data: list[dict[str, Any]]
    data_label: str = "Imported Data"
    context: str = ""
    send_email: bool = True


class PipelineStatus(BaseModel):
    job_id: str
    status: str
    message: str


# In-memory job store (production: use Redis or Airtable)
_jobs: dict[str, dict] = {}


def _run_and_store(job_id: str, req: PipelineRequest):
    try:
        result = run_pipeline(
            raw_data=req.data,
            data_label=req.data_label,
            context=req.context,
            send_email=req.send_email,
        )
        _jobs[job_id] = {"status": "complete", "result": result}
    except Exception as exc:
        _jobs[job_id] = {"status": "error", "error": str(exc)}


@router.post("/run", summary="Trigger the 3-agent AI pipeline")
def trigger_pipeline(
    req: PipelineRequest,
    background_tasks: BackgroundTasks,
    token_data: dict = Depends(verify_token),
):
    """
    Start the AI pipeline in the background.
    Returns a job_id to poll via GET /agents/status/{job_id}.
    """
    import uuid
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "running"}

    log_action(
        user=token_data.get("sub", "unknown"),
        action="AI_PIPELINE_TRIGGERED",
        resource="agents",
        resource_id=job_id,
        detail=f"label={req.data_label} records={len(req.data)} email={req.send_email}",
    )

    background_tasks.add_task(_run_and_store, job_id, req)
    return {"job_id": job_id, "status": "running", "message": "Pipeline started. Poll /agents/status/{job_id}"}


@router.get("/status/{job_id}", summary="Poll pipeline job status")
def job_status(job_id: str, token_data: dict = Depends(verify_token)):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/run-sync", summary="Run pipeline synchronously (small datasets only)")
def run_pipeline_sync(
    req: PipelineRequest,
    token_data: dict = Depends(verify_token),
):
    """Blocking pipeline call — use only for datasets < 50 records."""
    if len(req.data) > 200:
        raise HTTPException(status_code=400, detail="Dataset too large for sync mode. Use /agents/run instead.")

    log_action(
        user=token_data.get("sub", "unknown"),
        action="AI_PIPELINE_SYNC",
        resource="agents",
        resource_id="sync",
        detail=f"label={req.data_label} records={len(req.data)}",
    )

    result = run_pipeline(
        raw_data=req.data,
        data_label=req.data_label,
        context=req.context,
        send_email=req.send_email,
    )
    return result
