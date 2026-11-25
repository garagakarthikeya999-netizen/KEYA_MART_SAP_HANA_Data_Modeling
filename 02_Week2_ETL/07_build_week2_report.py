from io import BytesIO
from pathlib import Path
import pandas as pd
from PIL import Image
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

ROOT = Path(r"C:\Users\garag\Documents\SAP_HANA_WEEK1_PROJECT")
OUT_DIR = ROOT / "02_Week2_ETL" / "outputs"
DIAG_DIR = ROOT / "04_Diagrams"
SHOT_DIR = ROOT / "06_Screenshots"
DOC_PATH = ROOT / "05_Documentation" / "KEYA_MART_Week2_ETL_Report.docx"

SAP_BLUE = RGBColor(0x0F, 0x4C, 0x81)
DARK_TEXT = RGBColor(0x1F, 0x29, 0x37)
MUTED_TEXT = RGBColor(0x4B, 0x55, 0x63)

doc = Document()
for section in doc.sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

normal = doc.styles["Normal"]
normal.font.name = "Calibri"
normal.font.size = Pt(10.5)
normal.font.color.rgb = DARK_TEXT


def add_heading(text, level=1):
    h = doc.add_heading(text, level=level)
    for run in h.runs:
        run.font.name = "Calibri"
        run.font.color.rgb = SAP_BLUE
        run.font.bold = True
    h.paragraph_format.keep_with_next = True
    return h


def add_body(text, bold_prefix=None):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(6)
    if bold_prefix:
        r0 = p.add_run(bold_prefix)
        r0.bold = True
    p.add_run(text)
    return p


def add_csv_table(csv_name):
    df = pd.read_csv(OUT_DIR / csv_name)
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"

    hdr_cells = table.rows[0].cells
    for idx, col in enumerate(df.columns):
        hdr_cells[idx].text = str(col).replace("_", " ").title()
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="0F4C81"/>')
        hdr_cells[idx]._tc.get_or_add_tcPr().append(shading)
        for p in hdr_cells[idx].paragraphs:
            for r in p.runs:
                r.font.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)

    for r_idx, row in df.iterrows():
        cells = table.add_row().cells
        fill = "F4F7FA" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cells[c_idx].text = "" if pd.isna(val) else str(val)
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill}"/>')
            cells[c_idx]._tc.get_or_add_tcPr().append(shading)
            for p in cells[c_idx].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_image(img_path, caption, max_width_px=1400, quality=82):
    with Image.open(img_path) as im:
        rgb = im.convert("RGB")
        if rgb.width > max_width_px:
            ratio = max_width_px / rgb.width
            rgb = rgb.resize((max_width_px, int(rgb.height * ratio)), Image.Resampling.LANCZOS)
        buf = BytesIO()
        rgb.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(buf, width=Inches(6.4))
    cap = doc.add_paragraph(caption)
    cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in cap.runs:
        r.italic = True
        r.font.size = Pt(9.5)
        r.font.color.rgb = MUTED_TEXT


# --- Title Section ---
title = doc.add_paragraph()
title.alignment = WD_ALIGN_PARAGRAPH.CENTER
title.paragraph_format.space_before = Pt(36)
r_t = title.add_run("WEEK 2 REPORT\nDATA EXTRACTION, TRANSFORMATION AND LOADING\nUSING SAP HANA CLOUD")
r_t.bold = True
r_t.font.size = Pt(20)
r_t.font.color.rgb = SAP_BLUE

sub = doc.add_paragraph()
sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
sub.paragraph_format.space_after = Pt(18)
r_s = sub.add_run("Project: KEYA MART - E-Commerce Analytics Using SAP HANA Cloud\nSchema: KEYA_MART | Dataset: Olist Brazilian E-Commerce\nAuthor: Karthikeya Garaga (GitHub: garagakarthikeya999-netizen)")
r_s.font.size = Pt(11)
r_s.font.color.rgb = MUTED_TEXT

doc.add_page_break()

# --- 1. Executive Summary ---
add_heading("1. Executive Summary", level=1)
add_body(
    "This report documents the complete Week 2 Extract, Transform, and Load (ETL) pipeline for the KEYA MART "
    "E-Commerce Analytics project on SAP HANA Cloud. Starting from 9 raw Olist Brazilian E-Commerce CSV files "
    "(1,550,922 raw records), the Python pipeline extracted, profiled, cleaned, deduplicated, and integrated the "
    "data into 8 clean CSV datasets totaling 569,703 records. All table counts were verified against the KEYA_MART "
    "schema (13 COLUMN tables and 3 analytical views), 19,015 deduplicated geolocation rows were batch-loaded into "
    "WEEK2_STAGING_GEOLOCATION in 10.92 seconds, and 17 out of 17 end-to-end SQL validation checks passed."
)

# --- 2. Environment & Workspace ---
add_heading("2. Technical Environment & Workspace", level=1)
add_body("C:\\Users\\garag\\Documents\\SAP_HANA_WEEK1_PROJECT (Windows, VS Code, Python .venv)", "Local Workspace: ")
add_body("pandas 3.1.1, numpy 2.5.5, hdbcli 2.30.32, python-docx 1.2.0, Pillow 13.0.0", "Python Libraries: ")
add_body("SAP HANA Cloud (TLS Port 443), Schema: KEYA_MART, User: DBADMIN (<REDACTED>)", "Cloud Database: ")

# --- 3. Architecture & Workflow Diagrams ---
add_heading("3. ETL Architecture & Workflow Diagrams", level=1)
add_body("The five diagrams below illustrate the complete Week 2 ETL design created in Draw.io.")
add_image(DIAG_DIR / "01_Overall_ETL_Architecture.drawio.png", "Figure 1: Overall ETL Architecture")
add_image(DIAG_DIR / "02_Data_Extraction_Flowchart.drawio.png", "Figure 2: Data Extraction Flowchart (01_extract_olist.py)")
add_image(DIAG_DIR / "03_Data_Transformation_Flowchart.drawio.png", "Figure 3: Data Transformation Flowchart (03_transform_olist.py)")
add_image(DIAG_DIR / "04_SAP_HANA_Loading_Architecture.drawio.png", "Figure 4: SAP HANA Data Loading Architecture (04_load_to_hana.py)")
add_image(DIAG_DIR / "05_End_to_End_ETL_Workflow.drawio.png", "Figure 5: Complete End-to-End ETL Workflow")

# --- 4. Data Extraction ---
add_heading("4. Phase 2 - Data Extraction (01_extract_olist.py)", level=1)
add_body(
    "The extraction script verified all 9 raw Olist CSV files for existence, UTF-8 encoding, and comma delimitation, "
    "confirming 1,550,922 raw records across the dataset."
)
add_csv_table("01_extraction_summary.csv")

# --- 5. Data Profiling ---
add_heading("5. Phase 3 - Data Profiling (02_profile_olist.py)", level=1)
add_body(
    "Profiling identified key data quality issues before loading: 261,831 exact duplicates in geolocation, "
    "814 single-column review_id duplicates (0 duplicates on composite key review_id + order_id), "
    "610 missing product categories, 13 untranslated Portuguese categories, 2 missing dimensions, and valid business nulls in orders."
)
add_csv_table("02_file_quality_summary.csv")

# --- 6. Data Transformation ---
add_heading("6. Phase 4 - Data Transformation & Integration (03_transform_olist.py)", level=1)
add_body(
    "Transformation reduced geolocation from 1,000,163 rows to 19,015 unique zip code prefixes (removing 981,148 redundant rows), "
    "applied 625 product fixes (English category translations, missing category handling, and fixing the 'lenght' column typo), "
    "standardized timestamps and strings, and produced 8 clean CSVs totaling 569,703 records with 0 rejected rows."
)
add_csv_table("03_transformation_audit.csv")

# --- 7. SAP HANA Loading ---
add_heading("7. Phase 5 - SAP HANA Cloud Data Loading (04_load_to_hana.py)", level=1)
add_body(
    "Using hdbcli 2.30.32 over TLS port 443, the loader verified 8/8 table row counts between the clean CSVs and "
    "KEYA_MART tables, and batch-loaded 19,015 rows (5,000 rows per batch) into KEYA_MART.WEEK2_STAGING_GEOLOCATION "
    "in 10.92 seconds with committed transaction handling."
)
add_csv_table("04_hana_load_verification.csv")

# --- 8. E2E SQL Validation ---
add_heading("8. Phase 6 - End-to-End SQL Data Validation (05_validate_hana_e2e.py)", level=1)
add_body(
    "All 17 live SQL checks passed in SAP HANA Cloud: 0 primary/composite key duplicates, 0 critical nulls, "
    "0 foreign key orphans, 0 negative prices or payments, FACT_SALES verified at 112,650 rows, and all 3 analytical views "
    "verified (VW_KEYA_MART_SALES_CUBE: 112,650 rows; VW_CATEGORY_SALES_SUMMARY: 74 rows; VW_MONTHLY_STATE_PERFORMANCE: 556 rows)."
)
add_csv_table("05_e2e_validation_summary.csv")

# --- 9. Challenges & Solutions ---
add_heading("9. Phase 8 - Challenges & Solutions", level=1)
add_body("The table below summarizes the real cloud connectivity, authentication, and data quality challenges resolved during Week 2.")
add_csv_table("06_challenges_and_solutions.csv")

# --- 10. Execution & Verification Screenshots ---
screenshots = sorted(
    p for p in SHOT_DIR.iterdir()
    if p.is_file() and p.suffix.lower() in {".png", ".jpg", ".jpeg"}
) if SHOT_DIR.exists() else []

add_heading("10. Execution & Verification Screenshots", level=1)
if screenshots:
    add_body(f"Included {len(screenshots)} verification screenshot(s) from 06_Screenshots.")
    for idx, shot in enumerate(screenshots, start=6):
        label = shot.stem.replace("_", " ").replace("-", " ").title()
        add_image(shot, f"Figure {idx}: {label}", max_width_px=1300, quality=78)
else:
    add_body("No screenshots were found in 06_Screenshots at build time.")

# --- 11. Conclusion ---
add_heading("11. Conclusion", level=1)
add_body(
    "The Week 2 ETL pipeline successfully transformed 1,550,922 raw Olist records into 569,703 clean, validated records "
    "in SAP HANA Cloud (KEYA_MART), backed by automated Python audit logs, 17 passing SQL integrity checks, and 5 architecture diagrams."
)

DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
doc.save(DOC_PATH)
size_kb = DOC_PATH.stat().st_size / 1024
print(f"Generated: {DOC_PATH}")
print(f"Screenshots embedded: {len(screenshots)} -> {[s.name for s in screenshots]}")
print(f"File size: {size_kb:.1f} KB (Limit: 2048 KB)")