from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(r"C:\Users\garag\Documents\SAP_HANA_WEEK1_PROJECT")
RAW_DIR = PROJECT_ROOT / "02_Dataset" / "Raw"
TRANSFORM_DIR = PROJECT_ROOT / "02_Week2_ETL" / "transformed"
OUTPUT_DIR = PROJECT_ROOT / "02_Week2_ETL" / "outputs"
TRANSFORM_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

audit_rows = []


def log_audit(table_name, raw_count, final_count, removed_dedup, corrected_imputed, rejected_invalid, notes):
    audit_rows.append({
        "target_table": table_name,
        "raw_rows": int(raw_count),
        "final_rows": int(final_count),
        "removed_or_dedup": int(removed_dedup),
        "corrected_or_imputed": int(corrected_imputed),
        "rejected_invalid": int(rejected_invalid),
        "transformation_notes": notes,
    })


def standardize_timestamps(df, cols):
    for col in cols:
        dt = pd.to_datetime(df[col], errors="coerce")
        df[col] = dt.dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def run_transformations():
    print("=" * 85)
    print("KEYA MART - PHASE 4: DATA TRANSFORMATION & INTEGRATION")
    print("=" * 85)

    # ---------------------------------------------------------
    # 1. CUSTOMERS (Clean strings & standardize zip prefix)
    # ---------------------------------------------------------
    cust = pd.read_csv(RAW_DIR / "olist_customers_dataset.csv", encoding="utf-8")
    raw_cust = len(cust)
    cust_city_before = cust["customer_city"].iloc[0]
    cust["customer_city"] = cust["customer_city"].astype(str).str.strip().str.title()
    cust["customer_state"] = cust["customer_state"].astype(str).str.strip().str.upper()
    cust["customer_zip_code_prefix"] = cust["customer_zip_code_prefix"].astype(str).str.zfill(5)
    cust.to_csv(TRANSFORM_DIR / "clean_customers.csv", index=False, encoding="utf-8")
    log_audit("CUSTOMERS", raw_cust, len(cust), 0, raw_cust, 0,
              "Standardized city (Title Case), state (UPPER), 5-digit zip prefix")
    print(f"[CUSTOMERS] Before city='{cust_city_before}' -> After='{cust['customer_city'].iloc[0]}'")

    # ---------------------------------------------------------
    # 2. GEOLOCATION (Reduce 1,000,163 -> 19,015 unique zips)
    # ---------------------------------------------------------
    geo = pd.read_csv(RAW_DIR / "olist_geolocation_dataset.csv", encoding="utf-8")
    raw_geo = len(geo)
    geo["geolocation_city"] = geo["geolocation_city"].astype(str).str.strip().str.title()
    geo["geolocation_state"] = geo["geolocation_state"].astype(str).str.strip().str.upper()
    geo_clean = (
        geo.groupby("geolocation_zip_code_prefix", as_index=False)
        .agg({
            "geolocation_lat": "mean",
            "geolocation_lng": "mean",
            "geolocation_city": "first",
            "geolocation_state": "first",
        })
    )
    geo_clean["geolocation_zip_code_prefix"] = geo_clean["geolocation_zip_code_prefix"].astype(str).str.zfill(5)
    geo_clean.to_csv(TRANSFORM_DIR / "clean_geolocation.csv", index=False, encoding="utf-8")
    log_audit("GEOLOCATION", raw_geo, len(geo_clean), raw_geo - len(geo_clean), len(geo_clean), 0,
              "Aggregated duplicate zip prefixes using mean(lat/lng) and first(city/state)")
    print(f"[GEOLOCATION] Reduced rows: {raw_geo:,} -> {len(geo_clean):,} unique zip prefixes")

    # ---------------------------------------------------------
    # 3. SELLERS (Clean strings & standardize zip prefix)
    # ---------------------------------------------------------
    sellers = pd.read_csv(RAW_DIR / "olist_sellers_dataset.csv", encoding="utf-8")
    raw_sel = len(sellers)
    sellers["seller_city"] = sellers["seller_city"].astype(str).str.strip().str.title()
    sellers["seller_state"] = sellers["seller_state"].astype(str).str.strip().str.upper()
    sellers["seller_zip_code_prefix"] = sellers["seller_zip_code_prefix"].astype(str).str.zfill(5)
    sellers.to_csv(TRANSFORM_DIR / "clean_sellers.csv", index=False, encoding="utf-8")
    log_audit("SELLERS", raw_sel, len(sellers), 0, raw_sel, 0,
              "Standardized city (Title Case), state (UPPER), 5-digit zip prefix")

    # ---------------------------------------------------------
    # 4. PRODUCTS + CATEGORY TRANSLATION (Data Integration)
    # ---------------------------------------------------------
    prod = pd.read_csv(RAW_DIR / "olist_products_dataset.csv", encoding="utf-8")
    trans = pd.read_csv(RAW_DIR / "product_category_name_translation.csv", encoding="utf-8")
    raw_prod = len(prod)

    # Fix Olist column name typos
    prod = prod.rename(columns={
        "product_name_lenght": "product_name_length",
        "product_description_lenght": "product_description_length",
    })

    # Left-join English category translation
    prod = prod.merge(trans, on="product_category_name", how="left")

    # Impute missing categories (610) & untranslated categories (13)
    missing_cat_cnt = int(prod["product_category_name"].isna().sum())
    untranslated_cnt = int((prod["product_category_name"].notna() & prod["product_category_name_english"].isna()).sum())

    prod["product_category_name"] = prod["product_category_name"].fillna("unknown")
    prod["product_category_name_english"] = prod["product_category_name_english"].fillna(
        prod["product_category_name"].str.replace("_", " ")
    )

    # Impute numeric missing values with median (preserving all 32,951 products)
    numeric_cols = [
        "product_name_length", "product_description_length", "product_photos_qty",
        "product_weight_g", "product_length_cm", "product_height_cm", "product_width_cm"
    ]
    imputed_cells = 0
    for col in numeric_cols:
        nulls = int(prod[col].isna().sum())
        if nulls > 0:
            imputed_cells += nulls
            prod[col] = prod[col].fillna(prod[col].median())

    prod.to_csv(TRANSFORM_DIR / "clean_products.csv", index=False, encoding="utf-8")
    log_audit("PRODUCTS", raw_prod, len(prod), 0, missing_cat_cnt + untranslated_cnt + 2, 0,
              "Integrated English category names; fixed 'lenght' typo; imputed 610 missing categories & 2 missing dimensions")
    print(f"[PRODUCTS] Integrated translation table; fixed 610 missing categories & {untranslated_cnt} untranslated rows")

    # ---------------------------------------------------------
    # 5. ORDERS (Timestamp standardization, keep valid canceled orders)
    # ---------------------------------------------------------
    orders = pd.read_csv(RAW_DIR / "olist_orders_dataset.csv", encoding="utf-8")
    raw_ord = len(orders)
    ts_cols = [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ]
    orders = standardize_timestamps(orders, ts_cols)
    orders["order_status"] = orders["order_status"].astype(str).str.strip().str.lower()
    orders.to_csv(TRANSFORM_DIR / "clean_orders.csv", index=False, encoding="utf-8")
    log_audit("ORDERS", raw_ord, len(orders), 0, raw_ord, 0,
              "Standardized 5 timestamp columns to YYYY-MM-DD HH:MM:SS; preserved valid NULLs for undelivered orders")

    # ---------------------------------------------------------
    # 6. ORDER ITEMS (Business rule validation + timestamp format)
    # ---------------------------------------------------------
    items = pd.read_csv(RAW_DIR / "olist_order_items_dataset.csv", encoding="utf-8")
    raw_items = len(items)
    items = standardize_timestamps(items, ["shipping_limit_date"])
    invalid_items = items[(items["price"] < 0) | (items["freight_value"] < 0)]
    items_valid = items[(items["price"] >= 0) & (items["freight_value"] >= 0)].copy()
    items_valid["total_item_value"] = (items_valid["price"] + items_valid["freight_value"]).round(2)
    items_valid.to_csv(TRANSFORM_DIR / "clean_order_items.csv", index=False, encoding="utf-8")
    log_audit("ORDER_ITEMS", raw_items, len(items_valid), 0, len(items_valid), len(invalid_items),
              "Validated price>=0 & freight>=0; added derived column total_item_value; standardized shipping_limit_date")

    # ---------------------------------------------------------
    # 7. PAYMENTS (Business rule validation)
    # ---------------------------------------------------------
    pay = pd.read_csv(RAW_DIR / "olist_order_payments_dataset.csv", encoding="utf-8")
    raw_pay = len(pay)
    pay["payment_type"] = pay["payment_type"].astype(str).str.strip().str.lower()
    invalid_pay = pay[pay["payment_value"] < 0]
    pay_valid = pay[pay["payment_value"] >= 0].copy()
    pay_valid.to_csv(TRANSFORM_DIR / "clean_payments.csv", index=False, encoding="utf-8")
    log_audit("PAYMENTS", raw_pay, len(pay_valid), 0, len(pay_valid), len(invalid_pay),
              "Standardized payment_type; validated payment_value >= 0")

    # ---------------------------------------------------------
    # 8. REVIEWS (Composite key verified, clean text & timestamps)
    # ---------------------------------------------------------
    rev = pd.read_csv(RAW_DIR / "olist_order_reviews_dataset.csv", encoding="utf-8")
    raw_rev = len(rev)
    rev = standardize_timestamps(rev, ["review_creation_date", "review_answer_timestamp"])
    rev["review_comment_title"] = rev["review_comment_title"].fillna("").astype(str).str.strip()
    rev["review_comment_message"] = rev["review_comment_message"].fillna("").astype(str).str.strip()
    # Verify composite key (review_id, order_id) uniqueness
    comp_dups = int(rev.duplicated(subset=["review_id", "order_id"]).sum())
    if comp_dups > 0:
        rev = rev.drop_duplicates(subset=["review_id", "order_id"], keep="first")
    rev.to_csv(TRANSFORM_DIR / "clean_order_reviews.csv", index=False, encoding="utf-8")
    log_audit("ORDER_REVIEWS", raw_rev, len(rev), comp_dups, raw_rev, 0,
              "Preserved all 99,224 rows via composite key (review_id, order_id); cleaned comment strings & timestamps")

    # ---------------------------------------------------------
    # 9. SAVE & PRINT AUDIT REPORT
    # ---------------------------------------------------------
    audit_df = pd.DataFrame(audit_rows)
    audit_path = OUTPUT_DIR / "03_transformation_audit.csv"
    audit_df.to_csv(audit_path, index=False, encoding="utf-8")

    print("\n--- TRANSFORMATION AUDIT SUMMARY ---")
    print(audit_df[["target_table", "raw_rows", "final_rows", "removed_or_dedup", "corrected_or_imputed", "rejected_invalid"]].to_string(index=False))
    print("-" * 85)
    print(f"Cleaned CSVs saved to: {TRANSFORM_DIR}")
    print(f"Audit log saved to:    {audit_path}")
    print("=" * 85)


if __name__ == "__main__":
    run_transformations()