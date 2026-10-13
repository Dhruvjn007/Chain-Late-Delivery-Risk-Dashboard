"""Step 1: load the raw DataCo file, validate it, clean it and add features.

Output: data/processed/order_lines_clean.csv (one row per order line).
"""
import numpy as np
import pandas as pd

import config


def load_raw() -> pd.DataFrame:
    df = pd.read_csv(config.RAW_FILE, encoding=config.RAW_ENCODING)
    # Several headers carry trailing spaces ("Days for shipping (real)     ").
    df.columns = df.columns.str.strip()
    return df


def validate_raw(df: pd.DataFrame) -> dict:
    """Fail loudly if the raw file breaks an assumption the analysis relies on."""
    checks = {}
    checks["rows"] = len(df)
    checks["exact_duplicate_rows"] = int(df.duplicated().sum())
    checks["order_item_id_unique"] = bool(df["Order Item Id"].is_unique)

    for a, b in config.DUPLICATE_PAIRS:
        same = bool((df[a] == df[b]).all())
        checks[f"{a} == {b}"] = same
        assert same, f"{a} is not a duplicate of {b}; do not drop it"

    # The source late flag must equal real > scheduled for shipped orders.
    shipped = df["Delivery Status"] != "Shipping canceled"
    recomputed = (df["Days for shipping (real)"] > df["Days for shipment (scheduled)"]).astype(int)
    checks["late_flag_matches_rule"] = bool((recomputed[shipped] == df.loc[shipped, "Late_delivery_risk"]).all())

    # Days real = calendar-day gap between order date and ship date.
    od = pd.to_datetime(df["order date (DateOrders)"], format="%m/%d/%Y %H:%M")
    sd = pd.to_datetime(df["shipping date (DateOrders)"], format="%m/%d/%Y %H:%M")
    gap = (sd.dt.normalize() - od.dt.normalize()).dt.days
    checks["days_real_matches_dates"] = bool((gap == df["Days for shipping (real)"]).all())

    # Each order ships with one mode, to one region, with one status.
    per_order = df.groupby("Order Id")[["Shipping Mode", "Order Region", "Delivery Status"]].nunique()
    checks["one_mode_region_status_per_order"] = bool((per_order.max() == 1).all())

    # Money identities.
    checks["gross_sales = price x qty"] = bool(
        np.isclose(df["Order Item Product Price"] * df["Order Item Quantity"], df["Sales"], atol=0.01).all()
    )
    checks["net_sales = gross - discount (share)"] = float(
        np.isclose(df["Sales"] - df["Order Item Discount"], df["Order Item Total"], atol=0.01).mean()
    )
    return checks


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop(columns=list(config.DROP_COLUMNS)).rename(columns=config.RENAME)

    # Text tidy-up: collapse double spaces and trim ("South of  USA " -> "South of USA").
    for col in df.select_dtypes("object"):
        df[col] = df[col].str.replace(r"\s+", " ", regex=True).str.strip()

    df["order_date"] = pd.to_datetime(df["order_date"], format="%m/%d/%Y %H:%M")
    df["ship_date"] = pd.to_datetime(df["ship_date"], format="%m/%d/%Y %H:%M")

    df["store_country"] = df["store_country"].replace(config.STORE_COUNTRY_FIX)
    df["order_country"] = df["order_country_es"].map(config.COUNTRY_ES_TO_EN)
    missing = df.loc[df["order_country"].isna(), "order_country_es"].unique()
    assert len(missing) == 0, f"Untranslated countries: {missing}"
    df = df.drop(columns="order_country_es")

    df["store_zipcode"] = df["store_zipcode"].astype("Int64")
    return df


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    # Canceled lines never shipped, so they carry late flag 0 by default.
    # Counting them as "on time" would understate the late rate.
    df["is_canceled"] = (df["delivery_status"] == "Shipping canceled").astype(int)
    df["is_late"] = np.where(df["is_canceled"] == 1, np.nan, df["late_flag_source"]).astype("float")

    df["delay_days"] = df["days_real"] - df["days_scheduled"]  # >0 late, 0 on time, <0 early
    df["delivery_outcome"] = np.select(
        [df["is_canceled"] == 1, df["delay_days"] > 0, df["delay_days"] == 0],
        ["Canceled", "Late", "On time"],
        default="Early",
    )
    df["delay_bucket"] = np.select(
        [df["is_canceled"] == 1, df["delay_days"] <= 0, df["delay_days"] == 1, df["delay_days"] == 2],
        ["Canceled", "Not late", "1 day late", "2 days late"],
        default="3-4 days late",
    )

    df["is_loss"] = (df["profit"] < 0).astype(int)
    df["late_profit"] = np.where(df["is_late"] == 1, df["profit"], 0.0)
    df["loss_amount"] = np.where(df["profit"] < 0, -df["profit"], 0.0)

    df["order_month"] = df["order_date"].dt.to_period("M").dt.to_timestamp()
    df["order_year"] = df["order_date"].dt.year
    df["order_weekday"] = df["order_date"].dt.day_name()
    df["in_trend_window"] = (df["order_date"] < config.TREND_CUTOFF).astype(int)

    df["discount_band"] = pd.cut(
        df["discount_rate"], [-0.001, 0.05, 0.10, 0.15, 0.25], labels=["0-5%", "5-10%", "10-15%", "15-25%"]
    ).astype(str)
    return df


def run() -> pd.DataFrame:
    raw = load_raw()
    checks = validate_raw(raw)
    pd.Series(checks, name="result").to_csv(config.TABLES_DIR / "00_data_quality_checks.csv")
    for k, v in checks.items():
        print(f"  check  {k}: {v}")

    df = add_features(clean(raw))
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(config.CLEAN_FILE, index=False)
    print(f"  wrote  {config.CLEAN_FILE.name}: {len(df):,} rows x {df.shape[1]} cols")
    return df


if __name__ == "__main__":
    run()
