"""The landing tab: APDEX, request summary and the statistics table."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from charts import common as charts
from core import aggregate
from core.parser import Jtl

APDEX_GOOD = 0.94
APDEX_FAIR = 0.85


def render(jtl: Jtl, frame: pd.DataFrame, settings: config.Settings) -> None:
    _headline(frame)

    st.subheader("APDEX")
    apdex = aggregate.apdex_table(frame, settings.apdex_satisfied_ms, settings.apdex_tolerated_ms)
    st.dataframe(
        apdex.style.format({"Apdex": "{:.3f}"}).map(_apdex_colour, subset=["Apdex"]),
        width="stretch",
        hide_index=True,
    )

    st.subheader("Requests summary")
    summary = aggregate.requests_summary(frame)
    left, right = st.columns([1, 2])
    with left:
        st.plotly_chart(
            charts.pie(summary, names="Result", values="#Samples", title="Success vs failure"),
            width="stretch",
        )
    with right:
        st.subheader("Statistics")
        st.dataframe(
            aggregate.statistics_table(frame).style.format(precision=2),
            width="stretch",
            hide_index=True,
        )


def _headline(frame: pd.DataFrame) -> None:
    start, end = aggregate.time_bounds(frame)
    seconds = aggregate.duration_seconds(frame)
    failures = int((~frame[config.SUCCESS]).sum())
    columns = st.columns(5)
    columns[0].metric("Samples", f"{len(frame):,}")
    columns[1].metric(
        "Errors",
        f"{failures:,}",
        f"{failures / len(frame) * 100:.2f}%",
        delta_color="inverse",  # more errors is worse, so show it red
    )
    columns[2].metric("Duration", f"{seconds:,.0f} s")
    columns[3].metric("Throughput", f"{len(frame) / seconds:,.1f} /s")
    columns[4].metric("Average", _milliseconds(frame[config.ELAPSED].mean()))
    st.caption(f"Window: {start:%Y-%m-%d %H:%M:%S} to {end:%Y-%m-%d %H:%M:%S} (UTC)")


def _milliseconds(value: float) -> str:
    """Keep the metric short enough not to be truncated in a narrow column."""
    return f"{value / 1000:,.2f} s" if value >= 1000 else f"{value:,.0f} ms"


def _apdex_colour(value: float) -> str:
    if value >= APDEX_GOOD:
        return "background-color: #1b5e20; color: white"
    if value >= APDEX_FAIR:
        return "background-color: #8d6e00; color: white"
    return "background-color: #8e1b1b; color: white"
