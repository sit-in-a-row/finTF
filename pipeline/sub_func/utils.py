import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import re
from pykrx import stock

current_dir = os.path.dirname(os.path.abspath(__file__))

# 데이터 경로 설정
price_data_path = os.path.join(current_dir, '../../store_data/raw/market_data/price')
corp_in_index_path = os.path.join(current_dir, '../../store_data/raw/market_data')
index_OHLCV_path = os.path.join(current_dir, '../../store_data/raw/market_data')
interest_rate_data_path = os.path.join(current_dir, '../../store_data/raw/market_data/interest_rate_data')
fin_report_path = os.path.join(current_dir, '../../store_data/raw/opendart/store_reports')

quarter_map = {
    'Q1': [1, 2, 3],
    'Q2': [4, 5, 6],
    'Q3': [7, 8, 9],
    'Q4': [10, 11, 12]
}

# 0. util 함수들 정의
def calculate_cumulative_returns(df):
    '''
    Close열 기준, 가격 기반 누적 수익률 계산해서 'Return' 컬럼 더해주는 함수
    '''
    # DataFrame의 복사본 생성
    df = df.copy()

    # 일별 수익률 계산
    df['Return'] = df['Close'].pct_change().fillna(0)

    # 누적 수익률 계산
    df['Cumulative_Return'] = (1 + df['Return']).cumprod() - 1

    return df

# 1. 개별 종목 OHLCV 데이터 로드
def get_corp_OHLCV(ticker, year, month_or_quarter) -> pd.DataFrame:
    '''
    종목 코드와 연도, 월 또는 분기(Q1, Q2, Q3, Q4)를 입력하면 해당 종목의 OHLCV 데이터를 DB에서 탐색 후 df로 반환.
    만약 분기를 선택하면 해당 분기에 해당하는 월의 데이터를 묶어서 반환.
    '''
    try:
        OHLCV_df_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Delta']
        combined_df = pd.DataFrame()

        # 분기 데이터 로드
        if month_or_quarter in quarter_map:
            months = quarter_map[month_or_quarter]
            for month in months:
                df_path = os.path.join(price_data_path, ticker, f'{year}.{str(month).zfill(2)}', f'{year}.{str(month).zfill(2)}_{ticker}.csv')
                if os.path.exists(df_path):
                    monthly_df = pd.read_csv(df_path)
                    monthly_df.columns = OHLCV_df_columns
                    monthly_df.set_index('Date', inplace=True)
                    combined_df = pd.concat([combined_df, monthly_df], axis=0)
                else:
                    print(f'{df_path} 파일을 찾을 수 없습니다.')

        # 개별 월 데이터 로드
        else:
            df_path = os.path.join(price_data_path, ticker, f'{year}.{month_or_quarter}', f'{year}.{month_or_quarter}_{ticker}.csv')
            if os.path.exists(df_path):
                combined_df = pd.read_csv(df_path)
                combined_df.columns = OHLCV_df_columns
                combined_df.set_index('Date', inplace=True)
            else:
                print(f'{df_path} 파일을 찾을 수 없습니다.')

        # 누적 수익률 계산
        if not combined_df.empty:
            combined_df = calculate_cumulative_returns(combined_df)
        
        return combined_df
    
    except Exception as e:
        print(f'get_corp_OHLCV 함수 오류: {e}')
        return None

# 2. 인덱스 지표의 OHLCV 데이터 로드
def get_index_OHLCV(index_name, year, quarter) -> pd.DataFrame:
    '''
    인덱스 정보 넣으면 df로 반환
    '''
    # 파일명에서 공백 및 특수 문자 변환
    # cleansed_index_name = index_name.replace(' ', '_')
    # cleansed_index_name = cleansed_index_name.replace('/', '_')

    # 파일명에서 공백 및 특수 문자 변환
    # index_name = index_name.replace(' ', '_')
    # index_name = index_name.replace('/', '_')

    # CSV 파일 경로 설정
    index_df_path = os.path.join(index_OHLCV_path, index_name, year, f'{year}_{index_name}.csv')
    index_df = pd.read_csv(index_df_path)

    # 컬럼 설정
    index_df_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Transaction_Val', 'Market_Cap']
    index_df.columns = index_df_columns

    # Date 컬럼을 datetime 형식으로 변환하고 인덱스로 설정
    index_df['Date'] = pd.to_datetime(index_df['Date'])
    index_df.set_index('Date', inplace=True)

    try:
        int(quarter)
        try:
            quarter = int(quarter)
            # 주어진 start_date와 end_date로 필터링
            if 1 <= quarter <= 12:
                start_date = f'{year}-{quarter:02d}-01'
                end_date = f'{year}-{quarter:02d}-{pd.Period(f"{year}-{quarter:02d}").days_in_month}'
            
                # 주어진 start_date와 end_date로 필터링
                filtered_df = index_df.loc[start_date:end_date]
                filtered_df = calculate_cumulative_returns(filtered_df)

                return filtered_df
            else:
                raise ValueError("유효한 월을 입력하세요 (1-12).")

        except Exception as e:
            print(f'인덱스 지표 가격을 요청하는 과정에서 오류가 발생했습니다: {e}')
            return None

    except:
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

        try:
            # 주어진 start_date와 end_date로 필터링
            filtered_df = index_df.loc[start_date:end_date]
            filtered_df = calculate_cumulative_returns(filtered_df)

            return filtered_df
        except Exception as e:
            print(f'인덱스 지표 가격을 요청하는 과정에서 오류가 발생했습니다: {e}')
            return None

# 3. 채권 데이터 로드
def get_bond(year, quarter) -> pd.DataFrame:
    '''
    연도와 분기를 입력하면 해당 시점의 한국 국채 10년물 수익률을 DB에서 탐색 후 df로 반환
    '''
    bond_df_path = os.path.join(interest_rate_data_path, year, f'{year}_korea_bond_yield.csv')
    bond_df_columns = ['Date', 'Bond_Yield', 'Return']

    bond_df = pd.read_csv(bond_df_path)
    bond_df.columns = bond_df_columns
    bond_df.set_index('Date', inplace=True)

    try:
        int(quarter)
        quarter = int(quarter)
        # 주어진 start_date와 end_date로 필터링
        if 1 <= quarter <= 12:
            start_date = f'{year}-{quarter:02d}-01'
            end_date = f'{year}-{quarter:02d}-{pd.Period(f"{year}-{quarter:02d}").days_in_month}'
        
            # 주어진 start_date와 end_date로 필터링
            bond_df = bond_df.loc[start_date:end_date]
            return bond_df
        else:
            raise ValueError("유효한 월을 입력하세요 (1-12).")

    except:
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

        try:
            bond_df = bond_df.loc[start_date:end_date]
            return bond_df
            
        except Exception as e:
            print(f'get_bond에서 오류 발생: {e}')
            return None
    