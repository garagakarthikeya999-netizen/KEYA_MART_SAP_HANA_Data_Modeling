import os
import re
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


def parse_queries(sql_path: Path):
    text = sql_path.read_text(encoding="utf-8")
    pattern = re.compile(r"--\s*\[(Q\d+)\]\s*(.+?)\n(.*?);", re.DOTALL)
    return {m.group(1).strip(): m.group(3).strip() for m in pattern.finditer(text)}


base_q = parse_queries(PROJECT_ROOT / "03_Week3_Optimization" / "sql" / "01_baseline_queries.sql")
opt_q = parse_queries(PROJECT_ROOT / "03_Week3_Optimization" / "sql" / "02_optimized_queries.sql")

conn = dbapi.connect(
    address=os.environ["HANA_HOST"],
    port=int(os.environ.get("HANA_PORT", "443")),
    user=os.environ["HANA_USER"],
    password=os.environ["HANA_PASSWORD"],
)

results = []
for qid in sorted(base_q.keys()):
    df_b = pd.read_sql(base_q[qid], conn)
    df_o = pd.read_sql(opt_q[qid], conn)
    same_shape = df_b.shape == df_o.shape
    same_vals = False
    if same_shape:
        try:
            pd.testing.assert_frame_equal(
                df_b.astype(str).reset_index(drop=True),
                df_o.astype(str).reset_index(drop=True),
                check_dtype=False,
            )
            same_vals = True
        except AssertionError:
            same_vals = False

    status = "PASS" if (same_shape and same_vals) else "CHECK_MISMATCH"
    print(f"[{qid}] Baseline: {df_b.shape} | Optimized: {df_o.shape} | Status: {status}")
    results.append({
        "Query_ID": qid,
        "Baseline_Rows": df_b.shape[0],
        "Optimized_Rows": df_o.shape[0],
        "Equivalence_Status": status,
    })

conn.close()
out_path = PROJECT_ROOT / "03_Week3_Optimization" / "outputs" / "07_equivalence_check.csv"
pd.DataFrame(results).to_csv(out_path, index=False, encoding="utf-8")
print(f"\nSaved equivalence report to {out_path}")