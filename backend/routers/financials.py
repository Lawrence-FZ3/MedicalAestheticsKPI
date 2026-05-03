"""
Full financial engine — Income Statement, Balance Sheet, Cash Flow.
Revenue comes from the Appointments table; expenses from the Expenses table.
"""
import uuid
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from backend.auth import verify_token, TokenData
from backend.audit import log_action
from backend.airtable_client import appointments_table, expenses_table, coa_table, inventory_table

router = APIRouter(prefix="/financials", tags=["financials"])


class ExpenseCreate(BaseModel):
    date: date
    vendor: str
    description: str
    category: str
    amount: float
    payment_method: Optional[str] = None
    tax_deductible: bool = True
    recurring: bool = False
    notes: Optional[str] = None


def _parse_date(d: str) -> Optional[date]:
    if not d:
        return None
    try:
        return date.fromisoformat(d[:10])
    except Exception:
        return None


@router.get("/income-statement")
def income_statement(
    start_date: str,
    end_date: str,
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    """
    Computes a P&L / Income Statement for a given date range.
    Revenue = completed appointment revenue
    COGS = supplies & products expenses
    Gross Profit = Revenue - COGS
    Operating Expenses = all other expenses
    Net Income = Gross Profit - Operating Expenses
    """
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not start or not end:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")

    # Revenue from completed appointments
    appts = appointments_table().all(formula="AND({Status}='Completed')")
    revenue_by_service: dict = {}
    total_revenue = 0.0
    for a in appts:
        f = a["fields"]
        appt_date_str = f.get("Appointment Date", "")
        appt_date = _parse_date(appt_date_str)
        if appt_date and start <= appt_date <= end:
            amount = float(f.get("Revenue") or 0)
            service = f.get("Service", "Other")
            revenue_by_service[service] = revenue_by_service.get(service, 0) + amount
            total_revenue += amount

    # Expenses
    all_expenses = expenses_table().all()
    expense_categories: dict = {}
    total_expenses = 0.0
    cogs_total = 0.0
    for e in all_expenses:
        f = e["fields"]
        exp_date = _parse_date(str(f.get("Date", "")))
        if exp_date and start <= exp_date <= end:
            amount = float(f.get("Amount") or 0)
            category = f.get("Category", "Other")
            if category == "Supplies & Products":
                cogs_total += amount
            else:
                expense_categories[category] = expense_categories.get(category, 0) + amount
                total_expenses += amount

    gross_profit = total_revenue - cogs_total
    operating_income = gross_profit - total_expenses
    gross_margin = round(gross_profit / total_revenue * 100, 1) if total_revenue else 0
    net_margin = round(operating_income / total_revenue * 100, 1) if total_revenue else 0

    log_action(token.username, "VIEW", "Financial", ip_address=request.client.host if request else "", details=f"Income Statement {start_date} to {end_date}")

    return {
        "period": {"start": start_date, "end": end_date},
        "revenue": {
            "total": round(total_revenue, 2),
            "by_service": revenue_by_service,
        },
        "cost_of_goods_sold": round(cogs_total, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_margin_pct": gross_margin,
        "operating_expenses": {
            "total": round(total_expenses, 2),
            "by_category": expense_categories,
        },
        "operating_income": round(operating_income, 2),
        "net_margin_pct": net_margin,
    }


@router.get("/cash-flow")
def cash_flow(
    start_date: str,
    end_date: str,
    request: Request = None,
    token: TokenData = Depends(verify_token),
):
    """Cash flow statement for the period."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if not start or not end:
        raise HTTPException(status_code=400, detail="Invalid date format.")

    appts = appointments_table().all(formula="AND({Status}='Completed')")
    cash_inflows = 0.0
    inflow_detail: dict = {}
    for a in appts:
        f = a["fields"]
        appt_date = _parse_date(str(f.get("Appointment Date", "")))
        if appt_date and start <= appt_date <= end:
            amount = float(f.get("Revenue") or 0)
            cash_inflows += amount
            payment = f.get("Source", "Other")
            inflow_detail[payment] = inflow_detail.get(payment, 0) + amount

    all_expenses = expenses_table().all()
    cash_outflows = 0.0
    outflow_detail: dict = {}
    for e in all_expenses:
        f = e["fields"]
        exp_date = _parse_date(str(f.get("Date", "")))
        if exp_date and start <= exp_date <= end:
            amount = float(f.get("Amount") or 0)
            cat = f.get("Category", "Other")
            cash_outflows += amount
            outflow_detail[cat] = outflow_detail.get(cat, 0) + amount

    net_cash = cash_inflows - cash_outflows
    log_action(token.username, "VIEW", "Financial", ip_address=request.client.host if request else "", details=f"Cash Flow {start_date} to {end_date}")

    return {
        "period": {"start": start_date, "end": end_date},
        "operating_activities": {
            "cash_inflows": round(cash_inflows, 2),
            "inflow_detail": inflow_detail,
            "cash_outflows": round(cash_outflows, 2),
            "outflow_detail": outflow_detail,
            "net_operating_cash_flow": round(net_cash, 2),
        },
        "net_change_in_cash": round(net_cash, 2),
    }


@router.get("/balance-sheet")
def balance_sheet(token: TokenData = Depends(verify_token)):
    """Simplified balance sheet — assets, liabilities, equity snapshot."""
    # Inventory as current asset
    inv_records = inventory_table().all()
    inventory_value = sum(
        float(r["fields"].get("Unit Cost") or 0) * float(r["fields"].get("Units In Stock") or 0)
        for r in inv_records
    )

    # All-time revenue (AR proxy)
    appts = appointments_table().all(formula="{Status}='Completed'")
    total_revenue = sum(float(a["fields"].get("Revenue") or 0) for a in appts)

    # All-time expenses
    all_expenses = expenses_table().all()
    total_expenses = sum(float(e["fields"].get("Amount") or 0) for e in all_expenses)

    retained_earnings = total_revenue - total_expenses
    total_assets = inventory_value + max(retained_earnings, 0)
    total_equity = retained_earnings

    return {
        "as_of": date.today().isoformat(),
        "assets": {
            "current_assets": {
                "cash_and_equivalents": round(max(retained_earnings, 0), 2),
                "inventory": round(inventory_value, 2),
            },
            "total_assets": round(total_assets, 2),
        },
        "liabilities": {
            "current_liabilities": {},
            "total_liabilities": 0.0,
        },
        "equity": {
            "retained_earnings": round(retained_earnings, 2),
            "total_equity": round(total_equity, 2),
        },
        "total_liabilities_and_equity": round(total_equity, 2),
    }


@router.post("/expenses", status_code=201)
def create_expense(body: ExpenseCreate, request: Request = None, token: TokenData = Depends(verify_token)):
    fields = {
        "Expense ID": f"EXP-{uuid.uuid4().hex[:8].upper()}",
        "Date": body.date.strftime("%Y-%m-%d"),
        "Vendor": body.vendor,
        "Description": body.description,
        "Category": body.category,
        "Amount": body.amount,
        "Tax Deductible": body.tax_deductible,
        "Recurring": body.recurring,
    }
    if body.payment_method:
        fields["Payment Method"] = body.payment_method
    if body.notes:
        fields["Notes"] = body.notes
    record = expenses_table().create(fields)
    log_action(token.username, "CREATE", "Financial", resource_id=record["id"], ip_address=request.client.host if request else "")
    return {"id": record["id"], **record["fields"]}


@router.get("/expenses")
def list_expenses(
    category: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    token: TokenData = Depends(verify_token),
):
    formulas = []
    if category:
        formulas.append(f"{{Category}}='{category}'")
    formula = f"AND({','.join(formulas)})" if formulas else None
    records = expenses_table().all(formula=formula, sort=[{"field": "Date", "direction": "desc"}])
    expenses = [{"id": r["id"], **r["fields"]} for r in records]

    # Client-side date filter
    if start_date or end_date:
        start = _parse_date(start_date) if start_date else date.min
        end = _parse_date(end_date) if end_date else date.max
        expenses = [
            e for e in expenses
            if (d := _parse_date(str(e.get("Date", "")))) and start <= d <= end
        ]
    return expenses


@router.get("/medspa-kpis")
def medspa_kpis(token: TokenData = Depends(verify_token)):
    """MedSpa-specific KPI benchmarks computed from live data."""
    appts = appointments_table().all()
    all_expenses = expenses_table().all()

    total_revenue = 0.0
    completed = 0
    no_shows = 0
    revenue_by_provider: dict = {}
    revenue_by_service: dict = {}

    for a in appts:
        f = a["fields"]
        rev = float(f.get("Revenue") or 0)
        total_revenue += rev
        provider = f.get("Provider", "Unknown")
        service = f.get("Service", "Other")
        revenue_by_provider[provider] = revenue_by_provider.get(provider, 0) + rev
        revenue_by_service[service] = revenue_by_service.get(service, 0) + rev
        if f.get("Status") == "Completed":
            completed += 1
        elif f.get("Status") == "No-Show":
            no_shows += 1

    total_appts = len(appts)
    total_expenses = sum(float(e["fields"].get("Amount") or 0) for e in all_expenses)
    payroll = sum(float(e["fields"].get("Amount") or 0) for e in all_expenses if e["fields"].get("Category") == "Payroll")
    marketing = sum(float(e["fields"].get("Amount") or 0) for e in all_expenses if e["fields"].get("Category") == "Marketing")

    revenue_per_appointment = round(total_revenue / completed, 2) if completed else 0
    no_show_rate = round(no_shows / total_appts * 100, 1) if total_appts else 0
    overhead_ratio = round(total_expenses / total_revenue * 100, 1) if total_revenue else 0
    payroll_ratio = round(payroll / total_revenue * 100, 1) if total_revenue else 0
    marketing_roi = round(total_revenue / marketing, 2) if marketing else 0
    net_profit = total_revenue - total_expenses
    profit_margin = round(net_profit / total_revenue * 100, 1) if total_revenue else 0

    return {
        "revenue": {
            "total": round(total_revenue, 2),
            "per_appointment": revenue_per_appointment,
            "by_provider": revenue_by_provider,
            "top_services": dict(sorted(revenue_by_service.items(), key=lambda x: x[1], reverse=True)[:5]),
        },
        "appointments": {
            "total": total_appts,
            "completed": completed,
            "no_shows": no_shows,
            "no_show_rate_pct": no_show_rate,
        },
        "expenses": {
            "total": round(total_expenses, 2),
            "payroll": round(payroll, 2),
            "marketing": round(marketing, 2),
        },
        "profitability": {
            "gross_profit": round(net_profit, 2),
            "profit_margin_pct": profit_margin,
            "overhead_ratio_pct": overhead_ratio,
            "payroll_ratio_pct": payroll_ratio,
            "marketing_roi": marketing_roi,
        },
        "benchmarks": {
            "ideal_no_show_rate": "< 10%",
            "ideal_payroll_ratio": "35-45%",
            "ideal_profit_margin": "15-25%",
            "ideal_overhead_ratio": "< 70%",
        },
    }
