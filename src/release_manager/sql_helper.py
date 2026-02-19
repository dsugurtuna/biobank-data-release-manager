"""SQL query helper module.

Generates SQL clauses from sample/barcode lists, and cleans metadata
exported from database management tools.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List


class SQLQueryBuilder:
    """Generate SQL query fragments for biobank data retrieval.

    Useful for converting flat barcode or sample ID lists into SQL IN
    clauses, and for cleaning TSV/CSV exports from database tools.
    """

    @staticmethod
    def build_in_clause(
        ids: List[str],
        column_name: str = "barcode",
    ) -> str:
        """Build a SQL IN clause from a list of identifiers.

        Parameters
        ----------
        ids : list of str
            Identifiers to include.
        column_name : str
            The SQL column name.

        Returns
        -------
        str
            A complete SQL IN clause, e.g.
            ``barcode IN ('BC001','BC002','BC003')``
        """
        quoted = ", ".join(f"'{i.strip()}'" for i in ids if i.strip())
        return f"{column_name} IN ({quoted})"

    @staticmethod
    def ids_from_file(path: str | Path) -> List[str]:
        """Load identifiers from a flat text file (one per line)."""
        with open(path) as fh:
            return [line.strip() for line in fh if line.strip()]

    @staticmethod
    def clean_tsv_export(
        input_path: str | Path,
        output_path: str | Path,
        deduplicate: bool = True,
    ) -> int:
        """Clean a TSV export from a database tool.

        Strips quotes, deduplicates rows, and writes a clean output.
        Returns the number of output rows.
        """
        rows: list = []
        seen: set = set()
        with open(input_path) as fh:
            reader = csv.reader(fh, delimiter="\t")
            header = next(reader, None)
            if header:
                rows.append([h.strip().strip('"') for h in header])
            for row in reader:
                cleaned = [c.strip().strip('"') for c in row]
                key = tuple(cleaned)
                if deduplicate and key in seen:
                    continue
                seen.add(key)
                rows.append(cleaned)

        with open(output_path, "w", newline="") as fh:
            writer = csv.writer(fh, delimiter="\t")
            writer.writerows(rows)

        return len(rows) - 1  # exclude header
