import os
import csv
import getpass
from pathlib import Path
from hdbcli import dbapi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

HOST = os.environ.get(
    "HANA_HOST",
    "bb2e6931-61eb-40f2-ac16-34972b965bc5.hna0.prod-us10.hanacloud.ondemand.com",
)
PORT = int(os.environ.get("HANA_PORT", "443"))
USER = os.environ.get("HANA_USER", "DBADMIN")
PASSWORD = os.environ.get("HANA_PASSWORD") or getpass.getpass(
    f"Enter SAP HANA password for {USER}: "
)

OUT_DIR = PROJECT_ROOT / "03_Week3_Optimization" / "outputs"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"\nConnecting to SAP HANA Cloud ({HOST}:{PORT}) as {USER}...")
conn = dbapi.connect(address=HOST, port=PORT, user=USER, password=PASSWORD)
cur = conn.cursor()

cur.execute("SELECT VERSION FROM SYS.M_DATABASE")
hana_version = cur.fetchone()[0]
print(f"Connected! SAP HANA Version: {hana_version}\n")

cur.execute("""
    SELECT t.TABLE_NAME, t.TABLE_TYPE, t.IS_COLUMN_TABLE,
           COALESCE(m.RECORD_COUNT, 0) AS RECORD_COUNT,
           ROUND(COALESCE(m.MEMORY_SIZE_IN_TOTAL, 0) / 1024.0 / 1024.0, 2) AS MEMORY_MB
    FROM SYS.TABLES t
    LEFT JOIN SYS.M_TABLES m
      ON t.SCHEMA_NAME = m.SCHEMA_NAME AND t.TABLE_NAME = m.TABLE_NAME
    WHERE t.SCHEMA_NAME = 'KEYA_MART'
    ORDER BY t.TABLE_NAME
""")
tables = cur.fetchall()

print("=== KEYA_MART TABLES ===")
print(f"{'Table Name':<32} {'Type':<10} {'Column?':<8} {'Rows':>10} {'Mem (MB)':>10}")
print("-" * 74)
for row in tables:
    print(f"{row[0]:<32} {row[1]:<10} {row[2]:<8} {row[3]:>10,} {row[4]:>10.2f}")

with open(OUT_DIR / "01_tables_inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["TABLE_NAME", "TABLE_TYPE", "IS_COLUMN_TABLE", "RECORD_COUNT", "MEMORY_MB"])
    w.writerows(tables)

cur.execute("""
    SELECT VIEW_NAME, VIEW_TYPE, IS_VALID
    FROM SYS.VIEWS
    WHERE SCHEMA_NAME = 'KEYA_MART'
    ORDER BY VIEW_NAME
""")
views = cur.fetchall()
print("\n=== KEYA_MART VIEWS ===")
for v in views:
    print(f"- {v[0]} (Type: {v[1]}, Valid: {v[2]})")

with open(OUT_DIR / "01_views_inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["VIEW_NAME", "VIEW_TYPE", "IS_VALID"])
    w.writerows(views)

cur.execute("""
    SELECT TABLE_NAME, POSITION, COLUMN_NAME, DATA_TYPE_NAME, LENGTH, IS_NULLABLE
    FROM SYS.TABLE_COLUMNS
    WHERE SCHEMA_NAME = 'KEYA_MART'
    ORDER BY TABLE_NAME, POSITION
""")
cols = cur.fetchall()
with open(OUT_DIR / "01_columns_inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["TABLE_NAME", "POSITION", "COLUMN_NAME", "DATA_TYPE_NAME", "LENGTH", "IS_NULLABLE"])
    w.writerows(cols)

cur.execute("""
    SELECT TABLE_NAME, INDEX_NAME, INDEX_TYPE, CONSTRAINT
    FROM SYS.INDEXES
    WHERE SCHEMA_NAME = 'KEYA_MART'
    ORDER BY TABLE_NAME, INDEX_NAME
""")
indexes = cur.fetchall()
print(f"\n=== KEYA_MART INDEXES ({len(indexes)} found) ===")
for idx in indexes:
    print(f"- {idx[0]}.{idx[1]} ({idx[2]}, Constraint: {idx[3]})")

with open(OUT_DIR / "01_indexes_inventory.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["TABLE_NAME", "INDEX_NAME", "INDEX_TYPE", "CONSTRAINT"])
    w.writerows(indexes)

cur.close()
conn.close()
print(f"\nSaved all inventory CSVs to: {OUT_DIR}")