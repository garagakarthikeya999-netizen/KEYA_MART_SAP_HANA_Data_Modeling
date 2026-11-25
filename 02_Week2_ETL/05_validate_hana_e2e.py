"""
KEYA MART - Week 2 ETL Pipeline
Phase 6: End-to-End SQL Data Validation in SAP HANA Cloud
Executes live SQL validation checks on KEYA_MART:
- Source vs Target row counts
- Duplicate & Primary Key uniqueness checks
- Critical Null value checks
- Foreign Key referential integrity checks
- Business rule checks & Analytical View verification
"""

import getpass
from pathlib import Path
import pandas as pd
from hdbcli import dbapi

PROJECT_ROOT = Path(r"C:\Users\garag\Documents\SAP_HANA_WEEK1_PROJECT")
OUTPUT_DIR = PROJECT_ROOT / "02_Week2_ETL" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_check(cursor, check_name, category, sql, expected_desc, pass_condition):
    cursor.execute(sql)
    val = cursor.fetchone()[0]
    passed = pass_condition(val)
    status = "PASS" if passed else "FAIL"
    print(f"[{status}] {category:<16} | {check_name:<42} | Result: {val} (Expected: {expected_desc})")
    return {
        "category": category,
        "check_name": check_name,
        "expected": expected_desc,
        "actual_value": val,
        "status": status,
        "sql_query": " ".join(sql.split()),
    }


def main():
    print("=" * 95)
    print("KEYA MART - PHASE 6: END-TO-END SAP HANA SQL VALIDATION")
    print("=" * 95)

    host = input("Enter SAP HANA Cloud Host (without :443): ").strip()
    if host.endswith(":443"):
        host = host[:-4]
    user = input("Enter Username [default: DBADMIN]: ").strip() or "DBADMIN"
    password = getpass.getpass("Enter Password (hidden): ")

    conn = dbapi.connect(
        address=host,
        port=443,
        user=user,
        password=password,
        encrypt=True,
        sslValidateCertificate=False,
    )
    cursor = conn.cursor()
    cursor.execute("SET SCHEMA KEYA_MART")

    results = []

    print("\n--- 1. RUNNING SQL VALIDATION CHECKS ---")
    # A. Primary Key & Duplicate Checks
    results.append(run_check(
        cursor, "CUSTOMERS PK uniqueness (CUSTOMER_ID)", "PK / Duplicates",
        "SELECT COUNT(*) - COUNT(DISTINCT CUSTOMER_ID) FROM KEYA_MART.CUSTOMERS",
        "0 duplicates", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "ORDERS PK uniqueness (ORDER_ID)", "PK / Duplicates",
        "SELECT COUNT(*) - COUNT(DISTINCT ORDER_ID) FROM KEYA_MART.ORDERS",
        "0 duplicates", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "ORDER_ITEMS composite PK (ORDER+ITEM)", "PK / Duplicates",
        "SELECT COUNT(*) - COUNT(DISTINCT ORDER_ID || '-' || ORDER_ITEM_ID) FROM KEYA_MART.ORDER_ITEMS",
        "0 duplicates", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "ORDER_REVIEWS composite PK (REV+ORD)", "PK / Duplicates",
        "SELECT COUNT(*) - COUNT(DISTINCT REVIEW_ID || '-' || ORDER_ID) FROM KEYA_MART.ORDER_REVIEWS",
        "0 duplicates", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "WEEK2_STAGING_GEOLOCATION PK uniqueness", "PK / Duplicates",
        "SELECT COUNT(*) - COUNT(DISTINCT GEOLOCATION_ZIP_CODE_PREFIX) FROM KEYA_MART.WEEK2_STAGING_GEOLOCATION",
        "0 duplicates", lambda v: v == 0
    ))

    # B. Critical Null Checks
    results.append(run_check(
        cursor, "ORDERS null ORDER_ID or CUSTOMER_ID", "Null Check",
        "SELECT COUNT(*) FROM KEYA_MART.ORDERS WHERE ORDER_ID IS NULL OR CUSTOMER_ID IS NULL",
        "0 nulls", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "ORDER_ITEMS null PK/FK/PRICE", "Null Check",
        "SELECT COUNT(*) FROM KEYA_MART.ORDER_ITEMS WHERE ORDER_ID IS NULL OR PRODUCT_ID IS NULL OR SELLER_ID IS NULL OR PRICE IS NULL",
        "0 nulls", lambda v: v == 0
    ))

    # C. Foreign Key Referential Integrity
    results.append(run_check(
        cursor, "FK: ORDERS -> CUSTOMERS", "FK Integrity",
        "SELECT COUNT(*) FROM KEYA_MART.ORDERS o LEFT JOIN KEYA_MART.CUSTOMERS c ON o.CUSTOMER_ID = c.CUSTOMER_ID WHERE c.CUSTOMER_ID IS NULL",
        "0 orphans", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "FK: ORDER_ITEMS -> ORDERS", "FK Integrity",
        "SELECT COUNT(*) FROM KEYA_MART.ORDER_ITEMS oi LEFT JOIN KEYA_MART.ORDERS o ON oi.ORDER_ID = o.ORDER_ID WHERE o.ORDER_ID IS NULL",
        "0 orphans", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "FK: ORDER_ITEMS -> PRODUCTS", "FK Integrity",
        "SELECT COUNT(*) FROM KEYA_MART.ORDER_ITEMS oi LEFT JOIN KEYA_MART.PRODUCTS p ON oi.PRODUCT_ID = p.PRODUCT_ID WHERE p.PRODUCT_ID IS NULL",
        "0 orphans", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "FK: ORDER_ITEMS -> SELLERS", "FK Integrity",
        "SELECT COUNT(*) FROM KEYA_MART.ORDER_ITEMS oi LEFT JOIN KEYA_MART.SELLERS s ON oi.SELLER_ID = s.SELLER_ID WHERE s.SELLER_ID IS NULL",
        "0 orphans", lambda v: v == 0
    ))

    # D. Business Rules
    results.append(run_check(
        cursor, "Negative PRICE or FREIGHT_VALUE", "Business Rule",
        "SELECT COUNT(*) FROM KEYA_MART.ORDER_ITEMS WHERE PRICE < 0 OR FREIGHT_VALUE < 0",
        "0 invalid", lambda v: v == 0
    ))
    results.append(run_check(
        cursor, "Negative PAYMENT_VALUE", "Business Rule",
        "SELECT COUNT(*) FROM KEYA_MART.PAYMENTS WHERE PAYMENT_VALUE < 0",
        "0 invalid", lambda v: v == 0
    ))

    # E. Star Schema & Analytical Views Verification
    results.append(run_check(
        cursor, "FACT_SALES total records", "Star Schema",
        "SELECT COUNT(*) FROM KEYA_MART.FACT_SALES",
        "112650", lambda v: v == 112650
    ))
    results.append(run_check(
        cursor, "VW_KEYA_MART_SALES_CUBE row count", "Views",
        "SELECT COUNT(*) FROM KEYA_MART.VW_KEYA_MART_SALES_CUBE",
        "> 0", lambda v: v > 0
    ))
    results.append(run_check(
        cursor, "VW_CATEGORY_SALES_SUMMARY row count", "Views",
        "SELECT COUNT(*) FROM KEYA_MART.VW_CATEGORY_SALES_SUMMARY",
        "> 0", lambda v: v > 0
    ))
    results.append(run_check(
        cursor, "VW_MONTHLY_STATE_PERFORMANCE row count", "Views",
        "SELECT COUNT(*) FROM KEYA_MART.VW_MONTHLY_STATE_PERFORMANCE",
        "> 0", lambda v: v > 0
    ))

    # 2. Sample Analytical Query Output
    print("\n--- 2. TOP 5 CATEGORIES FROM VW_CATEGORY_SALES_SUMMARY ---")
    cursor.execute("SELECT TOP 5 * FROM KEYA_MART.VW_CATEGORY_SALES_SUMMARY")
    cols = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    top_df = pd.DataFrame(rows, columns=cols)
    print(top_df.to_string(index=False))

    # 3. Save Validation Scorecard
    val_df = pd.DataFrame(results)
    val_path = OUTPUT_DIR / "05_e2e_validation_summary.csv"
    val_df.to_csv(val_path, index=False, encoding="utf-8")

    passed_cnt = (val_df["status"] == "PASS").sum()
    print("\n" + "-" * 95)
    print(f"Validation Complete: {passed_cnt}/{len(val_df)} Checks PASSED")
    print(f"Scorecard saved to: {val_path}")
    print("=" * 95)

    conn.close()


if __name__ == "__main__":
    main()