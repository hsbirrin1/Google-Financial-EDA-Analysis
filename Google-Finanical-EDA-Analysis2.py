
import requests 
import pandas as pd 
import matplotlib.pyplot as plt

# config of the connection via CIK number 
CIK_googl = '0001652044' # Googl Alphabet Inc. 
headers = {'User-Agent': "hbirring@seattleu.edu"}

url = f'http://data.sec.gov/api/xbrl/companyfacts/CIK{CIK_googl.zfill(10)}.json'
companyFacts = requests.get(url, headers=headers).json()

#tag the data
def get_tag_df(tag):
    try:
        return pd.DataFrame(companyFacts['facts']['us-gaap'][tag]['units']['USD'])
    except KeyError:
        return pd.DataFrame(columns=['accn', 'end', 'val', 'form', 'fy'])
    
#load the dataframes
revenues_df = get_tag_df('Revenues')
net_income_df = get_tag_df('NetIncomeLoss')
cost_of_revenue_df = get_tag_df('CostOfRevenue')

# Load balance sheet dataframes for ratios
current_assets_df = get_tag_df('AssetsCurrent')
current_liabilities_df = get_tag_df('LiabilitiesCurrent')
inventory_df = get_tag_df('InventoryNet')
total_liabilities_df = get_tag_df('Liabilities')
total_equity_df = get_tag_df('StockholdersEquity')

# filter the dataframes for the 10-k filings
revenues_df = revenues_df[revenues_df['form'] == '10-K']
net_income_df = net_income_df[net_income_df['form'] == '10-K']
cost_of_revenue_df = cost_of_revenue_df[cost_of_revenue_df['form'] == '10-K']
current_assets_df = current_assets_df[current_assets_df['form'] == '10-K']
current_liabilities_df = current_liabilities_df[current_liabilities_df['form'] == '10-K']
inventory_df = inventory_df[inventory_df['form'] == '10-K']
total_liabilities_df = total_liabilities_df[total_liabilities_df['form'] == '10-K']
total_equity_df = total_equity_df[total_equity_df['form'] == '10-K']

# get the most recent filings
revenues_df = revenues_df.sort_values('end').drop_duplicates('accn', keep= 'last')
net_income_df = net_income_df.sort_values('end').drop_duplicates('accn', keep= 'last')
cost_of_revenue_df = cost_of_revenue_df.sort_values('end').drop_duplicates('accn', keep= 'last')
current_liabilities_df = current_liabilities_df.sort_values('end').drop_duplicates('accn', keep='last')
inventory_df = inventory_df.sort_values('end').drop_duplicates('accn', keep='last')
total_liabilities_df = total_liabilities_df.sort_values('end').drop_duplicates('accn', keep='last')
total_equity_df = total_equity_df.sort_values('end').drop_duplicates('accn', keep='last')

#merge all dataframes on 'accn' and 'end' columns
df = revenues_df[['accn', 'end', 'val']].rename(columns={'val': 'revenue'})
df = df.merge(net_income_df[['accn', 'end', 'val']].rename(columns={'val': 'net_income'}), on=['accn', 'end'])
df = df.merge(cost_of_revenue_df[['accn', 'end', 'val']].rename(columns={'val': 'cost_of_revenue'}), on=['accn', 'end'])
df = df.merge(current_assets_df[['accn', 'end', 'val']].rename(columns={'val': 'current_assets'}), on=['accn','end'], how='left')
df = df.merge(current_liabilities_df[['accn', 'end', 'val']].rename(columns={'val': 'current_liabilities'}), on=['accn','end'], how='left')
df = df.merge(inventory_df[['accn', 'end', 'val']].rename(columns={'val': 'inventory'}), on=['accn','end'], how='left')
df = df.merge(total_liabilities_df[['accn', 'end', 'val']].rename(columns={'val': 'total_liabilities'}), on=['accn','end'], how='left')
df = df.merge(total_equity_df[['accn', 'end', 'val']].rename(columns={'val': 'total_equity'}), on=['accn','end'], how='left')

# calculate the net profit & gross profit margins 
df['gross_profit'] = df['revenue'] - df['cost_of_revenue']
df['gross_profit_margin'] = df['gross_profit'] / df['revenue']
df['net_profit_margin'] = df['net_income'] / df['revenue']

df['quick_assets'] = df['current_assets'] - df['inventory']
df['current_ratio'] = df['current_assets'] / df['current_liabilities']
df['quick_ratio'] = (df['current_assets'] - df['inventory']) / df['current_liabilities']
df['debt_to_equity'] = df['total_liabilities'] / df['total_equity']

#print out the results 
print(df[['end', 'revenue', 'net_income', 'cost_of_revenue', 'gross_profit', 
          'gross_profit_margin', 'net_profit_margin', 
          'current_assets', 'current_liabilities', 'inventory',
          'current_ratio', 'quick_ratio', 'debt_to_equity']])


# Sort for plotting
df = df.sort_values('end')

# Plot the ratios
plt.figure(figsize=(16,10))

plt.subplot(311)
plt.plot(df['end'], df['current_ratio'], marker='o', label='Current Ratio')
plt.title('Current Ratio')
plt.ylabel('Current Ratio')
plt.xticks(rotation=45)
plt.legend()

plt.subplot(312)
plt.plot(df['end'], df['quick_ratio'], marker='o', color='orange', label='Quick Ratio')
plt.title('Quick Ratio')
plt.ylabel('Quick Ratio')
plt.xticks(rotation=45)
plt.legend()

plt.subplot(313)
plt.plot(df['end'], df['debt_to_equity'], marker='o', color='green', label='Debt-to-Equity')
plt.title('Debt-to-Equity Ratio')
plt.ylabel('D/E Ratio')
plt.xticks(rotation=45)
plt.legend()

plt.tight_layout()
plt.show()
