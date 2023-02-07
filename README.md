# Stocks
This was a quick project with web scraping to track prices of stocks of interest and send email alerts when prices go above or below certain set points.

`stocks.py` is the main document, while `params.py` and `utils.py` provides some helper variables and functions.

To use, you will need to update stocks of interest and email account credentials in `config/stocks.yml`. See [example site](https://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html) for how to obtain google client ID, secret, and refresh token.

You will also need to update `Portfolio_Positions.csv` with information for stocks you own and the desired profit % at which to sell.

This could be combined with a job scheduler such as crontab to automatically send daily digests and alerts for when trigger prices are reached. If on MacOS, you may need to [update some security and privacy settings](https://osxdaily.com/2020/04/27/fix-cron-permissions-macos-full-disk-access/) to be able to update cron jobs.

**Examples:**
- `45 9-15 * * 1-5 (cd /path/to/Stocks/folder/ && /anaconda3/bin/python stocks.py > /tmp/test.log)` to run the `stocks.py` code every hour between 9:45 am and 3:45 pm on weekdays.
- `45 9-15 * * 1-5 (cd /path/to/Stocks/folder/ && venv/bin/python bollinger_stocks.py > /tmp/test3.log)` to run the `bollinger_stocks.py` code every hour between 9:45 am and 3:45 pm on weekdays.
    - `venv` virtual environment with the required packages is created using `make setup`


## Sample email output
<img src="https://raw.githubusercontent.com/AMWen/Stocks/main/images/example.png" width="75%">


## Streamlit app

There is also a companion streamlit app for viewing the tables broken up into categories you specify (e.g., stocks you plan to keep as short-term vs. long-term investments). This can be accessed locally with `streamlit run stocks-sl.py`. It also gives a view of the stocks' performance over time. (It is normal for it to take several minutes to run the first time.)

## Algorithmic trading with Bollinger Bands

Taking the project a step further, the Bollinger Bands method was added to set up automatic alerts for when stock prices hit buy and sell points (below and above 2 standard deviations in a roling 20 day window, respectively).

`bollinger_stocks.py` is the main file, and you will need to update `config/bollinger_stocks.yml` with the stocks of interest and email account credentials (see first section on setting up the email credentials).
