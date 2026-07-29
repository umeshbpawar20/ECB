import os
import sys
import time
import pandas as pd
import numpy as np
from python_calamine import CalamineWorkbook

start_time = time.time()
print("Starting 2-Month Multi-Account Inventory Data Cleaning & Concatenation Pipeline...")

may_dir = r"\\oneabbott.com\Asiapac\Mumbai\BKC\Data03\EPD Channel team\Umesh\D2R\Inventory\1. Data Input\May'26"
jun_dir = r"\\oneabbott.com\Asiapac\Mumbai\BKC\Data03\EPD Channel team\Umesh\D2R\Inventory\1. Data Input\Jun'26"
output_csv = r"\\oneabbott.com\Asiapac\Mumbai\BKC\Data03\EPD Channel team\Umesh\D2R\Inventory\3. Outputs\Cleaned_Inventory_Combined.csv"
store_mapping_file = r"\\oneabbott.com\Asiapac\Mumbai\BKC\Data03\EPD Channel team\Umesh\D2R\Inventory\1. Data Input\Static Files\2026_store_mapping_frankross_wellness.xlsx"
pincode_master_file = r"\\oneabbott.com\Asiapac\Mumbai\BKC\Data03\EPD Channel team\Umesh\D2R\Inventory\1. Data Input\Static Files\2026_PinCodes_with_States_and_Districts.csv"
unassigned_wellness_file = r"\\oneabbott.com\Asiapac\Mumbai\BKC\Data03\EPD Channel team\Umesh\D2R\Inventory\3. Outputs\unassigned pincodes wellness.csv"

# Comprehensive City -> State Lookup Dictionary
CITY_TO_STATE = {
    # Madhya Pradesh
    'BHOPAL': ('BHOPAL', 'MADHYA PRADESH'),
    'INDORE': ('INDORE', 'MADHYA PRADESH'),
    'UJJAIN': ('UJJAIN', 'MADHYA PRADESH'),
    'GWALIOR': ('GWALIOR', 'MADHYA PRADESH'),
    'JABALPUR': ('JABALPUR', 'MADHYA PRADESH'),
    'RATLAM': ('RATLAM', 'MADHYA PRADESH'),
    'DEWAS': ('DEWAS', 'MADHYA PRADESH'),
    'SATNA': ('SATNA', 'MADHYA PRADESH'),

    # Karnataka
    'BANGALORE': ('BANGALORE', 'KARNATAKA'),
    'BENGALURU': ('BANGALORE', 'KARNATAKA'),
    'SHIVAMOGGA': ('SHIVAMOGGA', 'KARNATAKA'),
    'SHIMOGA': ('SHIVAMOGGA', 'KARNATAKA'),
    'MYSORE': ('MYSORE', 'KARNATAKA'),
    'MYSURU': ('MYSORE', 'KARNATAKA'),
    'MANGALORE': ('MANGALORE', 'KARNATAKA'),
    'MANGALURU': ('MANGALORE', 'KARNATAKA'),
    'BELGAUM': ('BELAGAVI', 'KARNATAKA'),
    'BELAGAVI': ('BELAGAVI', 'KARNATAKA'),
    'HUBLI': ('HUBLI', 'KARNATAKA'),
    'HUBALI': ('HUBLI', 'KARNATAKA'),
    'DHARWAD': ('HUBLI', 'KARNATAKA'),
    'DAVANAGERE': ('DAVANAGERE', 'KARNATAKA'),
    'HAVERI': ('HAVERI', 'KARNATAKA'),

    # Goa
    'GOA': ('GOA', 'GOA'),
    'PANAJI': ('PANAJI', 'GOA'),
    'MARGAO': ('MARGAO', 'GOA'),
    'VASCO': ('VASCO', 'GOA'),
    'MAPUSA': ('MAPUSA', 'GOA'),
    'PONDA': ('PONDA', 'GOA'),

    # Gujarat
    'VADODARA': ('VADODARA', 'GUJARAT'),
    'BARODA': ('VADODARA', 'GUJARAT'),
    'AHMEDABAD': ('AHMEDABAD', 'GUJARAT'),
    'SURAT': ('SURAT', 'GUJARAT'),
    'RAJKOT': ('RAJKOT', 'GUJARAT'),
    'VAPI': ('VAPI', 'GUJARAT'),
    'VALSAD': ('VALSAD', 'GUJARAT'),

    # Telangana / AP
    'HYDERABAD': ('HYDERABAD', 'TELANGANA'),
    'SECUNDERABAD': ('HYDERABAD', 'TELANGANA'),
    'WARANGAL': ('WARANGAL', 'TELANGANA'),

    # Maharashtra Cities & Towns
    'NASHIK': ('NASHIK', 'MAHARASHTRA'),
    'NASIK': ('NASHIK', 'MAHARASHTRA'),
    'PUNE': ('PUNE', 'MAHARASHTRA'),
    'MUMBAI': ('MUMBAI', 'MAHARASHTRA'),
    'THANE': ('THANE', 'MAHARASHTRA'),
    'NAVI MUMBAI': ('NAVI MUMBAI', 'MAHARASHTRA'),
    'BHIWANDI': ('BHIWANDI', 'MAHARASHTRA'),
    'BADLAPUR': ('BADLAPUR', 'MAHARASHTRA'),
    'AMBERNATH': ('AMBERNATH', 'MAHARASHTRA'),
    'AMBARNATH': ('AMBERNATH', 'MAHARASHTRA'),
    'DOMBIVLI': ('DOMBIVLI', 'MAHARASHTRA'),
    'DOMBIVALI': ('DOMBIVLI', 'MAHARASHTRA'),
    'KALYAN': ('KALYAN', 'MAHARASHTRA'),
    'BHAYANDER': ('BHAYANDAR', 'MAHARASHTRA'),
    'BHAYANDAR': ('BHAYANDAR', 'MAHARASHTRA'),
    'BOISAR': ('BOISAR', 'MAHARASHTRA'),
    'CHIPLUN': ('CHIPLUN', 'MAHARASHTRA'),
    'ICHALKARANJI': ('ICHALKARANJI', 'MAHARASHTRA'),
    'ICHALKARANAJI': ('ICHALKARANJI', 'MAHARASHTRA'),
    'SATANA': ('SATANA', 'MAHARASHTRA'),
    'AHMEDNAGAR': ('AHMEDNAGAR', 'MAHARASHTRA'),
    'SOLAPUR': ('SOLAPUR', 'MAHARASHTRA'),
    'KOLHAPUR': ('KOLHAPUR', 'MAHARASHTRA'),
    'NAGPUR': ('NAGPUR', 'MAHARASHTRA'),
    'AURANGABAD': ('AURANGABAD', 'MAHARASHTRA'),
    'SAMBHAJI': ('AURANGABAD', 'MAHARASHTRA'),
    'SAMBHAJINAGAR': ('AURANGABAD', 'MAHARASHTRA'),
    'SATARA': ('SATARA', 'MAHARASHTRA'),
    'SANGLI': ('SANGLI', 'MAHARASHTRA'),
    'JALGAON': ('JALGAON', 'MAHARASHTRA'),
    'DHULE': ('DHULE', 'MAHARASHTRA'),
    'RATNAGIRI': ('RATNAGIRI', 'MAHARASHTRA'),
    'AMRAVATI': ('AMRAVATI', 'MAHARASHTRA'),
    'PANVEL': ('PANVEL', 'MAHARASHTRA'),
    'ULHASNAGAR': ('ULHASNAGAR', 'MAHARASHTRA'),
    'VASAI': ('VASAI', 'MAHARASHTRA'),
    'VIRAR': ('VIRAR', 'MAHARASHTRA'),
    'MIRA ROAD': ('MIRA ROAD', 'MAHARASHTRA'),
    'PALGHAR': ('PALGHAR', 'MAHARASHTRA'),
    'WARDHA': ('WARDHA', 'MAHARASHTRA'),
    'JATH': ('JATH', 'MAHARASHTRA'),
    'KHED': ('KHED', 'MAHARASHTRA'),
    'PANCHGANI': ('PANCHGANI', 'MAHARASHTRA'),
    'SINDHUDURG': ('SINDHUDURG', 'MAHARASHTRA'),
    'KANKAVLI': ('SINDHUDURG', 'MAHARASHTRA'),
    'JALNA': ('JALNA', 'MAHARASHTRA'),
    'LONAND': ('LONAND', 'MAHARASHTRA'),
    'MALKAPUR': ('MALKAPUR', 'MAHARASHTRA'),
    'MANGAON': ('MANGAON', 'MAHARASHTRA'),
    'MIRAJ': ('MIRAJ', 'MAHARASHTRA'),
    'ISLAMPUR': ('ISLAMPUR', 'MAHARASHTRA'),
    'SAWANTWADI': ('SAWANTWADI', 'MAHARASHTRA'),
    'NALLASOPARA': ('MUMBAI', 'MAHARASHTRA'),
    'NALASOPARA': ('MUMBAI', 'MAHARASHTRA'),
    'BARAMATI': ('BARAMATI', 'MAHARASHTRA'),
    'KARAD': ('KARAD', 'MAHARASHTRA'),
    'ALIBAUG': ('ALIBAUG', 'MAHARASHTRA'),
    'LONAVALA': ('LONAVALA', 'MAHARASHTRA'),
}

# Mumbai & Thane Suburbs -> Mumbai / Maharashtra
MUMBAI_SUBURBS = [
    'BORIVALI', 'BHANDUP', 'CBD BELAPUR', 'CHANDIVALI', 'GHATKOPAR', 'THAKURLI',
    'ANDHERI', 'BANDRA', 'DADAR', 'KANDIVALI', 'MALAD', 'MULUND', 'POWAI',
    'KOPAR KHAIRANE', 'KOPARKHAIRANE', 'VASHI', 'NERUL', 'KHARGHAR', 'AIROLI', 'SANPADA', 'TURBHE',
    'KAMOTHE', 'KALAMBOLI', 'SEAWOODS', 'SION', 'CHEMBUR', 'KURLA', 'COLABA', 'JUHU',
    'SANTACRUZ', 'VILE PARLE', 'GOREGAON', 'DAHISAR', 'NAUPADA', 'SANTACRUZ',
    'KALWA', 'MAJIWADA', 'GHODBUNDER', 'WORLI', 'PAREL', 'CHARNI ROAD', 'GRANT ROAD',
    'MUMBAI CENTRAL', 'MAHIM', 'MATUNGA', 'WADALA', 'TROMBAY', 'GOVANDI', 'MANKHURD',
    'TILAK NAGAR', 'KANJURMARG', 'VIKHROLI', 'VIDYAVIHAR', 'ASALFA', 'SAKINAKA', 'GATKOPAR',
    'MAHALAXMI', 'JACOB CIRCLE', 'BHAWANI PETH', 'SHIVAJI NAGAR', 'LOKHANDWALA', 'TULSI'
]
for sub in MUMBAI_SUBURBS:
    CITY_TO_STATE[sub] = ('MUMBAI', 'MAHARASHTRA')

def get_wellness_city_state(store_name):
    name = str(store_name).upper()
    for kw, (city, state) in CITY_TO_STATE.items():
        if kw in name:
            return city, state
    return 'OTHER', 'MAHARASHTRA'

combined_dfs = []

# ==========================================
# 1. PROCESS FRANKROSS (May & June)
# ==========================================
def process_frankross(path, month_str):
    print(f"[{month_str}] Loading Frankross dataset: {os.path.basename(path)}...")
    wb = CalamineWorkbook.from_path(path)
    sheet = wb.get_sheet_by_name("Sheet1")
    rows = sheet.to_python()
    if not rows:
        return pd.DataFrame()
    
    header = rows[0]
    df = pd.DataFrame(rows[1:], columns=header)
    
    c_name_indices = [i for i, c in enumerate(header) if c == 'c_name']
    n_bal_indices = [i for i, c in enumerate(header) if c == 'n_bal_qty']
    
    cols = list(df.columns)
    if len(c_name_indices) >= 2:
        cols[c_name_indices[0]] = 'Store_Name'
        cols[c_name_indices[1]] = 'Product_Name'
    elif len(c_name_indices) == 1:
        cols[c_name_indices[0]] = 'Store_Name'

    if len(n_bal_indices) >= 2:
        cols[n_bal_indices[0]] = 'Stock_Qty'
        cols[n_bal_indices[1]] = 'DROP_BAL_QTY_2'
    elif len(n_bal_indices) == 1:
        cols[n_bal_indices[0]] = 'Stock_Qty'

    df.columns = cols
    if 'DROP_BAL_QTY_2' in df.columns:
        df = df.drop(columns=['DROP_BAL_QTY_2'])

    res = pd.DataFrame()
    res['Store_Code'] = df['c_br_code'].astype(str).str.replace('.0', '', regex=False).str.strip()
    res['Store_Name'] = df['Store_Name'].astype(str).str.strip().str.upper()
    res['State'] = df['State'].fillna('WEST BENGAL').astype(str).str.strip().str.upper()
    res['City'] = df['City'].fillna('UNASSIGNED').astype(str).str.strip().str.upper()
    res['Product_Code'] = df['c_item_code'].astype(str).str.strip()
    res['Product_Name'] = df['Product_Name'].astype(str).str.strip().str.upper()
    res['Category'] = df['item_category_class_name'].fillna('PHARMA').astype(str).str.strip().str.upper()
    res['Manufacturer_Name'] = df['c_mfac_name'].fillna('UNASSIGNED').astype(str).str.strip().str.upper()
    
    res['Stock_Qty'] = pd.to_numeric(df['Stock_Qty'], errors='coerce').fillna(0)
    res['Stock_Cost_Value'] = pd.to_numeric(df['n_pur_amt'], errors='coerce').fillna(0)
    res['Stock_MRP_Value'] = pd.to_numeric(df['n_mrp_amt'], errors='coerce').fillna(0)

    res['Report_Month'] = month_str
    res['Account_Name'] = 'Frankross'
    
    print(f"  -> Frankross {month_str} processed: {len(res):,} rows")
    return res

path_may_fr = os.path.join(may_dir, "Frankross Inventory May'26.XLSB")
combined_dfs.append(process_frankross(path_may_fr, "May 2026"))

path_jun_fr = os.path.join(jun_dir, "Frankross SOH June'2026.xlsb")
combined_dfs.append(process_frankross(path_jun_fr, "June 2026"))

# ==========================================
# 2. PROCESS MEDPLUS (May & June)
# ==========================================
def process_medplus(path, month_str):
    print(f"[{month_str}] Loading Medplus dataset: {os.path.basename(path)}...")
    wb = CalamineWorkbook.from_path(path)
    sheet_name = [s for s in wb.sheet_names if s.strip() == 'Store_SOH'][0]
    sheet = wb.get_sheet_by_name(sheet_name)
    rows = sheet.to_python()
    if not rows:
        return pd.DataFrame()

    header = rows[0]
    df = pd.DataFrame(rows[1:], columns=header)

    res = pd.DataFrame()
    res['Store_Code'] = df['StoreId'].astype(str).str.strip()
    res['Store_Name'] = df['StoreName'].astype(str).str.strip().str.upper()
    res['Pincode'] = df['Pincode'].fillna('').astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    res['State'] = df['State'].fillna('TELANGANA').astype(str).str.strip().str.upper()
    res['City'] = df['City'].fillna('HYDERABAD').astype(str).str.strip().str.upper()
    res['Product_Code'] = df['ProductId'].astype(str).str.strip()
    res['Product_Name'] = df['ProductName'].astype(str).str.strip().str.upper()
    res['Category'] = df['AuditForm'].fillna('MEDICINES').astype(str).str.strip().str.upper()
    res['Manufacturer_Name'] = df['ManufacturerName'].fillna('UNASSIGNED').astype(str).str.strip().str.upper()

    res['Stock_Qty'] = pd.to_numeric(df['AvailableQty'], errors='coerce').fillna(0)
    res['Stock_Cost_Value'] = pd.to_numeric(df['Cost_Value_E_Tax'], errors='coerce').fillna(0)
    res['Stock_MRP_Value'] = pd.to_numeric(df['MRP_Value'], errors='coerce').fillna(0)

    res['Report_Month'] = month_str
    res['Account_Name'] = 'Medplus'

    print(f"  -> Medplus {month_str} processed: {len(res):,} rows")
    return res

path_may_mp = os.path.join(may_dir, "Medplus_Monthly_Inventory_4_From2026_05_01To2026_05_31_Stores.xlsx")
combined_dfs.append(process_medplus(path_may_mp, "May 2026"))

path_jun_mp = os.path.join(jun_dir, "Medplus_Monthly_Inventory_4_From2026_06_01To2026_06_30_Stores.xlsx")
combined_dfs.append(process_medplus(path_jun_mp, "June 2026"))

# ==========================================
# 3. PROCESS WELLNESS (May & June)
# ==========================================
def process_wellness(path, month_str):
    print(f"[{month_str}] Loading Wellness dataset: {os.path.basename(path)}...")
    wb = CalamineWorkbook.from_path(path)
    sheet = wb.get_sheet_by_name(wb.sheet_names[0])
    rows = sheet.to_python()
    if not rows:
        return pd.DataFrame()

    header = rows[0]
    df = pd.DataFrame(rows[1:], columns=header)

    res = pd.DataFrame()
    res['Store_Code'] = df['brcode'].astype(str).str.replace('.0', '', regex=False).str.strip()
    res['Store_Name'] = df['brname'].astype(str).str.strip().str.upper()

    # Map Wellness branch code + branch name to Pincode.
    store_map = pd.read_excel(store_mapping_file, engine='openpyxl')
    store_map.columns = store_map.columns.astype(str).str.strip()
    store_map = store_map[
        store_map['Chain name'].astype(str).str.strip().str.lower().eq('wellness')
    ].copy()

    # Normalize keys so values such as 005, 5, and VASHI1:005 match consistently.
    wellness_code_key = res['Store_Code'].str.replace(r'\.0$', '', regex=True).str.lstrip('0').replace('', '0')
    wellness_name_key = res['Store_Name'].str.replace(r'\s+', ' ', regex=True).str.strip()

    store_map_code_key = (
        store_map['branch'].astype(str).str.strip().str.split(':').str[-1]
        .str.replace(r'\.0$', '', regex=True).str.lstrip('0').replace('', '0')
    )
    store_map_name_key = (
        store_map['BR_Name'].astype(str).str.strip().str.upper()
        .str.replace(r'\s+', ' ', regex=True).str.strip()
    )

    location_lookup = pd.DataFrame({
        '_Store_Code_Key': store_map_code_key,
        '_Store_Name_Key': store_map_name_key,
        'Pincode': store_map['PinCode'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    }).drop_duplicates(subset=['_Store_Code_Key', '_Store_Name_Key'])

    wellness_locations = pd.DataFrame({
        '_Store_Code_Key': wellness_code_key,
        '_Store_Name_Key': wellness_name_key
    }).merge(
        location_lookup,
        on=['_Store_Code_Key', '_Store_Name_Key'],
        how='left',
        validate='many_to_one'
    )

    # Use Pincode to obtain State and District; District is written to City.
    pincode_lookup = pd.read_csv(pincode_master_file, dtype=str, encoding='latin1')
    pincode_lookup.columns = pincode_lookup.columns.astype(str).str.strip()
    pincode_lookup = pincode_lookup.rename(columns={'Pin.Code': 'Pincode', 'District': 'City'})
    pincode_lookup['Pincode'] = pincode_lookup['Pincode'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
    pincode_lookup = pincode_lookup[['Pincode', 'State', 'City']].drop_duplicates(subset=['Pincode'])

    wellness_locations = wellness_locations.merge(
        pincode_lookup,
        on='Pincode',
        how='left',
        validate='many_to_one'
    )

    # Supplemental mapping: fill only Wellness records still missing after the main mapping.
    supplemental = pd.read_csv(
        unassigned_wellness_file,
        dtype=str,
        encoding='utf-8-sig',
        na_values=['#N/A', 'N/A', 'NA', ''],
        keep_default_na=True
    )
    supplemental.columns = supplemental.columns.astype(str).str.strip()
    supplemental['_Store_Code_Key'] = (
        supplemental['Store_Code'].astype(str)
        .str.replace(r'\.0$', '', regex=True)
        .str.strip()
        .str.lstrip('0')
        .replace('', '0')
    )
    supplemental = supplemental.rename(columns={
        'Pincode': 'Pincode_Supplemental',
        'State': 'State_Supplemental',
        'District': 'City_Supplemental'
    })
    supplemental = supplemental[
        ['_Store_Code_Key', 'Pincode_Supplemental', 'State_Supplemental', 'City_Supplemental']
    ].drop_duplicates(subset=['_Store_Code_Key'])

    wellness_locations = wellness_locations.merge(
        supplemental,
        on='_Store_Code_Key',
        how='left',
        validate='many_to_one'
    )

    # Main mapping remains the first priority; supplemental values are fallback only.
    wellness_locations['Pincode'] = wellness_locations['Pincode'].fillna(
        wellness_locations['Pincode_Supplemental']
    )
    wellness_locations['State'] = wellness_locations['State'].fillna(
        wellness_locations['State_Supplemental']
    )
    wellness_locations['City'] = wellness_locations['City'].fillna(
        wellness_locations['City_Supplemental']
    )

    res['Pincode'] = (
        wellness_locations['Pincode'].fillna('').astype(str)
        .str.replace(r'\.0$', '', regex=True).str.strip()
        .replace({'nan': '', 'None': '', '#N/A': ''})
    )
    res['State'] = wellness_locations['State'].fillna('UNASSIGNED').astype(str).str.strip().str.upper()
    res['City'] = wellness_locations['City'].fillna('UNASSIGNED').astype(str).str.strip().str.upper()

    res['Product_Code'] = df['i_code'].astype(str).str.replace('.0', '', regex=False).str.strip()
    res['Product_Name'] = df['i_name'].astype(str).str.strip().str.upper()

    if 'Category' in df.columns:
        res['Category'] = df['Category'].fillna('GENERAL').astype(str).str.strip().str.upper()
    elif 'Cat_Class_Name' in df.columns:
        res['Category'] = df['Cat_Class_Name'].fillna('GENERAL').astype(str).str.strip().str.upper()
    else:
        res['Category'] = 'GENERAL'

    if 'Manufacturer_Name' in df.columns:
        res['Manufacturer_Name'] = df['Manufacturer_Name'].fillna('UNASSIGNED').astype(str).str.strip().str.upper()
    elif 'MFG_GR_name' in df.columns:
        res['Manufacturer_Name'] = df['MFG_GR_name'].fillna('UNASSIGNED').astype(str).str.strip().str.upper()
    else:
        res['Manufacturer_Name'] = 'UNASSIGNED'

    res['Stock_Qty'] = pd.to_numeric(df['StkQty'], errors='coerce').fillna(0)
    res['Stock_Cost_Value'] = pd.to_numeric(df['StkValue'], errors='coerce').fillna(0)
    res['Stock_MRP_Value'] = 0.0

    res['Report_Month'] = month_str
    res['Account_Name'] = 'Wellness'

    print(f"  -> Wellness {month_str} processed: {len(res):,} rows")
    return res

path_may_wl = os.path.join(may_dir, "Wellness Inventory May'26.xlsx")
combined_dfs.append(process_wellness(path_may_wl, "May 2026"))

path_jun_wl = os.path.join(jun_dir, "Wellness June SOH 2026.xlsx")
combined_dfs.append(process_wellness(path_jun_wl, "June 2026"))

# ==========================================
# 4. CONCATENATE & INTERLEAVE BY ACCOUNT
# ==========================================
print("\nConcatenating and sorting all datasets...")
final_df = pd.concat(combined_dfs, ignore_index=True)

# Sort by Account_Name, Report_Month, Store_Name so Wellness, Frankross, Medplus appear interleaved
final_df = final_df.sort_values(by=['Report_Month', 'Account_Name', 'Store_Name']).reset_index(drop=True)

col_order = [
    'Report_Month', 'Account_Name', 'Store_Code', 'Store_Name', 'Pincode', 'State', 'City',
    'Product_Code', 'Product_Name', 'Category', 'Manufacturer_Name',
    'Stock_Qty', 'Stock_Cost_Value', 'Stock_MRP_Value'
]
final_df = final_df[col_order]

# Calculate Unit_Cost safely
final_df['Unit_Cost'] = np.where(
    final_df['Stock_Qty'] > 0,
    (final_df['Stock_Cost_Value'] / final_df['Stock_Qty']).round(4),
    0.0
)

# Round numeric values to 2 decimal places
final_df['Stock_Qty'] = final_df['Stock_Qty'].round(2)
final_df['Stock_Cost_Value'] = final_df['Stock_Cost_Value'].round(2)
final_df['Stock_MRP_Value'] = final_df['Stock_MRP_Value'].round(2)

print(f"\nTotal Records in Combined Dataset: {len(final_df):,} rows")
print("\nAccount Distribution:")
print(final_df.groupby(['Report_Month', 'Account_Name']).size())

# ==========================================
# 5. EXPORT TO CSV
# ==========================================
print(f"\nExporting master clean dataset to CSV: {output_csv}...")
final_df.to_csv(output_csv, index=False)

elapsed = time.time() - start_time
print(f"SUCCESS! Master Dataset created successfully in {elapsed:.2f} seconds.")
print(f"File Location: {output_csv}")
