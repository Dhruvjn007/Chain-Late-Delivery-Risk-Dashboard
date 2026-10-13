"""Step 2: answer the business questions and write one CSV per result.

Q1  How big is the late-delivery problem?
Q2  Which shipping modes, markets, regions, departments drive it?
Q3  How strong is each driver (statistically)?
Q4  Does lateness cost profit, and where is profit being lost?
Q5  What would fixing the shipping-mode promise do (what-if)?
"""
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, ttest_ind
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

import config


def save(df: pd.DataFrame, name: str) -> pd.DataFrame:
    df.to_csv(config.TABLES_DIR / f"{name}.csv", index=isinstance(df.index, pd.MultiIndex) or df.index.name is not None)
    print(f"  table  {name}.csv ({len(df)} rows)")
    return df


def kpis(df: pd.DataFrame) -> pd.DataFrame:
    shipped = df[df["is_canceled"] == 0]
    rows = {
        "order_lines": len(df),
        "orders": df["order_id"].nunique(),
        "customers": df["customer_id"].nunique(),
        "first_order": df["order_date"].min().date(),
        "last_order": df["order_date"].max().date(),
        "canceled_lines": int(df["is_canceled"].sum()),
        "late_rate_shipped": shipped["is_late"].mean(),
        "late_rate_naive_incl_canceled": df["late_flag_source"].mean(),
        "late_orders": shipped.loc[shipped["is_late"] == 1, "order_id"].nunique(),
        "avg_delay_days_when_late": shipped.loc[shipped["is_late"] == 1, "delay_days"].mean(),
        "gross_sales": df["gross_sales"].sum(),
        "net_sales": df["net_sales"].sum(),
        "profit": df["profit"].sum(),
        "profit_margin": df["profit"].sum() / df["net_sales"].sum(),
        "loss_lines_share": df["is_loss"].mean(),
        "loss_amount": df["loss_amount"].sum(),
        "gross_profit_before_losses": df.loc[df["profit"] > 0, "profit"].sum(),
        "profit_on_late_lines": shipped["late_profit"].sum(),
    }
    return pd.DataFrame({"metric": rows.keys(), "value": rows.values()})


def driver_table(df: pd.DataFrame, by: str, min_lines: int = 0) -> pd.DataFrame:
    """Late rate and money for one dimension, shipped lines only for lateness."""
    shipped = df[df["is_canceled"] == 0]
    late = shipped.groupby(by).agg(
        shipped_lines=("is_late", "size"),
        late_lines=("is_late", "sum"),
        late_rate=("is_late", "mean"),
        avg_delay_days=("delay_days", "mean"),
        avg_days_scheduled=("days_scheduled", "mean"),
        avg_days_real=("days_real", "mean"),
        late_profit=("late_profit", "sum"),
    )
    money = df.groupby(by).agg(
        orders=("order_id", "nunique"),
        net_sales=("net_sales", "sum"),
        profit=("profit", "sum"),
        loss_lines_share=("is_loss", "mean"),
        loss_amount=("loss_amount", "sum"),
    )
    out = late.join(money)
    out["margin"] = out["profit"] / out["net_sales"]
    out["share_of_all_late_lines"] = out["late_lines"] / out["late_lines"].sum()
    overall = shipped["is_late"].mean()
    out["late_rate_vs_avg_pts"] = (out["late_rate"] - overall) * 100
    out = out[out["shipped_lines"] >= min_lines]
    return out.sort_values("late_rate", ascending=False).round(4)


def driver_strength(df: pd.DataFrame) -> pd.DataFrame:
    """Chi-square test of independence + Cramer's V for each candidate driver."""
    shipped = df[df["is_canceled"] == 0]
    rows = []
    for col in ["shipping_mode", "order_region", "market", "department", "category",
                "customer_segment", "payment_type", "order_weekday", "discount_band"]:
        ct = pd.crosstab(shipped[col], shipped["is_late"])
        chi2, p, dof, _ = chi2_contingency(ct)
        n = ct.values.sum()
        rates = ct[1.0] / ct.sum(axis=1)
        rows.append({
            "driver": col,
            "levels": ct.shape[0],
            "chi2": round(chi2, 1),
            "p_value": p,
            "cramers_v": round(np.sqrt(chi2 / (n * (min(ct.shape) - 1))), 4),
            "min_late_rate": round(rates.min(), 4),
            "max_late_rate": round(rates.max(), 4),
            "spread_pts": round((rates.max() - rates.min()) * 100, 1),
            "significant_at_5pct": p < 0.05,
        })
    return pd.DataFrame(rows).sort_values("cramers_v", ascending=False)


def model_check(df: pd.DataFrame) -> pd.DataFrame:
    """Logistic regression AUC: how much does each feature set predict lateness?"""
    shipped = df[df["is_canceled"] == 0]
    y = shipped["is_late"].astype(int)
    sets = {
        "shipping_mode only": ["shipping_mode"],
        "region + market + department + segment": ["order_region", "market", "department", "customer_segment"],
        "all of the above": ["shipping_mode", "order_region", "market", "department", "customer_segment"],
    }
    rows = []
    for name, cols in sets.items():
        X = pd.get_dummies(shipped[cols], drop_first=True)
        X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
        model = LogisticRegression(max_iter=1000).fit(X_tr, y_tr)
        rows.append({"features": name, "test_auc": round(roc_auc_score(y_te, model.predict_proba(X_te)[:, 1]), 4)})
    return pd.DataFrame(rows)


def mode_days_distribution(df: pd.DataFrame) -> pd.DataFrame:
    shipped = df[df["is_canceled"] == 0]
    dist = pd.crosstab(shipped["shipping_mode"], shipped["days_real"], normalize="index").round(4)
    dist.columns = [f"real_{c}_days" for c in dist.columns]
    dist.insert(0, "days_scheduled", shipped.groupby("shipping_mode")["days_scheduled"].first())
    return dist.loc[config.SHIPPING_MODE_ORDER]


def mode_by_market(df: pd.DataFrame) -> pd.DataFrame:
    shipped = df[df["is_canceled"] == 0]
    return shipped.pivot_table(index="shipping_mode", columns="market", values="is_late", aggfunc="mean").round(4)


def monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    m = df.groupby("order_month").agg(
        order_lines=("order_item_id", "size"),
        orders=("order_id", "nunique"),
        late_rate=("is_late", "mean"),
        net_sales=("net_sales", "sum"),
        profit=("profit", "sum"),
        categories=("category", "nunique"),
        in_trend_window=("in_trend_window", "max"),
    )
    m["lines_per_order"] = m["order_lines"] / m["orders"]
    return m.round(4)


def profit_vs_lateness(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    by_outcome = df.groupby("delivery_outcome").agg(
        lines=("profit", "size"),
        avg_profit=("profit", "mean"),
        avg_profit_ratio=("profit_ratio", "mean"),
        loss_lines_share=("is_loss", "mean"),
        net_sales=("net_sales", "sum"),
        profit=("profit", "sum"),
    )
    by_outcome["margin"] = by_outcome["profit"] / by_outcome["net_sales"]

    shipped = df[df["is_canceled"] == 0]
    late = shipped.loc[shipped["is_late"] == 1, "profit"]
    not_late = shipped.loc[shipped["is_late"] == 0, "profit"]
    t, p = ttest_ind(late, not_late, equal_var=False)
    test = pd.DataFrame([{
        "avg_profit_late": late.mean(),
        "avg_profit_not_late": not_late.mean(),
        "difference": late.mean() - not_late.mean(),
        "welch_t": t,
        "p_value": p,
        "implied_profit_gap_on_late_lines": (late.mean() - not_late.mean()) * len(late),
    }]).round(4)
    return by_outcome.round(4), test


def loss_concentration(df: pd.DataFrame) -> pd.DataFrame:
    """Which products carry the losses? Top 15 by loss amount."""
    p = df.groupby(["product", "department", "category"]).agg(
        lines=("profit", "size"),
        loss_lines=("is_loss", "sum"),
        loss_amount=("loss_amount", "sum"),
        profit=("profit", "sum"),
        net_sales=("net_sales", "sum"),
    ).reset_index()
    p["loss_share_of_total"] = p["loss_amount"] / p["loss_amount"].sum()
    p["cum_loss_share"] = p.sort_values("loss_amount", ascending=False)["loss_share_of_total"].cumsum()
    return p.sort_values("loss_amount", ascending=False).head(15).round(4)


def loss_by_discount(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("discount_band").agg(
        lines=("profit", "size"), loss_lines_share=("is_loss", "mean"), avg_profit=("profit", "mean")
    ).round(4)


def sla_whatif(df: pd.DataFrame) -> pd.DataFrame:
    """Late rate if each mode's promise were extended by N days (Tableau parameter mirrors this)."""
    shipped = df[df["is_canceled"] == 0]
    rows = []
    for buffer in range(0, 4):
        late = shipped["days_real"] > shipped["days_scheduled"] + buffer
        by_mode = late.groupby(shipped["shipping_mode"]).mean()
        rows.append({"buffer_days": buffer, "overall_late_rate": late.mean(), **{f"late_{m}": by_mode[m] for m in config.SHIPPING_MODE_ORDER}})

    # Targeted fix: re-promise only First and Second Class at their real lead times.
    target = shipped["days_scheduled"].copy()
    target[shipped["shipping_mode"] == "First Class"] = 2
    target[shipped["shipping_mode"] == "Second Class"] = 4
    late = shipped["days_real"] > target
    rows.append({"buffer_days": "targeted: First=2d, Second=4d", "overall_late_rate": late.mean(),
                 **{f"late_{m}": late[shipped["shipping_mode"] == m].mean() for m in config.SHIPPING_MODE_ORDER}})
    return pd.DataFrame(rows).round(4)


def run(df: pd.DataFrame | None = None) -> None:
    if df is None:
        df = pd.read_csv(config.CLEAN_FILE, parse_dates=["order_date", "ship_date", "order_month"])

    save(kpis(df), "01_kpi_summary")
    save(driver_table(df, "shipping_mode"), "02_by_shipping_mode")
    save(mode_days_distribution(df), "03_mode_real_days_distribution")
    save(driver_table(df, "market"), "04_by_market")
    save(driver_table(df, "order_region"), "05_by_region")
    save(driver_table(df, "department"), "06_by_department")
    save(driver_table(df, "category", min_lines=300), "07_by_category_min300")
    save(driver_table(df, "customer_segment"), "08_by_segment")
    save(driver_strength(df), "09_driver_strength")
    save(model_check(df), "10_model_auc_by_feature_set")
    save(mode_by_market(df), "11_late_rate_mode_x_market")
    save(monthly_trend(df), "12_monthly_trend")
    by_outcome, test = profit_vs_lateness(df)
    save(by_outcome, "13_profit_by_delivery_outcome")
    save(test, "14_profit_late_vs_not_ttest")
    save(loss_concentration(df), "15_top_loss_products")
    save(loss_by_discount(df), "16_loss_by_discount_band")
    save(sla_whatif(df), "17_sla_whatif")


if __name__ == "__main__":
    run()
