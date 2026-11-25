import time
import getpass
from pathlib import Path
import pandas as pd
from hdbcli import dbapi

PROJECT_ROOT = Path(r"C:\Users\garag\Documents\SAP_HANA_WEEK1_PROJECT")
TRANSFORM_DIR = PROJECT_ROOT / "02_Week2_ETL" / "transformed"
OUTPUT_DIR = PROJECT_ROOT / "02_Week2_ETL" / "outputs"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TARGET_CHECK_TABLES = {
    "CUSTOMERS": "clean_customers.csv",
    "GEOLOCATION": "clean_geolocation.csv",
    "SELLERS": "clean_sellers.csv",
    "PRODUCTS": "clean_products.csv",
    "ORDERS": "clean_orders.csv",
    "ORDER_ITEMS": "clean_order_items.csv",
    "PAYMENTS": "clean_payments.csv",
    "ORDER_REVIEWS": "clean_order_reviews.csv",
}


def main():
    print("=" * 85)
    print("KEYA MART - PHASE 5: SAP HANA CLOUD CONNECTION & BATCH LOAD")
    print("=" * 85)

    host = input("Enter SAP HANA Cloud Host (without :443): ").strip()
    if host.endswith(":443"):
        host = host[:-4]
    user = input("Enter Username [default: DBADMIN]: ").strip() or "DBADMIN"
    password = getpass.getpass("Enter Password (hidden): ")

    conn = None
    try:
        # 1. Connect to SAP HANA Cloud
        conn = dbapi.connect(
            address=host,
            port=443,
            user=user,
            password=password,
            encrypt=True,
            sslValidateCertificate=False,
        )
        conn.setautocommit(False)
        cursor = conn.cursor()
        print("\n[CONNECTED] Successfully connected to SAP HANA Cloud!")

        # 2. Select KEYA_MART schema
        cursor.execute("SET SCHEMA KEYA_MART")
        print("[SCHEMA] Active schema set to KEYA_MART")

        # 3. Check existing Week 1 table compatibility & counts
        print("\n--- 1. EXISTING KEYA_MART TABLE COMPATIBILITY CHECK ---")
        check_rows = []
        for tbl_name, csv_name in TARGET_CHECK_TABLES.items():
            csv_rows = len(pd.read_csv(TRANSFORM_DIR / csv_name, encoding="utf-8"))
            cursor.execute(f"SELECT COUNT(*) FROM KEYA_MART.{tbl_name}")
            hana_rows = cursor.fetchone()[0]
            match_status = "MATCH" if csv_rows == hana_rows else "DIFF"
            print(f"{tbl_name:<15} | Clean CSV: {csv_rows:>8,} | HANA Table: {hana_rows:>8,} | {match_status}")
            check_rows.append({
                "table_name": tbl_name,
                "clean_csv_rows": csv_rows,
                "hana_table_rows": hana_rows,
                "status": match_status,
            })

        # 4. Safe Batch Load Demonstration into WEEK2_STAGING_GEOLOCATION
        print("\n--- 2. BATCH LOADING INTO KEYA_MART.WEEK2_STAGING_GEOLOCATION ---")
        cursor.execute("""
            DO BEGIN
                DECLARE tbl_exists INT;
                SELECT COUNT(*) INTO tbl_exists
                FROM SYS.TABLES
                WHERE SCHEMA_NAME = 'KEYA_MART' AND TABLE_NAME = 'WEEK2_STAGING_GEOLOCATION';
                IF :tbl_exists > 0 THEN
                    EXEC 'DROP TABLE KEYA_MART.WEEK2_STAGING_GEOLOCATION';
                END IF;
            END;
        """)
        cursor.execute("""
            CREATE COLUMN TABLE KEYA_MART.WEEK2_STAGING_GEOLOCATION (
                GEOLOCATION_ZIP_CODE_PREFIX NVARCHAR(10) PRIMARY KEY,
                GEOLOCATION_LAT DOUBLE,
                GEOLOCATION_LNG DOUBLE,
                GEOLOCATION_CITY NVARCHAR(100),
                GEOLOCATION_STATE NVARCHAR(10)
            )
        """)

        geo_df = pd.read_csv(TRANSFORM_DIR / "clean_geolocation.csv", encoding="utf-8")
        geo_df = geo_df.where(pd.notnull(geo_df), None)
        records = [
            (
                str(r.geolocation_zip_code_prefix).zfill(5),
                float(r.geolocation_lat),
                float(r.geolocation_lng),
                str(r.geolocation_city),
                str(r.geolocation_state),
            )
            for r in geo_df.itertuples(index=False)
        ]

        insert_sql = """
            INSERT INTO KEYA_MART.WEEK2_STAGING_GEOLOCATION
            (GEOLOCATION_ZIP_CODE_PREFIX, GEOLOCATION_LAT, GEOLOCATION_LNG, GEOLOCATION_CITY, GEOLOCATION_STATE)
            VALUES (?, ?, ?, ?, ?)
        """

        batch_size = 5000
        start_time = time.time()
        for i in range(0, len(records), batch_size):
            batch = records[i : i + batch_size]
            cursor.executemany(insert_sql, batch)
            print(f"  Inserted batch {i // batch_size + 1}: {len(batch):,} rows")

        conn.commit()
        elapsed = round(time.time() - start_time, 2)

        # 5. Verify loaded row count
        cursor.execute("SELECT COUNT(*) FROM KEYA_MART.WEEK2_STAGING_GEOLOCATION")
        loaded_count = cursor.fetchone()[0]
        print(f"\n[VERIFIED] Loaded {loaded_count:,} / {len(records):,} rows in {elapsed}s (Transaction Committed!)")

        # Save verification CSV
        pd.DataFrame(check_rows).to_csv(
            OUTPUT_DIR / "04_hana_load_verification.csv", index=False, encoding="utf-8"
        )
        print(f"Verification summary saved to: {OUTPUT_DIR / '04_hana_load_verification.csv'}")
        print("=" * 85)

    except dbapi.Error as err:
        if conn:
            conn.rollback()
        print(f"\n[HANA ERROR - ROLLED BACK] {err}")
    except Exception as ex:
        if conn:
            conn.rollback()
        print(f"\n[ERROR - ROLLED BACK] {ex}")
    finally:
        if conn:
            conn.close()
            print("[CLOSED] SAP HANA connection closed.")


if __name__ == "__main__":
    main()