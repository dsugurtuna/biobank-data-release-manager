"""Genotype extraction engine.

Wraps bcftools to extract a participant subset from a VCF/BCF, with a
pre-flight check that every requested sample exists in the source and a
post-extraction check that the output holds exactly the requested samples.
"""

from __future__ import annotations

import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

_OUTPUT_TYPES = {".vcf.gz": "z", ".vcf.bgz": "z", ".bcf": "b", ".vcf": "v"}


def output_type_for(path: str | Path) -> str:
    """Return the bcftools -O code for an output file name.

    Setting -O explicitly avoids writing uncompressed text to a file named
    .vcf.gz on bcftools versions that do not infer the type from the name.
    """
    name = str(path).lower()
    for suffix, code in _OUTPUT_TYPES.items():
        if name.endswith(suffix):
            return code
    raise ValueError(
        f"Cannot infer output type from {path!r}; use .vcf.gz, .bcf or .vcf"
    )


@dataclass
class ExtractionResult:
    """Result of a genotype extraction."""

    source_vcf: str
    output_vcf: str
    requested_samples: int
    extracted_samples: int = 0
    # Requested but not in the source (pre-flight) or not in the output.
    missing_samples: list[str] = field(default_factory=list)
    # In the output but not requested.
    unexpected_samples: list[str] = field(default_factory=list)
    duplicate_requests: list[str] = field(default_factory=list)
    success: bool = False
    error: str | None = None

    @property
    def concordance_rate(self) -> float:
        if self.requested_samples == 0:
            return 0.0
        return (
            self.extracted_samples - len(self.unexpected_samples)
        ) / self.requested_samples


class GenotypeExtractor:
    """Extract participant subsets from VCF files using bcftools.

    Parameters
    ----------
    bcftools_path : str
        Path to bcftools executable.
    """

    def __init__(self, bcftools_path: str = "bcftools") -> None:
        self.bcftools_path = bcftools_path

    def _load_sample_list(self, sample_file: str | Path) -> list[str]:
        """Load sample IDs from a flat text file (one per line)."""
        with open(sample_file) as fh:
            return [line.strip() for line in fh if line.strip()]

    def _get_vcf_samples(self, vcf_path: str | Path) -> set[str]:
        """Return sample IDs from a VCF/BCF header (``bcftools query -l``)."""
        result = subprocess.run(
            [self.bcftools_path, "query", "-l", str(vcf_path)],
            capture_output=True,
            text=True,
            check=True,
        )
        return {s.strip() for s in result.stdout.splitlines() if s.strip()}

    def extract(
        self,
        source_vcf: str | Path,
        sample_file: str | Path,
        output_vcf: str | Path,
        regions: str | None = None,
        allow_missing: bool = False,
    ) -> ExtractionResult:
        """Extract a subset of samples from a VCF.

        Parameters
        ----------
        source_vcf : path
            Input VCF/BCF file.
        sample_file : path
            Text file with one sample ID per line.
        output_vcf : path
            Output path; the extension sets the format (.vcf.gz, .bcf, .vcf).
        regions : str, optional
            Region filter (e.g. ``"chr6:26000000-34000000"``). Needs an index
            on the source file.
        allow_missing : bool
            If False (default), stop before extracting when any requested
            sample is absent from the source. If True, extract the samples
            that exist (``--force-samples``) and list the rest as missing.

        Returns
        -------
        ExtractionResult
            ``success`` is True only when the output holds exactly the
            requested samples. Errors are reported in ``error``.
        """
        requested = self._load_sample_list(sample_file)
        duplicates = sorted(s for s, n in Counter(requested).items() if n > 1)
        requested_set = set(requested)
        result = ExtractionResult(
            source_vcf=str(source_vcf),
            output_vcf=str(output_vcf),
            requested_samples=len(requested_set),
            duplicate_requests=duplicates,
        )

        try:
            out_type = output_type_for(output_vcf)
            available = self._get_vcf_samples(source_vcf)
        except ValueError as exc:
            result.error = str(exc)
            return result
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            result.error = f"Could not read samples from {source_vcf}: {exc}"
            return result

        # Pre-flight: are all requested samples in the source?
        absent = sorted(requested_set - available)
        if absent and not allow_missing:
            result.missing_samples = absent
            result.error = (
                f"{len(absent)} requested sample(s) not in source; nothing extracted"
            )
            return result

        cmd = [self.bcftools_path, "view", "-S", str(sample_file)]
        if allow_missing:
            cmd.append("--force-samples")
        if regions:
            cmd.extend(["-r", regions])
        cmd.extend(["-O", out_type, "-o", str(output_vcf), str(source_vcf)])

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            extracted = self._get_vcf_samples(output_vcf)
        except subprocess.CalledProcessError as exc:
            result.error = (exc.stderr or str(exc)).strip()
            return result
        except FileNotFoundError as exc:
            result.error = str(exc)
            return result

        # Post-extraction validation
        result.extracted_samples = len(extracted)
        result.missing_samples = sorted(requested_set - extracted)
        result.unexpected_samples = sorted(extracted - requested_set)
        result.success = extracted == requested_set
        return result
