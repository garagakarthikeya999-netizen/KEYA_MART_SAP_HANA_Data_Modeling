from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "03_Week3_Optimization" / "outputs"

BASE_CSV = OUT_DIR / "baseline_benchmark_summary.csv"
OPT_CSV = OUT_DIR / "optimized_benchmark_summary.csv"

if not BASE_CSV.exists() or not OPT_CSV.exists():
    raise FileNotFoundError(
        "Both baseline_benchmark_summary.csv and optimized_benchmark_summary.csv "
        "must exist in 03_Week3_Optimization/outputs/ before generating charts."
    )

df_base = pd.read_csv(BASE_CSV)
df_opt = pd.read_csv(OPT_CSV)

df = pd.merge(
    df_base[["Query_ID", "Description", "Client_Median_ms", "Server_Avg_ms", "Server_Avg_Mem_MB"]],
    df_opt[["Query_ID", "Client_Median_ms", "Server_Avg_ms", "Server_Avg_Mem_MB"]],
    on="Query_ID",
    suffixes=("_Base", "_Opt"),
)

df["Improvement_Pct"] = (
    (df["Client_Median_ms_Base"] - df["Client_Median_ms_Opt"]) / df["Client_Median_ms_Base"]
) * 100.0
df["Speedup_X"] = df["Client_Median_ms_Base"] / df["Client_Median_ms_Opt"]

df.to_csv(OUT_DIR / "comparison_summary.csv", index=False, encoding="utf-8")

plt.rcParams.update({"font.size": 10, "axes.edgecolor": "#CCCCCC"})

# Chart 1: Baseline vs Optimized Median Execution Time
fig, ax = plt.subplots(figsize=(10, 5))
x = range(len(df))
w = 0.38
ax.bar([i - w / 2 for i in x], df["Client_Median_ms_Base"], width=w, label="Baseline (ms)", color="#D9534F")
ax.bar([i + w / 2 for i in x], df["Client_Median_ms_Opt"], width=w, label="Optimized (ms)", color="#2E86AB")
ax.set_xticks(list(x))
ax.set_xticklabels(df["Query_ID"])
ax.set_ylabel("Median Execution Time (ms)")
ax.set_title("KEYA MART: Baseline vs. Optimized Query Execution Time (Median)")
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(OUT_DIR / "chart1_baseline_vs_optimized_ms.png", dpi=200)
plt.close()

# Chart 2: Percentage Improvement by Query
fig, ax = plt.subplots(figsize=(10, 5))
colors = ["#2E8B57" if v >= 0 else "#D9534F" for v in df["Improvement_Pct"]]
bars = ax.bar(df["Query_ID"], df["Improvement_Pct"], color=colors)
ax.axhline(0, color="#333333", linewidth=0.8)
ax.set_ylabel("Performance Improvement (%)")
ax.set_title("KEYA MART: Percentage Performance Improvement by Query")
for b in bars:
    h = b.get_height()
    ax.text(b.get_x() + b.get_width() / 2, h + (1 if h >= 0 else -3), f"{h:.1f}%", ha="center", fontsize=8)
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(OUT_DIR / "chart2_improvement_pct_by_query.png", dpi=200)
plt.close()

# Chart 3: Speedup Factor (Baseline / Optimized)
fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(df["Query_ID"], df["Speedup_X"], color="#4A6FA5")
ax.axhline(1.0, color="#888888", linestyle="--", linewidth=1, label="1.0x (No Change)")
ax.set_ylabel("Speedup Factor (x)")
ax.set_title("KEYA MART: Query Execution Speedup Factor (Baseline / Optimized)")
for b in bars:
    h = b.get_height()
    ax.text(b.get_x() + b.get_width() / 2, h + 0.03, f"{h:.2f}x", ha="center", fontsize=8)
ax.legend()
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(OUT_DIR / "chart3_speedup_factor.png", dpi=200)
plt.close()

# Chart 4: Overall Average Execution Time & Improvement
avg_base = df["Client_Median_ms_Base"].mean()
avg_opt = df["Client_Median_ms_Opt"].mean()
avg_imp = ((avg_base - avg_opt) / avg_base) * 100.0

fig, ax = plt.subplots(figsize=(6, 4.5))
bars = ax.bar(["Baseline Avg", "Optimized Avg"], [avg_base, avg_opt], color=["#D9534F", "#2E86AB"], width=0.5)
ax.set_ylabel("Average Median Execution Time (ms)")
ax.set_title(f"Overall Average Query Time (Avg Improvement: {avg_imp:.1f}%)")
for b in bars:
    h = b.get_height()
    ax.text(b.get_x() + b.get_width() / 2, h + 1, f"{h:.1f} ms", ha="center", fontweight="bold")
ax.grid(axis="y", linestyle="--", alpha=0.4)
plt.tight_layout()
plt.savefig(OUT_DIR / "chart4_overall_average_comparison.png", dpi=200)
plt.close()

# Chart 5: Optional Server Memory Comparison (only if non-null data exists)
if df["Server_Avg_Mem_MB_Base"].notna().any() and df["Server_Avg_Mem_MB_Opt"].notna().any():
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar([i - w / 2 for i in x], df["Server_Avg_Mem_MB_Base"].fillna(0), width=w, label="Baseline Memory (MB)", color="#E09F3E")
    ax.bar([i + w / 2 for i in x], df["Server_Avg_Mem_MB_Opt"].fillna(0), width=w, label="Optimized Memory (MB)", color="#3D5A80")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["Query_ID"])
    ax.set_ylabel("Avg Execution Memory (MB)")
    ax.set_title("KEYA MART: Server Memory Consumption Comparison")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    plt.savefig(OUT_DIR / "chart5_memory_comparison_mb.png", dpi=200)
    plt.close()

print("All charts generated successfully in:", OUT_DIR)