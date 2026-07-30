# Doing the Cleaning in Power Query Instead of Python

## Query structure

Build these as separate queries, in this dependency order. Right-click →
**disable "Enable Load"** on the staging ones (Source, Main_Clean,
Fact_Staging) so they don't clutter the model — only the final tables load.

```
Source                  (raw CSV, staging — no load)
 ├─ Quarantined_Negative_Qty   (loads)
 └─ Main_Clean            (staging — no load)
     ├─ Fact_Staging       (staging — no load)
     │   ├─ Dim_Date       (loads)
     │   └─ Fact_Inventory (loads, merges in Dim_Date)
     ├─ Dim_Store          (loads)
     └─ Category_Counts    (staging → merge with manual mapping → Dim_Product, loads)
```

## 1. Source — load with correct types

Get Data → Text/CSV → in the applied steps, use **Change Type** on:
`Store_Code`, `Product_Code`, `Pincode` → Text (not Whole Number — you'll lose
leading zeros silently otherwise).

## 2. Split out negative quantity — two queries referencing Source

**Main_Clean** (reference Source):
```m
= Table.SelectRows(Source, each [Stock_Qty] >= 0)
```

**Quarantined_Negative_Qty** (reference Source):
```m
= Table.SelectRows(Source, each [Stock_Qty] < 0)
```

## 3. Collapse duplicates — Fact_Staging (reference Main_Clean)

```m
= Table.Group(
    Main_Clean,
    {"Report_Month", "Account_Name", "Store_Code", "Product_Code"},
    {
        {"Stock_Qty", each List.Sum([Stock_Qty]), type number},
        {"Stock_Cost_Value", each List.Sum([Stock_Cost_Value]), type number},
        {"Stock_MRP_Value", each List.Sum([Stock_MRP_Value]), type number}
    }
)
```
Then add the recomputed Unit_Cost as a custom column:
```m
= Table.AddColumn(PreviousStepName, "Unit_Cost",
    each try [Stock_Cost_Value] / [Stock_Qty] otherwise null, type number)
```

## 4. Dim_Date (reference Fact_Staging)

Get distinct months, then parse "May 2026" style text into a real date:
```m
= Table.Distinct(Table.SelectColumns(Fact_Staging, {"Report_Month"}))
```
Add columns:
```m
Date       = Date.FromText("1 " & [Report_Month], "en-US")
Month_Name = Date.MonthName([Date])
```
You don't need a separate `Month_Sort` column — since Dim_Date is one row per
month, just set **Sort by Column**: `Month_Name` sorted by `Date` directly.

## 5. Dim_Store (reference Main_Clean)

```m
= Table.Group(
    Main_Clean,
    {"Store_Code"},
    {
        {"Store_Name", each List.First([Store_Name]), type text},
        {"Account_Name", each List.First([Account_Name]), type text},
        {"State", each List.First([State]), type text},
        {"City", each List.First([City]), type text},
        {"Pincode", each List.Mode(List.RemoveNulls([Pincode])), type text}
    }
)
```
`List.RemoveNulls` before `List.Mode` is what makes this "most common non-null
Pincode, or blank if the store never had one" — exactly the same logic as the
Python version.

## 6. Category mapping — Category_Counts (reference Main_Clean)

```m
= Table.Group(
    Main_Clean,
    {"Category"},
    {
        {"Row_Count", each Table.RowCount(_), Int64.Type},
        {"Total_Stock_Cost_Value", each List.Sum([Stock_Cost_Value]), type number}
    }
)
```
Export this once (right-click the query → Copy, or just view it) to see the
~78 raw values with their row counts and value contribution. Fill in a small
two-column Excel file yourself: `Category | Clean_Therapy_Area`. Load that
file as its own query (`Category_Map_Manual`), then **Merge Queries** —
`Category_Counts` (or wherever Category lives) with `Category_Map_Manual` on
`Category`, Left Outer join, expand `Clean_Therapy_Area`. This becomes the
source your `Dim_Product` query merges from, so re-running the refresh next
month reuses your existing mapping automatically — you only add rows for
genuinely new Category values.

## 7. Dim_Product (reference Main_Clean, then merge in Clean_Therapy_Area)

```m
= Table.Group(
    Main_Clean,
    {"Product_Code"},
    {
        {"Product_Name", each List.First([Product_Name]), type text},
        {"Category", each List.First([Category]), type text},
        {"Manufacturer_Name", each List.First([Manufacturer_Name]), type text}
    }
)
```
Then merge with the mapped `Category_Counts` (step 6) on `Category` to pull in
`Clean_Therapy_Area`.

## 8. Fact_Inventory (reference Fact_Staging, merge in Dim_Date)

Merge `Fact_Staging` with `Dim_Date` on `Report_Month`, expand `Date`, then
**Remove Columns**: `Report_Month`, `Account_Name` (redundant — comes from
Dim_Store via the relationship). Keep: `Store_Code`, `Product_Code`, `Date`,
`Stock_Qty`, `Stock_Cost_Value`, `Stock_MRP_Value`, `Unit_Cost`.

## 9. Reconciliation — no Python assert, so make it a query that errors on failure

Build one more small query, `QC_Check`:
```m
let
    RawTotal = List.Sum(Source[Stock_Cost_Value]),
    CleanTotal = List.Sum(Fact_Inventory[Stock_Cost_Value])
              + List.Sum(Quarantined_Negative_Qty[Stock_Cost_Value]),
    Diff = Number.Round(RawTotal - CleanTotal, 2),
    Result = if Diff <> 0 then error "Reconciliation mismatch: " & Text.From(Diff) else "OK"
in
    Result
```
If the totals don't match, this query **fails on refresh** instead of silently
publishing wrong numbers — same intent as the Python assert, just enforced by
Power BI itself.

## 10. Row-count summary → build it as a page, not stdout

Power Query has no console output, so instead of printing a summary, this
becomes your **Data Quality page** in the report (already planned): cards for
`Rows with Null Pincode`, `Rows Unmapped Category`, quarantined row count and
value — all DAX measures reading directly off these same tables.
