# -*- coding: utf-8 -*-

# Import packages
import base64
import json
import random
import time
from collections import OrderedDict
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from multiprocessing.pool import ThreadPool
from smtplib import SMTP
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd
import requests
import streamlit as st
import yfinance as yf
from lxml import etree, html

from params import access_token_params, toaddr, username

# Headers needed for requests
headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
    "cache-control": "max-age=0",
    "dnt": "1",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36",
}


# Function to get data for specific stock ticker
def parse(args):
    ticker, qty, bought, sell_pct, sell_prc = args

    # Random wait time between requests
    random_no = random.random() - 0.5
    time.sleep(0.55 + random_no)

    try:
        # Get company name and summary table from site
        url = f"http://finance.yahoo.com/quote/{ticker}"
        response = requests.get(url, headers=headers, timeout=30)
        parser = html.fromstring(response.text)

        # Title looks like 'Bank of America Corporation (BAC) Stock Price, News, Quote & History - Yahoo Finance'
        name = parser.xpath('//title[1]/text()')[0].split(' (')[:-1]  # find name from <title>
        name = ' ('.join(name)  # rejoin for any parentheses in actual name
        summary_table = parser.xpath(
            '//div[contains(@data-test,"summary-table")]//tr'
        )  # find <div> where data-test contains "summary-table"

        # Add information about purchase price and quantity
        summary_data = OrderedDict()
        summary_data.update(
            {
                'Name': name,
                'Purchase Price': bought,
                'Quantity': qty,
                'Sell Pct': sell_pct,
                'Sell/Buy Price': sell_prc,
            }
        )

        # Add information from summary table
        for table_data in summary_table:
            raw_table_key = table_data.xpath('.//td[1]//text()')
            raw_table_value = table_data.xpath('.//td[2]//text()')
            table_key = ''.join(raw_table_key).strip()
            table_value = ''.join(raw_table_value).strip()
            summary_data.update({table_key: table_value})

        # Get additional details (current price, 1y target estimate, EPS, and earnings date)
        other_details_json_link = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{ticker}?modules=summaryProfile%2CfinancialData"  # can play around with the various modules
        summary_json_response = requests.get(other_details_json_link, headers=headers, timeout=30)

        # Add additional details from JSON link
        try:
            json_loaded_summary = json.loads(summary_json_response.text)
            cur_price = json_loaded_summary["quoteSummary"]["result"][0]["financialData"]["currentPrice"]['raw']
        except Exception:
            print("Error with loading additional details")
            cur_price = summary_data['Bid'].split(' x ')[0]

        summary_data.update({'Current Price': cur_price})

        return summary_data

    except ValueError:
        return {"error": "Failed to parse json response"}

    except Exception:
        return {"error": "Unhandled Error"}


# Function to sort df according to specified columns and move some columns to the front
def rearrange_df(
    df,
    columns,
    order=['% Change Cost Basis', '% Change Previous Close'],
    ascending=[False, True],
    first_cols=[
        'Name',
        'Quantity',
        'Purchase Price',
        'Sell Pct',
        'Sell/Buy Price',
        'Current Price',
        'Earnings',
        '% Change Cost Basis',
        '% Change Previous Close',
    ],
):
    df = df.sort_values(order, ascending=ascending)
    other_cols = [col for col in columns if col not in first_cols]
    df = df[first_cols + other_cols]

    return df


# Function to organize the df
def organize_df(scraped_data, columns, index):
    df = pd.DataFrame(scraped_data, columns=columns, index=index)

    # Convert columns to float
    convert = ['Previous Close', 'Open']
    df[convert] = df[convert].fillna('0.001')
    df[convert] = df[convert].applymap(lambda x: x.replace(',', '')).astype(float)

    # Add columns to calculate earnings and % change
    df['Cost Basis'] = df['Purchase Price'] * df['Quantity']
    df['Current Value'] = df['Current Price'] * df['Quantity']
    df['Earnings'] = df['Current Value'] - df['Cost Basis']
    df['% Change Cost Basis'] = df['Earnings'] / df['Cost Basis'] * 100
    df['% Change Previous Close'] = (df['Current Price'] - df['Previous Close']) / df['Previous Close'] * 100

    # Order by stocks doing the best to the worst and rearrange the columns
    df = rearrange_df(df, columns)

    return df


# Function to parse the data from Yahoo then organize into a df
@st.cache
def scrape_data(df, threads):
    cols = ['Symbol', 'Quantity', 'Cost Basis Per Share', 'Sell Pct', 'Sell/Buy Price']
    with ThreadPool(threads) as p:
        scraped_data = list(p.map(parse, df[cols].to_numpy().tolist()))
    columns = list(scraped_data)[0]

    # Organize into pandas df
    df = organize_df(scraped_data, columns, list(df['Symbol']))

    return df


# Function to parse data from Yahoo and create upper and lower bounds for Bollinger Bands
def get_bollinger_bands(stocks, window, num_stdev):
    # Get stock information
    df_stocks = yf.download(stocks, period="3mo").reset_index()
    df_closing_prices = df_stocks['Close'].reset_index(drop=True)

    # Calculate moving average and upper and lower bounds
    SMA = df_closing_prices.rolling(window).mean()
    STDEV = df_closing_prices.rolling(window).std()
    UB = SMA + (num_stdev * STDEV)
    LB = SMA - (num_stdev * STDEV)

    # Add information about current price, moving average, and std dev to moving average ratio
    last_day = SMA.index[-1]
    df_counts = pd.concat(
        {
            'Current Price': df_closing_prices[-1:].T[last_day],
            'Avg Price': SMA[-1:].T[last_day],
            '# Std Dev': (df_closing_prices[-1:].T[last_day] - SMA[-1:].T[last_day]) / STDEV[-1:].T[last_day],
            'Two Std Dev': 2 * STDEV[-1:].T[last_day],
            'Std Dev Ratio': 2 * STDEV[-1:].T[last_day] / SMA[-1:].T[last_day],
            '% Change': round((df_closing_prices.iloc[-1] / df_closing_prices.iloc[-2] - 1) * 100, 2).astype(str),
        },
        axis=1,
    )

    # Compare closing prices to upper and lower bounds in the past 10 days
    df_sell = (df_closing_prices - UB >= 0)[-10:].T
    df_buy = (LB - df_closing_prices >= 0)[-10:].T

    # Get count of times a buy or sell signal was triggered in the past 10 days
    df_counts['Sell Count'] = df_sell.sum(axis=1)
    df_counts['Buy Count'] = df_buy.sum(axis=1)

    # Get recommendation for last closing price (current price)
    df_counts['Recommend Sell'] = df_sell[last_day]
    df_counts['Recommend Buy'] = df_buy[last_day]

    # Limit to stocks where the buy or sell recommendation count is > 0 and sort
    df_counts = df_counts.query('`Sell Count` > 0 or `Buy Count` > 0').sort_values(
        ['Recommend Buy', 'Recommend Sell', '# Std Dev', 'Std Dev Ratio', 'Sell Count', 'Buy Count'],
        ascending=False,
    )
    stocks_to_sell = list(df_counts.query('`Recommend Sell` == True').index)
    stocks_to_buy = list(df_counts.query('`Recommend Buy` == True').index)

    # Force the formatting to be 2 decimal places (more digits get printed when rounding is used)
    for col in ['Current Price', 'Avg Price', 'Two Std Dev', '# Std Dev']:
        df_counts[col] = df_counts[col].map('{:.2f}'.format)

    return df_counts, stocks_to_sell, stocks_to_buy


# Function to set background red for negative values, white otherwise
def color_negative_red(val):
    try:
        val = float(val)  # convert strings

        if val < 0:
            color = 'tomato'
        elif val > 0:
            color = 'lightgreen'
        else:
            color = 'white'

    except Exception:
        color = 'white'

    return 'background-color: %s' % color


# Function to style the df
def style_df(df, color=['% Change Cost Basis', '% Change Previous Close'], bar=['Earnings']):
    return df.style.applymap(color_negative_red, subset=color).bar(
        subset=bar, align='zero', color=['tomato', 'lightblue']
    )


# Function to send email containing df of interest and subject (whether daily update or a price alert)
def send_email(
    subject,
    df_dict,
    color=['% Change Cost Basis', '% Change Previous Close'],
    bar=['Earnings'],
    other_msg='',
):
    # Get access token
    request_url = f"{access_token_params['base_url']}/o/oauth2/token"
    response = urlopen(request_url, urlencode(access_token_params).encode('UTF-8')).read().decode('UTF-8')
    response = json.loads(response)
    access_token = response['access_token']

    # Get authorization string
    auth_string = f'user={username}\1auth=Bearer {access_token}\1\1'
    auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')

    # Set up the SMTP server
    s = SMTP(host='smtp.gmail.com', port=587)
    s.ehlo(access_token_params['client_id'])
    s.starttls()
    s.docmd('AUTH', 'XOAUTH2 ' + auth_string)

    # Create message
    msg = MIMEMultipart()

    # Set up the parameters of the message
    msg['From'] = 'Python'
    msg['To'] = toaddr
    msg['Subject'] = subject

    # Style df and add css style portion to be between <head></head> tags
    addl_style = """\ntable, th, td {border: 0px solid black; background-color: #eee; padding: 0px;}
        th {background-color: lightblue; color: black; text-align: center;}
        td {background-color: #fff; padding: 10px; text-align: center;}"""

    html = ""
    for df_segment in df_dict:
        df = df_dict[df_segment]
        styled = style_df(df, color, bar).to_html()

        # Add df in the message body as html format
        html += f"""<b>{df_segment}:</b> <br>{styled}<br>"""

    html = f"""<html><head>{other_msg}</head>{html}</html>""".replace('<style', '<head><style').replace(
        '</style>', addl_style + '</style></head>\n'
    )
    msg.attach(MIMEText(html, 'html'))

    # Send the message
    s.send_message(msg)
    del msg

    # Terminate the SMTP session and close the connection
    s.quit()


# Function to get stock prices for given ticker in the past 100 days
@st.cache
def get_history(ticker):
    url = f"http://finance.yahoo.com/quote/{ticker}/history"
    response = requests.get(url, headers=headers, timeout=30)
    parser = html.fromstring(response.text)
    table = parser.xpath('//table')  # javascript limits this to 100 entries
    table_tree = etree.tostring(table[0], method='xml')
    history = pd.read_html(table_tree)[0][:-1]

    # Remove rows containing dividend or other random information
    history = history[~history['Close*'].str.contains(' ')]

    # Convert formats
    history['Date'] = pd.to_datetime(history['Date'])
    history['Close*'] = history['Close*'].astype('float')

    return history
