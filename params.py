import pandas as pd
import yaml

# Load config parameters (primarily desired stocks by categories)
desired_stocks = yaml.load(open('config/stocks.yml').read(), yaml.FullLoader)  # load from config file
globals().update(desired_stocks)  # convert dictionary entries into variables within a namespace

# Get owned stocks from CSV file (important columns are ['Symbol', 'Quantity', 'Cost Basis Per Share', 'Sell Pct'])
current_stocks = pd.read_csv(filename, index_col=False)

# Only keep rows containing stock information, clean up cost format, select columns of interest, and convert to float
stocks = current_stocks[~current_stocks['Cost Basis Per Share'].isna()]
stocks['Cost Basis Per Share'] = (
    stocks['Cost Basis Per Share'].str.replace('$', '', regex=False).str.replace(',', '', regex=False)
)

cols = ['Quantity', 'Cost Basis Per Share', 'Sell Pct']
stocks = stocks[['Symbol'] + cols]
stocks[cols] = stocks[cols].astype('float')


# Stocks to buy (remove if already have it)
owned_tickers = list(stocks['Symbol'])
buy_list = [item for item in buy_list if item[0] not in owned_tickers]
buy_tickers, target, buy_pct = [list(item) for item in zip(*buy_list)]  # make into separate lists

# Additional stocks to track
additional = [stock for stock in set(additional) if stock not in owned_tickers + buy_tickers]  # remove any overlaps


# Combine the 3 types
stocks = pd.concat(
    [
        stocks,
        pd.DataFrame(buy_list, columns=['Symbol', 'Cost Basis Per Share', 'Sell Pct']),
        pd.DataFrame(additional, columns=['Symbol']),
    ],
    ignore_index=True,
    sort=False,
).fillna(0)

stocks['Sell/Buy Price'] = (1 + stocks['Sell Pct'] / 100) * stocks['Cost Basis Per Share']
stocks.loc[stocks['Sell Pct'] == 0, 'Sell/Buy Price'] = 10000
