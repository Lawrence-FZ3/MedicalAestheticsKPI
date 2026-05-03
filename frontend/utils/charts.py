"""Reusable Plotly chart helpers for the Zentox CRM dashboard."""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

BRAND_COLORS = ["#6C63FF", "#48CAE4", "#90BE6D", "#F9C74F", "#F94144", "#577590", "#F3722C"]


def revenue_trend(df: pd.DataFrame, date_col: str, revenue_col: str) -> go.Figure:
    fig = px.line(df, x=date_col, y=revenue_col, markers=True, color_discrete_sequence=BRAND_COLORS)
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eee", tickprefix="$")
    return fig


def pipeline_funnel(stage_counts: dict) -> go.Figure:
    stages = list(stage_counts.keys())
    values = list(stage_counts.values())
    fig = go.Figure(go.Funnel(y=stages, x=values, marker_color=BRAND_COLORS))
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor="rgba(0,0,0,0)")
    return fig


def appointment_status_donut(by_status: dict) -> go.Figure:
    labels = list(by_status.keys())
    values = list(by_status.values())
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.55, marker_colors=BRAND_COLORS))
    fig.update_layout(margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor="rgba(0,0,0,0)", showlegend=True)
    return fig


def lead_source_bar(source_counts: dict) -> go.Figure:
    df = pd.DataFrame(list(source_counts.items()), columns=["Source", "Count"])
    fig = px.bar(df, x="Count", y="Source", orientation="h", color="Source", color_discrete_sequence=BRAND_COLORS)
    fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=30, b=0), paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
    return fig


def kpi_gauge(value: float, title: str, max_val: float = 100, suffix: str = "%") -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={"text": title},
        number={"suffix": suffix},
        gauge={
            "axis": {"range": [0, max_val]},
            "bar": {"color": BRAND_COLORS[0]},
            "steps": [
                {"range": [0, max_val * 0.5], "color": "#f0f0f0"},
                {"range": [max_val * 0.5, max_val * 0.8], "color": "#ddd"},
            ],
        },
    ))
    fig.update_layout(height=200, margin=dict(l=10, r=10, t=40, b=10), paper_bgcolor="rgba(0,0,0,0)")
    return fig
