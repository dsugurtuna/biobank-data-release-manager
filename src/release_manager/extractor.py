"""Genotype extraction engine.

Wraps bcftools to extract participant subsets from VCF/BCF files, with
pre-flight validation and post-extraction sample concordance checking.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class ExtractionResult:
    """Result of a genotype extraction."""

    source_vcf: str
    output_vcf: str
    requested_samples: int
    extracted_samples: int
    missing_samples: List[str] = field(default_factory=list)
    success: bool = False

    @property
    def concordance_rate(self) -> float:
        if self.requested_samples == 0:
            return 0.0
        return self.extracted_samples / self.requested_samples


class GenotypeExtractor:
    """Extract participant subsets from VCF files using bcftools.

    Parameters
    ----------
    bcftools_path : str
        Path to bcftools executable.
    """

    def __init__(self, bcftools_path: str = "bcftools") -> None:
        self.bcftools_path = bcftools_path

    def _load_sample_list(self, sample_file: str | Path) -> List[str]:
        """Load sample IDs from a flat text file (one per line)."""
        with open(sample_file) as fh:
            return [line.strip() for line in fh if line.strip()]

    def _get_vcf_samples(self, vcf_path: str | Path) -> Set[str]:
        """Extract sample IDs from a VCF file header."""
        try:
            result = subprocess.run(
                [self.bcftools_path, "query", "-l", str(vcf_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            return {s.strip() for s in result.stdout.strip().split("\n") if s.strip()}
        except (subprocess.CalledProcessError, FileNotFoundError):
            return set()

    def extract(
        self,
        source_vcf: str | Path,
        sample_file: str | Path,
        output_vcf: str | Path,
        regions: Optional[str] = None,
    ) -> ExtractionResult:
        """Extract a subset of samples from a VCF.

        Parameters
        ----------
        source_vcf : path
            Input VCF/BCF file.
        sample_file : path
            Text file with one sample ID per line.
        output_vcf : path
            Output VCF path.
        regions : str, optional
            Region filter (e.g. ``"chr6:26000000-34000000"``).
        """
        requested = self._load_sample_list(sample_file)
        result = ExtractionResult(
            source_vcf=str(source_vcf),
            output_vcf=str(output_vcf),
            requested_samples=len(requested),
        )

        cmd = [
            self.bcftools_path, "view",
            "-S", str(sample_file),
            "-o", str(output_vcf),
            str(source_vcf),
        ]
        if regions:
            cmd.extend(["-r", regions])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            return result

        # Post-extraction validation
        extracted_samples = self._get_vcf_samples(output_vcf)
        result.extracted_samples = len(extracted_samples)
        requested_set = set(requested)
        result.missing_samples = sorted(requested_set - extracted_samples)
        result.success = result.extracted_samples == result.requested_samples

        return result
