#!/bin/bash
#
# Portfolio/Educational Purpose Only
# -----------------------------------------------------------------------------
# Script: parse_sql_metadata.sh
# Description: Processes raw metadata exports from clinical databases (e.g., 
#              HeidiSQL/MySQL dumps). Cleans formatting issues (quoted strings)
#              to prepare clean ID lists for the extraction pipeline.
#

INPUT_FILE="raw_sql_export.tsv"
OUTPUT_FILE="clean_sample_ids.txt"

# Simulation: Create dummy input if missing
if [ ! -f "${INPUT_FILE}" ]; then
    echo "Creating mock SQL export file..."
    echo -e "row_id\tproject_code\tvcf_sample_id" > "${INPUT_FILE}"
    echo -e "1\tPROJ_001\t\"SAMPLE_001\"" >> "${INPUT_FILE}"
    echo -e "2\tPROJ_001\t\"SAMPLE_002\"" >> "${INPUT_FILE}"
    echo -e "3\tPROJ_001\t\"SAMPLE_003\"" >> "${INPUT_FILE}"
fi

echo "Processing SQL results from '${INPUT_FILE}'..."

# Logic:
# 1. Skip header (NR>1)
# 2. Target 3rd column (vcf_sample_id)
# 3. Remove leading/trailing quotes using gsub
# 4. Sort and unique
awk 'BEGIN{FS="\t"; OFS="\n"} NR>1 {gsub(/^\"|\"$/, "", $3); print $3}' "${INPUT_FILE}" | sort -u > "${OUTPUT_FILE}"

if [ -s "${OUTPUT_FILE}" ]; then
    COUNT=$(wc -l < "${OUTPUT_FILE}")
    echo "Success: Extracted ${COUNT} unique IDs."
    echo "Preview:"
    head -n 3 "${OUTPUT_FILE}"
else
    echo "Error: Output file is empty."
    exit 1
fi
