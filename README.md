# Biobank Data Release Manager

**A secure, automated pipeline for extracting, validating, and packaging genomic datasets for research delivery.**

This repository demonstrates a robust workflow used to manage data access requests (DAAs) in a large-scale biobank environment. It bridges the gap between clinical metadata (SQL) and genomic file storage (VCFs), ensuring that researchers receive exactly the data they are approved for—no more, no less.

## 📂 Repository Contents

| Script | Role | Description |
| :--- | :--- | :--- |
| `extract_and_validate_genotypes.sh` | **Core Pipeline** | The engine of the delivery system. Performs pre-flight checks, executes `bcftools` extraction from master VCFs, and validates sample concordance. |
| `parse_sql_metadata.sh` | **Data Wrangling** | Cleans raw exports from clinical databases (e.g., HeidiSQL), handling quoting inconsistencies and formatting issues to produce clean ID lists. |
| `generate_sql_query_params.sh` | **SQL Helper** | Automates the generation of massive SQL `IN (...)` clauses from flat text files, eliminating manual formatting errors for large cohorts. |

## 🚀 Workflow Overview

1.  **Cohort Identification**: Receive a list of requested barcodes/IDs from the research team.
2.  **Metadata Querying**: Use `generate_sql_query_params.sh` to format these IDs for the internal database, retrieving the corresponding VCF Sample IDs.
3.  **List Cleaning**: Process the database export with `parse_sql_metadata.sh` to ensure a strictly formatted input list.
4.  **Extraction & Validation**: Run `extract_and_validate_genotypes.sh` to:
    *   Verify the existence of the source VCF.
    *   Check that all requested IDs exist in the source header.
    *   Extract the subset using `bcftools`.
    *   **Audit** the output to confirm the final sample count matches the request.

## 🛡️ Security & Compliance

*   **Sanitized Code**: All internal paths, participant IDs, and institutional keys have been removed for this public portfolio.
*   **Validation First**: The pipeline prioritizes data integrity. If a requested sample is missing from the source, the system flags it immediately rather than failing silently.

## 🛠️ Technical Stack

*   **Bash/Shell Scripting**: For orchestration and glue logic.
*   **BCFtools**: For high-performance manipulation of VCF/BCF genomic files.
*   **AWK/Sed**: For efficient text processing and SQL query generation.

---
*Created by [dsugurtuna](https://github.com/dsugurtuna)*
