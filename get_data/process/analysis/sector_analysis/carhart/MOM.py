from .load_data import get_corp_OHLCV, get_index_OHLCV
import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))

def get_target_timespan(year, quarter):
    year = int(year)
    if quarter == 'Q1':
        timespan = [
            f'{year-2}_Q4',
            f'{year-1}_Q1',
            f'{year-1}_Q2',
            f'{year-1}_Q3',
            f'{year-1}_Q4',
            f'{year}_Q1',
        ]
    elif quarter == 'Q2':
        timespan = [
            f'{year-1}_Q1',
            f'{year-1}_Q2',
            f'{year-1}_Q3',
            f'{year-1}_Q4',
            f'{year}_Q1',
            f'{year}_Q2',
        ]
    elif quarter == 'Q3':
        timespan = [
            f'{year-1}_Q2',
            f'{year-1}_Q3',
            f'{year-1}_Q4',
            f'{year}_Q1',
            f'{year}_Q2',
            f'{year}_Q3',
        ]
    elif quarter == 'Q4':
        timespan = [
            f'{year-1}_Q3',
            f'{year-1}_Q4',
            f'{year}_Q1',
            f'{year}_Q2',
            f'{year}_Q3',
            f'{year}_Q4',
        ]

    return timespan

def get_last_month_data(df):
    # Date 컬럼이 인덱스로 설정되어 있는지 확인하고 없으면 설정
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # 가장 최근 날짜 추출
    last_date = df.index.max()
    
    # 마지막 달을 기준으로 해당 달의 데이터만 필터링
    last_month_data = df[df.index.month == last_date.month]
    
    return last_month_data

def remove_last_month_data(df):
    # Date 컬럼이 인덱스로 설정되어 있는지 확인하고 없으면 설정
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # 가장 최근 날짜 추출
    last_date = df.index.max()
    
    # 마지막 달 데이터를 제외한 데이터만 필터링
    df_without_last_month = df[df.index.month != last_date.month]
    
    return df_without_last_month

# 0번째, 5번째 인덱스 데이터에 각각 다른 함수를 적용하여 하나로 합치는 함수
def combine_dfs(df_list):
    # 각 DataFrame을 처리
    df_1 = get_last_month_data(df_list[0])
    df_2 = df_list[1]
    df_3 = df_list[2]
    df_4 = df_list[3]
    df_5 = df_list[4]
    df_6 = remove_last_month_data(df_list[5])
    
    # 처리된 DataFrame들을 하나로 합치기 (행 단위로 합침)
    combined_df = pd.concat([df_1, df_2, df_3, df_4, df_5, df_6], axis=0)
    
    return combined_df

# 모멘텀 분석에 필요한 가격 데이터 로드하는 함수
def get_momentum_OHLCV(ticker, year, quarter):
    '''
    분석 시작 기점이 되는 year, quarter를 넣으면 해당하는 ticker의 가격데이터 로드
    ex. 2023년 1분기 분석하고자 하면 2021 12월 ~ 2022 11월까지 로드
    '''
    target_timespan = get_target_timespan(year, quarter)

    df_list = []

    for i in range(len(target_timespan)):
        year_and_quarter = target_timespan[i].split('_')
        year = year_and_quarter[0]
        quarter = year_and_quarter[1]

        try:
            int(ticker)
            df = get_corp_OHLCV(ticker, year, quarter)
        except:
            df = get_index_OHLCV(ticker, year, quarter)
        
        df_list.append(df)

    past_data = combine_dfs(df_list)
    past_data.index = pd.to_datetime(past_data.index)

    try:
        int(ticker)
        current_data = get_corp_OHLCV(ticker, year, quarter)
    except:
        current_data = get_index_OHLCV(ticker, year, quarter)
    
    current_data.index = pd.to_datetime(current_data.index)

    combined_data = pd.concat([past_data, current_data], axis=0)

    return combined_data

# 모멘텀을 계산하는 함수
def calculate_momentum(df, lookback_period=252):
    """
    모멘텀 팩터를 계산하는 함수
    lookback_period: 모멘텀 계산을 위한 과거 데이터 기간 (일 수 기준, 252는 대략 1년의 영업일 수)
    """
    df['MOM'] = df['Close'].pct_change(periods=lookback_period).fillna(0)
    return df

# 필요한 분기별 날짜만 df에서 추출
def filter_by_quarter(df, year, quarter):
    """
    주어진 DataFrame에서 특정 년도와 분기에 해당하는 데이터를 반환하는 함수
    """
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
        raise ValueError(f"올바른 분기를 입력하세요: {quarter}")

    # Date 인덱스가 있는지 확인하고 없으면 변환
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    
    # 인덱스를 날짜순으로 정렬
    df = df.sort_index()

    # 인덱스 범위 내에서 유효한 데이터가 있는지 확인
    available_dates = df.index[(df.index >= start_date) & (df.index <= end_date)]
    
    if available_dates.empty:
        raise KeyError(f"해당 분기({start_date}~{end_date})의 거래일 데이터가 없습니다.")
    
    # 해당 분기에 해당하는 데이터만 반환 (가장 가까운 거래일 포함)
    return df.loc[available_dates]

# 모멘텀 팩터를 추가하는 함수
def get_MOM(ticker, year, quarter):
    save_path = os.path.join(current_dir, f'./factor_data/MOM/{year}/{quarter}/{ticker}')
    df_name = f'{quarter}_{ticker}_MOM.csv'

    try:
        df_path = os.path.join(save_path)
        df_with_momentum = pd.read_csv(os.path.join(save_path, df_name))

        return df_with_momentum

    except:
        # 주어진 분기 데이터 로드
        df = get_momentum_OHLCV(ticker, year, quarter)

        df_with_momentum = df

        # 모멘텀 계산 (최근 12개월을 기준으로, 252 영업일)
        df_with_momentum = calculate_momentum(df)
        df_with_momentum = filter_by_quarter(df_with_momentum, year, quarter)

        df_with_momentum = df_with_momentum['MOM']

        os.makedirs(save_path, exist_ok=True)
        df_with_momentum.to_csv(os.path.join(save_path, df_name))
        
        return df_with_momentum