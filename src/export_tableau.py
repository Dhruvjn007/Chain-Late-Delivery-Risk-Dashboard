"""Step 4: write the Tableau-ready extract.

One row per order line, only the columns the dashboard uses, with
Tableau-friendly names. Rates are NOT pre-computed here: Tableau
calculates them so they re-aggregate correctly under any filter.
"""
import pandas as pd

import config

COLUMNS = {
    "order_id": "Order Id",
    "order_item_id": "Order Item Id",
    "order_date": "Order Date",
    "ship_date": "Ship Date",
    "shipping_mode": "Shipping Mode",
    "days_scheduled": "Days Scheduled",
    "days_real": "Days Real",
    "delay_days": "Delay Days",
    "delivery_status": "Delivery Status",
    "delivery_outcome": "Delivery Outcome",
    "delay_bucket": "Delay Bucket",
    "is_canceled": "Is Canceled",
    "late_flag_source": "Late Delivery Risk",
    "market": "Market",
    "order_region": "Order Region",
    "order_country": "Order Country",
    "order_city": "Order City",
    "department": "Department",
    "category": "Category",
    "product": "Product",
    "customer_segment": "Customer Segment",
    "payment_type": "Payment Type",
    "order_status": "Order Status",
    "quantity": "Quantity",
    "unit_price": "Unit Price",
    "discount_rate": "Discount Rate",
    "discount_band": "Discount Band",
    "gross_sales": "Gross Sales",
    "discount": "Discount",
    "net_sales": "Net Sales",
    "profit": "Profit",
    "is_loss": "Is Loss Line",
    "in_trend_window": "In Trend Window",
}


def run(df: pd.DataFrame | None = None) -> None:
    if df is None:
        df = pd.read_csv(config.CLEAN_FILE, parse_dates=["order_date", "ship_date"])
    out = df[list(COLUMNS)].rename(columns=COLUMNS)
    config.TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(config.TABLEAU_FILE, index=False, date_format="%Y-%m-%d %H:%M")
    size_mb = config.TABLEAU_FILE.stat().st_size / 1e6
    print(f"  wrote  {config.TABLEAU_FILE.name}: {len(out):,} rows x {out.shape[1]} cols, {size_mb:.1f} MB")


if __name__ == "__main__":
    run()
