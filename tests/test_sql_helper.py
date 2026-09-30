"""Tests for release_manager.sql_helper."""

from pathlib import Path

import pytest

from release_manager.sql_helper import SQLQueryBuilder


class TestSQLQueryBuilder:
    def test_build_in_clause(self) -> None:
        clause = SQLQueryBuilder.build_in_clause(["BC001", "BC002", "BC003"])
        assert clause == "barcode IN ('BC001', 'BC002', 'BC003')"

    def test_build_in_clause_custom_col(self) -> None:
        clause = SQLQueryBuilder.build_in_clause(["S001"], column_name="sample_id")
        assert clause == "sample_id IN ('S001')"

    def test_ids_from_file(self, tmp_path: Path) -> None:
        p = tmp_path / "ids.txt"
        p.write_text("BC001\nBC002\n\nBC003\n")
        ids = SQLQueryBuilder.ids_from_file(p)
        assert ids == ["BC001", "BC002", "BC003"]

    def test_clean_tsv_export(self, tmp_path: Path) -> None:
        inp = tmp_path / "raw.tsv"
        inp.write_text(
            '"barcode"\t"sample_name"\n'
            '"BC001"\t"Sample A"\n'
            '"BC002"\t"Sample B"\n'
            '"BC002"\t"Sample B"\n'  # duplicate
        )
        out = tmp_path / "clean.tsv"
        count = SQLQueryBuilder.clean_tsv_export(inp, out)
        assert count == 2  # deduplicated
        lines = out.read_text().strip().split("\n")
        assert len(lines) == 3  # header + 2 rows

    def test_quotes_are_escaped(self) -> None:
        clause = SQLQueryBuilder.build_in_clause(["O'Brien", "BC001"])
        assert clause == "barcode IN ('O''Brien', 'BC001')"

    def test_injection_attempt_stays_a_literal(self) -> None:
        clause = SQLQueryBuilder.build_in_clause(["x'); DROP TABLE samples; --"])
        assert clause == "barcode IN ('x''); DROP TABLE samples; --')"

    def test_bad_column_name_rejected(self) -> None:
        with pytest.raises(ValueError):
            SQLQueryBuilder.build_in_clause(["BC001"], column_name="barcode; DROP")

    def test_empty_list_rejected(self) -> None:
        with pytest.raises(ValueError):
            SQLQueryBuilder.build_in_clause(["", "  "])

    def test_duplicates_dropped(self) -> None:
        clause = SQLQueryBuilder.build_in_clause(["BC1", "BC1", "BC2"])
        assert clause == "barcode IN ('BC1', 'BC2')"

    def test_parameterised_clause_runs_in_sqlite(self) -> None:
        import sqlite3

        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE samples (barcode TEXT, vcf_id TEXT)")
        con.executemany(
            "INSERT INTO samples VALUES (?, ?)",
            [("BC1", "S1"), ("O'Brien", "S2"), ("BC3", "S3")],
        )
        sql, params = SQLQueryBuilder.build_parameterised_in_clause(["O'Brien", "BC3"])
        rows = con.execute(f"SELECT vcf_id FROM samples WHERE {sql}", params).fetchall()
        assert sorted(r[0] for r in rows) == ["S2", "S3"]
