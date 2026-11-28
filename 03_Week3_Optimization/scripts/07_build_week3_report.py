import re
from pathlib import Path
import pandas as pd
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

PROJECT_ROOT = Path(__file__).resolve().parents[2]
W3_DIR = PROJECT_ROOT / "03_Week3_Optimization"
OUT_DIR = W3_DIR / "outputs"
SQL_DIR = W3_DIR / "sql"
SCR_DIR = W3_DIR / "screenshots"
DOC_DIR = PROJECT_ROOT / "05_Documentation"
DOC_DIR.mkdir(parents=True, exist_ok=True)
REPORT_PATH = DOC_DIR / "KEYA_MART_Week3_Performance_Optimization_Report.docx"


def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run("KEYA MART – Week 3 SQL Performance Optimization   |   Page ")
    run.font.size = Pt(8.5)
    run.font.color.rgb = RGBColor(110, 110, 110)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    p._p.append(fld)


def set_cell_bg(cell, hex_color: str):
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def add_styled_table(doc, df: pd.DataFrame, col_widths=None):
    table = doc.add_table(rows=1, cols=len(df.columns))
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = table.rows[0].cells
    for i, col in enumerate(df.columns):
        hdr[i].text = str(col)
        set_cell_bg(hdr[i], "1F4E79")
        for p in hdr[i].paragraphs:
            for r in p.runs:
                r.bold = True
                r.font.size = Pt(9)
                r.font.color.rgb = RGBColor(255, 255, 255)
    for r_idx, row in df.iterrows():
        cells = table.add_row().cells
        bg = "F4F7FA" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row):
            cells[c_idx].text = "" if pd.isna(val) else str(val)
            set_cell_bg(cells[c_idx], bg)
            for p in cells[c_idx].paragraphs:
                for r in p.runs:
                    r.font.size = Pt(8.5)
    if col_widths:
        for row in table.rows:
            for idx, w in enumerate(col_widths):
                row.cells[idx].width = Inches(w)
    doc.add_paragraph()


def add_code_block(doc, title: str, code_text: str):
    p_title = doc.add_paragraph()
    r_t = p_title.add_run(title)
    r_t.bold = True
    r_t.font.size = Pt(10)
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.2)
    r = p.add_run(code_text.strip())
    r.font.name = "Consolas"
    r.font.size = Pt(8)
    r.font.color.rgb = RGBColor(30, 30, 30)


def main():
    # Load real measured outputs
    df_tables = pd.read_csv(OUT_DIR / "01_tables_inventory.csv")
    df_views = pd.read_csv(OUT_DIR / "01_views_inventory.csv")
    df_idx = pd.read_csv(OUT_DIR / "01_indexes_inventory.csv")
    df_base = pd.read_csv(OUT_DIR / "baseline_benchmark_summary.csv")
    df_opt = pd.read_csv(OUT_DIR / "optimized_benchmark_summary.csv")
    df_comp = pd.read_csv(OUT_DIR / "comparison_summary.csv")
    df_eq = pd.read_csv(OUT_DIR / "07_equivalence_check.csv")
    df_exp = pd.read_csv(OUT_DIR / "05_explain_plans.csv")
    df_chal = (
        pd.read_csv(OUT_DIR / "06_week3_challenges_and_solutions.csv")
        if (OUT_DIR / "06_week3_challenges_and_solutions.csv").exists()
        else pd.DataFrame(columns=["Challenge_ID", "Phase", "Problem", "Root_Cause", "Troubleshooting_Process", "Solution", "Result"])
    )

    doc = Document()
    style = doc.styles["Normal"]
    style.font.name = "Calibri"
    style.font.size = Pt(10.5)

    for s in doc.sections:
        s.top_margin = Inches(0.75)
        s.bottom_margin = Inches(0.75)
        s.left_margin = Inches(0.8)
        s.right_margin = Inches(0.8)
        add_page_number_footer(s)

    # 1 & 2. Cover Page & Project Title
    p_kicker = doc.add_paragraph()
    p_kicker.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rk = p_kicker.add_run("\n\nSAP HANA CLOUD PERFORMANCE ENGINEERING – WEEK 3 SUBMISSION\n")
    rk.bold = True
    rk.font.size = Pt(11)
    rk.font.color.rgb = RGBColor(31, 78, 121)

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rt = p_title.add_run("KEYA MART – E-Commerce Analytics\nSQL Query Performance Optimization")
    rt.bold = True
    rt.font.size = Pt(24)
    rt.font.color.rgb = RGBColor(20, 45, 76)

    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    rs = p_sub.add_run("\nSubmitted by: GARAGA KARTHI KEYA\nDataset: Brazilian E-Commerce Public Dataset by Olist\nPlatform: SAP HANA Cloud | Python | pandas | matplotlib\n")
    rs.font.size = Pt(11.5)
    doc.add_page_break()

    avg_base = df_comp["Client_Median_ms_Base"].mean()
    avg_opt = df_comp["Client_Median_ms_Opt"].mean()
    avg_imp = ((avg_base - avg_opt) / avg_base) * 100.0
    best_row = df_comp.loc[df_comp["Improvement_Pct"].idxmax()]

    # 3. Executive Summary
    doc.add_heading("1. Executive Summary", level=1)
    doc.add_paragraph(
        f"This Week 3 report documents the end-to-end SQL query performance optimization of the KEYA MART "
        f"e-commerce analytics warehouse on SAP HANA Cloud. Ten analytical queries (Q01–Q10) were benchmarked "
        f"using a 1-warm-up + 5-trial methodology. Across all 10 queries, average median execution time "
        f"changed from {avg_base:.2f} ms (baseline) to {avg_opt:.2f} ms (optimized), achieving an overall "
        f"average improvement of {avg_imp:.2f}%. The highest gain was observed on {best_row['Query_ID']} "
        f"({best_row['Improvement_Pct']:.2f}% improvement, {best_row['Speedup_X']:.2f}x speedup)."
    )

    # 4. Table of Contents
    doc.add_heading("2. Table of Contents", level=1)
    toc_items = [
        "1. Executive Summary", "2. Table of Contents", "3. Introduction & Project Objectives",
        "4. Business Scenario & Dataset Description", "5. SAP HANA Cloud Environment & Schema Overview",
        "6. SQL Performance Optimization Fundamentals", "7. Benchmarking Methodology",
        "8. Query Selection & Baseline SQL Queries", "9. Initial Benchmark Results",
        "10. Query Execution Plan Analysis & Bottlenecks", "11. Optimization Strategies & Optimized SQL",
        "12. Indexing & Partitioning Analysis", "13. Post-Optimization Benchmark & Before-vs-After Comparison",
        "14. Charts and Visualizations", "15. Challenges and Solutions",
        "16. Technical Observations, Conclusion & Future Enhancements", "17. References & Appendices"
    ]
    for item in toc_items:
        doc.add_paragraph(item, style="List Bullet")

    # 5 & 6. Introduction & Project Objectives
    doc.add_heading("3. Introduction & Project Objectives", level=1)
    doc.add_paragraph(
        "Building on Week 1 (Star Schema modeling) and Week 2 (automated Python ETL), Week 3 focuses on "
        "measuring real SQL query performance in SAP HANA Cloud, analyzing execution plans, removing "
        "unnecessary view joins and intermediate data movement, verifying 100% result equivalence, and "
        "quantifying before-and-after improvements with charts and tables."
    )

    # 7 & 8. Business Scenario & Dataset
    doc.add_heading("4. Business Scenario & Dataset Description", level=1)
    doc.add_paragraph(
        "KEYA MART is an e-commerce analytics platform built on the Brazilian E-Commerce Public Dataset by Olist. "
        "It supports reporting across sales revenue, monthly trends, product categories, seller rankings, repeat "
        "customers, state-level sales, order statuses, delivery SLAs, and payment methods."
    )

    # 9 & 10. Environment & Schema Overview
    doc.add_heading("5. SAP HANA Cloud Environment & Schema Overview", level=1)
    doc.add_paragraph("Live table inventory in schema KEYA_MART:")
    add_styled_table(doc, df_tables)
    doc.add_paragraph("Analytical views in schema KEYA_MART:")
    add_styled_table(doc, df_views)

    # 11. Fundamentals
    doc.add_heading("6. SQL Performance Optimization Fundamentals", level=1)
    concepts = [
        ("1. SQL Query Performance", "Speed and resource efficiency of answering a query.", "Summing 112,650 FACT_SALES rows in ms."),
        ("2. Query Optimization", "Rewriting or restructuring SQL for faster execution with identical results.", "Bypassing nested 4-join views."),
        ("3. Query Execution Time", "Total clock time from query submission to result delivery.", "5-trial median time per query (Q01-Q10)."),
        ("4. Execution Planning", "Optimizer choosing the lowest-cost execution path using statistics.", "Choosing join order for FACT_SALES + DIM_PRODUCT."),
        ("5. Execution Plan", "Step-by-step operator blueprint generated by the database.", "Viewed via EXPLAIN_PLAN_TABLE."),
        ("6. SAP HANA PlanViz", "Visual timeline and operator graph in Database Explorer.", "Identifies exact ms per join/aggregation box."),
        ("7. Explain Plan", "Tabular cost estimate before or without full visualization.", "EXPLAIN PLAN SET STATEMENT_NAME FOR ..."),
        ("8. SQLScript", "Procedural SQL language running logic inside HANA engine.", "Avoids pulling large datasets into Python."),
        ("9. Column-Store Table", "Stores each column separately with dictionary compression.", "FACT_SALES reads only item_price when summing."),
        ("10. Row-Store Table", "Stores full records contiguously; suited for single-row OLTP lookups.", "Not used for KEYA_MART analytical tables."),
        ("11. Indexing", "Lookup structure; HANA columns are already dictionary-encoded.", "Secondary indexes justified only for selective lookups."),
        ("12. Partitioning", "Splitting huge tables into smaller physical parts.", "Not needed for 112,650 rows in FACT_SALES."),
        ("13. Query Pruning", "Skipping unneeded columns (column pruning) or partitions.", "Replacing SELECT * with explicit columns."),
        ("14. Joins and Aggregations", "Combining tables and summarizing metrics.", "Pre-aggregating before joins shrinks cardinality."),
        ("15. Expensive SQL", "Queries consuming excessive CPU, RAM, or execution time.", "5-table OLTP joins (Q10) or redundant views."),
        ("16. Memory and CPU", "In-memory RAM and parallel vCPU usage on HANA Cloud.", "Free tier provides 30 GB RAM and 2 vCPUs."),
        ("17. Data Locality", "Keeping data close to CPU cache to minimize movement.", "Pre-filtering via CTEs before joining."),
        ("18. Query Caching", "Reusing compiled plans (Plan Cache) and hot memory pages.", "Reason we run 1 warm-up + 5 timed trials.")
    ]
    add_styled_table(doc, pd.DataFrame(concepts, columns=["Concept", "Simple Definition", "KEYA MART Application"]))
    trad_vs_hana = pd.DataFrame([
        ("Table Scans", "Full scans are slow; add B-tree indexes.", "Column scans are fast and vectorized."),
        ("Indexes", "Heavy reliance on composite indexes.", "Dictionary compression acts as built-in index."),
        ("Column Selection", "SELECT * mostly affects network I/O.", "SELECT * breaks column pruning and wastes RAM."),
        ("Views", "Views often materialize row-by-row.", "Unneeded joins inside views still add CPU/RAM cost.")
    ], columns=["Area", "Traditional Row-Store", "SAP HANA Column-Store"])
    add_styled_table(doc, trad_vs_hana)

    # 12. Benchmarking Methodology
    doc.add_heading("7. Benchmarking Methodology", level=1)
    doc.add_paragraph(
        "Each query was executed with 1 unrecorded warm-up run (to populate the SQL plan cache and column memory) "
        "followed by 5 timed trials. Client-side wall-clock time (Python time.perf_counter()) and server-side "
        "metrics (SYS.M_SQL_PLAN_CACHE) were recorded. Median execution time was used as the primary metric to "
        "reduce the impact of network outliers, alongside average, min, max, and standard deviation."
    )

    # 13 & 14. Query Selection & Baseline SQL
    doc.add_heading("8. Query Selection & Baseline SQL Queries", level=1)
    add_styled_table(doc, df_base[["Query_ID", "Description", "Rows_Returned"]])
    base_sql = (SQL_DIR / "01_baseline_queries.sql").read_text(encoding="utf-8")
    add_code_block(doc, "Baseline SQL Queries (01_baseline_queries.sql)", base_sql)

    # 15. Initial Benchmark Results
    doc.add_heading("9. Initial Benchmark Results", level=1)
    add_styled_table(
        doc,
        df_base[["Query_ID", "Rows_Returned", "Client_Median_ms", "Client_Avg_ms", "Client_Min_ms", "Client_Max_ms", "Server_Avg_ms"]],
    )

    # 16 & 17. Execution Plan Analysis & Bottlenecks
    doc.add_heading("10. Query Execution Plan Analysis & Bottlenecks", level=1)
    doc.add_paragraph(
        "EXPLAIN PLAN analysis across Q01–Q10 showed that queries referencing VW_KEYA_MART_SALES_CUBE (Q02, Q03, Q06) "
        "triggered unnecessary 4-dimension star joins even when only 1 dimension was needed. High-cardinality "
        "COUNT(DISTINCT order_id) on NVARCHAR(36) and multi-table OLTP joins (Q10) also increased operator cost."
    )
    add_styled_table(doc, df_exp.head(30)[["Query_ID", "Op_ID", "Operator", "Table", "Est_Rows", "Subtree_Cost"]])

    # 18 & 19. Optimization Strategies & Optimized SQL
    doc.add_heading("11. Optimization Strategies & Optimized SQL", level=1)
    doc.add_paragraph(
        "Applied optimizations: (1) Bypassing multi-join views in Q02, Q03, and Q06 to join FACT_SALES directly to "
        "only the required dimension; (2) Pre-aggregating FACT_SALES by surrogate key before dimension joins in Q04; "
        "(3) Early filtering and column pruning via CTEs in Q08, Q09, and Q10."
    )
    opt_sql = (SQL_DIR / "02_optimized_queries.sql").read_text(encoding="utf-8")
    add_code_block(doc, "Optimized SQL Queries (02_optimized_queries.sql)", opt_sql)

    # 20 & 21. Indexing & Partitioning Analysis
    doc.add_heading("12. Indexing & Partitioning Analysis", level=1)
    doc.add_paragraph(
        "Existing indexes were inspected from SYS.INDEXES (shown below). Because FACT_SALES contains 112,650 rows "
        "in an in-memory column store (~few MBs), adding secondary indexes or horizontal partitioning is not "
        "technically justified and would increase memory footprint and write overhead without measurable scan gains."
    )
    add_styled_table(doc, df_idx)

    # 22, 23, 24. Post-Optimization & Comparison
    doc.add_heading("13. Post-Optimization Benchmark & Before-vs-After Comparison", level=1)
    doc.add_paragraph("Formulae: Improvement (%) = ((Baseline - Optimized) / Baseline) x 100 | Speedup = Baseline / Optimized")
    df_comp_disp = df_comp.copy()
    for c in ["Client_Median_ms_Base", "Client_Median_ms_Opt", "Improvement_Pct", "Speedup_X"]:
        df_comp_disp[c] = df_comp_disp[c].round(2)
    add_styled_table(
        doc,
        df_comp_disp[["Query_ID", "Description", "Client_Median_ms_Base", "Client_Median_ms_Opt", "Improvement_Pct", "Speedup_X"]],
    )
    doc.add_paragraph("Result Equivalence Verification (Baseline vs. Optimized):")
    add_styled_table(doc, df_eq)

    # 25. Charts & Screenshots
    doc.add_heading("14. Charts and Visualizations", level=1)
    for img_path in sorted(OUT_DIR.glob("chart*.png")):
        doc.add_picture(str(img_path), width=Inches(6.2))
        cap = doc.add_paragraph(f"Figure: {img_path.stem.replace('_', ' ').title()}")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    if SCR_DIR.exists():
        imgs = sorted([p for p in SCR_DIR.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")])
        if imgs:
            doc.add_heading("Execution Plan & Tool Screenshots", level=2)
            for s_path in imgs:
                doc.add_picture(str(s_path), width=Inches(6.2))
                cap = doc.add_paragraph(f"Screenshot: {s_path.name}")
                cap.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # 26. Challenges & Solutions
    doc.add_heading("15. Challenges and Solutions", level=1)
    if not df_chal.empty:
        add_styled_table(doc, df_chal)

    # 27, 28, 29. Observations, Conclusion, Future Enhancements
    doc.add_heading("16. Technical Observations, Conclusion & Future Enhancements", level=1)
    doc.add_paragraph(
        "Observations: Column-store pruning and direct star joins consistently outperformed nested 4-table views. "
        "Future enhancements include materialized aggregate tables or HANA Calculation Views with explicit pruning "
        "as order volume scales beyond millions of rows."
    )

    # 30-33. References & Appendices
    doc.add_heading("17. References & Appendices", level=1)
    doc.add_paragraph("References: SAP HANA Cloud SQL Reference; SAP HANA Performance Analysis Guide; Olist Brazilian E-Commerce Dataset (Kaggle).")
    doc.add_paragraph("Appendix Scripts: 01_env_assessment.py, 02_run_benchmarks.py, 05_explain_plans.py, 06_verify_equivalence.py, 03_generate_charts.py, 07_build_week3_report.py.")

    doc.save(REPORT_PATH)
    size_kb = REPORT_PATH.stat().st_size / 1024.0
    print(f"Report saved to: {REPORT_PATH}")
    print(f"File size: {size_kb:.1f} KB (Portal limit: 2,048 KB)")


if __name__ == "__main__":
    main()