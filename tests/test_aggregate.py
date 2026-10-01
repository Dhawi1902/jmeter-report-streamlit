import pandas as pd
import pytest

import config
from core import aggregate


def _row(table, label):
    return table[table["Label"] == label].iloc[0]


def test_duration_spans_first_start_to_last_end(frame):
    # First sample starts at t=0s; the 2000ms sample started at t=2s and ends at t=4s.
    assert aggregate.duration_seconds(frame) == pytest.approx(4.0)


def test_statistics_total_row(frame):
    total = _row(aggregate.statistics_table(frame), aggregate.TOTAL_LABEL)
    assert total["#Samples"] == 4
    assert total["FAIL"] == 1
    assert total["Error %"] == pytest.approx(25.0)
    assert total["Average"] == pytest.approx(775.0)
    assert total["Min"] == 100
    assert total["Max"] == 2000
    assert total["Throughput /s"] == pytest.approx(4 / 4.0)


def test_statistics_per_label(frame):
    row = _row(aggregate.statistics_table(frame), "A")
    assert row["#Samples"] == 2
    assert row["FAIL"] == 0
    assert row["Average"] == pytest.approx(200.0)


def test_statistics_percentiles_are_interpolated(frame):
    total = _row(aggregate.statistics_table(frame), aggregate.TOTAL_LABEL)
    # sorted: 100, 300, 700, 2000 -> p90 sits between 700 and 2000.
    assert total["p90"] == pytest.approx(1610.0)


def test_apdex_counts_failures_as_frustrated(frame):
    total = _row(aggregate.apdex_table(frame, 500, 1500), aggregate.TOTAL_LABEL)
    assert total["Satisfied"] == 2   # 100ms and 300ms, both successful
    assert total["Tolerated"] == 1   # 700ms, successful
    assert total["Frustrated"] == 1  # the failed sample
    assert total["Apdex"] == pytest.approx((2 + 0.5) / 4)


def test_apdex_thresholds_are_applied(frame):
    total = _row(aggregate.apdex_table(frame, 50, 100), aggregate.TOTAL_LABEL)
    assert total["Satisfied"] == 0
    assert total["Tolerated"] == 1  # the 100ms sample
    assert total["Frustrated"] == 3


def test_requests_summary(frame):
    summary = aggregate.requests_summary(frame).set_index("Result")["#Samples"]
    assert summary["Success"] == 3
    assert summary["Failure"] == 1


def test_rate_over_time_is_per_second(frame):
    rate = aggregate.rate_over_time(frame, granularity_ms=1_000)
    assert len(rate) == 4
    assert set(rate["per second"]) == {1.0}

    coarse = aggregate.rate_over_time(frame, granularity_ms=60_000)
    assert len(coarse) == 1
    assert coarse["per second"].iloc[0] == pytest.approx(4 / 60)


def test_over_time_groups_by_label(frame):
    series = aggregate.over_time(frame, config.ELAPSED, granularity_ms=60_000)
    assert set(series[config.LABEL]) == {"A", "B"}
    assert _label_value(series, "A", config.ELAPSED) == pytest.approx(200.0)


def test_percentiles_over_time_uses_successful_samples_only(frame):
    table = aggregate.percentiles_over_time(frame, granularity_ms=60_000)
    assert len(table) == 1
    # successful elapsed times are 100, 300, 700
    assert table["Max"].iloc[0] == 700
    assert table["p90"].iloc[0] == pytest.approx(620.0)


def test_active_threads_over_time_takes_the_peak(frame):
    table = aggregate.active_threads_over_time(frame, granularity_ms=60_000)
    assert table["threads"].iloc[0] == 2
    assert table[config.THREAD_GROUP].iloc[0] == "TG 1"


def test_bytes_over_time_converts_to_kb_per_second(frame):
    table = aggregate.bytes_over_time(frame, granularity_ms=60_000)
    assert table["Received KB/s"].iloc[0] == pytest.approx(4096 / 1024 / 60)
    assert table["Sent KB/s"].iloc[0] == pytest.approx(400 / 1024 / 60)


def test_response_time_distribution_bands(frame):
    table = aggregate.response_time_distribution(frame, bucket_ms=500)
    bands = table.set_index(["band", config.LABEL])["#Samples"]
    assert bands[(0, "A")] == 2       # 100ms and 300ms
    assert bands[(500, "B")] == 1     # 700ms
    assert bands[(2000, "B")] == 1


def test_percentile_curve_spans_zero_to_hundred(frame):
    curve = aggregate.percentile_curve(frame, step=10.0)
    for_a = curve[curve[config.LABEL] == "A"]
    assert for_a["percentile"].min() == 0
    assert for_a["percentile"].max() == 100
    assert for_a[config.ELAPSED].iloc[0] == 100
    assert for_a[config.ELAPSED].iloc[-1] == 300


def test_apply_filters_narrows_labels_and_window(frame):
    settings = config.Settings(labels=("A",))
    assert len(aggregate.apply_filters(frame, settings)) == 2

    start, end = aggregate.time_bounds(frame)
    windowed = config.Settings(start=start, end=end - pd.Timedelta(seconds=2))
    assert len(aggregate.apply_filters(frame, windowed)) == 2


def _label_value(table, label, column):
    return table[table[config.LABEL] == label][column].iloc[0]
