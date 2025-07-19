# Import required modules
import requests
import pandas as pd
import plotly.express as px
import plotly.io as pio

# Set Plotly renderer for non-notebook environments
pio.renderers.default = 'browser'

# Create a request header (customize as needed)
headers = {'User-Agent': "hbirring@seattleu.edu"}

# Fetch all company tickers from the SEC website
companyTickers = requests.get("https://www.sec.gov/files/company_tickers.json", headers=headers)
companyCIK = pd.DataFrame.from_dict(companyTickers.json(), orient='index')
companyCIK['cik_str'] = companyCIK['cik_str'].astype(str).str.zfill(10)
companyCIK = companyCIK.set_index('ticker')

# Extract Alphabet's CIK
alphabet_cik = companyCIK.at['GOOGL', 'cik_str']

# Fetch company facts (financials) for Alphabet
companyFacts = requests.get(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{alphabet_cik}.json", headers=headers)

# Convert revenue facts to DataFrame
revenues = companyFacts.json()['facts']['us-gaap']['Revenues']['units']['USD']
revenues_dataframe = pd.DataFrame(revenues)
revenues_dataframe = revenues_dataframe[revenues_dataframe['frame'].notna()]  # Keep only rows with a frame

# Convert date columns and sort by end date
revenues_dataframe['end'] = pd.to_datetime(revenues_dataframe['end'])
revenues_dataframe['val'] = revenues_dataframe['val'].astype(float)
revenues_dataframe = revenues_dataframe.sort_values('end')

# --- FILTER FOR ANNUAL (10-K) DATA ONLY ---
annual_revenues = revenues_dataframe[
    (revenues_dataframe['form'] == '10-K') &
    (revenues_dataframe['frame'].str.match(r'^CY\d{4}$'))
].copy()

# --- Outlier Detection (IQR method) ---
Q1 = revenues_dataframe['val'].quantile(0.25)
Q3 = revenues_dataframe['val'].quantile(0.75)
IQR = Q3 - Q1
outliers = revenues_dataframe[
    (revenues_dataframe['val'] < (Q1 - 1.5 * IQR)) |
    (revenues_dataframe['val'] > (Q3 + 1.5 * IQR))
]
print("Revenue Outliers Detected (outside 1.5*IQR):")
if not outliers.empty:
    print(outliers[['end', 'val', 'form', 'frame']])
else:
    print("No significant revenue outliers detected.")

# --- Missing Values ---
missing = revenues_dataframe.isnull().sum()
print("\nMissing values per column:")
print(missing)
if missing.sum() == 0:
    print("No missing or null values detected in any examined columns.")

# --- Duplicates (by 'end' date) ---
duplicates = revenues_dataframe[revenues_dataframe.duplicated(subset=['end'], keep=False)]
print("\nDuplicate Entries (same period):")
if not duplicates.empty:
    print(duplicates[['end', 'val', 'accn', 'form', 'frame']])
else:
    print("No duplicate period entries detected.")

# --- Statistical Summaries (Annual Only) ---
summary_stats = annual_revenues['val'].describe()
print("Annual Revenue Statistical Summary:")
print(summary_stats)
print("\nStandard Deviation:", annual_revenues['val'].std())

# --- Visualization: Annual Revenue Line Chart ---
fig_line = px.line(
    annual_revenues,
    x='end',
    y='val',
    title='Google Annual Revenue Trend Over Time',
    labels={'end': 'Year End Date', 'val': 'Annual Revenue (USD)'}
)
fig_line.show()

# --- Visualization: Year-over-Year Annual Growth ---
annual_revenues = annual_revenues.sort_values('end').reset_index(drop=True)
annual_revenues['YoY_Growth_%'] = annual_revenues['val'].pct_change() * 100

fig_growth = px.line(
    annual_revenues,
    x='end',
    y='YoY_Growth_%',
    title='Google Year-over-Year Annual Revenue Growth',
    labels={'end': 'Year End Date', 'YoY_Growth_%': 'YoY Growth (%)'}
)
fig_growth.show()
