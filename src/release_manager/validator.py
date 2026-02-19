"""Sample validation module.

Validates that extracted output files contain the expected samples, checking
concordance between request lists and actual file contents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Set


@dataclass
class ValidationReport:
    """Report from sample concordance validation."""

    expected_count: int = 0
    actual_count: int = 0
    matched: int = 0
    missing: List[str] = field(default_factory=list)
    unexpected: List[str] = field(default_factory=list)

    @property
    def is_concordant(self) -> bool:
        return self.expected_count == self.actual_count and len(self.missing) == 0

    @property
    def concordance_rate(self) -> float:
        if self.expected_count == 0:
            return 0.0
        return self.matched / self.expected_count


class SampleValidator:
    """Validate sample concordance between request and output.

    Compares a requested sample list against what actually appears in an
    output file (PLINK .fam, VCF header, or plain ID list).
    """

    @staticmethod
    def load_ids_from_fam(fam_path: str | Path) -> Set[str]:
        """Extract sample IDs from a PLINK .fam file (column 2)."""
        ids: Set[str] = set()
        with open(fam_path) as fh:
            for line in fh:
                parts = line.strip().split()
                if len(parts) >= 2:
                    ids.add(parts[1])
        return ids

    @staticmethod
    def load_ids_from_list(list_path: str | Path) -> Set[str]:
        """Load sample IDs from a plain text file (one per line)."""
        with open(list_path) as fh:
            return {line.strip() for line in fh if line.strip()}

    def validate(
        self,
        expected_ids: Set[str],
        actual_ids: Set[str],
    ) -> ValidationReport:
        """Compare expected and actual sample ID sets.

        Parameters
        ----------
        expected_ids : set of str
            The samples that were requested.
        actual_ids : set of str
            The samples that appear in the output.
        """
        matched = expected_ids & actual_ids
        missing = sorted(expected_ids - actual_ids)
        unexpected = sorted(actual_ids - expected_ids)

        return ValidationReport(
            expected_count=len(expected_ids),
            actual_count=len(actual_ids),
            matched=len(matched),
            missing=missing,
            unexpected=unexpected,
        )

    def validate_fam(
        self,
        request_file: str | Path,
        fam_file: str | Path,
    ) -> ValidationReport:
        """Validate a .fam file against a request list."""
        expected = self.load_ids_from_list(request_file)
        actual = self.load_ids_from_fam(fam_file)
        return self.validate(expected, actual)
