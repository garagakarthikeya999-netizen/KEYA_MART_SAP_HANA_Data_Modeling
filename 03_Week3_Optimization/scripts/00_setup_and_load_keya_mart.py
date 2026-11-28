import getpass
from pathlib import Path
import numpy as np
import pandas as pd
from hdbcli import dbapi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

raw_host = input("Paste your new SAP HANA SQL Endpoint (host or host:443): ").strip()
host = raw_host.split(":")[0].strip()
port = 443
user = "DBADMIN"
password = getpass.getpass(f"Enter SAP HANA password for {user}: ")

# Save .env for all future Week 3 scripts
ENV_FILE.write_text(
    f"HANA_HOST={host}\nHANA_PORT={port}\nHANA_USER={user}\nHANA_PASSWORD={password}\n",
    encoding="utf-8",
)
print(f"Saved connection settings to {ENV_FILE}")

print(f"\nConnecting to {host}:{port} as {user}...")
conn = dbapi.connect(address=host, port=port, user=user, password=password)
cur = conn.cursor()
print("Connected successfully!")

# Check if KEYA_MART.FACT_SALES already exists
cur.execute("""
    SELECT COUNT(*) FROM SYS.TABLES
    WHERE SCHEMA_NAME = 'KEYA_MART' AND TABLE_NAME = 'FACT_SALES'
""")
fact_exists = cur.fetchone()[0] > 0

if fact_exists:
    cur.execute("SELECT COUNT(*) FROM KEYA_MART.FACT_SALES")
    cnt = cur.fetchone()[0]
    if cnt > 0:
        print(f"KEYA_MART.FACT_SALES already has {cnt:,} rows. Skipping reload!")
        cur.close()
        conn.close()
        raise SystemExit(0)


def run_sql_file(sql_path: Path):
    print(f"\nExecuting {sql_path.name}...")
    raw = sql_path.read_text(encoding="utf-8")
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    cleaned = "\n".join(lines)
    for stmt in [s.strip() for s in cleaned.split(";") if s.strip()]:
        try:
            cur.execute(stmt)
        except Exception as e:
            msg = str(e)
            if "cannot use duplicate schema name" in msg.lower() or "already exists" in msg.lower():
                print(f"  [Info] Skipping existing object: {msg.splitlines()[0]}")
            else:
                raise
    conn.commit()
    print(f"  Done: {sql_path.name}")


# 1. Create schema & 8 OLTP tables
run_sql_file(PROJECT_ROOT / "03_SQL_Scripts" / "01_create_schema_and_tables.sql")

# 2. Load 8 clean CSVs in parent-before-child order
load_order = [
    ("GEOLOCATION", "clean_geolocation.csv"),
    ("CUSTOMERS", "clean_customers.csv"),
    ("SELLERS", "clean_sellers.csv"),
    ("PRODUCTS", "clean_products.csv"),
    ("ORDERS", "clean_orders.csv"),
    ("ORDER_ITEMS", "clean_order_items.csv"),
    ("PAYMENTS", "clean_payments.csv"),
    ("ORDER_REVIEWS", "clean_order_reviews.csv"),
]

csv_dir = PROJECT_ROOT / "02_Week2_ETL" / "transformed"
BATCH_SIZE = 5000

for table_name, csv_name in load_order:
    csv_path = csv_dir / csv_name
    df = pd.read_csv(csv_path, low_memory=False)
    df = df.replace({np.nan: None})
    cols = ", ".join(df.columns)
    placeholders = ", ".join(["?"] * len(df.columns))
    sql = f"INSERT INTO KEYA_MART.{table_name} ({cols}) VALUES ({placeholders})"
    rows = list(df.itertuples(index=False, name=None))
    print(f"Loading {len(rows):,} rows into KEYA_MART.{table_name}...")
    for i in range(0, len(rows), BATCH_SIZE):
        cur.executemany(sql, rows[i : i + BATCH_SIZE])
    conn.commit()

# 3. Create Star Schema & Analytical Views
run_sql_file(PROJECT_ROOT / "03_SQL_Scripts" / "03_create_star_schema.sql")
run_sql_file(PROJECT_ROOT / "03_SQL_Scripts" / "04_create_analytical_views.sql")

cur.execute("SELECT COUNT(*) FROM KEYA_MART.FACT_SALES")
print(f"\nALL DONE! KEYA_MART.FACT_SALES loaded with {cur.fetchone()[0]:,} rows.")
cur.close()
conn.close()