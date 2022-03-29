# Import packages
from datetime import datetime, timedelta
import pandas as pd

import streamlit as st
import altair as alt

# Import parameters and utility functions
from params import stocks, threads, margin, long_term, short_term, buy_asap, sell_asap
from utils import style_df, scrape_data, get_history, rearrange_df


# Scrape and parse the data
df = scrape_data(stocks, threads)


# Display df
st.text('Stocks overview')
st.dataframe(style_df(df, bar=[]))

st.text('Stocks with > 4% dip')
df_dip = df[(df['% Change Previous Close'] < margin) | (df['% Change Cost Basis'] < margin)]
st.dataframe(style_df(df_dip, bar=[]))

st.text('Stocks below desired buy price')
df_buy = df[(df['Current Price'] < df['Sell/Buy Price']) & (df['Sell Pct'] < 0)]
st.dataframe(style_df(df_buy, bar=[]))

st.text('Stocks above desired sell price')
df_sell = df[(df['Current Price'] > df['Sell/Buy Price']) & (df['Sell Pct'] > 0)]
st.dataframe(style_df(df_sell, bar=[]))

st.text('Short-term stocks')
all_tickers = list(df.index)
short_term = [x for x in short_term if x in all_tickers]
df = df.sort_index()
df_dip = df[df.index.isin(short_term)]
st.dataframe(style_df(df_dip, bar=[]))

st.text('Earnings or dividends in next month')
start = datetime.today()
end = start + timedelta(30)
df_tmp = df.copy()
df_tmp['Ex-Dividend Date'] = pd.to_datetime(df_tmp['Ex-Dividend Date'], format='%b %d, %Y', errors='coerce')
df_tmp['Earnings Date'] = pd.to_datetime(df['Earnings Date'].str.slice(stop=10), format='%Y-%m-%d', errors='coerce')
df_soon = df_tmp[((df_tmp['Ex-Dividend Date'] > start) & (df_tmp['Ex-Dividend Date'] < end)) |
                 ((df_tmp['Earnings Date'] > start) & (df_tmp['Earnings Date'] < end))]

df_soon = rearrange_df(df_soon, df_soon.columns, 'Ex-Dividend Date', True, ['Name', 'Ex-Dividend Date', 'Earnings Date', 'Forward Dividend & Yield'])
st.dataframe(style_df(df_soon, bar=[]))

st.text('Buy ASAP stocks')
buy_asap = [x for x in buy_asap if x in all_tickers]
df_buy = df[df.index.isin(buy_asap)]
st.dataframe(style_df(df_buy, bar=[]))

st.text('Sell ASAP stocks')
sell_asap = [x for x in sell_asap if x in all_tickers]
df_sell = df[df.index.isin(sell_asap) & (df['Quantity'] > 0)]
st.dataframe(style_df(df_sell, bar=[]))

st.text('Long-term stocks')
long_term = [x for x in long_term if x in all_tickers]
df_long = df[df.index.isin(long_term) & (df['Quantity'] > 0)]
st.dataframe(style_df(df_long, bar=[]))

st.text('See past history')
for ticker in [st.selectbox('Stock of interest', all_tickers)] + all_tickers:
    st.text(ticker)
    history = get_history(ticker)

    # Plot on altair chart
    min = history['Close*'].min()
    max = history['Close*'].max()
    line = alt.Chart(history).mark_line().encode(x='Date',
                                                 y=alt.Y('Close*', scale=alt.Scale(domain=(min*.98, max*1.02))),
                                                 tooltip=['Date', 'Close*'])

    # Create a selection that chooses the nearest point & selects based on x-value
    nearest = alt.selection(type='single', nearest=True, on='mouseover', fields=['Date'], empty='none')

    # Transparent selectors across the chart to give x-value of the cursor
    selectors = alt.Chart(history).mark_point().encode(x='Date', opacity=alt.value(0)).add_selection(nearest)

    # Draw points on the line, and highlight based on selection
    points = line.mark_point().encode(opacity=alt.condition(nearest, alt.value(1), alt.value(0)))

    # Draw text labels near the points, and highlight based on selection
    text = line.mark_text(align='left', dx=-20, dy=-15).encode(text=alt.condition(nearest, 'Close*', alt.value(' ')))

    # Draw a rule at the location of the selection
    rules = alt.Chart(history).mark_rule(color='gray').encode(x='Date').transform_filter(nearest)

    # Put the five layers into a chart and bind the data
    c = alt.layer(line, selectors, points, rules, text).properties(width=900, height=500, title=ticker)
    st.write(c)
