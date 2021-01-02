# Import packages
from multiprocessing.pool import ThreadPool
import pandas as pd
import time
from datetime import datetime

# Import parameters and utility functions
from params import owned_tickers, buy_tickers, additional, bought, qty, sell_prc
from utils import style_df, parse, organize_df, send_email


update = False

# Parse the data
args = (owned_tickers + buy_tickers + additional, bought, qty, sell_prc)
with ThreadPool(5) as p:
    scraped_data = list(p.map(parse, list(zip(*args))))
columns = list(scraped_data)[0]

# Organize into pandas df
df = organize_df(scraped_data, columns, owned_tickers + buy_tickers + additional)


# Send summary in the morning (automatic runs scheduled for 9:45 and hourly after that)
now = datetime.now().strftime("%H:%M")  # current time
print(now)  # Log of when last update was
if (now < '10:00') or (now > '15:00') or (update):  # send update if before 10 am or after 3 pm or if requested
    send_email('Daily Update', df)


# Additionally, send alert if:
# 1) price dips below X% (margin) of previous close
# 2) price dips below X% (margin) of price at which stock was bought
# 3) price is above desired sell price
# 4) price is below desired buy price
# Get all rows where this is true
margin = -4
df_send = df[(df['% Change Previous Close'] < margin) |
             (df['% Change Cost Basis'] < margin) |
             ((df['Current Price'] > df['Desired Sell Price']) & (df['Desired Sell Price'] > 0)) |
             ((df['Current Price'] < -df['Desired Sell Price']) & (df['Desired Sell Price'] < 0)) ]

# If any rows are identified, send an email
if len(df_send) > 0:
    send_email('Price Alert', df_send)
