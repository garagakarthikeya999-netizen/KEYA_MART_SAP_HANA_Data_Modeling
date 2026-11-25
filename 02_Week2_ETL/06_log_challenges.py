from pathlib import Path
import pandas as pd

output_dir = Path(r"C:\Users\garag\Documents\SAP_HANA_WEEK1_PROJECT\02_Week2_ETL\outputs")
output_dir.mkdir(parents=True, exist_ok=True)

challenges = [
    {
        "challenge_id": "CH-01",
        "phase": "Phase 5 - SAP HANA Load",
        "category": "Cloud Connectivity",
        "issue_encountered": "SAP HANA connection failed with Error -10709 (socket closed from host).",
        "root_cause": "Local machine IP address was not listed in SAP HANA Cloud Central Allowed Connections.",
        "solution_applied": "Added the current public IP address to the IP Allowlist in SAP HANA Cloud Central and re-tested TLS port 443.",
        "verified_outcome": "Python hdbcli 2.30.32 connected cleanly to KEYA_MART."
    },
    {
        "challenge_id": "CH-02",
        "phase": "Phase 5 - SAP HANA Load",
        "category": "Authentication",
        "issue_encountered": "Login failed with Error 414 (forced password change required for DBADMIN).",
        "root_cause": "Initial or expired DBADMIN password required an interactive reset before programmatic SQL access.",
        "solution_applied": "Executed ALTER USER DBADMIN PASSWORD in SAP HANA Database Explorer SQL Console using a new password.",
        "verified_outcome": "Programmatic login succeeded; credentials kept redacted in scripts and reports."
    },
    {
        "challenge_id": "CH-03",
        "phase": "Phase 3 & 4 - Profiling & Transform",
        "category": "Data Volume / Duplicates",
        "issue_encountered": "Geolocation CSV contained 1,000,163 rows with 261,831 exact duplicates.",
        "root_cause": "Multiple latitude/longitude entries existed per Brazilian zip code prefix.",
        "solution_applied": "Aggregated geolocation records by geolocation_zip_code_prefix in 03_transform_olist.py.",
        "verified_outcome": "Reduced table to 19,015 unique zip prefixes (981,148 redundant rows removed) and batch-loaded in 10.92s."
    },
    {
        "challenge_id": "CH-04",
        "phase": "Phase 3 & 6 - Profiling & Validation",
        "category": "Primary Key Integrity",
        "issue_encountered": "Found 814 duplicate values on single-column review_id in olist_order_reviews_dataset.csv.",
        "root_cause": "A single review_id can appear across multiple order_id entries in Olist data.",
        "solution_applied": "Validated uniqueness using the composite key (review_id, order_id) instead of review_id alone.",
        "verified_outcome": "0 duplicate composite keys confirmed in both Python profiling and Phase 6 SQL checks."
    },
    {
        "challenge_id": "CH-05",
        "phase": "Phase 3 & 4 - Profiling & Transform",
        "category": "Missing & Untranslated Data",
        "issue_encountered": "610 missing product categories, 13 untranslated Portuguese categories, 2 missing dimensions, and 'lenght' column typo.",
        "root_cause": "Incomplete source product metadata and inconsistent column naming in raw Olist CSVs.",
        "solution_applied": "Joined English category translations, standardized missing values, and renamed 'lenght' to 'length' in 03_transform_olist.py.",
        "verified_outcome": "625 product fixes applied cleanly with 0 rejected records."
    }
]

df = pd.DataFrame(challenges)
out_file = output_dir / "06_challenges_and_solutions.csv"
df.to_csv(out_file, index=False, encoding="utf-8")

print(f"Saved {len(df)} challenges to: {out_file}")
print(df[["challenge_id", "phase", "category"]].to_string(index=False))