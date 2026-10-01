import io

import pytest

from core import errors
from core.parser import load_jtl

from .conftest import SAMPLE_CSV


def test_error_table_uses_the_assertion_message(frame):
    table = errors.error_table(frame)
    assert len(table) == 1
    row = table.iloc[0]
    assert row[errors.ERROR_TYPE] == "Assertion failed"
    assert row["#Samples"] == 1
    assert row["% of all"] == pytest.approx(25.0)
    assert row["% of errors"] == pytest.approx(100.0)


def test_error_table_falls_back_to_code_and_message():
    csv = SAMPLE_CSV.replace("Assertion failed", "")
    frame = load_jtl(io.StringIO(csv)).df
    assert errors.error_table(frame).iloc[0][errors.ERROR_TYPE] == "500/Server Error"


def test_top_errors_by_sampler(frame):
    table = errors.top_errors_by_sampler(frame)
    assert list(table["Label"]) == ["B"]
    row = table.iloc[0]
    assert row["#Samples"] == 2
    assert row["FAIL"] == 1
    assert row["Error #1"] == "Assertion failed"
    assert row["Count #1"] == 1


def test_no_errors_gives_empty_tables():
    csv = SAMPLE_CSV.replace("false", "true")
    frame = load_jtl(io.StringIO(csv)).df
    assert errors.error_table(frame).empty
    assert errors.top_errors_by_sampler(frame).empty
