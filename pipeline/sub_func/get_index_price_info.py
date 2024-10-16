import os
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, '../../store_data/process/market_data/sector/')

available_sector_list = os.listdir(path)
OHLCV_df_columns = [
    'Open', 'High', 'Low', 'Close', 'Volume', 'Transaction_Val', 'Market_Cap', 'Date',
    'MA_20', 'RSI_14', 'BBL_20_2.0', 'BBM_20_2.0', 'BBU_20_2.0', 'BBB_20_2.0', 'BBP_20_2.0'
]

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
        df.columns = OHLCV_df_columns  # 컬럼 이름 재설정

        # 인덱스를 datetime 형식으로 변환
        df.index = pd.to_datetime(df.index)

        # start_date와 end_date를 datetime으로 변환
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # 시작일과 종료일 사이 데이터 필터링
        return_df = df.loc[start_date:end_date]

        return return_df
    else:
        print(f'{sector}에 해당하는 가격 정보를 찾을 수 없습니다!')
        return None
