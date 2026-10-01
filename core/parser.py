"""Read a JMeter CSV results file (.jtl) into a normalised DataFrame.

Only CSV is supported: XML results carry the same data but parse an order of
magnitude slower, and the HTML dashboard does not need anything extra from them.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import IO

import pandas as pd

import config

PEEK_BYTES = 4096


class JtlError(ValueError):
    """The input is not a usable JMeter CSV result file."""


@dataclass(frozen=True)
class Jtl:
    """A parsed result file plus the set of columns it actually contains."""

    df: pd.DataFrame
    columns: frozenset[str]

    def has(self, *columns: str) -> bool:
        return all(column in self.columns for column in columns)

    @property
    def missing_optional(self) -> tuple[str, ...]:
        return tuple(c for c in config.KNOWN_COLUMNS if c not in self.columns)


def load_jtl(source: str | Path | IO) -> Jtl:
    """Parse `source` (a path or a file-like object) into a `Jtl`."""
    head = _peek(source)
    _reject_unsupported(head)
    frame = pd.read_csv(source, low_memory=False)
    frame = frame.rename(columns=_canonical_names(frame.columns))
    _require_columns(frame.columns)
    frame = _coerce(frame)
    if frame.empty:
        raise JtlError("No usable rows: every row had an unreadable timestamp or elapsed time.")
    return Jtl(df=frame, columns=frozenset(frame.columns))


def _peek(source: str | Path | IO) -> str:
    """Return the first few KB of `source`, leaving file objects rewound."""
    if hasattr(source, "read"):
        source.seek(0)
        head = source.read(PEEK_BYTES)
        source.seek(0)
        return head.decode("utf-8", "replace") if isinstance(head, bytes) else head
    with open(source, "r", encoding="utf-8", errors="replace") as handle:
        return handle.read(PEEK_BYTES)


def _reject_unsupported(head: str) -> None:
    stripped = head.lstrip()
    if not stripped:
        raise JtlError("The file is empty.")
    if stripped.startswith("<"):
        raise JtlError(
            "This looks like an XML .jtl. Re-run with CSV output "
            "(jmeter.save.saveservice.output_format=csv) or convert it first."
        )
    first_line = stripped.splitlines()[0]
    if config.TIMESTAMP.lower() not in first_line.lower():
        raise JtlError(
            "No header row found. Set jmeter.save.saveservice.print_field_names=true "
            "so the .jtl starts with a 'timeStamp,elapsed,label,...' line."
        )


def _canonical_names(names) -> dict[str, str]:
    """Map the file's header to JMeter's canonical spelling, ignoring case."""
    known = {column.lower(): column for column in config.KNOWN_COLUMNS}
    return {name: known.get(str(name).strip().lower(), str(name).strip()) for name in names}


def _require_columns(columns) -> None:
    missing = [column for column in config.REQUIRED_COLUMNS if column not in columns]
    if missing:
        raise JtlError(f"Missing required column(s): {', '.join(missing)}")


def _coerce(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with typed columns and the derived ts / threadGroup columns."""
    derived = {config.TS: _to_datetime(frame[config.TIMESTAMP])}
    for column in config.NUMERIC_COLUMNS:
        if column in frame.columns:
            derived[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in config.TEXT_COLUMNS:
        if column in frame.columns:
            derived[column] = frame[column].fillna("").astype(str)
    derived[config.SUCCESS] = _to_bool(frame[config.SUCCESS])
    if config.THREAD_NAME in frame.columns:
        derived[config.THREAD_GROUP] = _thread_group(frame[config.THREAD_NAME])
    return frame.assign(**derived).dropna(subset=[config.TS, config.ELAPSED])


def _to_datetime(values: pd.Series) -> pd.Series:
    """Accept epoch milliseconds (JMeter's default) or a formatted timestamp."""
    numeric = pd.to_numeric(values, errors="coerce")
    if numeric.notna().all():
        return pd.to_datetime(numeric, unit="ms")
    return pd.to_datetime(values, errors="coerce")


def _to_bool(values: pd.Series) -> pd.Series:
    if values.dtype == bool:
        return values
    return values.astype(str).str.strip().str.lower().eq("true")


def _thread_group(values: pd.Series) -> pd.Series:
    """'Shop Users 1-14' -> 'Shop Users 1' (the thread group name JMeter shows)."""
    return values.fillna("").astype(str).str.rsplit("-", n=1).str[0].str.strip()
