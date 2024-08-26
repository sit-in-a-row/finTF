from pykrx import stock

def get_daily_OHLCV(start_date:str, end_date:str, stock_code:str,):
    '''
    지정된 일자 간격에 대해 OHLCV 정보를 1시간봉 기준으로 조회 후 df형태로 반환
    '''
    try:
        data = stock.get_market_ohlcv(start_date, end_date, stock_code)
        return data
    except Exception as e:
        print(f"pykrx 일자간 가격정보 Fetch 실패: {e}")
        return None