"""Charts > Response Times."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from charts import common as charts
from core import aggregate
from core.parser import Jtl
from views.common import requires


def render(jtl: Jtl, frame: pd.DataFrame, settings: config.Settings) -> None:
    curve = aggregate.percentile_curve(frame)
    st.plotly_chart(
        charts.line(
            curve,
            x="percentile",
            y=config.ELAPSED,
            color=config.LABEL,
            title="Response time percentiles",
            x_title="Percentile",
            y_title="Response time (ms)",
        ),
        width="stretch",
    )

    bucket_ms = st.select_slider(
        "Distribution band width (ms)",
        options=[100, 250, 500, 1000, 2000],
        value=config.DISTRIBUTION_BUCKET_MS,
    )
    distribution = aggregate.response_time_distribution(frame, bucket_ms)
    st.plotly_chart(
        charts.bar(
            distribution,
            x="band",
            y="#Samples",
            color=config.LABEL,
            title="Response time distribution",
            x_title=f"Response time band (ms, width {bucket_ms})",
            y_title="Samples",
        ),
        width="stretch",
    )

    st.plotly_chart(
        charts.bar(
            _overview(frame),
            x="Metric",
            y="Milliseconds",
            color=config.LABEL,
            title="Response time overview",
            x_title="",
            y_title="Milliseconds",
            barmode="group",
        ),
        width="stretch",
    )

    if requires(jtl, config.ALL_THREADS, chart="Time vs threads"):
        st.plotly_chart(
            charts.line(
                aggregate.time_vs_threads(frame),
                x=config.ALL_THREADS,
                y=config.ELAPSED,
                color=config.LABEL,
                title="Time vs threads",
                x_title="Active threads",
                y_title="Average response time (ms)",
            ),
            width="stretch",
        )


def _overview(frame: pd.DataFrame) -> pd.DataFrame:
    """Average / median / percentile bars per label, in long form for plotting."""
    statistics = aggregate.statistics_table(frame)
    metrics = ["Average", "Median"] + [aggregate.pct_label(p) for p in config.PERCENTILES]
    return statistics.melt(
        id_vars="Label", value_vars=metrics, var_name="Metric", value_name="Milliseconds"
    ).rename(columns={"Label": config.LABEL})
