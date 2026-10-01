"""Shared view helpers."""
from __future__ import annotations

import streamlit as st

from core.parser import Jtl

SAVE_PROPERTY = {
    "Latency": "jmeter.save.saveservice.latency",
    "Connect": "jmeter.save.saveservice.connect_time",
    "bytes": "jmeter.save.saveservice.bytes",
    "sentBytes": "jmeter.save.saveservice.sent_bytes",
    "allThreads": "jmeter.save.saveservice.thread_counts",
    "grpThreads": "jmeter.save.saveservice.thread_counts",
    "threadName": "jmeter.save.saveservice.thread_name",
    "responseMessage": "jmeter.save.saveservice.response_message",
    "failureMessage": "jmeter.save.saveservice.assertion_results_failure_message",
}


def requires(jtl: Jtl, *columns: str, chart: str) -> bool:
    """Show a note instead of a chart when the .jtl lacks the needed columns."""
    missing = [column for column in columns if not jtl.has(column)]
    if not missing:
        return True
    hints = ", ".join(
        f"`{column}` (set {SAVE_PROPERTY.get(column, 'the matching saveservice property')}=true)"
        for column in missing
    )
    st.info(f"**{chart}** needs {hints} — not present in this result file.")
    return False
