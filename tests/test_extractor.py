"""Tests for GenotypeExtractor, run against a fake bcftools."""

import stat
import sys
from pathlib import Path

import pytest

from release_manager.extractor import GenotypeExtractor, output_type_for

FAKE = Path(__file__).resolve().parent.parent / "examples" / "fake_bcftools.py"


@pytest.fixture()
def bcftools(tmp_path: Path) -> str:
    exe = tmp_path / "bin" / "bcftools"
    exe.parent.mkdir()
    exe.write_text(f"#!{sys.executable}\n" + FAKE.read_text())
    exe.chmod(exe.stat().st_mode | stat.S_IXUSR)
    return str(exe)


@pytest.fixture()
def source(tmp_path: Path) -> Path:
    vcf = tmp_path / "source.vcf"
    header = "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tS1\tS2\tS3\n"
    vcf.write_text(
        "##fileformat=VCFv4.2\n"
        + header
        + "1\t100\trs1\tA\tG\t.\tPASS\t.\tGT\t0/0\t0/1\t1/1\n"
    )
    return vcf


def _samples(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "samples.txt"
    p.write_text(text)
    return p


def test_extract_exact_subset(bcftools, source, tmp_path):
    out = tmp_path / "out.vcf.gz"
    result = GenotypeExtractor(bcftools).extract(
        source, _samples(tmp_path, "S1\nS3\n"), out
    )
    assert result.error is None
    assert result.success
    assert result.extracted_samples == 2
    assert result.concordance_rate == 1.0


def test_preflight_stops_on_missing_sample(bcftools, source, tmp_path):
    out = tmp_path / "out.vcf.gz"
    result = GenotypeExtractor(bcftools).extract(
        source, _samples(tmp_path, "S1\nS9\n"), out
    )
    assert not result.success
    assert result.missing_samples == ["S9"]
    assert "nothing extracted" in (result.error or "")
    assert not out.exists()


def test_allow_missing_extracts_the_rest(bcftools, source, tmp_path):
    out = tmp_path / "out.vcf.gz"
    result = GenotypeExtractor(bcftools).extract(
        source, _samples(tmp_path, "S1\nS9\n"), out, allow_missing=True
    )
    assert not result.success
    assert result.extracted_samples == 1
    assert result.missing_samples == ["S9"]


def test_duplicate_requests_reported(bcftools, source, tmp_path):
    out = tmp_path / "out.vcf.gz"
    result = GenotypeExtractor(bcftools).extract(
        source, _samples(tmp_path, "S1\nS1\n"), out
    )
    assert result.duplicate_requests == ["S1"]
    assert result.requested_samples == 1
    assert result.success


def test_unreadable_source_reports_error(bcftools, tmp_path):
    result = GenotypeExtractor(bcftools).extract(
        tmp_path / "nope.vcf", _samples(tmp_path, "S1\n"), tmp_path / "o.vcf.gz"
    )
    assert not result.success
    assert "Could not read samples" in (result.error or "")


def test_missing_bcftools_reports_error(source, tmp_path):
    result = GenotypeExtractor("/nonexistent/bcftools").extract(
        source, _samples(tmp_path, "S1\n"), tmp_path / "o.vcf.gz"
    )
    assert not result.success
    assert result.error


@pytest.mark.parametrize(
    ("name", "code"),
    [("a.vcf.gz", "z"), ("a.bcf", "b"), ("a.vcf", "v"), ("A.VCF.GZ", "z")],
)
def test_output_type(name, code):
    assert output_type_for(name) == code


def test_output_type_unknown():
    with pytest.raises(ValueError):
        output_type_for("a.txt")
