"""Column names, defaults and the user-adjustable settings object."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

# --- JTL columns, spelled exactly as JMeter's SaveService writes them ---
TIMESTAMP = "timeStamp"
ELAPSED = "elapsed"
LABEL = "label"
RESPONSE_CODE = "responseCode"
RESPONSE_MESSAGE = "responseMessage"
THREAD_NAME = "threadName"
DATA_TYPE = "dataType"
SUCCESS = "success"
FAILURE_MESSAGE = "failureMessage"
BYTES = "bytes"
SENT_BYTES = "sentBytes"
GRP_THREADS = "grpThreads"
ALL_THREADS = "allThreads"
URL = "URL"
LATENCY = "Latency"
IDLE_TIME = "IdleTime"
CONNECT = "Connect"

KNOWN_COLUMNS = (
    TIMESTAMP, ELAPSED, LABEL, RESPONSE_CODE, RESPONSE_MESSAGE, THREAD_NAME,
    DATA_TYPE, SUCCESS, FAILURE_MESSAGE, BYTES, SENT_BYTES, GRP_THREADS,
    ALL_THREADS, URL, LATENCY, IDLE_TIME, CONNECT,
)

# Columns we add while parsing.
TS = "ts"                    # timeStamp as datetime
THREAD_GROUP = "threadGroup"  # threadName without its "-<n>" suffix
BUCKET = "bucket"             # start of the time bucket a sample falls in

REQUIRED_COLUMNS = (TIMESTAMP, ELAPSED, LABEL, SUCCESS)
NUMERIC_COLUMNS = (
    ELAPSED, BYTES, SENT_BYTES, GRP_THREADS, ALL_THREADS, LATENCY, IDLE_TIME, CONNECT,
)
TEXT_COLUMNS = (LABEL, RESPONSE_CODE, RESPONSE_MESSAGE, FAILURE_MESSAGE, URL, DATA_TYPE)

# --- Defaults, mirroring jmeter.reportgenerator.* properties ---
DEFAULT_GRANULARITY_MS = 60_000
DEFAULT_APDEX_SATISFIED_MS = 500
DEFAULT_APDEX_TOLERATED_MS = 1_500
PERCENTILES = (90, 95, 99)
DISTRIBUTION_BUCKET_MS = 500
TOP_ERRORS = 5

GRANULARITY_CHOICES = {
    "1 second": 1_000,
    "5 seconds": 5_000,
    "10 seconds": 10_000,
    "30 seconds": 30_000,
    "1 minute": 60_000,
    "5 minutes": 300_000,
}


@dataclass(frozen=True)
class Settings:
    """Everything the sidebar controls. Immutable: rebuilt on each rerun."""

    granularity_ms: int = DEFAULT_GRANULARITY_MS
    apdex_satisfied_ms: int = DEFAULT_APDEX_SATISFIED_MS
    apdex_tolerated_ms: int = DEFAULT_APDEX_TOLERATED_MS
    labels: tuple[str, ...] = ()
    start: datetime | None = None
    end: datetime | None = None
