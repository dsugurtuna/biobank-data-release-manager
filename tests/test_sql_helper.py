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
