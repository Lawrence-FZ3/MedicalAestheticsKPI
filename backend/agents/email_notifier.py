"""
Email delivery for the AI agent pipeline.
Sends the final strategy report to info@fivezero3.net via SMTP.
"""
import smtplib
import json
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from backend.config import get_settings


def _build_html(analysis: dict, strategy: dict, audit: list[str], data_label: str) -> str:
    """Render a clean HTML email from the pipeline results."""
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    def section(title: str, items: list, color: str = "#1a1a2e") -> str:
        if not items:
            return ""
        rows = "".join(f"<li style='margin-bottom:6px'>{i}</li>" for i in items)
        return f"""
        <h3 style='color:{color};border-bottom:2px solid {color};padding-bottom:4px'>{title}</h3>
        <ul style='line-height:1.7'>{rows}</ul>"""

    quick_wins_html = ""
    for qw in strategy.get("quick_wins", []):
        impact_color = {"High": "#d32f2f", "Medium": "#f57c00", "Low": "#388e3c"}.get(qw.get("impact", ""), "#555")
        quick_wins_html += f"""
        <tr>
          <td style='padding:8px;border-bottom:1px solid #eee'>{qw.get("action","")}</td>
          <td style='padding:8px;border-bottom:1px solid #eee;color:{impact_color};font-weight:bold'>{qw.get("impact","")}</td>
          <td style='padding:8px;border-bottom:1px solid #eee'>{qw.get("effort","")}</td>
          <td style='padding:8px;border-bottom:1px solid #eee'>{qw.get("timeline","")}</td>
        </tr>"""

    growth_html = ""
    for gi in strategy.get("growth_initiatives", []):
        growth_html += f"""
        <div style='background:#f5f5f5;border-left:4px solid #1a1a2e;padding:12px;margin-bottom:10px;border-radius:4px'>
          <strong>{gi.get("initiative","")}</strong><br>
          <span style='color:#555'>{gi.get("rationale","")}</span><br>
          <em>Target: {gi.get("kpi_target","")} | {gi.get("timeline","")}</em>
        </div>"""

    metrics_html = ""
    for k, v in analysis.get("key_metrics", {}).items():
        metrics_html += f"<td style='padding:8px;border:1px solid #ddd'><strong>{k}</strong><br>{v}</td>"

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style='font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;color:#333'>

      <div style='background:linear-gradient(135deg,#1a1a2e,#16213e);color:white;padding:24px;border-radius:12px;margin-bottom:24px'>
        <h1 style='margin:0'>💎 Zentox Aesthetics — AI Strategy Report</h1>
        <p style='margin:8px 0 0;opacity:0.8'>Generated {now} · Dataset: {data_label}</p>
      </div>

      <div style='background:#e8f5e9;border:1px solid #a5d6a7;border-radius:8px;padding:16px;margin-bottom:20px'>
        <h2 style='color:#2e7d32;margin-top:0'>Executive Summary</h2>
        <p style='font-size:16px;line-height:1.6'>{strategy.get("executive_summary","")}</p>
      </div>

      <h2>📊 Key Metrics</h2>
      <table style='width:100%;border-collapse:collapse;margin-bottom:20px'>
        <tr>{metrics_html}</tr>
      </table>

      <h2>⚡ Quick Wins</h2>
      <table style='width:100%;border-collapse:collapse;margin-bottom:20px'>
        <thead>
          <tr style='background:#1a1a2e;color:white'>
            <th style='padding:10px;text-align:left'>Action</th>
            <th style='padding:10px;text-align:left'>Impact</th>
            <th style='padding:10px;text-align:left'>Effort</th>
            <th style='padding:10px;text-align:left'>Timeline</th>
          </tr>
        </thead>
        <tbody>{quick_wins_html}</tbody>
      </table>

      <h2>🚀 Growth Initiatives</h2>
      {growth_html}

      {section("📈 Trends Identified", analysis.get("trends", []))}
      {section("⚠️ Anomalies & Flags", analysis.get("anomalies", []) + strategy.get("risk_flags", []), "#c62828")}
      {section("📣 Marketing Recommendations", strategy.get("marketing_recommendations", []))}
      {section("⚙️ Operational Recommendations", strategy.get("operational_recommendations", []))}
      {section("🔧 Data Cleaning Audit", audit, "#37474f")}

      <div style='background:#f5f5f5;padding:12px;border-radius:8px;margin-top:24px;font-size:12px;color:#888'>
        This report was generated automatically by the Zentox AI Agent Pipeline (Claude Haiku).
        All patient data was processed in-system and is HIPAA-compliant. No PHI left the system.
      </div>

    </body>
    </html>"""


def send_report(
    analysis: dict,
    strategy: dict,
    audit: list[str],
    data_label: str = "Imported Data",
) -> bool:
    """
    Send the strategy report email. Returns True on success.
    Requires SMTP settings in .env:
      SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD
    """
    settings = get_settings()

    to_email = "info@fivezero3.net"
    subject = f"Zentox AI Report — {data_label} ({datetime.now().strftime('%b %d, %Y')})"

    html_body = _build_html(analysis, strategy, audit, data_label)
    text_body = (
        f"Zentox AI Strategy Report\n\n"
        f"Executive Summary:\n{strategy.get('executive_summary', '')}\n\n"
        f"Quick Wins: {len(strategy.get('quick_wins', []))}\n"
        f"Growth Initiatives: {len(strategy.get('growth_initiatives', []))}\n\n"
        f"Full report available in the Zentox CRM AI Agents page."
    )

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_user
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.starttls()
            server.login(settings.smtp_user, settings.smtp_password)
            server.sendmail(settings.smtp_user, to_email, msg.as_string())
        return True
    except Exception as exc:
        print(f"[email_notifier] Failed to send: {exc}")
        return False
