
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

schema_inventory = []

print("=" * 70)
print("KEYA MART - SOURCE SCHEMA INVENTORY")
print("=" * 70)

for filename in sorted(os.listdir(RAW)):

    if not filename.lower().endswith(".csv"):
        continue

    filepath = os.path.join(RAW, filename)

    print("\nFILE:", filename)

    try:
        df = pd.read_csv(filepath, nrows=1000)

        print("Columns:", len(df.columns))

        for column in df.columns:

            dtype = str(df[column].dtype)
            null_count = int(df[column].isna().sum())

            schema_inventory.append({
                "source_file": filename,
                "column_name": column,
                "pandas_data_type": dtype,
                "null_values_in_sample": null_count,
                "sample_size": len(df)
            })

            print(
                f"  {column:<40} "
                f"Type: {dtype:<12} "
                f"Nulls in sample: {null_count}"
            )

    except Exception as error:
        print("ERROR:", error)

inventory = pd.DataFrame(schema_inventory)

output_file = os.path.join(
    OUTPUT,
    "source_schema_inventory.csv"
)

inventory.to_csv(output_file, index=False)

print("\n" + "=" * 70)
print("SCHEMA INSPECTION COMPLETED")
print("Saved report:", output_file)
print("=" * 70)
