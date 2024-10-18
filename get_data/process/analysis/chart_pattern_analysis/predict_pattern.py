import numpy as np
from sklearn.preprocessing import MinMaxScaler
from pykrx import stock
import mplfinance as mpf
from tensorflow.keras.models import load_model
import os
import pandas as pd

patterns = ['ascending_triangle', 'descending_triangle', 'ascending_wedge', 'descending_wedge', 'double_top', 'double_bottom']

current_dir = os.path.dirname(os.path.abspath(__file__))

model_path = os.path.join(current_dir, './save_model/chart_pattern_model.h5')
price_data_path = os.path.join(current_dir, '../../../../store_data/raw/market_data/price')
# price_data_path = '../../../../store_data/raw/market_data/price/'
save_path = os.path.join(current_dir, f'../../../../store_data/process/analysis/chart_pattern_analysis')

tickers_list = os.path.join(current_dir, '../../../../store_data/raw/market_data/price/')

quarter_map = {
    'Q1': [1, 2, 3],
    'Q2': [4, 5, 6],
    'Q3': [7, 8, 9],
    'Q4': [10, 11, 12]
}

# 모델 불러오기
model = load_model(model_path)

# 예측을 위한 함수
def predict_pattern(model, ohlcv_data, window_size=70):
    """
    외부에서 입력받은 OHLCV 데이터를 기반으로 6개의 차트 패턴에 대한 확률을 예측하는 함수
    :param model: 학습된 CNN-LSTM 모델
    :param ohlcv_data: 새로운 OHLCV 데이터 (numpy 배열 형태로)
    :param window_size: 모델이 사용한 윈도우 크기 (슬라이딩 윈도우 크기)
    :return: 각 패턴에 속할 확률
    """
    # OHLCV 데이터를 정규화 (외부 데이터)
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(ohlcv_data)

    # 입력 데이터를 슬라이딩 윈도우로 변환
    if len(scaled_data) < window_size:
        raise ValueError(f"Input data length should be at least {window_size}")

    input_data = np.array([scaled_data[-window_size:]])  # 최신 데이터로 슬라이딩 윈도우 생성
    
    # 모델 예측 (확률 반환)
    predictions = model.predict(input_data)

    # 6개의 클래스에 대한 확률 출력
    return predictions[0]  # 예측된 확률

# 누적 수익률 계산
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

# DataFrame 분할 함수
def split_df(df, split_window=70):
    df_length = len(df)

    if df_length < split_window:
        print(f'{split_window} 기준으로 분할할 수 없습니다! 현재 길이: {df_length}')
    
    final_df_list = []

    for i in range(len(df) - split_window):
        df_start_point = i
        df_end_point = i + split_window
        splited_df = df.iloc[df_start_point:df_end_point]
        final_df_list.append(splited_df)

    return final_df_list    

# 개별 종목 OHLCV 데이터 로드
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

# 정해진 날짜 사이의 범위만 필터링해서 로드    
def load_target_corp_OHLCV(ticker, start_date, end_date):
    # 시작일과 종료일이 Timestamp 형식인지 확인
    if not isinstance(start_date, pd.Timestamp):
        start_date = pd.Timestamp(start_date)
    if not isinstance(end_date, pd.Timestamp):
        end_date = pd.Timestamp(end_date)

    # 시작 연도 및 월 초기화
    current_year = start_date.year
    current_month = start_date.month

    target_year_month_list = []

    # 시작일이 종료일보다 이전이거나 같을 때까지 반복 (종료일을 포함)
    while pd.Timestamp(current_year, current_month, 1) <= end_date:
        target_year_month_list.append(f'{current_year}.{current_month:02d}')
        
        # 월을 1씩 증가시키고, 12월을 넘기면 연도도 증가
        current_month += 1
        if current_month > 12:
            current_month = 1
            current_year += 1

    df_list = []
    for time in target_year_month_list:
        year = time.split('.')[0]
        month = time.split('.')[-1]

        # 데이터 가져오기
        target_df = get_corp_OHLCV(ticker, year, month)
        df_list.append(target_df)

    # DataFrame들을 세로로 합치기
    merged_df = pd.concat(df_list, axis=0)
    merged_df.index = pd.to_datetime(merged_df.index)
    merged_df = merged_df.sort_index()

    # 시작일과 종료일 범위로 필터링
    merged_df = merged_df.loc[start_date:end_date]

    return merged_df

def chart_pattern_analysis(ticker:str, start_date:str, end_date:str, show_graph=False):
    '''
    ticker, start_date, end_date, show_graph를 인자로 받아서, start_date과 end_date 사이의 날짜를 70일 기준으로 나누어 각 window에 대해 패턴 및 확률값 저장
    show_graph는 기본적으로 False, True로 할 시 그래프도 함께 출력함
    '''
    save_path = os.path.join(current_dir, f'../../../../store_data/process/analysis/chart_pattern_analysis')
    save_path = os.path.join(save_path, ticker)

    start_date_val = pd.to_datetime(start_date).date()
    end_date_val = pd.to_datetime(end_date).date()
    time_delta = int(str(end_date_val - start_date_val).split(' ')[0])
    if time_delta < 70:
        print('최소 70일 이상의 기간을 선택해야 합니다.')
    elif time_delta <= 0:
        print('시작일이 종료일보다 빨라야합니다.')

    price_df = load_target_corp_OHLCV(ticker, start_date, end_date)
    df_list = split_df(price_df)

    for i in range(len(df_list)):
        target_to_predict = df_list[i][['Open', 'High', 'Low', 'Close', 'Volume']]

        predicted_probabilities = predict_pattern(model, target_to_predict)
        which_pattern_idx = list(predicted_probabilities).index(max(predicted_probabilities))

        detected_pattern = patterns[which_pattern_idx]
        detected_pattern_prob = predicted_probabilities[which_pattern_idx]

        df_list_start = df_list[i].index[0]
        df_list_end = df_list[i].index[-1]

        temp_dict = {
            'start_date': [str(df_list_start.date())],  
            'end_date': [str(df_list_end.date())],      
            'pattern': [detected_pattern],              
            'prob': [detected_pattern_prob]             
        }

        temp_df = pd.DataFrame(temp_dict)

        start_year = str(df_list_start.year)
        start_month = str(df_list_start.month).zfill(2)
        start_day = str(df_list_start.day).zfill(2)

        end_year = str(df_list_end.year)
        end_month = str(df_list_end.month).zfill(2)
        end_day = str(df_list_end.day).zfill(2)

        final_save_path = os.path.join(save_path, end_year, end_month)

        os.makedirs(final_save_path, exist_ok=True)
        final_name = f'{start_year}.{start_month}.{start_day}_{end_year}.{end_month}.{end_day}_{ticker}.csv'

        temp_df.to_csv(os.path.join(final_save_path, final_name))

        if show_graph:
            mpf.plot(df_list[i], type='candle', style='charles', title=f'Prediction: {patterns[which_pattern_idx]} | Prob: {predicted_probabilities[which_pattern_idx]:.4f}', figratio=(12, 8), figscale=1.0)

def get_predict_pattern(year:str):
    '''
    year를 입력하면, 해당하는 연도의 모든 종목에 대해 차트 패턴 분석 결과를 store_data/process/analysis/chart_pattern_analysis에 저장
    '''
    start_date = f'{year}0101'
    end_date = f'{year}1231'

    for i in range(len(tickers_list)):
        ticker = tickers_list[i]
        print(f'===== {i+1} / {len(tickers_list)} =====')
        try:
            chart_pattern_analysis(ticker, start_date, end_date, show_graph=False)
        except Exception as e:
            print(f'{ticker}에 대해 {start_date} ~ {end_date}간의 패턴 분석에 실패하였습니다. | {e}')