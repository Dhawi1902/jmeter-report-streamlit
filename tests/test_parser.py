import io

import pandas as pd
import pytest

import config
from core.parser import JtlError, load_jtl

from .conftest import SAMPLE_CSV


def test_parses_rows_and_types(frame):
    assert len(frame) == 4
    assert pd.api.types.is_datetime64_any_dtype(frame[config.TS])
    assert frame[config.SUCCESS].dtype == bool
    assert frame[config.SUCCESS].sum() == 3


def test_derives_thread_group(frame):
    assert set(frame[config.THREAD_GROUP]) == {"TG 1"}


def test_reports_absent_optional_columns(jtl):
    assert jtl.has(config.LATENCY, config.CONNECT)
    assert config.IDLE_TIME in jtl.missing_optional


FORMATTED = {
    "1700000000000": "2023-11-14 22:13:20",
    "1700000001000": "2023-11-14 22:13:21",
    "1700000002000": "2023-11-14 22:13:22",
    "1700000003000": "2023-11-14 22:13:23",
}


def test_accepts_formatted_timestamps():
    csv = SAMPLE_CSV
    for epoch, formatted in FORMATTED.items():
        csv = csv.replace(epoch, formatted)
    frame = load_jtl(io.StringIO(csv)).df
    assert frame[config.TS].iloc[0] == pd.Timestamp("2023-11-14 22:13:20")
    assert len(frame) == 4


def test_header_case_is_ignored():
    csv = SAMPLE_CSV.replace("timeStamp", "TIMESTAMP").replace("elapsed", "Elapsed", 1)
    assert len(load_jtl(io.StringIO(csv)).df) == 4


def test_rejects_xml():
    with pytest.raises(JtlError, match="XML"):
        load_jtl(io.StringIO('<?xml version="1.0"?><testResults/>'))


def test_rejects_file_without_header():
    with pytest.raises(JtlError, match="header"):
        load_jtl(io.StringIO("1700000000000,100,A,200,OK,TG 1-1,true\n"))


def test_rejects_missing_required_column():
    csv = SAMPLE_CSV.replace(",label,", ",name,")
    with pytest.raises(JtlError, match="label"):
        load_jtl(io.StringIO(csv))


def test_rejects_empty_file():
    with pytest.raises(JtlError, match="empty"):
        load_jtl(io.StringIO("   "))
