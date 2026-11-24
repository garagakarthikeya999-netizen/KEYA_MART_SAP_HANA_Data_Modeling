import os
import pandas as pd

BASE = os.path.join(
    os.path.expanduser("~"),
    "Documents",
    "SAP_HANA_WEEK1_PROJECT"
)

RAW = os.path.join(BASE, "02_Dataset", "Raw")
OUTPUT = os.path.join(BASE, "02_Dataset", "Processed")
os.makedirs(OUTPUT, exist_ok=True)


def load_file(name):
    return pd.read_csv(os.path.join(RAW, name))


print("=" * 70)
print("KEYA MART - PHASE 5 COMPLETE DATA QUALITY & KEY VALIDATION")
print("=" * 70)

customers = load_file("olist_customers_dataset.csv")
orders = load_file("olist_orders_dataset.csv")
items = load_file("olist_order_items_dataset.csv")
products = load_file("olist_products_dataset.csv")
sellers = load_file("olist_sellers_dataset.csv")
payments = load_file("olist_order_payments_dataset.csv")
reviews = load_file("olist_order_reviews_dataset.csv")
geolocation = load_file("olist_geolocation_dataset.csv")
cat_trans = load_file("product_category_name_translation.csv")

results = []


def check_pk(df, table, cols):
    if isinstance(cols, str):
        cols = [cols]
    nulls = int(df[cols].isna().any(axis=1).sum())
    dups = int(df.duplicated(subset=cols).sum())
    col_label = " + ".join(cols)
    kind = "Primary Key" if len(cols) == 1 else "Composite PK"
    results.append({
        "check_type": kind,
        "table_name": table,
        "column_name": col_label,
        "null_records": nulls,
        "duplicate_records": dups,
        "orphan_records": ""
    })
    print(f"[{kind}] {table} ({col_label}): NULL={nulls}, DUPLICATES={dups}")


def check_fk(child, parent, child_table, parent_table, child_col, parent_col=None):
    if parent_col is None:
        parent_col = child_col
    child_vals = child[child_col].dropna()
    parent_vals = set(parent[parent_col].dropna())
    orphans = int((~child_vals.isin(parent_vals)).sum())
    nulls = int(child[child_col].isna().sum())
    results.append({
        "check_type": "Foreign Key",
        "table_name": child_table,
        "column_name": f"{child_col} -> {parent_table}.{parent_col}",
        "null_records": nulls,
        "duplicate_records": "",
        "orphan_records": orphans
    })
    print(
        f"[Foreign Key] {child_table}.{child_col} -> "
        f"{parent_table}.{parent_col}: NULL={nulls}, ORPHANS={orphans}"
    )


print("\n1. PRIMARY KEY & COMPOSITE KEY CHECKS")
check_pk(customers, "CUSTOMERS", "customer_id")
check_pk(orders, "ORDERS", "order_id")
check_pk(products, "PRODUCTS", "product_id")
check_pk(sellers, "SELLERS", "seller_id")
check_pk(items, "ORDER_ITEMS", ["order_id", "order_item_id"])
check_pk(payments, "PAYMENTS", ["order_id", "payment_sequential"])
check_pk(reviews, "ORDER_REVIEWS", "review_id")
check_pk(reviews, "ORDER_REVIEWS", ["review_id", "order_id"])
check_pk(geolocation, "GEOLOCATION", "geolocation_zip_code_prefix")
check_pk(cat_trans, "CATEGORY_TRANSLATION", "product_category_name")

print("\n2. FOREIGN KEY / REFERENTIAL INTEGRITY CHECKS")
check_fk(orders, customers, "ORDERS", "CUSTOMERS", "customer_id")
check_fk(items, orders, "ORDER_ITEMS", "ORDERS", "order_id")
check_fk(items, products, "ORDER_ITEMS", "PRODUCTS", "product_id")
check_fk(items, sellers, "ORDER_ITEMS", "SELLERS", "seller_id")
check_fk(payments, orders, "PAYMENTS", "ORDERS", "order_id")
check_fk(reviews, orders, "ORDER_REVIEWS", "ORDERS", "order_id")
check_fk(
    customers, geolocation, "CUSTOMERS", "GEOLOCATION",
    "customer_zip_code_prefix", "geolocation_zip_code_prefix"
)
check_fk(
    sellers, geolocation, "SELLERS", "GEOLOCATION",
    "seller_zip_code_prefix", "geolocation_zip_code_prefix"
)
check_fk(
    products, cat_trans, "PRODUCTS", "CATEGORY_TRANSLATION",
    "product_category_name", "product_category_name"
)

print("\n3. EXACT DUPLICATE ROWS PER TABLE")
datasets = [
    ("CUSTOMERS", customers),
    ("ORDERS", orders),
    ("ORDER_ITEMS", items),
    ("PRODUCTS", products),
    ("SELLERS", sellers),
    ("PAYMENTS", payments),
    ("ORDER_REVIEWS", reviews),
    ("GEOLOCATION", geolocation),
    ("CATEGORY_TRANSLATION", cat_trans),
]
for name, df in datasets:
    exact_dups = int(df.duplicated().sum())
    print(f"{name}: total={len(df)}, exact_duplicate_rows={exact_dups}")

print("\n4. MISSING VALUES (COLUMNS WITH NULL > 0)")
missing_rows = []
for name, df in datasets:
    total = len(df)
    for col in df.columns:
        null_cnt = int(df[col].isna().sum())
        pct = round((null_cnt / total) * 100, 2) if total > 0 else 0.0
        missing_rows.append({
            "table_name": name,
            "column_name": col,
            "total_rows": total,
            "null_count": null_cnt,
            "null_percentage": pct
        })
        if null_cnt > 0:
            print(f"{name}.{col}: {null_cnt} ({pct}%)")

print("\n5. BUSINESS RULE CHECKS")
bad_price = int((items["price"] <= 0).sum())
bad_freight = int((items["freight_value"] < 0).sum())
bad_payment = int((payments["payment_value"] < 0).sum())
bad_score = int((~reviews["review_score"].isin([1, 2, 3, 4, 5])).sum())

purchase_dt = pd.to_datetime(orders["order_purchase_timestamp"], errors="coerce")
delivered_dt = pd.to_datetime(orders["order_delivered_customer_date"], errors="coerce")
bad_delivery_dt = int((delivered_dt < purchase_dt).sum())

print(f"ORDER_ITEMS price <= 0: {bad_price}")
print(f"ORDER_ITEMS freight_value < 0: {bad_freight}")
print(f"PAYMENTS payment_value < 0: {bad_payment}")
print(f"ORDER_REVIEWS score not in 1..5: {bad_score}")
print(f"ORDERS delivered_date < purchase_date: {bad_delivery_dt}")

pd.DataFrame(results).to_csv(
    os.path.join(OUTPUT, "data_quality_full_report.csv"), index=False
)
pd.DataFrame(missing_rows).to_csv(
    os.path.join(OUTPUT, "missing_values_report.csv"), index=False
)

print("\nVALIDATION COMPLETED")
print("Reports saved to:", OUTPUT)
print("=" * 70)