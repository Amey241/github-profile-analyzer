"""
analysis/languages.py
Aggregate language bytes and build a Plotly radar chart.
"""

import pandas as pd
import plotly.graph_objects as go
from config import ACCENT_COLORS
from utils.sanitize import safe_int, safe_sum


def aggregate_languages(lang_totals: dict) -> pd.DataFrame:
    """Convert raw {lang: bytes} dict to a percentage DataFrame."""
    if not lang_totals:
        return pd.DataFrame(columns=["language", "bytes", "pct"])

    cleaned = [(language, safe_int(byte_count, 0)) for language, byte_count in lang_totals.items()]
    cleaned = [(language, byte_count) for language, byte_count in cleaned if byte_count > 0]
    if not cleaned:
        return pd.DataFrame(columns=["language", "bytes", "pct"])

    df = pd.DataFrame(cleaned, columns=["language", "bytes"])
    df = df.sort_values("bytes", ascending=False).reset_index(drop=True)
    total_bytes = safe_sum(df["bytes"].tolist(), 0)
    df["pct"] = df["bytes"] / total_bytes * 100 if total_bytes > 0 else 0

    # Keep top-12, group the rest as "Other"
    if len(df) > 12:
        top = df.iloc[:12].copy()
        other_bytes = df.iloc[12:]["bytes"].sum()
        other_pct = df.iloc[12:]["pct"].sum()
        top = pd.concat([top, pd.DataFrame([{
            "language": "Other", "bytes": other_bytes, "pct": other_pct
        }])], ignore_index=True)
        df = top

    return df


def radar_chart(df: pd.DataFrame) -> go.Figure:
    """Return a Plotly polar/radar chart for language distribution."""
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No language data", x=0.5, y=0.5, showarrow=False)
        return fig

    categories = df["language"].tolist()
    values = df["pct"].tolist()

    # Close the loop for radar
    categories_closed = categories + [categories[0]]
    values_closed = values + [values[0]]

    colors = ACCENT_COLORS[:len(categories)]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values_closed,
        theta=categories_closed,
        fill="toself",
        fillcolor="rgba(108,99,255,0.2)",
        line=dict(color="#6C63FF", width=2),
        name="Languages",
        hovertemplate="%{theta}: %{r:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(
                visible=True,
                range=[0, max(values) * 1.15],
                showticklabels=False,
                gridcolor="rgba(255,255,255,0.1)",
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#E2E8F0"),
                gridcolor="rgba(255,255,255,0.1)",
            ),
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20, l=40, r=40),
        font=dict(color="#E2E8F0"),
    )
    return fig


def bar_chart(df: pd.DataFrame) -> go.Figure:
    """Horizontal bar chart alternative for language distribution."""
    if df.empty:
        return go.Figure()

    colors = (ACCENT_COLORS * 3)[:len(df)]
    fig = go.Figure(go.Bar(
        x=df["pct"],
        y=df["language"],
        orientation="h",
        marker_color=colors,
        text=df["pct"].map(lambda v: f"{v:.1f}%"),
        textposition="outside",
        hovertemplate="%{y}: %{x:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Percentage (%)", gridcolor="rgba(255,255,255,0.1)", color="#E2E8F0"),
        yaxis=dict(autorange="reversed", color="#E2E8F0"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        margin=dict(t=10, b=10, l=10, r=60),
    )
    return fig
