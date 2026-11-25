from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(r"C:\Users\garag\Documents\SAP_HANA_WEEK1_PROJECT")
RAW_DIR = PROJECT_ROOT / "02_Dataset" / "Raw"
OUTPUT_DIR = PROJECT_ROOT / "02_Week2_ETL" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "customers": "olist_customers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}


def profile_all_datasets():
    print("=" * 85)
    print("KEYA MART - PHASE 3: DATA PROFILING REPORT")
    print("=" * 85)

    dfs = {}
    column_profiles = []
    file_summaries = []

    for name, filename in FILES.items():
        df = pd.read_csv(RAW_DIR / filename, encoding="utf-8", low_memory=False)
        dfs[name] = df

        row_count, col_count = df.shape
        exact_dups = int(df.duplicated().sum())
        total_nulls = int(df.isna().sum().sum())

        # Identify single-column PK candidates
        pk_candidates = [
            col for col in df.columns
            if df[col].isna().sum() == 0 and df[col].nunique() == row_count
        ]

        file_summaries.append({
            "dataset": name,
            "file_name": filename,
            "row_count": row_count,
            "column_count": col_count,
            "exact_duplicate_rows": exact_dups,
            "total_missing_cells": total_nulls,
            "single_pk_candidates": ", ".join(pk_candidates) if pk_candidates else "None (Composite/Aggregation needed)"
        })

        for col in df.columns:
            non_null_series = df[col].dropna()
            sample_val = str(non_null_series.iloc[0])[:40] if not non_null_series.empty else "NULL"
            null_cnt = int(df[col].isna().sum())
            null_pct = round((null_cnt / row_count) * 100, 2) if row_count > 0 else 0.0
            uniq_cnt = int(df[col].nunique(dropna=True))

            column_profiles.append({
                "dataset": name,
                "column_name": col,
                "dtype": str(df[col].dtype),
                "row_count": row_count,
                "non_null_count": row_count - null_cnt,
                "null_count": null_cnt,
                "null_pct": null_pct,
                "unique_count": uniq_cnt,
                "is_unique_no_null": (null_cnt == 0 and uniq_cnt == row_count),
                "sample_value": sample_val,
            })

    # 1. Print File-Level Summary
    summary_df = pd.DataFrame(file_summaries)
    print("\n--- 1. FILE-LEVEL SUMMARY ---")
    print(summary_df.to_string(index=False))

    # 2. Print Columns with Missing Values
    col_df = pd.DataFrame(column_profiles)
    missing_df = col_df[col_df["null_count"] > 0][
        ["dataset", "column_name", "null_count", "null_pct"]
    ]
    print("\n--- 2. COLUMNS WITH MISSING VALUES ---")
    print(missing_df.to_string(index=False))

    # 3. Check Composite Primary Keys & Key Quality Issues
    print("\n--- 3. KEY & DATA QUALITY CHECKS ---")
    rev_id_dups = int(dfs["reviews"]["review_id"].duplicated().sum())
    rev_comp_dups = int(dfs["reviews"].duplicated(subset=["review_id", "order_id"]).sum())
    oi_comp_dups = int(dfs["order_items"].duplicated(subset=["order_id", "order_item_id"]).sum())
    pay_comp_dups = int(dfs["payments"].duplicated(subset=["order_id", "payment_sequential"]).sum())
    geo_unique_zips = int(dfs["geolocation"]["geolocation_zip_code_prefix"].nunique())

    print(f"Reviews duplicate review_id (single col): {rev_id_dups}")
    print(f"Reviews duplicate (review_id, order_id):  {rev_comp_dups}")
    print(f"Order Items duplicate (order_id, item_id): {oi_comp_dups}")
    print(f"Payments duplicate (order_id, seq):        {pay_comp_dups}")
    print(f"Geolocation total rows vs unique zips:     {len(dfs['geolocation']):,} -> {geo_unique_zips:,}")

    # 4. Foreign Key Integrity Checks
    print("\n--- 4. FOREIGN KEY INTEGRITY CHECKS ---")
    fk_checks = [
        ("orders.customer_id -> customers.customer_id",
         ~dfs["orders"]["customer_id"].isin(dfs["customers"]["customer_id"])),
        ("order_items.order_id -> orders.order_id",
         ~dfs["order_items"]["order_id"].isin(dfs["orders"]["order_id"])),
        ("order_items.product_id -> products.product_id",
         ~dfs["order_items"]["product_id"].isin(dfs["products"]["product_id"])),
        ("order_items.seller_id -> sellers.seller_id",
         ~dfs["order_items"]["seller_id"].isin(dfs["sellers"]["seller_id"])),
        ("payments.order_id -> orders.order_id",
         ~dfs["payments"]["order_id"].isin(dfs["orders"]["order_id"])),
        ("reviews.order_id -> orders.order_id",
         ~dfs["reviews"]["order_id"].isin(dfs["orders"]["order_id"])),
        ("products.category -> translation.category (excl. nulls)",
         ~dfs["products"]["product_category_name"].dropna().isin(
             dfs["category_translation"]["product_category_name"]
         )),
    ]

    for label, orphan_mask in fk_checks:
        orphan_count = int(orphan_mask.sum())
        status = "PASS" if orphan_count == 0 else f"ISSUE ({orphan_count} unmatched)"
        print(f"{label:<55} | {status}")

    # 5. Save profiling CSV reports
    summary_path = OUTPUT_DIR / "02_file_quality_summary.csv"
    col_path = OUTPUT_DIR / "02_column_profile.csv"
    summary_df.to_csv(summary_path, index=False, encoding="utf-8")
    col_df.to_csv(col_path, index=False, encoding="utf-8")

    print("\n" + "-" * 85)
    print(f"Saved file summary to:   {summary_path}")
    print(f"Saved column profile to: {col_path}")
    print("=" * 85)


if __name__ == "__main__":
    profile_all_datasets()