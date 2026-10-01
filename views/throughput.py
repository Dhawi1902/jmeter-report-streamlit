"""Charts > Throughput."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from charts import common as charts
from core import aggregate
from core.parser import Jtl
from views.common import requires

RATE = "per second"


def render(jtl: Jtl, frame: pd.DataFrame, settings: config.Settings) -> None:
    granularity = settings.granularity_ms

    total = aggregate.rate_over_time(frame, granularity)
    st.plotly_chart(
        charts.line(
            total,
            x=config.BUCKET,
            y=RATE,
            title="Hits per second (all samples)",
            x_title="Time",
            y_title="Hits / second",
        ),
        width="stretch",
    )

    per_label = aggregate.rate_over_time(frame, granularity, group_column=config.LABEL)
    st.plotly_chart(
        charts.line(
            per_label,
            x=config.BUCKET,
            y=RATE,
            color=config.LABEL,
            title="Transactions per second",
            x_title="Time",
            y_title="Transactions / second",
        ),
        width="stretch",
    )

    if requires(jtl, config.RESPONSE_CODE, chart="Response codes per second"):
        per_code = aggregate.rate_over_time(frame, granularity, group_column=config.RESPONSE_CODE)
        st.plotly_chart(
            charts.bar(
                per_code,
                x=config.BUCKET,
                y=RATE,
                color=config.RESPONSE_CODE,
                title="Response codes per second",
                x_title="Time",
                y_title="Responses / second",
            ),
            width="stretch",
        )

    _rate_scatter(frame, granularity, config.ELAPSED, "Response time vs request rate")

    if requires(jtl, config.LATENCY, chart="Latency vs request rate"):
        _rate_scatter(frame, granularity, config.LATENCY, "Latency vs request rate")


def _rate_scatter(frame: pd.DataFrame, granularity: int, column: str, title: str) -> None:
    points = aggregate.response_time_vs_rate(frame, granularity, value_column=column)
    st.plotly_chart(
        charts.scatter(
            points,
            x=RATE,
            y="response time",
            color=config.LABEL,
            title=title,
            x_title="Requests / second",
            y_title="Average (ms)",
        ),
        width="stretch",
    )
