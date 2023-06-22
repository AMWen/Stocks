# Import packages
import yaml

# Import utility functions
from utils import get_bollinger_bands, send_email

# Load config parameters
desired_stocks = yaml.load(open('config/bollinger_stocks.yml').read(), yaml.FullLoader)  # load from config file
stocks = desired_stocks['stocks']
window = desired_stocks['window']
num_stdev = desired_stocks['num_stdev']

# Get information about the Bollinger Bands and whether buy or sell signals were triggered
df, stocks_to_sell, stocks_to_buy = get_bollinger_bands(stocks, window, num_stdev)

# If any rows are identified, send an email
if len(df) > 0:
    send_email(
        'Bollinger Bands Info',
        df,
        color=['Recommend Buy', 'Recommend Sell', '% Change'],
        bar=['Std Dev Ratio', 'Buy Count', 'Sell Count'],
        other_msg=f"<b>Stocks to buy:</b> {', '.join(stocks_to_buy)}<br>"
        + f"<b>Stocks to sell:</b> {', '.join(stocks_to_sell)}<br><br>",
    )
