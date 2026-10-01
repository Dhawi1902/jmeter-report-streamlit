"""Turn raw samples into the tables and series the JMeter dashboard shows.

Every function takes a DataFrame and returns a new one; nothing is mutated.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

import config

TOTAL_LABEL = "Total"


# --------------------------------------------------------------------------- #
# selection helpers
# --------------------------------------------------------------------------- #
def apply_filters(frame: pd.DataFrame, settings: config.Settings) -> pd.DataFrame:
    """Narrow the samples to the labels and time window chosen in the sidebar."""
    selected = frame
    if settings.labels:
        selected = selected[selected[config.LABEL].isin(settings.labels)]
    if settings.start is not None:
        selected = selected[selected[config.TS] >= pd.Timestamp(settings.start)]
    if settings.end is not None:
        selected = selected[selected[config.TS] <= pd.Timestamp(settings.end)]
    return selected


def time_bounds(frame: pd.DataFrame) -> tuple[pd.Timestamp, pd.Timestamp]:
    return frame[config.TS].min(), frame[config.TS].max()


def duration_seconds(frame: pd.DataFrame) -> float:
    """Wall-clock span of a run: first sample start to last sample end."""
    if frame.empty:
        return 0.0
    start = frame[config.TS].min()
    end = (frame[config.TS] + pd.to_timedelta(frame[config.ELAPSED], unit="ms")).max()
    return max((end - start).total_seconds(), 0.001)


def buckets(frame: pd.DataFrame, granularity_ms: int) -> pd.Series:
    """Floor each timestamp to the start of the time bucket it belongs to."""
    return frame[config.TS].dt.floor(f"{granularity_ms}ms")


def pct_label(percentile: float) -> str:
    return f"p{percentile:g}"


# --------------------------------------------------------------------------- #
# dashboard tables
# --------------------------------------------------------------------------- #
def statistics_table(
    frame: pd.DataFrame, percentiles: tuple[int, ...] = config.PERCENTILES
) -> pd.DataFrame:
    """The Statistics table: one row per label, with a Total row first."""
    rows = [_statistics_row(TOTAL_LABEL, frame, percentiles)]
    rows += [
        _statistics_row(label, group, percentiles)
        for label, group in frame.groupby(config.LABEL, sort=True)
    ]
    return pd.DataFrame(rows)


def _statistics_row(label: str, group: pd.DataFrame, percentiles: tuple[int, ...]) -> dict:
    elapsed = group[config.ELAPSED]
    samples = len(group)
    failures = int((~group[config.SUCCESS]).sum())
    seconds = duration_seconds(group)
    row = {
        "Label": label,
        "#Samples": samples,
        "FAIL": failures,
        "Error %": _ratio(failures, samples) * 100,
        "Average": elapsed.mean(),
        "Min": elapsed.min(),
        "Max": elapsed.max(),
        "Median": elapsed.median(),
    }
    for percentile in percentiles:
        row[pct_label(percentile)] = elapsed.quantile(percentile / 100)
    row["Throughput /s"] = samples / seconds
    row["Received KB/s"] = _kb_per_second(group, config.BYTES, seconds)
    row["Sent KB/s"] = _kb_per_second(group, config.SENT_BYTES, seconds)
    return row


def apdex_table(frame: pd.DataFrame, satisfied_ms: int, tolerated_ms: int) -> pd.DataFrame:
    """APDEX per label. Failed samples are frustrated whatever their response time."""
    rows = [_apdex_row(TOTAL_LABEL, frame, satisfied_ms, tolerated_ms)]
    rows += [
        _apdex_row(label, group, satisfied_ms, tolerated_ms)
        for label, group in frame.groupby(config.LABEL, sort=True)
    ]
    return pd.DataFrame(rows)


def _apdex_row(label: str, group: pd.DataFrame, satisfied_ms: int, tolerated_ms: int) -> dict:
    ok = group[config.SUCCESS]
    elapsed = group[config.ELAPSED]
    satisfied = int((ok & (elapsed <= satisfied_ms)).sum())
    tolerated = int((ok & (elapsed > satisfied_ms) & (elapsed <= tolerated_ms)).sum())
    samples = len(group)
    return {
        "Label": label,
        "Apdex": _ratio(satisfied + tolerated / 2, samples),
        "Satisfied": satisfied,
        "Tolerated": tolerated,
        "Frustrated": samples - satisfied - tolerated,
        "T (ms)": satisfied_ms,
        "F (ms)": tolerated_ms,
    }


def requests_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """The OK / KO split behind the Requests Summary pie."""
    passed = int(frame[config.SUCCESS].sum())
    return pd.DataFrame(
        [
            {"Result": "Success", "#Samples": passed},
            {"Result": "Failure", "#Samples": len(frame) - passed},
        ]
    )


# --------------------------------------------------------------------------- #
# over-time series
# --------------------------------------------------------------------------- #
def over_time(
    frame: pd.DataFrame, value_column: str, granularity_ms: int, how: str = "mean"
) -> pd.DataFrame:
    """Aggregate one numeric column per time bucket, per label."""
    keys = [buckets(frame, granularity_ms), config.LABEL]
    series = frame.groupby(keys)[value_column].agg(how).rename(value_column)
    return series.reset_index().rename(columns={config.TS: config.BUCKET})


def percentiles_over_time(
    frame: pd.DataFrame,
    granularity_ms: int,
    percentiles: tuple[int, ...] = config.PERCENTILES,
) -> pd.DataFrame:
    """Percentiles of successful response times per time bucket."""
    successful = frame[frame[config.SUCCESS]]
    grouped = successful.groupby(buckets(successful, granularity_ms))[config.ELAPSED]
    columns = {pct_label(p): grouped.quantile(p / 100) for p in percentiles}
    columns["Average"] = grouped.mean()
    columns["Min"] = grouped.min()
    columns["Max"] = grouped.max()
    table = pd.DataFrame(columns)
    table.index.name = config.BUCKET
    return table.reset_index()


def active_threads_over_time(frame: pd.DataFrame, granularity_ms: int) -> pd.DataFrame:
    """Peak active threads per bucket, split by thread group when available."""
    if config.THREAD_GROUP in frame.columns and config.GRP_THREADS in frame.columns:
        keys = [buckets(frame, granularity_ms), config.THREAD_GROUP]
        table = frame.groupby(keys)[config.GRP_THREADS].max().rename("threads").reset_index()
    else:
        grouped = frame.groupby(buckets(frame, granularity_ms))[config.ALL_THREADS]
        table = grouped.max().rename("threads").reset_index()
        table[config.THREAD_GROUP] = "All threads"
    return table.rename(columns={config.TS: config.BUCKET})


def bytes_over_time(frame: pd.DataFrame, granularity_ms: int) -> pd.DataFrame:
    """Received and sent KB per second per bucket."""
    seconds = granularity_ms / 1000
    grouped = frame.groupby(buckets(frame, granularity_ms))
    columns = {}
    if config.BYTES in frame.columns:
        columns["Received KB/s"] = grouped[config.BYTES].sum() / 1024 / seconds
    if config.SENT_BYTES in frame.columns:
        columns["Sent KB/s"] = grouped[config.SENT_BYTES].sum() / 1024 / seconds
    table = pd.DataFrame(columns)
    table.index.name = config.BUCKET
    return table.reset_index()


# --------------------------------------------------------------------------- #
# throughput
# --------------------------------------------------------------------------- #
def rate_over_time(
    frame: pd.DataFrame, granularity_ms: int, group_column: str | None = None
) -> pd.DataFrame:
    """Samples per second per bucket, optionally split by a column."""
    seconds = granularity_ms / 1000
    keys = [buckets(frame, granularity_ms)]
    if group_column:
        keys.append(group_column)
    table = (frame.groupby(keys).size() / seconds).rename("per second").reset_index()
    return table.rename(columns={config.TS: config.BUCKET})


def response_time_vs_rate(
    frame: pd.DataFrame, granularity_ms: int, value_column: str = config.ELAPSED
) -> pd.DataFrame:
    """One point per label per bucket: requests/second against response time."""
    seconds = granularity_ms / 1000
    grouped = frame.groupby([buckets(frame, granularity_ms), config.LABEL])
    table = grouped[value_column].agg(["size", "mean"]).reset_index()
    table["per second"] = table["size"] / seconds
    table = table.rename(columns={"mean": "response time", config.TS: config.BUCKET})
    return table.drop(columns=["size"])


# --------------------------------------------------------------------------- #
# response time shape
# --------------------------------------------------------------------------- #
def percentile_curve(frame: pd.DataFrame, step: float = 1.0) -> pd.DataFrame:
    """Response time at every percentile, per label."""
    points = np.arange(0.0, 100.0 + step, step)
    curves = [
        pd.DataFrame(
            {
                config.LABEL: label,
                "percentile": points,
                config.ELAPSED: np.percentile(group[config.ELAPSED], points),
            }
        )
        for label, group in frame.groupby(config.LABEL, sort=True)
    ]
    return pd.concat(curves, ignore_index=True) if curves else pd.DataFrame()


def response_time_distribution(
    frame: pd.DataFrame, bucket_ms: int = config.DISTRIBUTION_BUCKET_MS
) -> pd.DataFrame:
    """Sample counts per response time band, per label."""
    bands = (frame[config.ELAPSED] // bucket_ms * bucket_ms).rename("band")
    return frame.groupby([bands, config.LABEL]).size().rename("#Samples").reset_index()


def time_vs_threads(frame: pd.DataFrame) -> pd.DataFrame:
    """Average response time at each observed active-thread count, per label."""
    grouped = frame.groupby([config.ALL_THREADS, config.LABEL])[config.ELAPSED]
    return grouped.mean().rename(config.ELAPSED).reset_index()


# --------------------------------------------------------------------------- #
def _ratio(part: float, whole: float) -> float:
    return float(part) / whole if whole else 0.0


def _kb_per_second(group: pd.DataFrame, column: str, seconds: float) -> float:
    if column not in group.columns:
        return float("nan")
    return group[column].sum() / 1024 / seconds
