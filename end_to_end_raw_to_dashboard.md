# End-to-End: Raw CSV → Published Dashboard (All in Power BI)

One manual pause point in the whole build: the Category → Therapy Area
mapping (Phase 6). Everything else is click-through or paste-in.

Performance note before you start: CSV sources don't support query folding, so
every Group By below runs entirely in Power Query's own engine against 1.34M
rows — expect the Group By steps to take real time, not be instant. If it's
painful while you're designing, temporarily add a "Keep Top Rows → 50,000"
step right after Source, build everything against that, then delete that one
step before your final Close & Apply.

---

## Phase 1 — Load the raw file

1. Power BI Desktop → Home → **Get Data → Text/CSV** → select
   `Cleaned_Inventory_Combined.csv` → click **Transform Data** (not Load).
2. Rename this query `Source`.
3. In Applied Steps, set explicit types (Transform → Data Type, or edit the
   "Changed Type" step directly):
   - `Store_Code`, `Product_Code`, `Pincode` → **Text** (not Whole Number —
     you'll silently lose leading zeros otherwise)
   - `Stock_Qty`, `Stock_Cost_Value`, `Stock_MRP_Value`, `Unit_Cost` →
     **Decimal Number**
   - everything else → Text

## Phase 2 — Split off the bad rows

4. Right-click `Source` → **Reference** → rename `Main_Clean`.
5. Right-click `Source` → **Reference** → rename `Quarantined_Negative_Qty`.
6. In `Quarantined_Negative_Qty`: Home → Reduce Rows → Keep Rows → Keep Rows
   Where → `Stock_Qty` → **Less Than** → `0`. Leave "Enable Load" **on** —
   you want this visible for the data-quality page later.
7. In `Main_Clean`: same dialog, but **Greater Than or Equal To** → `0`.
   Right-click the query → **uncheck "Enable Load"** (this is staging only).

## Phase 3 — Collapse duplicates into Fact_Staging

8. Right-click `Main_Clean` → Reference → rename `Fact_Staging`.
9. Home → **Group By** → Advanced → group by `Report_Month`, `Account_Name`,
   `Store_Code`, `Product_Code`; add aggregations: Sum of `Stock_Qty`, Sum of
   `Stock_Cost_Value`, Sum of `Stock_MRP_Value`.
10. Add Custom Column, name `Unit_Cost`:
    ```m
    = try [Stock_Cost_Value] / [Stock_Qty] otherwise null
    ```
11. Uncheck "Enable Load" — still staging.

## Phase 4 — Dim_Date

12. Right-click `Fact_Staging` → Reference → rename `Dim_Date`.
13. Choose Columns → keep only `Report_Month` → Remove Duplicates.
14. Add Custom Column `Date`:
    ```m
    = Date.FromText("1 " & [Report_Month], "en-US")
    ```
15. Add Custom Column `Month_Name`:
    ```m
    = Date.MonthName([Date])
    ```
16. Confirm "Enable Load" is **on**.

## Phase 5 — Dim_Store

17. Right-click `Main_Clean` → Reference → rename `Dim_Store`.
18. Home → Group By → set `Store_Code` as the group column, add any one
    placeholder aggregation (e.g. Count Rows) just to create the step.
19. Open the **Advanced Editor** and replace that step's code with:
    ```m
    = Table.Group(
        #"Previous Step",
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
    (`List.Mode` after `List.RemoveNulls` = "most common non-null Pincode for
    this store, or blank if it never had one" — matches the fill logic
    exactly.)
20. Confirm "Enable Load" is **on**.

## Phase 6 — Category mapping (the one manual step)

21. Right-click `Main_Clean` → Reference → rename `Category_Counts`.
22. Home → Group By → group by `Category`; aggregations: **Count Rows**
    (rename `Row_Count`), **Sum** of `Stock_Cost_Value` (rename
    `Total_Stock_Cost_Value`).
23. This resolves to only ~78 rows — you can see the full result right in the
    Query Editor preview pane. Select all, copy, paste into a new Excel file
    with two columns: `Category` and `Clean_Therapy_Area`. Fill in
    `Clean_Therapy_Area` by hand for each of the ~78 values. Save as
    `Category_Mapping.xlsx`.
24. Back in Power BI: Get Data → Excel → load `Category_Mapping.xlsx` as a new
    query, name it `Category_Map_Manual`.
25. In `Category_Counts` (or a new reference of it): Home → **Merge Queries**
    → merge with `Category_Map_Manual` on `Category`, **Left Outer** → expand
    `Clean_Therapy_Area`. Enable Load on.

Next month, when new Category values show up, you only need to add rows for
the *new* ones — the merge keeps working for everything already mapped.

## Phase 7 — Dim_Product

26. Right-click `Main_Clean` → Reference → rename `Dim_Product`.
27. Group By `Product_Code` → placeholder aggregation → Advanced Editor →
    replace with:
    ```m
    = Table.Group(
        #"Previous Step",
        {"Product_Code"},
        {
            {"Product_Name", each List.First([Product_Name]), type text},
            {"Category", each List.First([Category]), type text},
            {"Manufacturer_Name", each List.First([Manufacturer_Name]), type text}
        }
    )
    ```
28. Merge Queries → merge with the mapped `Category_Counts` on `Category` →
    expand `Clean_Therapy_Area`.
29. Enable Load on.

## Phase 8 — Fact_Inventory

30. Right-click `Fact_Staging` → Reference → rename `Fact_Inventory`.
31. Merge Queries → merge with `Dim_Date` on `Report_Month`, Left Outer →
    expand only `Date`.
32. Remove Columns: `Report_Month`, `Account_Name` (redundant — comes through
    the relationship to Dim_Store).
33. Enable Load on. Final columns: `Store_Code`, `Product_Code`, `Date`,
    `Stock_Qty`, `Stock_Cost_Value`, `Stock_MRP_Value`, `Unit_Cost`.

## Phase 9 — Reconciliation check

34. New Blank Query → Advanced Editor → paste:
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
35. Rename `QC_Check`. Enable Load on — if the totals ever don't match, this
    query fails the refresh instead of quietly publishing wrong numbers.

## Phase 10 — Load

36. Home → **Close & Apply**. With 1.34M source rows this will take a while —
    let it finish.

## Phase 11 — Model view

37. Switch to **Model** view. Confirm/create relationships:

    | From | To | Cardinality | Direction |
    |---|---|---|---|
    | Fact_Inventory[Store_Code] | Dim_Store[Store_Code] | Many-to-One | Single |
    | Fact_Inventory[Product_Code] | Dim_Product[Product_Code] | Many-to-One | Single |
    | Fact_Inventory[Date] | Dim_Date[Date] | Many-to-One | Single |

38. Select `Dim_Date` → Table tools → **Mark as Date Table** → column `Date`.
39. Select `Dim_Date[Month_Name]` → Column tools → **Sort by Column** → `Date`.
40. Right-click `Fact_Inventory[Store_Code]`, `[Product_Code]`, `[Date]` →
    **Hide in report view**.
41. Build hierarchies: `Dim_Store`: State → City → Store_Name. `Dim_Product`:
    Clean_Therapy_Area → Product_Name.

## Phase 12 — Measures

42. Home → Enter Data → create an empty table `_Measures` (any single dummy
    column) → Load. New Measure, once per formula below, with Display Folder
    set per group (right pane → Properties → Display Folder).

**01 Core**
```dax
Total Stock Value (Cost) = SUM(Fact_Inventory[Stock_Cost_Value])
Total Stock Value (MRP) = SUM(Fact_Inventory[Stock_MRP_Value])
Total Stock Value (Cost, Cr) = DIVIDE([Total Stock Value (Cost)], 10000000)
Total Stock Qty = SUM(Fact_Inventory[Stock_Qty])
Distinct SKUs = DISTINCTCOUNT(Fact_Inventory[Product_Code])
Distinct Stores = DISTINCTCOUNT(Fact_Inventory[Store_Code])
Avg Stock Value per Store = DIVIDE([Total Stock Value (Cost)], [Distinct Stores])
```
Format `Total Stock Value (Cost, Cr)` as `#,##0.00 "Cr"`.

**02 Movement / MoM**
```dax
Prior Month Value = CALCULATE([Total Stock Value (Cost)], DATEADD(Dim_Date[Date], -1, MONTH))
MoM Δ Value = [Total Stock Value (Cost)] - [Prior Month Value]
MoM Δ % = DIVIDE([MoM Δ Value], [Prior Month Value])
Prior Month Qty = CALCULATE([Total Stock Qty], DATEADD(Dim_Date[Date], -1, MONTH))
Dead Stock Flag =
IF([Total Stock Qty] = [Prior Month Qty] && NOT ISBLANK([Prior Month Value]), "Dead", "Moving")
```

**03 Ranking / ABC**
```dax
Rank by Value = RANKX(ALLSELECTED(Dim_Product[Product_Name]), [Total Stock Value (Cost)], , DESC)

Cumulative Value % =
VAR CurrentRank = [Rank by Value]
VAR TotalAll = CALCULATE([Total Stock Value (Cost)], ALLSELECTED(Dim_Product))
RETURN DIVIDE(
    CALCULATE([Total Stock Value (Cost)], FILTER(ALLSELECTED(Dim_Product), [Rank by Value] <= CurrentRank)),
    TotalAll
)

ABC Class =
SWITCH(TRUE(), [Cumulative Value %] <= 0.8, "A", [Cumulative Value %] <= 0.95, "B", "C")
```

**04 Shares**
```dax
Value % of Total =
DIVIDE([Total Stock Value (Cost)], CALCULATE([Total Stock Value (Cost)], ALLSELECTED(Dim_Store), ALLSELECTED(Dim_Product)))
```

**05 Data Quality**
```dax
Rows with Null Pincode = CALCULATE(COUNTROWS(Fact_Inventory), ISBLANK(RELATED(Dim_Store[Pincode])))
Rows Unmapped Category = CALCULATE(COUNTROWS(Fact_Inventory), ISBLANK(RELATED(Dim_Product[Clean_Therapy_Area])))
Quarantined Rows = COUNTROWS(Quarantined_Negative_Qty)
Quarantined Value (Cost) = SUM(Quarantined_Negative_Qty[Stock_Cost_Value])
```

## Phase 13 — Report pages

Build in this order, adding a synced slicer panel (`Account_Name`, `State`,
`Clean_Therapy_Area`, `Month_Name` — View → Sync Slicers) across pages 1–4.

1. **Executive Summary** — cards: `Total Stock Value (Cost, Cr)`,
   `Total Stock Qty`, `Distinct SKUs`, `Distinct Stores`; bar: Account_Name ×
   `Total Stock Value (Cost)`; filled map by State; waterfall of `MoM Δ Value`
   by month.
2. **Chain Deep-Dive** — matrix: rows Account_Name → Clean_Therapy_Area,
   values `Total Stock Value (Cost)`, `Value % of Total`; Top 20 table:
   Product_Name, value, `Rank by Value`, `ABC Class` (data bars); treemap:
   Store_Name sized by value, split by chain.
3. **Movement (May→June)** — waterfall of `MoM Δ Value` by
   Clean_Therapy_Area; two tables (gainers, decliners) on `MoM Δ Value` /
   `MoM Δ %`; a table filtered to `Dead Stock Flag = "Dead"`.
4. **Geography** — map on State/City by value; drill-through target page at
   Store level.
5. **Data Quality** — cards for `Rows with Null Pincode`, `Rows Unmapped
   Category`, `Quarantined Rows`, `Quarantined Value (Cost)`.

## Phase 14 — Validate & publish

49. Open `QC_Check` in Power Query — confirm it shows `"OK"`.
50. Spot-check 2–3 known Store_Code + Product_Code rows against the raw CSV.
51. Publish to your workspace. If this repeats monthly, keep the CSV in a
    OneDrive/SharePoint-synced folder (same pattern as your CHTF_INBU refresh
    setup) so scheduled refresh in the Service works without needing an
    on-premises gateway.
