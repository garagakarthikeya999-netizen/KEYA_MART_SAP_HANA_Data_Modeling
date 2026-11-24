
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

print("=" * 65)
print("KEYA MART - DATA QUALITY AND KEY VALIDATION")
print("=" * 65)

customers = load_file("olist_customers_dataset.csv")
orders = load_file("olist_orders_dataset.csv")
items = load_file("olist_order_items_dataset.csv")
products = load_file("olist_products_dataset.csv")
sellers = load_file("olist_sellers_dataset.csv")
payments = load_file("olist_order_payments_dataset.csv")

results = []

def check_primary_key(df, table, column):
    nulls = int(df[column].isna().sum())
    duplicates = int(df[column].duplicated().sum())

    results.append({
        "check_type": "Primary Key",
        "table_name": table,
        "column_name": column,
        "null_records": nulls,
        "duplicate_records": duplicates,
        "orphan_records": ""
    })

    print(
        f"{table}.{column}: "
        f"NULL={nulls}, DUPLICATES={duplicates}"
    )

def check_foreign_key(child, parent, child_table,
                      parent_table, column):
    child_values = child[column].dropna()
    parent_values = set(parent[column].dropna())

    orphan_count = int(
        (~child_values.isin(parent_values)).sum()
    )

    nulls = int(child[column].isna().sum())

    results.append({
        "check_type": "Foreign Key",
        "table_name": child_table,
        "column_name": column,
        "null_records": nulls,
        "duplicate_records": "",
        "orphan_records": orphan_count
    })

    print(
        f"{child_table}.{column} -> "
        f"{parent_table}.{column}: "
        f"NULL={nulls}, ORPHANS={orphan_count}"
    )

print("\n1. PRIMARY KEY CHECKS")

check_primary_key(customers, "CUSTOMERS", "customer_id")
check_primary_key(orders, "ORDERS", "order_id")
check_primary_key(products, "PRODUCTS", "product_id")
check_primary_key(sellers, "SELLERS", "seller_id")

# Composite key checks
item_duplicates = int(
    items.duplicated(
        subset=["order_id", "order_item_id"]
    ).sum()
)

payment_duplicates = int(
    payments.duplicated(
        subset=["order_id", "payment_sequential"]
    ).sum()
)

results.append({
    "check_type": "Composite Primary Key",
    "table_name": "ORDER_ITEMS",
    "column_name": "order_id + order_item_id",
    "null_records": int(
        items[["order_id", "order_item_id"]].isna().any(axis=1).sum()
    ),
    "duplicate_records": item_duplicates,
    "orphan_records": ""
})

results.append({
    "check_type": "Composite Primary Key",
    "table_name": "PAYMENTS",
    "column_name": "order_id + payment_sequential",
    "null_records": int(
        payments[["order_id", "payment_sequential"]].isna().any(axis=1).sum()
    ),
    "duplicate_records": payment_duplicates,
    "orphan_records": ""
})

print("\n2. FOREIGN KEY CHECKS")

check_foreign_key(
    orders, customers, "ORDERS", "CUSTOMERS", "customer_id"
)

check_foreign_key(
    items, orders, "ORDER_ITEMS", "ORDERS", "order_id"
)

check_foreign_key(
    items, products, "ORDER_ITEMS", "PRODUCTS", "product_id"
)

check_foreign_key(
    items, sellers, "ORDER_ITEMS", "SELLERS", "seller_id"
)

check_foreign_key(
    payments, orders, "PAYMENTS", "ORDERS", "order_id"
)

report = pd.DataFrame(results)

report.to_csv(
    os.path.join(OUTPUT, "data_quality_report.csv"),
    index=False
)

print("\n3. DATASET RECORD COUNTS")

for name, df in [
    ("CUSTOMERS", customers),
    ("ORDERS", orders),
    ("ORDER_ITEMS", items),
    ("PRODUCTS", products),
    ("SELLERS", sellers),
    ("PAYMENTS", payments)
]:
    print(f"{name}: {len(df)} records")

print("\nVALIDATION COMPLETED")
print("Report saved to:", OUTPUT)
print("=" * 65)
