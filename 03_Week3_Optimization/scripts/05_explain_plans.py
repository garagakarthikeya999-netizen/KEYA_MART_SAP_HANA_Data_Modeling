import os
import re
import csv
from pathlib import Path
import pandas as pd
from hdbcli import dbapi

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

conn = dbapi.connect(
    address=os.environ["HANA_HOST"],
    port=int(os.environ.get("HANA_PORT", "443")),
    user=os.environ["HANA_USER"],
    password=os.environ["HANA_PASSWORD"],
)
cur = conn.cursor()

sql_text = (PROJECT_ROOT / "03_Week3_Optimization" / "sql" / "01_baseline_queries.sql").read_text(encoding="utf-8")
pattern = re.compile(r"--\s*\[(Q\d+)\]\s*(.+?)\n(.*?);", re.DOTALL)

out_dir = PROJECT_ROOT / "03_Week3_Optimization" / "outputs"
rows_all = []

cur.execute("DELETE FROM EXPLAIN_PLAN_TABLE")

for m in pattern.finditer(sql_text):
    qid, desc, sql = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
    stmt_name = f"BASE_{qid}"
    cur.execute(f"EXPLAIN PLAN SET STATEMENT_NAME = '{stmt_name}' FOR {sql}")
    cur.execute("""
        SELECT OPERATOR_ID, PARENT_OPERATOR_ID, OPERATOR_NAME,
               COALESCE(TABLE_NAME, ''), COALESCE(OPERATOR_DETAILS, ''),
               ROUND(COALESCE(OUTPUT_SIZE, 0), 2), ROUND(COALESCE(SUBTREE_COST, 0), 6)
        FROM EXPLAIN_PLAN_TABLE
        WHERE STATEMENT_NAME = ?
        ORDER BY OPERATOR_ID
    """, (stmt_name,))
    ops = cur.fetchall()
    print(f"\n=== [{qid}] {desc} (Root Cost: {ops[0][6] if ops else 'N/A'}) ===")
    for op in ops[:8]:
        tbl = f" [{op[3]}]" if op[3] else ""
        print(f"  ID {op[0]} -> {op[2]}{tbl} | Rows: {op[5]} | Cost: {op[6]}")
        rows_all.append([qid, desc, op[0], op[1], op[2], op[3], op[4], op[5], op[6]])
    for op in ops[8:]:
        rows_all.append([qid, desc, op[0], op[1], op[2], op[3], op[4], op[5], op[6]])

with open(out_dir / "05_explain_plans.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["Query_ID", "Description", "Op_ID", "Parent_ID", "Operator", "Table", "Details", "Est_Rows", "Subtree_Cost"])
    w.writerows(rows_all)

print("\n=== BASELINE BENCHMARK SUMMARY ===")
df = pd.read_csv(out_dir / "baseline_benchmark_summary.csv")
print(df[["Query_ID", "Rows_Returned", "Client_Median_ms", "Client_Avg_ms", "Server_Avg_ms", "Server_Avg_Mem_MB"]].to_string(index=False))

cur.close()
conn.close()