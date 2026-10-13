"""Step 3: static PNG charts for the README (the interactive version is Tableau).

Style: grey for context, one blue accent on what the title is about.
"""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

import config

ACCENT = "#2a78d6"
GREY = "#b4b2a9"
INK = "#0b0b0b"
QUIET = "#52514e"
GRID = "#e6e5e0"

plt.rcParams.update({
    "font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": GRID, "axes.labelcolor": QUIET, "xtick.color": QUIET, "ytick.color": QUIET,
    "axes.titleweight": "bold", "axes.titlesize": 12, "axes.titlelocation": "left",
    "figure.facecolor": "#fcfcfb", "axes.facecolor": "#fcfcfb", "savefig.dpi": 150,
})


def table(name: str) -> pd.DataFrame:
    return pd.read_csv(config.TABLES_DIR / f"{name}.csv", index_col=0)


def finish(fig, name: str) -> None:
    fig.tight_layout()
    fig.savefig(config.CHARTS_DIR / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"  chart  {name}.png")


def hbar_late_rate(t: pd.DataFrame, title: str, name: str, highlight: set, overall: float, height=4.0) -> None:
    t = t.sort_values("late_rate")
    fig, ax = plt.subplots(figsize=(8, height))
    colors = [ACCENT if i in highlight else GREY for i in t.index]
    ax.barh(t.index, t["late_rate"] * 100, color=colors, height=0.65)
    for y, v in enumerate(t["late_rate"] * 100):
        ax.text(v + 0.8, y, f"{v:.1f}%", va="center", fontsize=9, color=INK)
    ax.axvline(overall * 100, color=QUIET, ls="--", lw=1)
    ax.text(overall * 100, len(t) - 0.4, f" avg {overall:.1%}", color=QUIET, fontsize=9, va="bottom")
    ax.set_xlim(0, 110)
    ax.set_xlabel("Late-delivery rate, shipped lines (%)")
    ax.set_title(title)
    ax.grid(axis="x", color=GRID)
    ax.set_axisbelow(True)
    finish(fig, name)


def run() -> None:
    config.CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    kpi = pd.read_csv(config.TABLES_DIR / "01_kpi_summary.csv").set_index("metric")["value"]
    overall = float(kpi["late_rate_shipped"])

    mode = table("02_by_shipping_mode")
    hbar_late_rate(mode, "First Class is late on 100% of shipments; Second Class on 80%",
                   "01_late_rate_by_shipping_mode", {"First Class", "Second Class"}, overall, 3.0)

    # Scheduled vs real days per mode: the root cause in one picture.
    dist = table("03_mode_real_days_distribution")
    fig, ax = plt.subplots(figsize=(8, 3.6))
    day_cols = [c for c in dist.columns if c.startswith("real_")]
    for y, m in enumerate(config.SHIPPING_MODE_ORDER):
        sched = dist.loc[m, "days_scheduled"]
        for c in day_cols:
            d = int(c.split("_")[1])
            share = dist.loc[m, c]
            if share > 0:
                ax.scatter(d, y, s=share * 1400, color=ACCENT if d > sched else GREY, alpha=0.85, zorder=3)
        ax.plot([sched, sched], [y - 0.35, y + 0.35], color=INK, lw=2.5, zorder=4)
    ax.set_yticks(range(4), config.SHIPPING_MODE_ORDER)
    ax.set_xticks(range(7))
    ax.set_xlabel("Days from order to shipment (bubble size = share of lines; black tick = promised days)")
    ax.set_title("Promises are tighter than real lead times: blue = shipped after the promise")
    ax.set_ylim(-0.6, 3.6)
    ax.grid(axis="x", color=GRID)
    finish(fig, "02_scheduled_vs_real_days")

    strength = table("09_driver_strength").sort_values("cramers_v")
    fig, ax = plt.subplots(figsize=(8, 3.8))
    colors = [ACCENT if d == "shipping_mode" else GREY for d in strength.index]
    ax.barh(strength.index, strength["cramers_v"], color=colors, height=0.65)
    for y, (v, sig) in enumerate(zip(strength["cramers_v"], strength["significant_at_5pct"])):
        ax.text(v + 0.006, y, f"{v:.3f}{'' if sig else '  (not significant)'}", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, 0.6)
    ax.set_xlabel("Cramer's V with late flag (0 = no association, 1 = perfect)")
    ax.set_title("Shipping mode explains lateness; region, market and department barely matter")
    ax.grid(axis="x", color=GRID)
    ax.set_axisbelow(True)
    finish(fig, "03_driver_strength")

    region = table("05_by_region")
    hbar_late_rate(region, f"Every region sits within 6 points of the {overall:.1%} average",
                   "04_late_rate_by_region", set(region.head(3).index), overall, 6.0)

    dept = table("06_by_department")
    hbar_late_rate(dept, "Departments: no department is meaningfully worse",
                   "05_late_rate_by_department", set(), overall, 4.2)

    whatif = table("17_sla_whatif")
    labels = ["Current promise", "+1 day all modes", "+2 days", "+3 days", "Re-promise First=2d,\nSecond=4d"]
    fig, ax = plt.subplots(figsize=(8, 3.4))
    vals = whatif["overall_late_rate"].values * 100
    colors = [GREY, GREY, GREY, GREY, ACCENT]
    ax.bar(labels, vals, color=colors, width=0.6)
    for x, v in enumerate(vals):
        ax.text(x, v + 1.5, f"{v:.1f}%", ha="center", fontsize=9, color=INK)
    ax.set_ylim(0, 70)
    ax.set_ylabel("Late rate, shipped lines (%)")
    ax.set_title(f"Honest promises for First and Second Class cut the late rate from {vals[0]:.0f}% to {vals[-1]:.0f}%")
    finish(fig, "06_sla_whatif")

    trend = table("12_monthly_trend")
    trend.index = pd.to_datetime(trend.index)
    fig, ax = plt.subplots(figsize=(8, 3.2))
    full = trend[trend["in_trend_window"] == 1]
    ax.plot(full.index, full["late_rate"] * 100, color=ACCENT, lw=2)
    ax.axhline(overall * 100, color=QUIET, ls="--", lw=1)
    ax.set_ylim(45, 65)
    ax.set_ylabel("Late rate (%)")
    lo, hi = full["late_rate"].min() * 100, full["late_rate"].max() * 100
    ax.set_title(f"Late rate stays between {lo:.0f}% and {hi:.0f}% every month: structural, not seasonal")
    ax.grid(axis="y", color=GRID)
    finish(fig, "07_monthly_late_rate")


if __name__ == "__main__":
    run()
