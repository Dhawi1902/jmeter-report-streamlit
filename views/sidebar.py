"""Sidebar: pick a result file, then the reporting options."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import streamlit as st

import config
from core import aggregate


@dataclass(frozen=True)
class Source:
    """Where the samples come from: an upload, or a path on this machine."""

    payload: bytes | None = None
    path: str | None = None

    @property
    def ready(self) -> bool:
        return self.payload is not None or bool(self.path)


def choose_source() -> Source:
    st.sidebar.header("Result file")
    upload = st.sidebar.file_uploader("Upload a .jtl / .csv", type=["jtl", "csv"])
    if upload is not None:
        return Source(payload=upload.getvalue())

    st.sidebar.caption("Large file? Point at it instead of uploading.")
    typed = st.sidebar.text_input("Path to .jtl", placeholder=r"C:\results\run.jtl").strip('" ')
    if typed and not Path(typed).is_file():
        st.sidebar.error("No file at that path.")
        return Source()
    return Source(path=typed or None)


def choose_settings(frame: pd.DataFrame) -> config.Settings:
    st.sidebar.header("Options")
    granularity_name = st.sidebar.selectbox(
        "Granularity",
        options=list(config.GRANULARITY_CHOICES),
        index=list(config.GRANULARITY_CHOICES).index("1 minute"),
    )

    st.sidebar.caption("APDEX thresholds")
    satisfied = st.sidebar.number_input(
        "Satisfied (T, ms)", min_value=1, value=config.DEFAULT_APDEX_SATISFIED_MS, step=100
    )
    tolerated = st.sidebar.number_input(
        "Tolerated (F, ms)", min_value=satisfied + 1, value=max(
            config.DEFAULT_APDEX_TOLERATED_MS, satisfied + 1
        ), step=100
    )

    labels = st.sidebar.multiselect(
        "Samplers", options=sorted(frame[config.LABEL].unique()), default=[]
    )

    first, last = aggregate.time_bounds(frame)
    start, end = first.to_pydatetime(), last.to_pydatetime()
    window = (start, end)
    if end > start:
        window = st.sidebar.slider("Time window", min_value=start, max_value=end, value=window)

    return config.Settings(
        granularity_ms=config.GRANULARITY_CHOICES[granularity_name],
        apdex_satisfied_ms=int(satisfied),
        apdex_tolerated_ms=int(tolerated),
        labels=tuple(labels),
        start=window[0],
        end=window[1],
    )
