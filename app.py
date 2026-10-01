"""A Streamlit stand-in for JMeter's HTML dashboard, built from a .jtl file."""
from __future__ import annotations

import io
from pathlib import Path

import streamlit as st

from core import aggregate
from core.parser import Jtl, JtlError, load_jtl
from views import dashboard, errors_view, over_time, response_times, sidebar, throughput

st.set_page_config(page_title="JMeter report", page_icon="📊", layout="wide")

TABS = (
    ("Dashboard", dashboard.render),
    ("Over time", over_time.render),
    ("Throughput", throughput.render),
    ("Response times", response_times.render),
    ("Errors", errors_view.render),
)


@st.cache_data(show_spinner="Parsing result file...")
def _load_upload(payload: bytes) -> Jtl:
    return load_jtl(io.BytesIO(payload))


@st.cache_data(show_spinner="Parsing result file...")
def _load_path(path: str, modified: float) -> Jtl:
    return load_jtl(path)


def _load(source: sidebar.Source) -> Jtl:
    if source.payload is not None:
        return _load_upload(source.payload)
    return _load_path(source.path, Path(source.path).stat().st_mtime)


def main() -> None:
    st.title("JMeter report")
    source = sidebar.choose_source()
    if not source.ready:
        st.info("Upload a JMeter CSV result file (.jtl), or give its path, to build the report.")
        return

    try:
        jtl = _load(source)
    except JtlError as error:
        st.error(str(error))
        return

    settings = sidebar.choose_settings(jtl.df)
    frame = aggregate.apply_filters(jtl.df, settings)
    if frame.empty:
        st.warning("No samples match the current filters.")
        return

    if jtl.missing_optional:
        st.caption("Columns absent from this file: " + ", ".join(jtl.missing_optional))

    for tab, (_, render) in zip(st.tabs([name for name, _ in TABS]), TABS):
        with tab:
            render(jtl, frame, settings)


main()
