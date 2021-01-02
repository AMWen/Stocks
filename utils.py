# -*- coding: utf-8 -*-

# Import packages
import streamlit as st

from lxml import html, etree
import requests
import json
from collections import OrderedDict
import pandas as pd
import random
import time

from datetime import datetime, timedelta

from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from urllib.request import urlopen
from urllib.parse import urlencode
import base64

# Headers needed for requests
headers = {"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7",
    "cache-control": "max-age=0",
    "dnt": "1",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "none",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36"}


# Function to get data for specific stock ticker
@st.cache
def parse(args):
    ticker = args[0]
    bought = args[1]
    qty = args[2]
    sell_prc = args[3]
    
    # Random wait time between requests
    random_no = (random.random()-0.5)
    time.sleep(0.55+random_no)
    
    try:
        # Get company name
        url = "http://finance.yahoo.com/quote/%s/profile" % ticker
        response = requests.get(url, headers=headers, timeout=30)
        parser = html.fromstring(response.text)
        name = parser.xpath('//h3[contains(@data-reactid,"6")]//text()')[0]
        
        # Get summary table from site
        url = "http://finance.yahoo.com/quote/%s" % ticker
        response = requests.get(url, headers=headers, timeout=30)
        parser = html.fromstring(response.text)
        summary_table = parser.xpath('//div[contains(@data-test,"summary-table")]//tr')
        
        # Get additional details (current price, 1y target estimate, EPS, and earnings date)
        other_details_json_link = "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{}".format(ticker) + \
            "?modules=summaryProfile%2CfinancialData%2CrecommendationTrend%2CupgradeDowngradeHistory%2Cearnings%2CdefaultKeyStatistics%2CcalendarEvents"
        summary_json_response = requests.get(other_details_json_link)

        # Add information about purchase price and quantity
        summary_data = OrderedDict()
        summary_data.update({'Name': name,
                            'Purchase Price': bought,
                            'Quantity': qty,
                            'Desired Sell Price': sell_prc})
                            
        # Add information from summary table
        for table_data in summary_table:
            raw_table_key = table_data.xpath('.//td[1]//text()')
            raw_table_value = table_data.xpath('.//td[2]//text()')
            table_key = ''.join(raw_table_key).strip()
            table_value = ''.join(raw_table_value).strip()
            summary_data.update({table_key: table_value})
        
        # Add additional details from JSON link
        json_loaded_summary = json.loads(summary_json_response.text)
        summary = json_loaded_summary["quoteSummary"]["result"][0]
        cur_price = summary["financialData"]["currentPrice"]['raw']
        y_Target_Est = summary["financialData"]["targetMeanPrice"]['raw']
        try:
            eps = summary["defaultKeyStatistics"]["trailingEps"]['raw']
        except:
            eps = None
        
        earnings_list = summary["calendarEvents"]['earnings']
        datelist = []
        for i in earnings_list['earningsDate']:
            datelist.append(i['fmt'])
        earnings_date = ' to '.join(datelist)
            
        summary_data.update({'Current Price': cur_price, '1y Target Est': y_Target_Est,
                        'EPS (TTM)': eps, 'Earnings Date': earnings_date})
                            
        return summary_data

    except ValueError:
        return {"error": "Failed to parse json response"}
    
    except:
        return {"error": "Unhandled Error"}


# Function to sort df according to specified columns and move some columns to the front
@st.cache
def rearrange_df(df, columns, order=['% Change Cost Basis', '% Change Previous Close'], ascending=[False, True],
                 first_cols=['Name', 'Quantity', 'Purchase Price', 'Desired Sell Price', 'Current Price',
                             'Earnings', '% Change Cost Basis', '% Change Previous Close']):
    df = df.sort_values(order, ascending=ascending)
    other_cols = [col for col in columns if col not in first_cols]
    df = df[first_cols + other_cols]

    return df


# Function to organize the df
@st.cache
def organize_df(scraped_data, columns, index):
    df = pd.DataFrame(scraped_data,
                      columns=columns,
                      index=index)

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


# Function to set background red for negative values, white otherwise
def color_negative_red(val):
    try:
        color = 'tomato' if val < 0 else 'white'
    except:
        color = 'white'

    return 'background-color: %s' % color


# Function to style the df
def style_df(df, subset=['% Change Cost Basis', '% Change Previous Close'], bar=['Earnings']):
    return df.style.applymap(color_negative_red, subset=subset) \
        .bar(subset=bar, align='zero', color=['tomato', 'lightblue'])


# Function to send email containing df of interest and subject (whether daily update or a price alert)
def send_email(subject, df):
    # Gmail variables and tokens
    GOOGLE_ACCOUNTS_BASE_URL = 'https://accounts.google.com'
    GOOGLE_CLIENT_ID = '' # need to enter these
    GOOGLE_CLIENT_SECRET = ''
    GOOGLE_REFRESH_TOKEN = ''
    
    # Emails
    username = ''
    toaddr = ''
    
    # Get access token
    params = {}
    params['client_id'] = GOOGLE_CLIENT_ID
    params['client_secret'] = GOOGLE_CLIENT_SECRET
    params['refresh_token'] = GOOGLE_REFRESH_TOKEN
    params['grant_type'] = 'refresh_token'
    request_url = '%s/%s' % (GOOGLE_ACCOUNTS_BASE_URL, 'o/oauth2/token')
    response = urlopen(request_url, urlencode(params).encode('UTF-8')).read().decode('UTF-8')
    response = json.loads(response)
    access_token = response['access_token']
    
    # Get authorization string
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    
    # Set up the SMTP server
    s = SMTP(host='smtp.gmail.com', port=587)
    s.ehlo(GOOGLE_CLIENT_ID)
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
    
    styled = style_df(df).render()
    styled = styled.replace('<style', '<head><style') \
        .replace('</style>', addl_style + '</style></head>\n')
            
    # Add df in the message body as html format
    html = """<html>{0}</html>""".format(styled)
    msg.attach(MIMEText(html, 'html'))

    # Send the message
    s.send_message(msg)
    del msg
    
    # Terminate the SMTP session and close the connection
    s.quit()


# Function to get stock prices for given ticker in the past 100 days
@st.cache
def get_history(ticker):
    url = "http://finance.yahoo.com/quote/%s/history" % ticker
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
