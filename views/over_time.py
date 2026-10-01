"""Charts > Over Time."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from charts import common as charts
from core import aggregate
from core.parser import Jtl
from views.common import requires


def render(jtl: Jtl, frame: pd.DataFrame, settings: config.Settings) -> None:
    granularity = settings.granularity_ms

    _timing_chart(frame, granularity, config.ELAPSED, "Response times over time")

    percentiles = aggregate.percentiles_over_time(frame, granularity)
    value_columns = [column for column in percentiles.columns if column != config.BUCKET]
    st.plotly_chart(
        charts.line(
            percentiles,
            x=config.BUCKET,
            y=value_columns,
            title="Response time percentiles over time (successful responses)",
            x_title="Time",
            y_title="Response time (ms)",
        ),
        width="stretch",
    )

    if requires(jtl, config.ALL_THREADS, chart="Active threads over time"):
        threads = aggregate.active_threads_over_time(frame, granularity)
        st.plotly_chart(
            charts.line(
                threads,
                x=config.BUCKET,
                y="threads",
                color=config.THREAD_GROUP,
                title="Active threads over time",
                x_title="Time",
                y_title="Threads",
            ),
            width="stretch",
        )

    if requires(jtl, config.BYTES, chart="Bytes throughput over time"):
        throughput = aggregate.bytes_over_time(frame, granularity)
        series = [column for column in throughput.columns if column != config.BUCKET]
        st.plotly_chart(
            charts.line(
                throughput,
                x=config.BUCKET,
                y=series,
                title="Bytes throughput over time",
                x_title="Time",
                y_title="KB / second",
            ),
            width="stretch",
        )

    if requires(jtl, config.LATENCY, chart="Latencies over time"):
        _timing_chart(frame, granularity, config.LATENCY, "Latencies over time")

    if requires(jtl, config.CONNECT, chart="Connect time over time"):
        _timing_chart(frame, granularity, config.CONNECT, "Connect time over time")


def _timing_chart(frame: pd.DataFrame, granularity: int, column: str, title: str) -> None:
    series = aggregate.over_time(frame, column, granularity, how="mean")
    st.plotly_chart(
        charts.line(
            series,
            x=config.BUCKET,
            y=column,
            color=config.LABEL,
            title=title,
            x_title="Time",
            y_title="Average (ms)",
        ),
        width="stretch",
    )
