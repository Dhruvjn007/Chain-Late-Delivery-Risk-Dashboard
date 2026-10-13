# Tableau Dashboard — Build Guide

Data source: `tableau/tableau_order_lines.csv` (written by `python src/run_pipeline.py`).
One row per order line, 180,519 rows, 33 columns. Built in Tableau Public (free).

The workbook has 3 dashboards:

| Dashboard | Question it answers |
| --- | --- |
| 1. Overview | How bad is lateness, where is it, is it getting worse? |
| 2. Driver Explorer | Which dimension actually drives lateness? |
| 3. Profit & What-if | What does lateness cost, and what would a new promise fix? |

---

## 1. Connect

1. Tableau Public → Connect → Text file → `tableau_order_lines.csv`.
2. Check the data types: `Order Date` and `Ship Date` = Date & Time. `Order Id` and `Order Item Id` = String
   (they are IDs, so they should never be summed). `Is Canceled`, `Late Delivery Risk`, `Is Loss Line`,
   `In Trend Window` = Number (whole).
3. Rename the data source to `DataCo Order Lines`.
4. Geographic role: `Order Country` → Country/Region.

## 2. Calculated fields

Create these in a folder named `Late Delivery KPIs`. Formulas are exact Tableau syntax.

### Row-level flags

```
// Shipped Line  (1 = the line actually shipped)
IF [Is Canceled] = 0 THEN 1 ELSE 0 END
```

```
// Late Line  (canceled lines are never late; they never shipped)
IF [Is Canceled] = 0 AND [Late Delivery Risk] = 1 THEN 1 ELSE 0 END
```

```
// Loss Amount  (positive $ lost on a money-losing line)
IF [Profit] < 0 THEN -[Profit] ELSE 0 END
```

### Aggregate KPIs

```
// Late Rate
SUM([Late Line]) / SUM([Shipped Line])
```

```
// Orders
COUNTD([Order Id])
```

```
// Late Orders
COUNTD(IF [Late Line] = 1 THEN [Order Id] END)
```

```
// Avg Delay When Late (days)
AVG(IF [Late Line] = 1 THEN [Delay Days] END)
```

```
// Profit Margin
SUM([Profit]) / SUM([Net Sales])
```

```
// Loss Line Share
SUM([Is Loss Line]) / COUNT([Order Item Id])
```

```
// Profit on Late Lines
SUM(IF [Late Line] = 1 THEN [Profit] END)
```

### Level-of-detail (LOD) benchmark

```
// Overall Late Rate  (company average, ignores the view's dimensions)
{ FIXED : SUM([Late Line]) / SUM([Shipped Line]) }
```

```
// Late Rate vs Avg (pts)
([Late Rate] - MIN([Overall Late Rate])) * 100
```

`FIXED` is computed before dimension filters. So when a user filters to one market, the benchmark stays
the global average. To make the benchmark follow a filter, right-click that filter → **Add to Context**.

```
// Risk Tier
IF [Late Rate] >= 0.75 THEN "High"
ELSEIF [Late Rate] >= 0.50 THEN "Medium"
ELSE "Low" END
```

## 3. Parameters

| Parameter | Type | Values | Default | Used by |
| --- | --- | --- | --- | --- |
| `Break Down By` | String, list | Order Region, Market, Department, Category, Customer Segment, Payment Type | Order Region | Driver Explorer |
| `Min Shipped Lines` | Integer, range 0–5000, step 100 | | 300 | hides tiny groups whose rates are noise |
| `First Class Promise (days)` | Integer, range 1–4 | | 1 | What-if |
| `Second Class Promise (days)` | Integer, range 2–6 | | 2 | What-if |
| `Extra Buffer (days)` | Integer, range 0–3 | | 0 | What-if, added to every mode |

Right-click each parameter → **Show Parameter**.

Parameter-driven calculated fields:

```
// Selected Dimension
CASE [Break Down By]
  WHEN "Order Region"     THEN [Order Region]
  WHEN "Market"           THEN [Market]
  WHEN "Department"       THEN [Department]
  WHEN "Category"         THEN [Category]
  WHEN "Customer Segment" THEN [Customer Segment]
  WHEN "Payment Type"     THEN [Payment Type]
END
```

```
// Simulated Promise (days)
CASE [Shipping Mode]
  WHEN "First Class"  THEN [First Class Promise (days)]
  WHEN "Second Class" THEN [Second Class Promise (days)]
  ELSE [Days Scheduled]
END + [Extra Buffer (days)]
```

```
// Simulated Late Line
IF [Is Canceled] = 0 AND [Days Real] > [Simulated Promise (days)] THEN 1 ELSE 0 END
```

```
// Simulated Late Rate
SUM([Simulated Late Line]) / SUM([Shipped Line])
```

```
// Late Rate Reduction (pts)
([Late Rate] - [Simulated Late Rate]) * 100
```

```
// Passes Min Volume  (use as a filter = True)
SUM([Shipped Line]) >= [Min Shipped Lines]
```

## 4. Worksheets

Number format for all rates: Percentage, 1 decimal. Colour: grey for everything, one blue for the
item the sheet is about. Use red/amber/grey only on `Risk Tier`.

| # | Sheet | Build |
| --- | --- | --- |
| S1 | `KPI - Late Rate` | Text mark. `Late Rate` on Text. Repeat for `Orders`, `Late Orders`, `Avg Delay When Late`, `SUM(Net Sales)`, `SUM(Profit)`, `Profit Margin`, `SUM(Loss Amount)`: one sheet each (S1a–S1h), large font, label underneath |
| S2 | `Late Rate by Shipping Mode` | Rows: `Shipping Mode` (sorted by `Late Rate` desc). Columns: `Late Rate`. Colour: `Risk Tier`. Label: `Late Rate`. Reference line: `MIN(Overall Late Rate)`, dashed, label "Company avg" |
| S3 | `Promised vs Actual Days` | Rows: `Shipping Mode`. Columns: `Days Real` (dimension, discrete). Mark: Square. Colour: `SUM(Shipped Line)` with Quick Table Calc → Percent of Total, compute using `Days Real` (each row sums to 100%). Label the same. Add `Days Scheduled` (as MIN) to Detail and draw a reference line per cell. The visual shows First Class 100% in the "2" column while it promises 1 |
| S4 | `Late Rate Map` | Double-click `Order Country`. Mark: Map. Colour: `Late Rate` (sequential blue, centred on 57%). Tooltip: country, `Late Rate`, `Orders`, `Late Rate vs Avg (pts)` |
| S5 | `Monthly Late Rate` | Filter `In Trend Window` = 1. Columns: `MONTH(Order Date)` continuous. Rows: `Late Rate`. Line. Reference line: `Overall Late Rate`. A second sheet, `Monthly Orders`, with `Orders` as bars. **No dual axis** |
| S6 | `Driver Breakdown` | Rows: `Selected Dimension` sorted by `Late Rate`. Columns: `Late Rate`. Filter: `Passes Min Volume` = True. Colour: `Late Rate vs Avg (pts)` diverging grey-to-blue around 0. Reference line: `Overall Late Rate`. Title: `Late rate by <Break Down By>` (insert the parameter into the title) |
| S7 | `Mode x Market Heatmap` | Rows: `Shipping Mode`. Columns: `Market`. Mark: Square. Colour + label: `Late Rate`. The point: the columns look identical, so geography does not change the mode effect |
| S8 | `Driver Strength` | Connect `outputs/tables/09_driver_strength.csv` as a second source. Bar: `driver` by `cramers_v`; colour by `significant_at_5pct` |
| S9 | `Profit by Delivery Outcome` | Rows: `Delivery Outcome`. Columns: `Profit Margin`. Tooltip: `Profit on Late Lines`, `Loss Line Share` |
| S10 | `Loss by Department` | Rows: `Department`. Columns: `SUM(Loss Amount)`. Label: `Loss Line Share`. Shows that losses follow volume (~18.7% of lines everywhere) |
| S11 | `What-if: Current vs Simulated` | Rows: `Shipping Mode`. Columns: `Measure Values` filtered to `Late Rate` and `Simulated Late Rate`, side by side (`Measure Names` on Colour: grey = current, blue = simulated) |
| S12 | `What-if KPI` | Text: "Late rate falls from `<Late Rate>` to `<Simulated Late Rate>` (`<Late Rate Reduction (pts)>` pts)" |

## 5. Dashboards

Size: Fixed 1366 × 900 (Tableau Public default desktop). Light background, one title row, filters in
one row at the top.

### Dashboard 1 — Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│ Title: 57% of shipped orders arrive late — and it's the promise      │
│ Filters: Market | Shipping Mode | Order Year | Customer Segment      │
├────────┬────────┬────────┬────────┬────────┬────────┬────────┬───────┤
│ S1a..S1h KPI tiles                                                   │
├──────────────────────────────┬───────────────────────────────────────┤
│ S2 Late Rate by Shipping Mode│ S4 Late Rate Map                      │
├──────────────────────────────┼───────────────────────────────────────┤
│ S3 Promised vs Actual Days   │ S5 Monthly Late Rate                  │
└──────────────────────────────┴───────────────────────────────────────┘
```

### Dashboard 2 — Driver Explorer

```
┌──────────────────────────────────────────────────────────────────────┐
│ Title: Shipping mode drives lateness; geography and product don't   │
│ Parameters: Break Down By | Min Shipped Lines   Filters: same 4      │
├──────────────────────────────────────┬───────────────────────────────┤
│ S6 Driver Breakdown (swappable)      │ S8 Driver Strength            │
├──────────────────────────────────────┴───────────────────────────────┤
│ S7 Mode x Market Heatmap                                             │
└──────────────────────────────────────────────────────────────────────┘
```

### Dashboard 3 — Profit & What-if

```
┌──────────────────────────────────────────────────────────────────────┐
│ Title: Losses come from pricing, not lateness; honest promises fix   │
│        lateness                                                      │
├──────────────────────────────┬───────────────────────────────────────┤
│ S9 Profit by Delivery Outcome│ S10 Loss by Department                │
├──────────────────────────────┴───────────────────────────────────────┤
│ Parameters: First Class Promise | Second Class Promise | Buffer      │
│ S12 What-if KPI                                                      │
│ S11 What-if: Current vs Simulated                                    │
└──────────────────────────────────────────────────────────────────────┘
```

## 6. Interactivity

| Feature | How to set it up | Why |
| --- | --- | --- |
| Global filters | On each filter: Apply to Worksheets → All Using This Data Source | One click filters every chart on every dashboard |
| Cross-filter: mode | Dashboard → Actions → Add Filter. Source: S2. Targets: all sheets. Run on: Select. Clearing: Show all values | Click "First Class" and the map, trend and KPIs show only First Class |
| Cross-filter: map | Filter action, Source: S4 (Order Country) → S2, S3, S5, KPIs | Click a country to see its mode mix and trend |
| Highlight: department | Highlight action, Source: S10, Run on: Hover | Hovering a department lights it up everywhere |
| Parameter action | Dashboard 2: Actions → Change Parameter, Source: S8, Target: `Break Down By`, Field: `driver` (map driver names to the list values) | Clicking a driver in the strength chart redraws the breakdown |
| Navigation | Objects → Navigation button on each dashboard | Moves between the 3 dashboards |
| Tooltips | Each tooltip: the dimension, `Late Rate`, `Orders`, `Late Rate vs Avg (pts)` in one sentence | Reads as a fact, not a dump of fields |

## 7. Publish

File → Save to Tableau Public. Name: `Supply Chain Late-Delivery Risk`. Copy the public URL into the
README's "Live dashboard" line. Take a 1600-px screenshot of each dashboard into `tableau/screenshots/`.

## 8. Numbers to check after building (they must match the Python output)

| Check | Expected |
| --- | --- |
| Late Rate, no filters | 57.3% |
| First Class Late Rate | 100.0% |
| Second Class Late Rate | 79.8% |
| Orders | 65,752 |
| SUM(Profit) | $3,966,903 |
| SUM(Loss Amount) | $3,883,547 |
| Simulated Late Rate with First = 2, Second = 4, Buffer = 0 | 34.1% |
| Simulated Late Rate with First = 1, Second = 2, Buffer = 1 | 23.7% |

If the late rate shows 54.8%, `Late Line` is counting canceled lines as not late. Check the formula.
