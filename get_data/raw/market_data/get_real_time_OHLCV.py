import yfinance as yf
from datetime import datetime, time

def get_real_time_OHLCV(stock_code):
    '''
    yfinance에서 현재 시간 기준으로 호출된 날짜의 개장 후 5분봉 데이터를 실시간으로 조회 후 반환
    '''
    try:
        # 종목 코드를 yfinance 형식에 맞게 변환
        stock_code = f'{stock_code}.KS'

        # 현재 시간
        end_time = datetime.now()

        # 당일 개장 시각 (오전 9시)
        market_open_time = datetime.combine(end_time.date(), time(9, 0))

        # 현재 시간이 개장 전일 경우 예외 처리
        if end_time < market_open_time:
            raise ValueError("시장이 아직 개장하지 않았습니다.")

        # 데이터 다운로드
        data = yf.download(stock_code, start=market_open_time, end=end_time, interval='5m')

        if len(data) < 1:
            print('yfinance 데이터 조회는 성공하였으나, 데이터가 존재하지 않습니다.')
            return None

        return data
    
    except Exception as e:
        print(f"yfinance 실시간 데이터 Fetch 실패: {e}")
        return None