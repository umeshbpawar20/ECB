Store Universe = 
DISTINCTCOUNT(Dim_Store[Store_Code])

Stores with Inventory = 
CALCULATE(DISTINCTCOUNT(Fact_Inventory[Store_Code]), Fact_Inventory[Stock_Qty] > 0)

Store Coverage % = 
DIVIDE([Stores with Inventory], [Store Universe])

L3M Avg Inventory Value = 
VAR CurrentDate = MAX(Dim_Date[Date])
VAR PriorWindow = DATESINPERIOD(Dim_Date[Date], EDATE(CurrentDate,-1), -3, MONTH)
RETURN AVERAGEX(PriorWindow, CALCULATE([Total Stock Value (Cost)]))

Current vs L3M Avg % = 
DIVIDE([Total Stock Value (Cost)] - [L3M Avg Inventory Value], [L3M Avg Inventory Value])
