import pandas as pd

# Stock categories
long_term = ['SLB']  # hold on
short_term = ['PLTR']  # buy when there's a dip
buy_asap = ['BAC']
sell_asap = ['ZM']

# Get owned stocks from CSV file (important columns are ['Quantity', 'Cost Basis Per Share', 'Sell'])
stocks = pd.read_csv('/Users/amywen/Insight/Stocks/Portfolio_Positions.csv', index_col=False)

# Only keep rows containing stock information, select columns of interest, and convert to float
stocks = stocks[~stocks['Cost Basis Per Share'].isna()]
cols = ['Quantity', 'Cost Basis Per Share', 'Sell']
stocks['Cost Basis Per Share'] = stocks['Cost Basis Per Share'].str.replace('$','').str.replace(',','')
stocks[cols] = stocks[cols].astype('float')
owned_tickers, qty, bought, sell_pct = [list(stocks[col]) for col in ['Symbol'] + cols]

# Want to buy stocks: ticker, target sell price, buy % (if fall X% from target sell price)
buy_list = [item for item in
            [('TSLA', 445, 15)]
            if item[0] not in owned_tickers]
buy_tickers, target, buy_pct = [list(item) for item in zip(*buy_list)]  # make into separate lists

# Stocks to track
additional = ['INTC']
additional = [stock for stock in set(additional) if stock not in owned_tickers + buy_tickers]  # remove any overlaps

# Combine the 3 types
n_buy = len(buy_tickers)
n = len(additional)
bought = bought + [0.0] * (n + n_buy)
qty = qty + [0.0] * (n + n_buy)

# Calculate sell_prc based on pct specified
# Mark with a negative if it's a stock I want to buy
sell_prc = [(1 + sell_pct[i]/100) * bought[i] for i in range(len(owned_tickers))]  # owned stocks
sell_prc = sell_prc + [-(1 - buy_pct[i]/100) * target[i] for i in range(len(buy_list))] # want to buy stocks
sell_prc = sell_prc + [10000] * n  # additional stocks
