import os
import pandas as pd
from pykrx import stock
from datetime import datetime, timedelta
from collections import defaultdict

def generate_monthly_date_ranges(start_date: str, end_date: str):
    # 문자열을 datetime 객체로 변환
    start_date = datetime.strptime(start_date, '%Y%m%d')
    end_date = datetime.strptime(end_date, '%Y%m%d')

    # 날짜를 월별로 저장할 딕셔너리
    monthly_dates = defaultdict(list)

    # 시작일부터 끝일까지 반복
    current_date = start_date
    while current_date <= end_date:
        # 현재 날짜의 연도와 월을 키로 사용
        key = current_date.strftime('%Y%m')
        monthly_dates[key].append(current_date.strftime('%Y%m%d'))
        # 다음 날로 이동
        current_date += timedelta(days=1)

    # 결과를 리스트 형태로 변환
    return list(monthly_dates.values())


def split_df_by_month(df):
    # 날짜 인덱스가 있는 DataFrame을 월별로 분할하여 리스트에 담음
    monthly_dfs = []
    
    # '날짜' 인덱스를 활용해 DataFrame을 그룹화
    grouped = df.groupby(pd.Grouper(freq='ME'))
    
    # 그룹화된 데이터를 월별로 분할하여 리스트에 추가
    for _, group in grouped:
        monthly_dfs.append(group)
    
    return monthly_dfs

def get_none_OHLCV_info(start_date, end_date, stock_code):
    '''
    가격정보 외 추가적인 정보 가져오는 함수

    ===========================

    1. BPS PER PBR EPS DIV DPS
    2. 거래 대금 & 거래량
    3. 외인 한도소진률

    ===========================

    '''
    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 저장 경로 부모 디렉토리의 절대 경로 생성
    store_path_parent = os.path.join(current_dir, f'../../../store_data/process/none_OHLCV_info/')

    freq = 'd'
    # BPS PER PBR EPS DIV DPS
    fin_ratio_df = stock.get_market_fundamental(start_date, end_date, stock_code, freq)
    # 외인 한도소진률
    foreign_investment_df = stock.get_exhaustion_rates_of_foreign_investment(fromdate = start_date, todate = end_date, ticker = stock_code)


    # 주식 비율 관련 정보와 거래대금/거래량 정보 구분해서 리스트에 담기
    fin_info_list = [fin_ratio_df, foreign_investment_df]

    for i in range(len(fin_info_list)):

        df_by_month = split_df_by_month(fin_info_list[i])

        for j in range(len(df_by_month)):
            target_df = df_by_month[j]

            year = df_by_month[j].index[0].year
            month = df_by_month[j].index[0].month
            target_YYYY_DD = f'{year}.{month}'

            which_type = ''

            if i==0:
                which_type = 'fin_ratio'
            elif i==1:
                which_type = 'foreign_investment'

            # 최종 저장 경로 생성
            store_path = os.path.join(store_path_parent, f'{which_type}/{stock_code}/{target_YYYY_DD}/{target_YYYY_DD}_{stock_code}.csv')

            # 디렉토리 생성 (이미 존재하는 경우 예외 처리)
            os.makedirs(os.path.dirname(store_path), exist_ok=True)

            # DataFrame을 CSV 파일로 저장
            target_df.to_csv(store_path, index=False)

            print(f'{stock_code}의 {target_YYYY_DD}에 대한 {which_type} 저장 완료')

    # 입력받은 start_date, end_date에 대해 [[일별], [일별], ...] 로 나눈 datetime 생성
    time_range = generate_monthly_date_ranges(start_date, end_date)

    # time_range 리스트는 우선 일별 날짜를 모두 모아 하나의 월을 구성함 
    # [[20240101, 20240102, ... 20240131], [20240201, 20240202, ...], ...]
    
    # 월 선택
    for day_list in time_range:

        year = day_list[0][:4]
        month = day_list[0][4:6]

        target_YYYY_DD = f'{year}.{month}'

        # 일 선택
        for k in range(len(day_list) - 1):
            transaction_start_date = day_list[k]
            transaction_end_date = day_list[k+1]

            transaction_price_df = stock.get_market_trading_value_by_investor(transaction_start_date, transaction_end_date, stock_code, etf=True, etn=True, elw=True)
            transaction_volume_df = stock.get_market_trading_volume_by_investor(transaction_start_date, transaction_end_date, stock_code, etf=True, etn=True, elw=True)

            transaction_list = [transaction_price_df, transaction_volume_df]

            for i in range(len(transaction_list)):
                
                which_type = ''
                
                if i == 0:
                    which_type = 'transaction_price'
                elif i == 1:
                    which_type = 'transaction_volume'

                # 최종 저장 경로 생성
                # ex) './transaction_price/005930/2024.01/2024.01_20240101_20240103_005930.csv'
                store_path = os.path.join(store_path_parent, f'{which_type}/{stock_code}/{target_YYYY_DD}/{target_YYYY_DD}_{transaction_start_date}_{transaction_end_date}_{stock_code}.csv')
                # 디렉토리 생성 (이미 존재하는 경우 예외 처리)
                os.makedirs(os.path.dirname(store_path), exist_ok=True)

                transaction_list[i].to_csv(store_path)

                print(f'{stock_code}의 {transaction_start_date}-{transaction_end_date}에 대한 {which_type} 저장 완료')