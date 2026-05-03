"""
QuickBooks Online integration — pulls invoices, payments, and P&L reports.
Uses the QBO REST API v3 with OAuth2 refresh-token flow.
"""
import httpx
from backend.config import get_settings

settings = get_settings()

QBO_BASE = "https://sandbox-quickbooks.api.intuit.com" if settings.qbo_sandbox else "https://quickbooks.api.intuit.com"
TOKEN_URL = "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer"


class QuickBooksClient:
    def __init__(self):
        self._access_token: str | None = None

    def _refresh_access_token(self) -> str:
        resp = httpx.post(
            TOKEN_URL,
            data={"grant_type": "refresh_token", "refresh_token": settings.qbo_refresh_token},
            auth=(settings.qbo_client_id, settings.qbo_client_secret),
        )
        resp.raise_for_status()
        self._access_token = resp.json()["access_token"]
        return self._access_token

    def _headers(self) -> dict:
        if not self._access_token:
            self._refresh_access_token()
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Accept": "application/json",
        }

    def _query(self, sql: str) -> list[dict]:
        url = f"{QBO_BASE}/v3/company/{settings.qbo_realm_id}/query"
        resp = httpx.get(url, headers=self._headers(), params={"query": sql, "minorversion": "65"})
        resp.raise_for_status()
        data = resp.json()
        return data.get("QueryResponse", {}).get(sql.split("FROM ")[1].split(" ")[0], [])

    def get_invoices(self, limit: int = 100) -> list[dict]:
        return self._query(f"SELECT * FROM Invoice MAXRESULTS {limit}")

    def get_payments(self, limit: int = 100) -> list[dict]:
        return self._query(f"SELECT * FROM Payment MAXRESULTS {limit}")

    def get_pnl_report(self, start_date: str, end_date: str) -> dict:
        url = f"{QBO_BASE}/v3/company/{settings.qbo_realm_id}/reports/ProfitAndLoss"
        resp = httpx.get(url, headers=self._headers(), params={
            "start_date": start_date,
            "end_date": end_date,
            "minorversion": "65",
        })
        resp.raise_for_status()
        return resp.json()

    def get_revenue_summary(self) -> dict:
        """Extract total revenue from recent invoices."""
        invoices = self.get_invoices()
        total = sum(float(inv.get("TotalAmt", 0)) for inv in invoices)
        paid = sum(float(inv.get("TotalAmt", 0)) for inv in invoices if inv.get("Balance", 1) == 0)
        outstanding = total - paid
        return {
            "total_invoiced": round(total, 2),
            "total_paid": round(paid, 2),
            "outstanding": round(outstanding, 2),
            "invoice_count": len(invoices),
        }
