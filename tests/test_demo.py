"""Smoke test: the README quickstart demo runs and prints what the README shows."""

import runpy
from pathlib import Path

DEMO = Path(__file__).resolve().parent.parent / "examples" / "demo.py"


def test_demo_output(capsys):
    runpy.run_path(str(DEMO), run_name="__main__")
    out = capsys.readouterr().out
    assert "Approved barcodes: 4; with a VCF sample ID: 3" in out
    assert "Extracted 3 of 3 requested" in out
    assert "Exact match: True; missing: []" in out
    assert "missing: ['VCF099']" in out
