#!/bin/bash
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# Script: generate_sql_query_params.sh
# Description: Converts a flat list of biological barcodes/IDs into a formatted
#              SQL 'IN' clause. Essential for querying metadata databases 
#              for large cohorts (N > 1000) without manual formatting.
#

INPUT_LIST="barcode_list.txt"
OUTPUT_SQL="sql_in_clause.txt"

# Simulation: Create dummy input
if [ ! -f "${INPUT_LIST}" ]; then
    echo "Creating mock barcode list..."
    echo "BC_1001" > "${INPUT_LIST}"
    echo "BC_1002" >> "${INPUT_LIST}"
    echo "BC_1003" >> "${INPUT_LIST}"
fi

echo "Formatting IDs for SQL Query..."

# Logic:
# 1. Wrap each line in single quotes
# 2. Add a trailing comma
# 3. Remove the comma from the very last line to ensure valid SQL syntax
awk '{printf "\x27%s\x27,\n", $1}' "${INPUT_LIST}" | sed '$s/,$//' > "${OUTPUT_SQL}"

echo "SQL Clause Generated:"
echo "--------------------------------------------------"
cat "${OUTPUT_SQL}"
echo "--------------------------------------------------"
echo "Copy the above block into your WHERE clause: WHERE barcode IN (...)"
