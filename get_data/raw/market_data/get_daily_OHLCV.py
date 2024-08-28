from pykrx import stock
import pandas as pd
import os

def split_df_by_month(df):
    # 날짜 인덱스가 있는 DataFrame을 월별로 분할하여 리스트에 담음
    monthly_dfs = []
    
    # '날짜' 인덱스를 활용해 DataFrame을 그룹화
    grouped = df.groupby(pd.Grouper(freq='ME'))
    
    # 그룹화된 데이터를 월별로 분할하여 리스트에 추가
    for _, group in grouped:
        monthly_dfs.append(group)
    
    return monthly_dfs

def get_daily_OHLCV(start_date: str, end_date: str, stock_code: str):
    '''
    지정된 일자 간격에 대해 OHLCV 정보를 1시간봉 기준으로 조회 후 df형태로 반환
    가격 데이터 저장
    '''
    try:
        # 현재 파일의 디렉토리 경로 가져오기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 저장 경로 부모 디렉토리의 절대 경로 생성
        store_path_parent = os.path.join(current_dir, f'../../../store_data/raw/market_data/price/')

        # PyKRX를 통해 OHLCV 데이터 가져오기
        data = stock.get_market_ohlcv(start_date, end_date, stock_code)

        # 월별로 데이터 분할
        df_list = split_df_by_month(data)

        for target_df in df_list:
            # target_df의 첫 번째 날짜로부터 연도와 월을 추출
            first_date = target_df.index[0]
            year_of_df = first_date.year
            month_of_df = first_date.month
            
            # 최종 저장 경로 생성
            store_path = os.path.join(store_path_parent, f'{stock_code}/{year_of_df}.{month_of_df:02d}/{year_of_df}.{month_of_df:02d}_{stock_code}.csv')
            
            # 디렉토리 생성 (이미 존재하는 경우 예외 처리)
            os.makedirs(os.path.dirname(store_path), exist_ok=True)
            
            # CSV 파일로 저장
            target_df.to_csv(store_path)

        return data
    except Exception as e:
        print(f"pykrx 일자간 가격정보 Fetch 실패: {e}")
        return None