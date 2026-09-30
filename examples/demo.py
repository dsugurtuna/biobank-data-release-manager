"""Offline demo of a data release on synthetic data.

1. A researcher's approved list of sample barcodes is looked up in a
   metadata database (here an in-memory SQLite table) to get VCF sample IDs.
2. The subset is extracted from a synthetic VCF. bcftools is replaced by
   examples/fake_bcftools.py so this runs anywhere; for real use install
   bcftools and pass its path to GenotypeExtractor.
3. The extraction is checked before and after.

All barcodes, samples and genotypes are made up.
Run from the repository root:  python examples/demo.py
"""

from __future__ import annotations

import sqlite3
import stat
import sys
import tempfile
from pathlib import Path

from release_manager import GenotypeExtractor, SQLQueryBuilder

HERE = Path(__file__).resolve().parent
SAMPLES = [f"VCF{i:03d}" for i in range(1, 9)]


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)

        # Synthetic metadata: barcode -> VCF sample ID. BC006 was never sequenced.
        db = sqlite3.connect(":memory:")
        db.execute("CREATE TABLE samples (barcode TEXT, vcf_sample_id TEXT)")
        rows = [(f"BC{i:03d}", f"VCF{i:03d}") for i in range(1, 9) if i != 6]
        db.executemany("INSERT INTO samples VALUES (?, ?)", rows)

        approved = ["BC002", "BC003", "BC005", "BC006"]
        sql, params = SQLQueryBuilder.build_parameterised_in_clause(approved)
        query = f"SELECT vcf_sample_id FROM samples WHERE {sql} ORDER BY 1"
        found = [r[0] for r in db.execute(query, params)]
        print(f"Approved barcodes: {len(approved)}; with a VCF sample ID: {len(found)}")

        sample_file = tmp / "samples.txt"
        sample_file.write_text("\n".join(found) + "\n")

        # Synthetic source VCF (plain text; the stand-in does not compress).
        source = tmp / "cohort.vcf"
        header = [
            "#CHROM",
            "POS",
            "ID",
            "REF",
            "ALT",
            "QUAL",
            "FILTER",
            "INFO",
            "FORMAT",
        ]
        source.write_text(
            "##fileformat=VCFv4.2\n"
            + "\t".join(header + SAMPLES)
            + "\n"
            + "\t".join(["1", "1000", "rs9400001", "A", "G", ".", "PASS", ".", "GT"])
            + "\t"
            + "\t".join(["0/1"] * len(SAMPLES))
            + "\n"
        )

        bcftools = tmp / "bcftools"
        bcftools.write_text(
            f"#!{sys.executable}\n" + (HERE / "fake_bcftools.py").read_text()
        )
        bcftools.chmod(bcftools.stat().st_mode | stat.S_IXUSR)

        result = GenotypeExtractor(str(bcftools)).extract(
            source, sample_file, tmp / "release.vcf.gz"
        )
        n_out, n_req = result.extracted_samples, result.requested_samples
        print(f"Extracted {n_out} of {n_req} requested")
        print(f"Exact match: {result.success}; missing: {result.missing_samples}")

        # A request that includes a sample not in the VCF stops before extraction.
        sample_file.write_text("VCF002\nVCF099\n")
        result = GenotypeExtractor(str(bcftools)).extract(
            source, sample_file, tmp / "release2.vcf.gz"
        )
        print(f"Second request: {result.error}; missing: {result.missing_samples}")


if __name__ == "__main__":
    main()
