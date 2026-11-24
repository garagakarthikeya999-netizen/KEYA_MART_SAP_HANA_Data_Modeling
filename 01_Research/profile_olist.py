
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

file_summary = []
column_profiles = []

print("=" * 65)
print("KEYA MART - OLIST DATASET PROFILING")
print("=" * 65)

for filename in sorted(os.listdir(RAW)):

    if not filename.lower().endswith(".csv"):
        continue

    filepath = os.path.join(RAW, filename)

    print("\nProcessing:", filename)

    total_rows = 0
    missing_counts = {}
    column_types = {}
    sample_parts = []

    try:
        for chunk in pd.read_csv(
            filepath,
            chunksize=100000,
            low_memory=False
        ):

            total_rows += len(chunk)

            for col in chunk.columns:
                missing_counts[col] = (
                    missing_counts.get(col, 0)
                    + int(chunk[col].isna().sum())
                )

                if col not in column_types:
                    column_types[col] = str(chunk[col].dtype)

            if not sample_parts:
                sample_parts.append(chunk.head(5))

        if sample_parts:
            sample_name = filename.replace(".csv", "_sample.csv")

            pd.concat(
                sample_parts,
                ignore_index=True
            ).to_csv(
                os.path.join(OUTPUT, sample_name),
                index=False
            )

        file_summary.append({
            "file_name": filename,
            "total_records": total_rows,
            "total_columns": len(column_types)
        })

        for col, dtype in column_types.items():

            missing = missing_counts[col]

            missing_percentage = (
                missing / total_rows * 100
                if total_rows else 0
            )

            column_profiles.append({
                "file_name": filename,
                "column_name": col,
                "inferred_data_type": dtype,
                "missing_values": missing,
                "missing_percentage": round(
                    missing_percentage, 2
                ),
                "business_meaning": "",
                "key_role": ""
            })

        print("Records:", total_rows)
        print("Columns:", len(column_types))

    except Exception as error:
        print("ERROR:", filename, error)

pd.DataFrame(file_summary).to_csv(
    os.path.join(OUTPUT, "file_summary.csv"),
    index=False
)

pd.DataFrame(column_profiles).to_csv(
    os.path.join(OUTPUT, "column_profile.csv"),
    index=False
)

print("\n" + "=" * 65)
print("DATA PROFILING COMPLETED")
print("Reports saved in:", OUTPUT)
print("=" * 65)
