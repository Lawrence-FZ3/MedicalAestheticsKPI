"""
AI Agent Orchestrator — runs the 3-agent pipeline end-to-end.

Pipeline:
  raw data → Agent 1 (Data Cleaner) → Agent 2 (Analyst) → Agent 3 (Strategist) → Email
"""
import time
from datetime import datetime
from .data_cleaner import clean_data
from .analyst import analyze_data
from .strategist import build_strategy
from .email_notifier import send_report


def run_pipeline(
    raw_data: list[dict],
    data_label: str = "Imported Data",
    context: str = "",
    send_email: bool = True,
) -> dict:
    """
    Execute the full 3-agent pipeline.

    Args:
        raw_data:    List of raw records (dicts) to process.
        data_label:  Human-readable label for this dataset (e.g. "AestheticsPro patients").
        context:     Optional domain context passed to the analyst.
        send_email:  Whether to email the final report to info@fivezero3.net.

    Returns a dict with the full pipeline result and timing metadata.
    """
    started_at = datetime.utcnow().isoformat()
    timings: dict[str, float] = {}

    # --- Agent 1: Clean ---
    t0 = time.perf_counter()
    cleaner_result = clean_data(raw_data)
    timings["agent1_cleaner_sec"] = round(time.perf_counter() - t0, 2)

    cleaned_records = cleaner_result.get("cleaned_data", raw_data)
    audit_trail = cleaner_result.get("audit", [])

    # --- Agent 2: Analyze ---
    t1 = time.perf_counter()
    analysis = analyze_data(cleaned_records, context=context)
    timings["agent2_analyst_sec"] = round(time.perf_counter() - t1, 2)

    # --- Agent 3: Strategy ---
    t2 = time.perf_counter()
    strategy = build_strategy(analysis)
    timings["agent3_strategist_sec"] = round(time.perf_counter() - t2, 2)

    # --- Email ---
    email_sent = False
    if send_email:
        t3 = time.perf_counter()
        email_sent = send_report(analysis, strategy, audit_trail, data_label)
        timings["email_sec"] = round(time.perf_counter() - t3, 2)

    return {
        "started_at": started_at,
        "data_label": data_label,
        "records_in": len(raw_data),
        "records_out": len(cleaned_records),
        "audit_trail": audit_trail,
        "analysis": analysis,
        "strategy": strategy,
        "email_sent": email_sent,
        "timings": timings,
    }
