# Stocks
This was a quick project with web scraping to track prices of stocks of interest and send email alerts when prices go above or below certain set points.

`stocks.py` is the main document, while `params.py` and `utils.py` provides some helper variables and functions.

To use, you will need to update stocks of interest and email account credentials in `config/stocks.yml`. See [example site](https://blog.macuyiko.com/post/2016/how-to-send-html-mails-with-oauth2-and-gmail-in-python.html) for how to obtain google client ID, secret, and refresh token.

You will also need to update `Portfolio_Positions.csv` with information for stocks you own and the desired profit % at which to sell.

This could be combined with a job scheduler such as crontab to automatically send daily digests and alerts for when trigger prices are reached.

**Example:** `45 9-15 * * 1-5 (cd /path/to/Stocks/folder/ && /anaconda3/bin/python stocks.py > /tmp/test.log)` to run the `stocks.py` code every hour between 9:45 am and 3:45 pm on weekdays.


## Sample email output
<img src="https://raw.githubusercontent.com/AMWen/Stocks/main/images/example.png" width="75%">
