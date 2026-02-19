"""Tests for release_manager.validator."""

from pathlib import Path

import pytest

from release_manager.validator import SampleValidator


@pytest.fixture()
def fam_file(tmp_path: Path) -> Path:
    p = tmp_path / "test.fam"
    p.write_text(
        "S001 S001 0 0 1 -9\n"
        "S002 S002 0 0 2 -9\n"
        "S003 S003 0 0 1 -9\n"
    )
    return p


@pytest.fixture()
def request_file(tmp_path: Path) -> Path:
    p = tmp_path / "request.txt"
    p.write_text("S001\nS002\nS004\n")
    return p


class TestSampleValidator:
    def test_validate_concordant(self) -> None:
        validator = SampleValidator()
        report = validator.validate({"A", "B"}, {"A", "B"})
        assert report.is_concordant
        assert report.concordance_rate == 1.0

    def test_validate_missing(self) -> None:
        validator = SampleValidator()
        report = validator.validate({"A", "B", "C"}, {"A", "B"})
        assert not report.is_concordant
        assert report.missing == ["C"]
        assert report.concordance_rate == pytest.approx(2 / 3)

    def test_validate_unexpected(self) -> None:
        validator = SampleValidator()
        report = validator.validate({"A"}, {"A", "B"})
        assert report.unexpected == ["B"]

    def test_validate_fam(self, request_file: Path, fam_file: Path) -> None:
        validator = SampleValidator()
        report = validator.validate_fam(request_file, fam_file)
        assert report.expected_count == 3
        assert report.actual_count == 3
        assert report.matched == 2  # S001, S002
        assert "S004" in report.missing
        assert "S003" in report.unexpected
