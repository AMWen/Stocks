import pandas as pd
import yaml
from types import SimpleNamespace


# Load config parameters (primarily desired stocks by categories)
desired_stocks = yaml.load(open('config/stocks.yml').read(), yaml.FullLoader)  # load from config file
globals().update(desired_stocks)  # convert dictionary entries into variables within a namespace

# Get owned stocks from CSV file (important columns are ['Symbol', 'Quantity', 'Cost Basis Per Share', 'Sell'])
current_stocks = pd.read_csv(filename, index_col=False)

# Only keep rows containing stock information, clean up cost format, select columns of interest, and convert to float
stocks = current_stocks[~current_stocks['Cost Basis Per Share'].isna()]
stocks['Cost Basis Per Share'] = stocks['Cost Basis Per Share'].str.replace('$','').str.replace(',','')

cols = ['Quantity', 'Cost Basis Per Share', 'Sell']
stocks[cols] = stocks[cols].astype('float')

# Convert the columns into individual lists
owned_tickers, qty, bought, sell_pct = [list(stocks[col]) for col in ['Symbol'] + cols]


# Stocks to buy (remove if already have it)
buy_list = [item for item in buy_list if item[0] not in owned_tickers]
buy_tickers, target, buy_pct = [list(item) for item in zip(*buy_list)]  # make into separate lists

# Additional stocks to track
additional = [stock for stock in set(additional) if stock not in owned_tickers + buy_tickers]  # remove any overlaps


# Combine the 3 types
n_buy = len(buy_tickers)
n = len(additional)
bought = bought + [0.0] * (n + n_buy)
qty = qty + [0.0] * (n + n_buy)

# Calculate sell_prc based on pct specified
# Mark with a negative if it's a stock to buy
sell_prc = [(1 + sell_pct[i]/100) * bought[i] for i in range(len(owned_tickers))]  # owned stocks: sell once profit exceeds specified sell %
sell_prc = sell_prc + [-(1 - buy_pct[i]/100) * target[i] for i in range(len(buy_list))]  # want to buy stocks: buy once price falls below specified % profit desired
sell_prc = sell_prc + [10000] * n  # additional stocks: just track so set trigger point to be really high
