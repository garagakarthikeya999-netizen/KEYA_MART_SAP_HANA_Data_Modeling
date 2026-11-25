"""
KEYA MART - Week 2 ETL Pipeline
Phase 2: Data Extraction & Source Validation Script
Reads all 9 raw Olist CSV files, checks encoding/delimiters,
inspects structure, and saves an extraction summary report.
"""

from pathlib import Path
import pandas as pd

# 1. Define exact project paths
PROJECT_ROOT = Path(r"C:\Users\garag\Documents\SAP_HANA_WEEK1_PROJECT")
RAW_DIR = PROJECT_ROOT / "02_Dataset" / "Raw"
OUTPUT_DIR = PROJECT_ROOT / "02_Week2_ETL" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 2. Expected 9 Olist source CSV files
EXPECTED_FILES = [
    "olist_customers_dataset.csv",
    "olist_geolocation_dataset.csv",
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "product_category_name_translation.csv",
]


def extract_and_validate():
    print("=" * 80)
    print("KEYA MART - PHASE 2: DATA EXTRACTION & VALIDATION")
    print(f"Source Folder: {RAW_DIR}")
    print("=" * 80)

    extraction_records = []

    for filename in EXPECTED_FILES:
        file_path = RAW_DIR / filename

        # Check if file exists
        if not file_path.exists():
            print(f"[MISSING] {filename} was not found!")
            extraction_records.append({
                "file_name": filename,
                "status": "MISSING",
                "encoding_used": "N/A",
                "delimiter": ",",
                "file_size_mb": 0.0,
                "row_count": 0,
                "column_count": 0,
                "memory_mb": 0.0,
                "columns": ""
            })
            continue

        file_size_mb = round(file_path.stat().st_size / (1024 * 1024), 2)

        # Try reading with UTF-8 first; fallback to latin-1 if needed
        encoding_used = "utf-8"
        try:
            df = pd.read_csv(
                file_path,
                encoding="utf-8",
                sep=",",
                quotechar='"',
                low_memory=False
            )
        except UnicodeDecodeError:
            encoding_used = "latin-1"
            df = pd.read_csv(
                file_path,
                encoding="latin-1",
                sep=",",
                quotechar='"',
                low_memory=False
            )

        row_count, col_count = df.shape
        memory_mb = round(df.memory_usage(deep=True).sum() / (1024 * 1024), 2)
        status = "VALID" if (row_count > 0 and col_count > 0) else "EMPTY"

        print(f"[{status}] {filename:<42} | Rows: {row_count:>9,} | Cols: {col_count:>2} | Size: {file_size_mb:>6.2f} MB | Enc: {encoding_used}")

        extraction_records.append({
            "file_name": filename,
            "status": status,
            "encoding_used": encoding_used,
            "delimiter": ",",
            "file_size_mb": file_size_mb,
            "row_count": row_count,
            "column_count": col_count,
            "memory_mb": memory_mb,
            "columns": ", ".join(df.columns.tolist())
        })

    # 3. Save extraction summary CSV
    summary_df = pd.DataFrame(extraction_records)
    output_csv = OUTPUT_DIR / "01_extraction_summary.csv"
    summary_df.to_csv(output_csv, index=False, encoding="utf-8")

    # 4. Final validation check
    valid_files = (summary_df["status"] == "VALID").sum()
    total_rows = summary_df["row_count"].sum()

    print("-" * 80)
    print(f"Extraction Complete: {valid_files}/{len(EXPECTED_FILES)} files VALID")
    print(f"Total Raw Records Extracted: {total_rows:,}")
    print(f"Summary saved to: {output_csv}")
    print("=" * 80)


if __name__ == "__main__":
    extract_and_validate()