import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, '../../../store_data/process/market_data/sector/')

available_sector_list = os.listdir(path)
OHLCV_df_columns = [
    'Date', 'Open', 'High', 'Low', 'Close', 'Volume', 'Transaction_Val', 'Market_Cap', 
    'MA_20', 'RSI_14', 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0'
]

def get_index_list():
    """
    인덱스 종류 반환하는 함수
    """
    return available_sector_list

def index_price_info(sector: str, start_date: str, end_date: str) -> pd.DataFrame:
    '''
    인덱스명, 시작일, 종료일을 파라미터로 입력하면

    'Open', 'High', 'Low', 'Close', 'Volume', 'Transaction_Val', 'Market_Cap', 'Date',
    'MA_20', 'RSI_14', 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0'

    다음 컬럼에 해당하는 정보를 반환함.
    '''

    if sector in available_sector_list:
        # 경로 설정
        df_path = os.path.join(path, sector)
        csv_path = os.path.join(df_path, f'{sector}_indicators.csv')

        # CSV 파일 읽기
        df = pd.read_csv(csv_path, index_col=0)

        # 컬럼 이름 재설정
        df.columns = OHLCV_df_columns  

        # 날짜 컬럼을 datetime으로 변환 후 인덱스로 설정
        df['Date'] = pd.to_datetime(df['Date']).dt.date  # 날짜만 남기기
        df.set_index('Date', inplace=True)
        df = df.sort_index()  # 인덱스를 날짜순으로 정렬

        # start_date와 end_date를 날짜 형식으로 변환
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()

        # 시작일과 종료일이 데이터 범위 내에 있는지 확인
        if start_date < df.index.min() or end_date > df.index.max():
            print(f"Error: 날짜 범위가 데이터 범위를 벗어났습니다. 데이터 범위: {df.index.min()} ~ {df.index.max()}")
            return None

        # 범위 내 데이터 필터링
        return_df = df.loc[start_date:end_date]

        return return_df
    else:
        print(f'{sector}에 해당하는 가격 정보를 찾을 수 없습니다!')
        return None
