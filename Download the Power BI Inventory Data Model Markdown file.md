# Power BI Inventory Data Model Explained

The important idea is understanding **how data moves through the Power Query tables and why each table exists**.

# Your Data Model in Simple Terms

Your model follows a **star schema**:

```text
                         Dim_Date
                             |
                             |
Dim_Store -------- Fact_Inventory -------- Dim_Product
```

- `Fact_Inventory` stores the inventory numbers.
- Dimension tables describe the inventory:
  - `Dim_Date` describes the month.
  - `Dim_Store` describes the store.
  - `Dim_Product` describes the SKU.
- Staging queries clean and prepare the data before it reaches the model.

---

# Complete Power Query Data Flow

Your Power Query structure is approximately:

```text
Source
├── Main_Clean
│   ├── Fact_Staging
│   │   ├── Fact_Inventory
│   │   └── Dim_Date
│   └── Dim_Store
└── Quarantined_Negative_Qty

External SKU Reference
└── Dim_Product

QC_Check
```

The process can be understood in three layers:

## Layer 1: Raw and cleaning

```text
Source
Main_Clean
Quarantined_Negative_Qty
```

## Layer 2: Preparation and aggregation

```text
Fact_Staging
```

## Layer 3: Final model tables

```text
Fact_Inventory
Dim_Date
Dim_Store
Dim_Product
```

`QC_Check` sits outside these layers and validates the totals.

---

# 1. Source

## Purpose

`Source` is the starting point of your entire inventory model.

It connects Power BI to:

```text
Cleaned_Inventory_Combined.csv
```

It contains the original rows imported from the CSV before the model-specific cleaning and aggregation.

## What happens in Source

The main transformation is setting the correct data types.

Examples:

```text
Store_Code         → Text
SKU No             → Text
Pincode            → Text
Stock_Qty          → Decimal Number
Stock_Cost_Value   → Decimal Number
Stock_MRP_Value    → Decimal Number
```

## Why codes are stored as Text

Fields such as:

```text
Store_Code
SKU No
Pincode
```

are identifiers, not values used for mathematical calculations.

For example, Power BI should not add two SKU numbers together. Storing these columns as Text also protects leading zeros.

## Is Source loaded into the model?

Normally:

```text
Enable Load: Off
```

`Source` is a staging query. Loading it would create an unnecessary copy of all the raw data in the model.

## Simple meaning

> `Source` is the untouched starting point with corrected column types.

---

# 2. Main_Clean

## Purpose

`Main_Clean` contains inventory rows where the stock quantity is valid for the main inventory analysis.

The filter is:

```text
Stock_Qty >= 0
```

This means it contains:

- Positive stock
- Zero stock
- No negative stock

## Why zero stock is retained

A zero-stock row can still be useful because it shows that a store-SKU combination existed in a reporting month but had no closing stock.

Zero must therefore remain in the clean dataset.

## Why Main_Clean is a reference of Source

Because `Main_Clean` references `Source`, any corrections made in `Source` flow automatically into `Main_Clean`.

For example:

```text
Source data type correction
        ↓
Main_Clean receives the correction
        ↓
All downstream queries receive it
```

## Is Main_Clean loaded?

Normally:

```text
Enable Load: Off
```

It is an intermediate cleaning query.

## Simple meaning

> `Main_Clean` is the usable inventory data after excluding negative quantities.

---

# 3. Quarantined_Negative_Qty

## Purpose

This query contains rows where:

```text
Stock_Qty < 0
```

These rows were not deleted. They were separated from the normal inventory data.

## Why separate the negative rows?

A negative stock quantity may indicate:

- Adjustment entries
- Returns
- Timing differences
- Incorrect stock capture
- Posting or reconciliation issues
- Legitimate negative inventory in the source system

Power BI should not silently treat those rows as ordinary positive inventory.

Keeping them separately lets you inspect:

```text
How many negative rows exist?
Which stores have them?
Which SKUs are affected?
What stock value is associated with them?
```

## Is this table loaded?

Yes:

```text
Enable Load: On
```

It is loaded because you may use it for data-quality analysis and because it contributes to the reconciliation check.

## Important distinction

`Quarantined_Negative_Qty` is not part of the main inventory fact table.

Therefore:

```text
Main inventory analysis
    → Fact_Inventory

Negative quantity investigation
    → Quarantined_Negative_Qty
```

## Simple meaning

> `Quarantined_Negative_Qty` is a holding table for suspicious negative-stock records.

---

# 4. Fact_Staging

## Purpose

`Fact_Staging` combines duplicate inventory rows into one row at the required reporting level.

Your intended grouping level is approximately:

```text
Month
Account_Name
Store_Code
SKU No
```

Originally, the model used `Product_Code`, but you replaced it with `SKU No`.

## Why grouping was required

Suppose the raw data contains:

| Month | Store | SKU | Stock Qty | Stock Cost |
|---|---|---|---:|---:|
| May 2026 | S001 | SKU-A | 10 | 1,000 |
| May 2026 | S001 | SKU-A | 5 | 500 |

Both rows refer to the same month, store, and SKU.

`Fact_Staging` groups them into:

| Month | Store | SKU | Stock Qty | Stock Cost |
|---|---|---|---:|---:|
| May 2026 | S001 | SKU-A | 15 | 1,500 |

The following values are summed:

```text
Stock_Qty
Stock_Cost_Value
Stock_MRP_Value
```

## Unit Cost calculation

After summing, `Unit_Cost` is recalculated:

```text
Unit_Cost = Stock_Cost_Value ÷ Stock_Qty
```

This is important because unit cost should be calculated from the final aggregated totals.

For example:

```text
Stock_Cost_Value = 1,500
Stock_Qty = 15

Unit_Cost = 1,500 ÷ 15 = 100
```

If quantity is zero, the result is blank rather than an error.

## What is the grain of Fact_Staging?

The **grain** means what one row represents.

One row in `Fact_Staging` represents:

> One SKU, in one store, for one reporting month, after duplicate rows have been combined.

This is one of the most important concepts in your model.

## Is Fact_Staging loaded?

Normally:

```text
Enable Load: Off
```

It prepares the data for `Fact_Inventory`.

## Simple meaning

> `Fact_Staging` combines repeated inventory records into one monthly store-SKU record.

---

# 5. Fact_Inventory

## Purpose

`Fact_Inventory` is the main numeric table used by the model.

It is the central table in the star schema.

## Intended final columns

Your final fact table should contain:

```text
Date
Store_Code
SKU No
Stock_Qty
Stock_Cost_Value
Stock_MRP_Value
Unit_Cost
```

Depending on the latest changes you made, some extra columns might still be present. The seven fields above are the core fields.

## What one row represents

One row represents:

> The inventory position of one SKU at one store for one reporting month.

For example:

```text
Date:             01-May-2026
Store_Code:       STORE001
SKU No:           2030003742
Stock_Qty:        20
Stock_Cost_Value: 2,000
Stock_MRP_Value:  2,600
Unit_Cost:        100
```

## Why it is called a Fact table

A fact table contains values that can be measured and aggregated.

Examples in your fact table:

```text
Stock_Qty
Stock_Cost_Value
Stock_MRP_Value
Unit_Cost
```

The first three are the primary inventory facts.

`Unit_Cost` is a calculated ratio based on stock cost and quantity.

## Why descriptive columns were removed

Fields such as these should not normally be repeated in the fact table:

```text
Store_Name
State
City
Pincode
Product_Name
Manufacturer_Name
```

Those descriptions belong in dimension tables.

For example:

```text
Fact_Inventory contains Store_Code
Dim_Store translates Store_Code into Store_Name, City and State
```

This reduces repetition and keeps the model easier to maintain.

## Why Account_Name was removed

`Account_Name` is stored in `Dim_Store`.

The relationship:

```text
Dim_Store[Store_Code]
    1 → * Fact_Inventory[Store_Code]
```

allows account filters to reach `Fact_Inventory`.

Therefore, `Account_Name` does not have to be repeated in every fact row.

## Is Fact_Inventory loaded?

Yes:

```text
Enable Load: On
```

This is the main reporting table.

## Simple meaning

> `Fact_Inventory` stores the final monthly inventory quantities and values by store and SKU.

---

# 6. Dim_Date

## Purpose

`Dim_Date` describes the monthly reporting period.

At present, your dataset contains two reporting months:

```text
01-May-2026
01-Jun-2026
```

Therefore, `Dim_Date` currently contains two rows.

## Typical columns

Your table contains or may contain:

```text
Date
Month_Name
Month_Number
Year
Month_Year
Month_Year_Sort
```

Not all columns are mandatory, but they serve different purposes.

### Date

Example:

```text
01-May-2026
01-Jun-2026
```

This is the relationship key to `Fact_Inventory`.

### Month_Name

Example:

```text
May
June
```

This gives a readable month name.

### Month_Number

Example:

```text
May  → 5
June → 6
```

This is used to put month names in calendar order instead of alphabetical order.

### Year

Example:

```text
2026
```

Useful when the data grows to multiple years.

### Month_Year

Example:

```text
May 2026
Jun 2026
```

This is more useful than `Month_Name` when data covers multiple years.

## Relationship

```text
Dim_Date[Date]
    1 → * Fact_Inventory[Date]
```

One row exists in `Dim_Date` for each month, while many inventory rows can exist for that month.

## Important current limitation

Your `Dim_Date` is a **monthly period dimension**, not a complete daily calendar.

It contains:

```text
01-May-2026
01-Jun-2026
```

but it does not contain every date between them.

That is acceptable for your current monthly inventory analysis, as long as the month-over-month calculations are designed for monthly dates.

## Is Dim_Date loaded?

Yes:

```text
Enable Load: On
```

## Simple meaning

> `Dim_Date` gives one common monthly timeline for filtering the inventory data.

---

# 7. Dim_Store

## Purpose

`Dim_Store` contains one row per store.

Instead of repeating the store details inside every inventory record, the details are stored once in this dimension.

## Typical columns

```text
Store_Code
Store_Name
Account_Name
State
City
Pincode
```

## What one row represents

One row represents:

> One unique store and its descriptive information.

For example:

| Store_Code | Store_Name | Account_Name | State | City | Pincode |
|---|---|---|---|---|---|
| S001 | Central Store | Medplus | Maharashtra | Mumbai | 400001 |

## How it was created

`Dim_Store` was created from `Main_Clean` and grouped by:

```text
Store_Code
```

Power Query then selected values for:

```text
Store_Name
Account_Name
State
City
Pincode
```

For pincode, the logic selected the most common available pincode for the store.

## Relationship

```text
Dim_Store[Store_Code]
    1 → * Fact_Inventory[Store_Code]
```

This means:

- One store row exists in `Dim_Store`.
- Many inventory rows may exist for that store.

For example, one store may have:

- Multiple SKUs
- Multiple months
- Multiple inventory records

## Why Store_Code is the key

`Store_Name` may not be reliable as a key because:

- Store names may be changed.
- Multiple stores may have similar names.
- Spelling can vary.
- Spaces and abbreviations can differ.

`Store_Code` is intended to be the stable identifier.

## Is Dim_Store loaded?

Yes:

```text
Enable Load: On
```

## Simple meaning

> `Dim_Store` is the store master containing one row per store.

---

# 8. Dim_Product

## Purpose

`Dim_Product` contains one row per SKU.

You initially considered using `Product_Code`, but the model now uses:

```text
SKU No
```

from an external product reference file.

## Current columns

Based on your latest version:

```text
SKU No
Product_Name
Manufacturer_Name
```

## What one row represents

One row represents:

> One unique SKU and its product description.

For example:

| SKU No | Product_Name | Manufacturer_Name |
|---|---|---|
| 2030003742 | ABVIDA M 50MG/500MG TAB 15'S | ABBOTT HEALTHCARE |

## Why SKU No is the key

The product name is descriptive but not necessarily unique.

There may be:

- Similar product names
- Different pack sizes
- Different strengths
- Slight spelling variations
- Multiple SKUs with similar descriptions

`SKU No` is therefore a better relationship key.

## Duplicate SKU issue

Power BI originally rejected the relationship because `Dim_Product` contained repeated:

```text
SKU Not Found
```

You resolved this by making `SKU No` unique in `Dim_Product`.

The correct structure is:

```text
Dim_Product:
One row for SKU Not Found

Fact_Inventory:
Potentially many rows for SKU Not Found
```

That allows unmatched inventory rows to remain in the totals while being grouped under an unknown-product member.

## Relationship

```text
Dim_Product[SKU No]
    1 → * Fact_Inventory[SKU No]
```

One SKU exists once in `Dim_Product`, but it can appear in many fact rows across stores and months.

## Category fields

You chose not to perform category or therapy-area analysis.

Therefore, the model does not require:

```text
Category_Counts
Category_Map_Manual
Clean_Therapy_Area
Dim_Category
```

That was a valid simplification based on your reporting requirement.

## Is Dim_Product loaded?

Yes:

```text
Enable Load: On
```

## Simple meaning

> `Dim_Product` is the SKU master containing one row per SKU.

---

# 9. QC_Check

## Purpose

`QC_Check` makes sure the cleaning process did not silently lose or duplicate stock cost value.

It compares:

```text
Total stock cost in Source
```

against:

```text
Total stock cost in Fact_Inventory
+
Total stock cost in Quarantined_Negative_Qty
```

The logic is:

```text
Raw total = Clean total + Quarantined total
```

## Your result

Your query returned:

```text
OK
```

That means the stock cost value reconciled successfully at the time of the check.

## What an error would mean

If `QC_Check` returns a difference, possible causes include:

- Rows lost during filtering
- Blank quantities excluded from both clean and quarantine queries
- A merge duplicated fact rows
- A transformation removed records
- A numeric conversion created errors

## Does QC_Check contain business data?

No.

It is a control query rather than a normal reporting table.

## Simple meaning

> `QC_Check` verifies that the clean and quarantined data together still equal the original source total.

---

# 10. `_Measures`

Although `_Measures` was created using **Enter Data**, not Power Query transformations, it is part of the final model design.

## Purpose

`_Measures` is an organizational table.

It stores calculations such as:

```text
Total Stock Value (Cost)
Total Stock Value (MRP)
Total Stock Qty
Distinct SKUs
Distinct Stores
Prior Month Value
MoM Δ %
Rank by Value
Cumulative Value %
ABC Class
```

## Does it contain real data?

Not in the normal sense.

The dummy `Placeholder` column exists only because Power BI requires a table. That column is hidden.

## Why use a separate measures table?

Without `_Measures`, measures may be scattered across:

```text
Fact_Inventory
Dim_Product
Dim_Store
Dim_Date
```

Keeping them in `_Measures` makes the model easier to navigate.

## Simple meaning

> `_Measures` is a folder-style table used to organize DAX calculations.

---

# How the Tables Work Together

Suppose `Fact_Inventory` contains this record:

| Date | Store_Code | SKU No | Stock_Qty | Stock_Cost_Value |
|---|---|---|---:|---:|
| 01-May-2026 | S001 | 2030003742 | 10 | 1,000 |

The dimension tables provide the descriptions.

`Dim_Date` says:

```text
01-May-2026 = May 2026
```

`Dim_Store` says:

```text
S001 = Central Store, Mumbai, Maharashtra
```

`Dim_Product` says:

```text
2030003742 = ABVIDA M 50MG/500MG TAB 15'S
```

Power BI combines that information through relationships, without physically copying all the descriptions into every fact row.

Conceptually, the result becomes:

```text
May 2026
Central Store
Mumbai
ABVIDA M 50MG/500MG TAB 15'S
Quantity: 10
Cost Value: 1,000
```

---

# Why This Design Is Better Than One Large Table

A single flat table would repeatedly store:

```text
Store name
City
State
Pincode
Product name
Manufacturer
```

for every month and every inventory record.

The star-schema design stores:

- Inventory values in `Fact_Inventory`
- Store descriptions in `Dim_Store`
- Product descriptions in `Dim_Product`
- Period information in `Dim_Date`

This provides:

- Cleaner relationships
- Less duplicated descriptive data
- Easier maintenance
- Clearer DAX calculations
- Better filtering behavior
- A more understandable model

---

# Final Table Classification

## Staging queries

These prepare the data but are not intended for report consumption:

```text
Source
Main_Clean
Fact_Staging
```

Recommended setting:

```text
Enable Load: Off
```

## Final reporting tables

These form the star schema:

```text
Fact_Inventory
Dim_Date
Dim_Store
Dim_Product
```

Recommended setting:

```text
Enable Load: On
```

## Data-quality table

```text
Quarantined_Negative_Qty
```

Recommended setting:

```text
Enable Load: On
```

## Validation query

```text
QC_Check
```

This validates reconciliation.

## Calculation container

```text
_Measures
```

This organizes DAX measures.

---

# Model Summary

| Table | One row represents | Main role |
|---|---|---|
| `Source` | One original CSV row | Raw starting point |
| `Main_Clean` | One nonnegative inventory row | Clean staging data |
| `Quarantined_Negative_Qty` | One negative-quantity row | Data-quality investigation |
| `Fact_Staging` | One month-store-SKU combination | Duplicate consolidation |
| `Fact_Inventory` | One month-store-SKU inventory position | Main numeric table |
| `Dim_Date` | One reporting month | Period description |
| `Dim_Store` | One store | Store master |
| `Dim_Product` | One SKU | Product master |
| `QC_Check` | One reconciliation result | Refresh validation |
| `_Measures` | Calculation container | Organizes DAX measures |

---

# The Most Important Concept

Your model separates **numbers** from **descriptions**:

```text
Fact_Inventory = What happened and how much
Dim_Date       = When
Dim_Store      = Where
Dim_Product    = Which SKU
```

That is the core of your inventory data model.
