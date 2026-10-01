"""Group failed samples the way the dashboard's Errors section does."""
from __future__ import annotations

import pandas as pd

import config

ERROR_TYPE = "Type of error"
UNKNOWN = "Unknown error"


def failures(frame: pd.DataFrame) -> pd.DataFrame:
    """Only the samples JMeter counts as errors, tagged with an error type."""
    failed = frame[~frame[config.SUCCESS]]
    return failed.assign(**{ERROR_TYPE: _error_type(failed)})


def error_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Counts per error type, as a share of all samples and of all errors."""
    failed = failures(frame)
    if failed.empty:
        return pd.DataFrame(columns=[ERROR_TYPE, "#Samples", "% of all", "% of errors"])
    counts = failed[ERROR_TYPE].value_counts().rename("#Samples").reset_index()
    counts.columns = [ERROR_TYPE, "#Samples"]
    counts["% of all"] = counts["#Samples"] / len(frame) * 100
    counts["% of errors"] = counts["#Samples"] / len(failed) * 100
    return counts


def top_errors_by_sampler(
    frame: pd.DataFrame, limit: int = config.TOP_ERRORS
) -> pd.DataFrame:
    """For each label: total samples, failures, and its most frequent error types."""
    failed = failures(frame)
    totals = frame.groupby(config.LABEL).size().rename("#Samples")
    rows = []
    for label, group in failed.groupby(config.LABEL, sort=True):
        row = {"Label": label, "#Samples": int(totals.get(label, 0)), "FAIL": len(group)}
        top = group[ERROR_TYPE].value_counts().head(limit)
        for position, (error_type, count) in enumerate(top.items(), start=1):
            row[f"Error #{position}"] = error_type
            row[f"Count #{position}"] = int(count)
        rows.append(row)
    return pd.DataFrame(rows)


def _error_type(failed: pd.DataFrame) -> pd.Series:
    """Prefer the assertion failure message; fall back to code/message."""
    code = _text(failed, config.RESPONSE_CODE)
    message = _text(failed, config.RESPONSE_MESSAGE)
    assertion = _text(failed, config.FAILURE_MESSAGE)
    combined = (code + "/" + message).str.strip("/")
    error_type = assertion.where(assertion.str.len() > 0, combined)
    return error_type.where(error_type.str.len() > 0, UNKNOWN)


def _text(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series("", index=frame.index, dtype="object")
    return frame[column].fillna("").astype(str).str.strip()
