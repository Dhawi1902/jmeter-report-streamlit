"""Write a synthetic JMeter CSV result file so the app can be tried without a real run.

    python tools/make_sample_jtl.py sample/sample.jtl --minutes 10
"""
from __future__ import annotations

import argparse
import csv
import random
import time
from pathlib import Path

HEADER = (
    "timeStamp,elapsed,label,responseCode,responseMessage,threadName,dataType,"
    "success,failureMessage,bytes,sentBytes,grpThreads,allThreads,URL,Latency,"
    "IdleTime,Connect"
).split(",")

SAMPLERS = (
    # label, base response time (ms), failure rate
    ("HomePage", 220, 0.005),
    ("Search", 480, 0.02),
    ("Login", 650, 0.01),
    ("Checkout", 1400, 0.06),
)
THREAD_GROUPS = ("Shop Users", "API Users")


def build_rows(minutes: int, threads: int, seed: int):
    random.seed(seed)
    start_ms = int(time.time() * 1000) - minutes * 60_000
    for second in range(minutes * 60):
        active = _active_threads(second, minutes * 60, threads)
        for _ in range(active):
            yield _row(start_ms + second * 1000 + random.randint(0, 999), active)


def _active_threads(second: int, total_seconds: int, threads: int) -> int:
    """Ramp up over the first fifth of the run, then hold."""
    ramp = max(total_seconds // 5, 1)
    return max(1, round(threads * min(second / ramp, 1.0)))


def _row(timestamp: int, active: int) -> dict:
    label, base, failure_rate = random.choice(SAMPLERS)
    load_factor = 1 + active / 40
    elapsed = max(1, int(random.gauss(base * load_factor, base * 0.25)))
    failed = random.random() < failure_rate
    group = random.choice(THREAD_GROUPS)
    latency = int(elapsed * random.uniform(0.6, 0.95))
    return {
        "timeStamp": timestamp,
        "elapsed": elapsed,
        "label": label,
        "responseCode": "500" if failed else "200",
        "responseMessage": "Internal Server Error" if failed else "OK",
        "threadName": f"{group} 1-{random.randint(1, max(active, 1))}",
        "dataType": "text",
        "success": "false" if failed else "true",
        "failureMessage": "Response code is not 200" if failed else "",
        "bytes": random.randint(900, 48_000),
        "sentBytes": random.randint(180, 1_200),
        "grpThreads": active,
        "allThreads": active * len(THREAD_GROUPS),
        "URL": f"https://example.test/{label.lower()}",
        "Latency": latency,
        "IdleTime": 0,
        "Connect": int(latency * random.uniform(0.05, 0.2)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--minutes", type=int, default=10)
    parser.add_argument("--threads", type=int, default=25)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        count = 0
        for row in build_rows(args.minutes, args.threads, args.seed):
            writer.writerow(row)
            count += 1
    print(f"Wrote {count:,} samples to {args.output}")


if __name__ == "__main__":
    main()
