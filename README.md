# JMeter report in Streamlit

A replacement for JMeter's generated HTML dashboard, built entirely from a CSV
`.jtl` result file — the same input JMeter's own report generator uses, so there
is nothing in the native report that cannot be recomputed here.

## Run it

```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt   # macOS/Linux: .venv/bin/python
.venv/Scripts/python -m streamlit run app.py
```

Then either upload a `.jtl` in the sidebar, or paste its path (better for large
files — nothing is copied into memory twice).

No result file to hand? Generate one:

```bash
python tools/make_sample_jtl.py sample/sample.jtl --minutes 10 --threads 25
```

## Tests

```bash
.venv/Scripts/python -m pytest
```

`tests/test_app_smoke.py` runs the real Streamlit script through `AppTest`, so
every tab and chart is exercised, not just the aggregation functions.

## What's covered

| Tab | Panels |
|---|---|
| Dashboard | headline metrics, APDEX (colour-coded), success/failure pie, statistics table |
| Over time | response times, percentiles, active threads, bytes throughput, latencies, connect time |
| Throughput | hits/s, transactions/s, response codes/s, response time and latency vs request rate |
| Response times | percentile curves, distribution, overview, time vs threads |
| Errors | error types, top errors per sampler, raw failed samples |

Sidebar controls that the static report cannot give you: granularity,
APDEX T/F thresholds, sampler filter and a time window — all applied live.

## Input requirements

CSV output with a header row. In `user.properties`:

```properties
jmeter.save.saveservice.output_format=csv
jmeter.save.saveservice.print_field_names=true
```

Everything except `timeStamp`, `elapsed`, `label` and `success` is optional; any
panel whose column is absent explains which `saveservice` property to switch on
instead of rendering. XML `.jtl` files are rejected with that message — convert
to CSV rather than parsing them here.

## Known differences from the native report

- **Percentiles.** JMeter computes them from an HdrHistogram (lossy by design);
  this uses exact interpolated quantiles. Expect differences of a millisecond or
  two, more on long-tailed distributions.
- **Timestamps** are treated as UTC. JMeter's HTML report renders them in the
  machine's local zone, so chart x-axes can be offset from it.
- **Hits per second** counts every row in the file. If sub-results (embedded
  resources) were saved, they are included — same as JMeter.

## Layout

```
app.py              Streamlit entry point: load, filter, render five tabs
config.py           column names, defaults, the Settings object
core/parser.py      .jtl sniffing, validation, typing
core/aggregate.py   statistics, APDEX, over-time series, distributions
core/errors.py      error grouping
charts/common.py    thin plotly wrappers
views/              one module per tab, plus the sidebar
tools/              sample data generator
```

Aggregation is pure pandas over a DataFrame and returns new frames; the view
layer only arranges what those functions return.

## If your files get big

Parsing is cached per file (upload bytes, or path + mtime), so widget changes do
not re-read anything. Beyond roughly 5M rows, the useful next steps are reading
with `polars.scan_csv` in `core/parser.py` and pre-aggregating to buckets once
rather than filtering the full frame per tab.
