from pykrx import stock

def get_stock_prices(past_date, today, ticker):
    return stock.get_market_ohlcv(past_date, today, ticker)