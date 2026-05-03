"""
HIPAA Audit Logging — every access to PHI is recorded in the Airtable Audit Log table.
Never log actual PHI values, only resource IDs and action types.
"""
import uuid
from datetime import datetime, timezone
from backend.airtable_client import audit_table


def log_action(
    user: str,
    action: str,
    resource_type: str,
    resource_id: str = "",
    ip_address: str = "",
    details: str = "",
) -> None:
    try:
        audit_table().create({
            "Log ID": str(uuid.uuid4()),
            "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "User": user,
            "Action": action,
            "Resource Type": resource_type,
            "Resource ID": resource_id,
            "IP Address": ip_address,
            "Details": details,
        })
    except Exception:
        # Audit log failure must not crash the primary request, but should be monitored
        pass
