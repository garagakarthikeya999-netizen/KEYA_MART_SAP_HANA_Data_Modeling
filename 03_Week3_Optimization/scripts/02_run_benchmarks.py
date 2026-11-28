import os
import re
import csv
import time
import argparse
import getpass
import statistics
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
    queries = []
    for match in pattern.finditer(text):
        qid = match.group(1).strip()
        desc = match.group(2).strip()
        sql = match.group(3).strip()
        queries.append((qid, desc, sql))
    return queries


def get_plan_cache_metrics(cur, marker: str):
    """Fetch server-side execution metrics from SYS.M_SQL_PLAN_CACHE if available."""
    try:
        cur.execute(
            """
            SELECT TOP 1
                ROUND(AVG_EXECUTION_TIME / 1000.0, 3) AS SERVER_AVG_MS,
                ROUND(AVG_EXECUTION_MEMORY_SIZE / 1048576.0, 3) AS AVG_MEM_MB,
                EXECUTION_COUNT
            FROM SYS.M_SQL_PLAN_CACHE
            WHERE STATEMENT_STRING LIKE ?
              AND STATEMENT_STRING NOT LIKE '%M_SQL_PLAN_CACHE%'
            ORDER BY LAST_EXECUTION_TIMESTAMP DESC
            """,
            (f"%{marker}%",),
        )
        row = cur.fetchone()
        if row:
            return float(row[0] or 0), float(row[1] or 0), int(row[2] or 0)
    except Exception:
        pass
    return None, None, None


def main():
    parser = argparse.ArgumentParser(description="KEYA MART SAP HANA Query Benchmarker")
    parser.add_argument("--sql", required=True, help="Path to SQL file")
    parser.add_argument("--tag", required=True, help="Output prefix (e.g. baseline or optimized)")
    parser.add_argument("--trials", type=int, default=5, help="Number of timed trials (default: 5)")
    args = parser.parse_args()

    sql_path = Path(args.sql)
    queries = parse_queries(sql_path)
    if not queries:
        raise RuntimeError(f"No [Qxx] queries found in {sql_path}")

    host = os.environ.get(
        "HANA_HOST",
        "bb2e6931-61eb-40f2-ac16-34972b965bc5.hna0.prod-us10.hanacloud.ondemand.com",
    )
    port = int(os.environ.get("HANA_PORT", "443"))
    user = os.environ.get("HANA_USER", "DBADMIN")
    password = os.environ.get("HANA_PASSWORD") or getpass.getpass(
        f"Enter SAP HANA password for {user}: "
    )

    out_dir = PROJECT_ROOT / "03_Week3_Optimization" / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nConnecting to SAP HANA Cloud ({host}:{port})...")
    conn = dbapi.connect(address=HOST if False else host, port=port, user=user, password=password)
    cur = conn.cursor()
    print(f"Connected! Running {len(queries)} queries (1 warm-up + {args.trials} trials each)...\n")

    summary_rows = []
    trial_rows = []

    for qid, desc, sql in queries:
        marker = f"/* {args.tag}_{qid} */"
        tagged_sql = f"{marker}\n{sql}"

        # 1. Warm-up run (not timed)
        cur.execute(tagged_sql)
        warmup_data = cur.fetchall()
        row_count = len(warmup_data)

        # 2. Timed trials
        times_ms = []
        for t in range(1, args.trials + 1):
            t0 = time.perf_counter()
            cur.execute(tagged_sql)
            cur.fetchall()
            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            times_ms.append(elapsed_ms)
            trial_rows.append({
                "Phase": args.tag,
                "Query_ID": qid,
                "Trial": t,
                "Client_Time_ms": elapsed_ms,
                "Rows_Returned": row_count,
            })

        srv_ms, mem_mb, exec_cnt = get_plan_cache_metrics(cur, f"{args.tag}_{qid}")
        med_ms = round(statistics.median(times_ms), 3)
        avg_ms = round(statistics.mean(times_ms), 3)
        min_ms = round(min(times_ms), 3)
        max_ms = round(max(times_ms), 3)
        std_ms = round(statistics.stdev(times_ms), 3) if len(times_ms) > 1 else 0.0

        print(
            f"[{qid}] {desc:<45} | Rows: {row_count:>3} | "
            f"Client Median: {med_ms:>8.2f} ms | Server Avg: {srv_ms if srv_ms is not None else 'N/A'} ms"
        )

        summary_rows.append({
            "Query_ID": qid,
            "Description": desc,
            "Rows_Returned": row_count,
            "Client_Median_ms": med_ms,
            "Client_Avg_ms": avg_ms,
            "Client_Min_ms": min_ms,
            "Client_Max_ms": max_ms,
            "Client_StdDev_ms": std_ms,
            "Server_Avg_ms": srv_ms,
            "Server_Avg_Mem_MB": mem_mb,
            "SQL_Statement": sql,
        })

    cur.close()
    conn.close()

    df_summary = pd.DataFrame(summary_rows)
    df_trials = pd.DataFrame(trial_rows)

    csv_path = out_dir / f"{args.tag}_benchmark_summary.csv"
    trials_path = out_dir / f"{args.tag}_benchmark_trials.csv"
    xlsx_path = out_dir / f"{args.tag}_benchmark_results.xlsx"

    df_summary.to_csv(csv_path, index=False, encoding="utf-8")
    df_trials.to_csv(trials_path, index=False, encoding="utf-8")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        df_summary.to_excel(writer, sheet_name="Summary", index=False)
        df_trials.to_excel(writer, sheet_name="All_Trials", index=False)

    print(f"\nSaved benchmark results to:\n- {csv_path}\n- {trials_path}\n- {xlsx_path}")


if __name__ == "__main__":
    main()
