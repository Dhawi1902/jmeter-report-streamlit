"""The Errors tab: error types, worst samplers, and a look at the raw failures."""
from __future__ import annotations

import pandas as pd
import streamlit as st

import config
from charts import common as charts
from core import errors
from core.parser import Jtl

PREVIEW_ROWS = 500
PREVIEW_COLUMNS = (
    config.TS,
    config.LABEL,
    config.RESPONSE_CODE,
    config.RESPONSE_MESSAGE,
    config.FAILURE_MESSAGE,
    config.ELAPSED,
    config.THREAD_NAME,
)


def render(jtl: Jtl, frame: pd.DataFrame, settings: config.Settings) -> None:
    table = errors.error_table(frame)
    if table.empty:
        st.success("No failed samples in the selected window.")
        return

    st.subheader("Errors")
    st.dataframe(table.style.format(precision=2), width="stretch", hide_index=True)
    st.plotly_chart(
        charts.bar(
            table,
            x=errors.ERROR_TYPE,
            y="#Samples",
            title="Errors by type",
            x_title="",
            y_title="Samples",
        ),
        width="stretch",
    )

    st.subheader(f"Top {config.TOP_ERRORS} errors by sampler")
    st.dataframe(errors.top_errors_by_sampler(frame), width="stretch", hide_index=True)

    st.subheader("Failed samples")
    failed = errors.failures(frame)
    columns = [column for column in PREVIEW_COLUMNS if column in failed.columns]
    st.caption(f"{len(failed):,} failed samples; showing the first {PREVIEW_ROWS:,}.")
    st.dataframe(failed[columns].head(PREVIEW_ROWS), width="stretch", hide_index=True)
