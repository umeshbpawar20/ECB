# Power BI Data Model & Measures — Complete Setup (A→Z)

Assumes the cleaning script has already produced: `Fact_Inventory.csv`,
`Dim_Store.csv`, `Dim_Product.csv`, `Dim_Date.csv`,
`Category_Mapping_Template.csv` (or a completed mapping already joined in).

## 1. Get Data

- Get Data → Text/CSV, once per file (or Get Data → Folder if you keep them
  all in one output directory).
- In Power Query, before loading, explicitly set types:
  - `Store_Code`, `Product_Code`, `Pincode` → **Text** (never Whole Number —
    leading zeros will silently vanish)
  - `Stock_Qty`, `Stock_Cost_Value`, `Stock_MRP_Value`, `Unit_Cost` → **Decimal
    Number**
  - `Date` (Dim_Date) → **Date**
- Load all five as separate tables.

## 2. Model view — relationships

| From | To | Cardinality | Direction |
|---|---|---|---|
| Fact_Inventory[Store_Code] | Dim_Store[Store_Code] | Many-to-One | Single |
| Fact_Inventory[Product_Code] | Dim_Product[Product_Code] | Many-to-One | Single |
| Fact_Inventory[Date] | Dim_Date[Date] | Many-to-One | Single |

- Select Dim_Date → Table tools → **Mark as Date Table** → column `Date`.
- Dim_Date[Month_Name] → Column tools → **Sort by Column** → `Month_Sort`.
- In Fact_Inventory, hide `Store_Code`, `Product_Code`, `Date` from report view
  (right-click → Hide in report view) — keep the field list to measures and
  drillable dimension fields only.
- Hierarchies:
  - Dim_Store: `State → City → Store_Name`
  - Dim_Product: `Clean_Therapy_Area → Product_Name`

## 3. Measures

Create a blank query / disconnected table called `_Measures` to hold all of
these (Home → Enter Data, no rows needed). Organize with Display Folders as
noted.

### 01 Core
```dax
Total Stock Value (Cost) = SUM(Fact_Inventory[Stock_Cost_Value])

Total Stock Value (MRP) = SUM(Fact_Inventory[Stock_MRP_Value])

Total Stock Value (Cost, Cr) = DIVIDE([Total Stock Value (Cost)], 10000000)

Total Stock Qty = SUM(Fact_Inventory[Stock_Qty])

Distinct SKUs = DISTINCTCOUNT(Fact_Inventory[Product_Code])

Distinct Stores = DISTINCTCOUNT(Fact_Inventory[Store_Code])

Avg Stock Value per Store = DIVIDE([Total Stock Value (Cost)], [Distinct Stores])
```
Format `Total Stock Value (Cost, Cr)` as `#,##0.00 "Cr"` — cleaner than fighting
DAX's comma-scaling for Indian crore display.

### 02 Movement / MoM
```dax
Prior Month Value =
CALCULATE([Total Stock Value (Cost)], DATEADD(Dim_Date[Date], -1, MONTH))

MoM Δ Value = [Total Stock Value (Cost)] - [Prior Month Value]

MoM Δ % = DIVIDE([MoM Δ Value], [Prior Month Value])

Prior Month Qty =
CALCULATE([Total Stock Qty], DATEADD(Dim_Date[Date], -1, MONTH))

Dead Stock Flag =
IF(
    [Total Stock Qty] = [Prior Month Qty] && NOT ISBLANK([Prior Month Value]),
    "Dead",
    "Moving"
)
```

### 03 Ranking / ABC
```dax
Rank by Value =
RANKX(ALLSELECTED(Dim_Product[Product_Name]), [Total Stock Value (Cost)], , DESC)

Cumulative Value % =
VAR CurrentRank = [Rank by Value]
VAR TotalAll = CALCULATE([Total Stock Value (Cost)], ALLSELECTED(Dim_Product))
RETURN
DIVIDE(
    CALCULATE(
        [Total Stock Value (Cost)],
        FILTER(ALLSELECTED(Dim_Product), [Rank by Value] <= CurrentRank)
    ),
    TotalAll
)

ABC Class =
SWITCH(
    TRUE(),
    [Cumulative Value %] <= 0.8, "A",
    [Cumulative Value %] <= 0.95, "B",
    "C"
)
```
Note: this is the standard running-total Pareto pattern — fine for a Top-N
table visual sorted by Rank. Ties in Rank can shift the cumulative % slightly;
don't over-index on it for edge-case SKUs.

### 04 Shares
```dax
Value % of Total =
DIVIDE(
    [Total Stock Value (Cost)],
    CALCULATE([Total Stock Value (Cost)], ALLSELECTED(Dim_Store), ALLSELECTED(Dim_Product))
)
```

### 05 Data Quality
```dax
Rows with Null Pincode =
CALCULATE(COUNTROWS(Fact_Inventory), ISBLANK(RELATED(Dim_Store[Pincode])))

Rows Unmapped Category =
CALCULATE(COUNTROWS(Fact_Inventory), ISBLANK(RELATED(Dim_Product[Clean_Therapy_Area])))

Quarantined Value (Cost) =
IF(
    ISFILTERED('Quarantined_Negative_Qty'),
    SUM('Quarantined_Negative_Qty'[Stock_Cost_Value])
)
```
Load `quarantined_negative_qty.csv` as its own table (unrelated to the model)
just to surface this last measure and a row count card.

## 4. Report pages — build in this order

1. **Executive Summary** — cards: `Total Stock Value (Cost, Cr)`,
   `Total Stock Qty`, `Distinct SKUs`, `Distinct Stores`; bar chart
   Account_Name × `Total Stock Value (Cost)`; filled map by State ×
   `Total Stock Value (Cost)`; line/waterfall of `MoM Δ Value` by month.
2. **Chain Deep-Dive** — matrix: rows `Account_Name` → `Clean_Therapy_Area`,
   values `Total Stock Value (Cost)`, `Value % of Total`; Top 20 table:
   `Product_Name`, `Total Stock Value (Cost)`, `Rank by Value`, `ABC Class`,
   conditional formatting (data bars) on value; treemap: `Store_Name` sized by
   value, split by chain.
3. **Movement (May→June)** — waterfall: `MoM Δ Value` by
   `Clean_Therapy_Area`; table: `Product_Name`, `Store_Name`, `MoM Δ Value`,
   `MoM Δ %`, sorted descending and ascending (two visuals — gainers,
   decliners); table filtered to `Dead Stock Flag = "Dead"`.
4. **Geography** — filled map or bubble map on State/City, `Total Stock Value
   (Cost)`; drill-through target page at Store level.
5. **Data Quality** — cards: `Rows with Null Pincode`, `Rows Unmapped
   Category`, `Quarantined Value (Cost)`, quarantined row count; small table
   listing unmapped raw Category values (from Category_Mapping_Template) still
   missing a `Clean_Therapy_Area`.

Add a slicer panel synced across pages 1–4: `Account_Name`, `State`,
`Clean_Therapy_Area`, `Month_Name` (View → Sync Slicers).

## 5. Validation before publish

- Compare the report's grand total `Total Stock Value (Cost)` against the
  PASS/FAIL reconciliation line the cleaning script prints — they must match.
- Spot-check 2–3 known Store_Code + Product_Code combinations against the raw
  CSV manually.

## 6. Publish & refresh

- Publish to the workspace.
- If this feeds from a recurring monthly drop, parameterize the Power Query
  source folder path and reuse the same "Run After" Power Automate refresh
  trigger you already have wired up for CHTF_INBU, pointed at this dataset
  instead.
