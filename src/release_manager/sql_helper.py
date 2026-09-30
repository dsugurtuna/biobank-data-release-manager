"""SQL query helper module.

Generates SQL clauses from sample/barcode lists, and cleans metadata
exported from database management tools.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

_IDENTIFIER = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(\.[A-Za-z_][A-Za-z0-9_]*)?$")


def _check_column(column_name: str) -> None:
    if not _IDENTIFIER.match(column_name):
        raise ValueError(f"Not a plain SQL identifier: {column_name!r}")


def _clean_ids(ids: list[str]) -> list[str]:
    """Strip whitespace, drop blanks and duplicates, keep first-seen order."""
    values = list(dict.fromkeys(i.strip() for i in ids if i.strip()))
    if not values:
        raise ValueError("No identifiers given; 'IN ()' is not valid SQL")
    return values


class SQLQueryBuilder:
    """Generate SQL query fragments for biobank data retrieval.

    Useful for converting flat barcode or sample ID lists into SQL IN
    clauses, and for cleaning TSV/CSV exports from database tools.
    """

    @staticmethod
    def build_in_clause(
        ids: list[str],
        column_name: str = "barcode",
    ) -> str:
        """Build a literal SQL IN clause from a list of identifiers.

        For pasting into an ad hoc query in a database client. Single quotes
        in identifiers are doubled (standard SQL escaping), the column name
        must be a plain identifier, and duplicates are dropped. In code,
        prefer :meth:`build_parameterised_in_clause`.

        Parameters
        ----------
        ids : list of str
            Identifiers to include.
        column_name : str
            The SQL column name (letters, digits, underscore, optional
            ``table.`` prefix).

        Returns
        -------
        str
            For example ``barcode IN ('BC001', 'BC002', 'BC003')``.

        Raises
        ------
        ValueError
            If there are no identifiers (``IN ()`` is invalid SQL) or the
            column name is not a plain identifier.
        """
        _check_column(column_name)
        values = _clean_ids(ids)
        quoted = ", ".join("'" + v.replace("'", "''") + "'" for v in values)
        return f"{column_name} IN ({quoted})"

    @staticmethod
    def build_parameterised_in_clause(
        ids: list[str],
        column_name: str = "barcode",
        placeholder: str = "?",
    ) -> tuple[str, list[str]]:
        """Build an IN clause with placeholders, plus the values to bind.

        Use with a DB-API cursor, e.g.
        ``cur.execute(f"SELECT * FROM samples WHERE {sql}", params)``.
        ``placeholder`` depends on the driver (``?`` for sqlite3, ``%s`` for
        psycopg and MySQL drivers).
        """
        _check_column(column_name)
        values = _clean_ids(ids)
        marks = ", ".join(placeholder for _ in values)
        return f"{column_name} IN ({marks})", values

    @staticmethod
    def ids_from_file(path: str | Path) -> list[str]:
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
        rows: list[list[str]] = []
        seen: set[tuple[str, ...]] = set()
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
