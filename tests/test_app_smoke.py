"""Runs the whole Streamlit script against a generated .jtl, every tab included."""
from __future__ import annotations

import csv
from pathlib import Path

import pytest

from tools.make_sample_jtl import HEADER, build_rows

APP = Path(__file__).resolve().parents[1] / "app.py"


@pytest.fixture(scope="module")
def sample_file(tmp_path_factory):
    path = tmp_path_factory.mktemp("jtl") / "run.jtl"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=HEADER)
        writer.writeheader()
        writer.writerows(build_rows(minutes=2, threads=6, seed=1))
    return path


def _run(path: Path):
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(str(APP), default_timeout=120)
    app.run()
    app.text_input[0].set_value(str(path)).run()
    return app


def test_app_renders_every_tab_without_error(sample_file):
    app = _run(sample_file)
    assert not app.exception
    assert len(app.tabs) == 5
    assert app.dataframe, "expected at least the statistics table to render"


def test_app_reports_a_bad_file(tmp_path):
    from streamlit.testing.v1 import AppTest

    broken = tmp_path / "broken.jtl"
    broken.write_text("<?xml version='1.0'?><testResults/>", encoding="utf-8")
    app = AppTest.from_file(str(APP), default_timeout=120)
    app.run()
    app.text_input[0].set_value(str(broken)).run()
    assert not app.exception
    assert "XML" in app.error[0].value
