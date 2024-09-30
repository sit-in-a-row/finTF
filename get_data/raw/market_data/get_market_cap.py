import os
import pandas as pd
from pykrx import stock

def get_market_cap(year):
    '''
    연도 입력 시 해당 연도에 상장된 모든 종목의 시가총액 정보 수집
    '''
    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))

    quarters = ['Q1', 'Q2', 'Q3', 'Q4']

    for quarter in quarters:
        ticker_parent_path = f'../../../store_data/raw/market_data/price/'
        ticker_parent_path = os.path.join(current_dir, ticker_parent_path)
        tickers = os.listdir(ticker_parent_path)

        save_path = f'../../../store_data/raw/market_data/market_cap/{year}'

        # 각 분기별 시작 날짜와 종료 날짜 설정
        if quarter == 'Q1':
            start_date = f'{year}-01-01'
            end_date = f'{year}-03-31'
        elif quarter == 'Q2':
            start_date = f'{year}-04-01'
            end_date = f'{year}-06-30'
        elif quarter == 'Q3':
            start_date = f'{year}-07-01'
            end_date = f'{year}-09-30'
        elif quarter == 'Q4':
            start_date = f'{year}-10-01'
            end_date = f'{year}-12-31'

        df_list = []

        for i in range(len(tickers)):
            print(i+1, '/', len(tickers))

            ticker = tickers[i]
            df = stock.get_market_cap(start_date, end_date, ticker)
            
            # 각 티커에 해당하는 디렉터리 생성
            df_save_path = os.path.join(save_path, ticker)
            os.makedirs(df_save_path, exist_ok=True)  # 티커별 디렉터리도 생성

            if len(df) > 0:
                df.to_csv(os.path.join(df_save_path, f'{quarter}_{ticker}_market_cap.csv'))
                df_list.append(df)
            else:
                print(f'{ticker} {quarter} df가 비어있습니다.')