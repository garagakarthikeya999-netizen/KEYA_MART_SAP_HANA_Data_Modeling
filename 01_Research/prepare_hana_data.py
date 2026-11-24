import os
import pandas as pd

BASE = os.path.join(
    os.path.expanduser("~"),
    "Documents",
    "SAP_HANA_WEEK1_PROJECT"
)

RAW = os.path.join(BASE, "02_Dataset", "Raw")
PROCESSED = os.path.join(BASE, "02_Dataset", "Processed")
os.makedirs(PROCESSED, exist_ok=True)

print("=" * 65)
print("KEYA MART - PREPARING CLEAN SAP HANA CSV FILES")
print("=" * 65)

# 1. Deduplicate Geolocation (1,000,163 -> 19,015 unique zip prefixes)
geo = pd.read_csv(os.path.join(RAW, "olist_geolocation_dataset.csv"))
geo_clean = (
    geo.groupby("geolocation_zip_code_prefix", as_index=False)
    .agg({
        "geolocation_lat": "mean",
        "geolocation_lng": "mean",
        "geolocation_city": "first",
        "geolocation_state": "first"
    })
)
geo_clean["geolocation_lat"] = geo_clean["geolocation_lat"].round(6)
geo_clean["geolocation_lng"] = geo_clean["geolocation_lng"].round(6)

dup_check = int(geo_clean["geolocation_zip_code_prefix"].duplicated().sum())
geo_clean.to_csv(os.path.join(PROCESSED, "hana_geolocation.csv"), index=False, encoding="utf-8")
print(f"hana_geolocation.csv: {len(geo_clean)} rows (PK duplicates={dup_check})")

# 2. Export the remaining 7 core tables cleanly in UTF-8
files_to_copy = [
    ("olist_customers_dataset.csv", "hana_customers.csv"),
    ("olist_orders_dataset.csv", "hana_orders.csv"),
    ("olist_order_items_dataset.csv", "hana_order_items.csv"),
    ("olist_products_dataset.csv", "hana_products.csv"),
    ("olist_sellers_dataset.csv", "hana_sellers.csv"),
    ("olist_order_payments_dataset.csv", "hana_payments.csv"),
    ("olist_order_reviews_dataset.csv", "hana_order_reviews.csv"),
]

for raw_name, clean_name in files_to_copy:
    df = pd.read_csv(os.path.join(RAW, raw_name))
    df.to_csv(os.path.join(PROCESSED, clean_name), index=False, encoding="utf-8")
    print(f"{clean_name}: {len(df)} rows")

print("\nALL 8 CLEAN CSV FILES SAVED TO:", PROCESSED)
print("=" * 65)