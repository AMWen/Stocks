# Import packages
import yaml

# Import utility functions
from utils import get_bollinger_bands, send_email

# Load config parameters
desired_stocks = yaml.load(open('config/bollinger_stocks.yml').read(), yaml.FullLoader)  # load from config file
df_dict = {}
stocks_to_sell = []
stocks_to_buy = []
for stock_type in desired_stocks:
    stocks = desired_stocks[stock_type]['stocks']
    window = desired_stocks[stock_type]['window']
    num_stdev = desired_stocks[stock_type]['num_stdev']

    # Get information about the Bollinger Bands and whether buy or sell signals were triggered
    _df, _stocks_to_sell, _stocks_to_buy = get_bollinger_bands(stocks, window, num_stdev)

    # If any rows are identified, add to summary
    if len(_df) > 0:
        df_dict[stock_type] = _df
        stocks_to_sell.extend(_stocks_to_sell)
        stocks_to_buy.extend(_stocks_to_buy)

# If any dfs are identified, send an email
if len(df_dict) > 0:
    send_email(
        'Bollinger Bands Info',
        df_dict,
        color=['Recommend Buy', 'Recommend Sell', '% Change'],
        bar=['Std Dev Ratio', 'Buy Count', 'Sell Count'],
        other_msg=f"<b>Stocks to buy:</b> {', '.join(stocks_to_buy)}<br>"
        + f"<b>Stocks to sell:</b> {', '.join(stocks_to_sell)}<br><br>",
    )
