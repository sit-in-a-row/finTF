import pandas as pd
import os
from .load_data import calculate_cumulative_returns

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_SMB(year, quarter):
    """
    year와 quarter를 입력받아 코스피 소형주와 대형주 데이터를 필터링하여 반환 후 SMB df반환
    
    Args:
    - year (str): 연도 (예: '2023')
    - quarter (str): 분기 ('Q1', 'Q2', 'Q3', 'Q4')
    
    Returns:
    - small_df (pd.DataFrame): 필터링된 소형주 데이터프레임
    - big_df (pd.DataFrame): 필터링된 대형주 데이터프레임
    - SMB_df (pd.DataFrame): small_df - big_df으로 ['SMB'] 컬럼만 반환
    """
    save_path = os.path.join(current_dir, f'./factor_data/SMB/{year}')

    try:
        df_path = os.path.join(save_path, f'{quarter}_SMB.csv')
        df = pd.read_csv(df_path, index_col='Date')
        print(f'{year}_{quarter}에 대한 SMB파일이 존재합니다. 해당 데이터를 로드합니다...')
        return df

    except:
        # print('SMB임')
        small_df = pd.read_csv(os.path.join(current_dir, f'../../../../../store_data/raw/market_data/sector/코스피 소형주/{year}/{year}_코스피 소형주.csv'))
        big_df =  pd.read_csv(os.path.join(current_dir, f'../../../../../store_data/raw/market_data/sector/코스피 대형주/{year}/{year}_코스피 대형주.csv'))

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
        else:
            raise ValueError("quarter는 'Q1', 'Q2', 'Q3', 'Q4' 중 하나여야 합니다.")

        # 컬럼 설정
        df_columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Transaction_Val', 'Market_Cap']
        
        # 소형주 데이터 처리
        small_df.columns = df_columns
        small_df['Date'] = pd.to_datetime(small_df['Date'])
        small_df.set_index('Date', inplace=True)
        small_df = small_df.loc[start_date:end_date]
        small_df = calculate_cumulative_returns(small_df)

        # 대형주 데이터 처리
        big_df.columns = df_columns
        big_df['Date'] = pd.to_datetime(big_df['Date'])
        big_df.set_index('Date', inplace=True)
        big_df = big_df.loc[start_date:end_date]
        big_df = calculate_cumulative_returns(big_df)

        SMB_df = pd.merge(small_df, big_df, left_index=True, right_index=True)

        SMB_df['SMB'] = SMB_df['Return_x'] - SMB_df['Return_y']

        os.makedirs(save_path, exist_ok=True)
        df_path = os.path.join(save_path, f'{quarter}_SMB.csv')
        SMB_df = SMB_df['SMB']
        SMB_df.to_csv(df_path, index=True)

        return SMB_df