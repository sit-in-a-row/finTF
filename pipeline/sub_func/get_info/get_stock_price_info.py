import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, '../../../store_data/process/market_data/price/')

available_ticker_list = os.listdir(path)
OHLCV_df_columns = [
    'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Delta', 'MA_20',
    'RSI_14', 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0'
]

def stock_price_info(ticker: str, start_date: str, end_date: str) -> pd.DataFrame:
    '''
    종목코드, 시작일, 종료일을 파라미터로 입력하면

    'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Delta', 'MA_20',
    'RSI_14', 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0'

    다음 컬럼에 해당하는 정보를 반환함.
    '''
    if ticker in available_ticker_list:
        # 경로 설정
        df_path = os.path.join(path, ticker)
        csv_path = os.path.join(df_path, f'{ticker}_indicators.csv')

        # CSV 파일 읽기
        df = pd.read_csv(csv_path, index_col=0)
        df.columns = OHLCV_df_columns  # 컬럼 이름 재설정

        # 날짜 컬럼을 datetime으로 변환 후 인덱스로 설정
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        # 시작일과 종료일 사이 데이터 필터링
        return_df = df.loc[start_date:end_date]

        return return_df
    else:
        print(f'{ticker}에 해당하는 가격 정보를 찾을 수 없습니다!')
        return None