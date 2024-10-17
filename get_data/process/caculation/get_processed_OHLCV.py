import os
import pandas as pd
import pandas_ta as ta

raw_price_path_parent = '../../../store_data/raw/market_data/price/'
store_price_path_parent = '../../../store_data/process/market_data/price'
# 티커 목록 불러오기
tickers_price = os.listdir(raw_price_path_parent)

# 경로 설정
raw_index_path_parent = '../../../store_data/raw/market_data/sector'
store_index_path_parent = '../../../store_data/process/market_data/sector'
# 티커 목록 불러오기
tickers_sector = os.listdir(raw_index_path_parent)

# MA, RSI, 볼린저 밴드 계산 함수
def calculate_indicators(df):
    # MA (이동평균)
    df['MA_20'] = ta.sma(df['종가'], length=20)  # 20일 이동평균

    # RSI (상대 강도 지수)
    df['RSI_14'] = ta.rsi(df['종가'], length=14)  # 14일 RSI

    # 볼린저 밴드
    bbands = ta.bbands(df['종가'], length=20)
    df = pd.concat([df, bbands], axis=1)  # 볼린저 밴드 컬럼 추가 (BBL: 하단, BBM: 중간, BBU: 상단)

    return df

def get_price_indicators():
    '''
    실행 시 store_data/raw/market_data/price 내에 있는 종목별 df를 하나로 합치고, 해당 df에 MA, RSI, BB를 컬럼으로 더함.
    '''
    for ticker in tickers_price:
        if ticker not in ['.DS_Store', 'temptext']:
            time_list_path = os.path.join(raw_price_path_parent, ticker)
            time_list = os.listdir(time_list_path)

            df_list = []
            for time in time_list:
                try:
                    # 각 시점별 가격 데이터 파일 경로 생성
                    price_df_path = os.path.join(time_list_path, time, f'{time}_{ticker}.csv')
                    
                    # CSV 파일 로드
                    price_df = pd.read_csv(price_df_path, encoding='utf-8', delimiter=',')
                    df_list.append(price_df)
                except Exception as e:
                    # 예외 발생 시 경로와 오류 메시지 출력
                    print(f"Error processing {price_df_path}: {e}")
                    continue

            # DataFrame들을 세로로 합치기
            if df_list:
                merged_df = pd.concat(df_list, axis=0, ignore_index=True)
            else:
                print(f"No valid data for ticker {ticker}")
                continue

            # 날짜 컬럼을 datetime으로 변환 후 유효한 데이터만 남기기
            merged_df['날짜'] = pd.to_datetime(merged_df['날짜'], errors='coerce')
            merged_df = merged_df.dropna(subset=['날짜'])

            # 날짜를 기준으로 정렬
            merged_df = merged_df.sort_values(by='날짜').reset_index(drop=True)

            # 지표 계산 후 저장
            try:
                calculated_df = calculate_indicators(merged_df)

                store_path_final = os.path.join(store_price_path_parent, ticker)
                os.makedirs(store_path_final, exist_ok=True)

                # 인덱스 포함하여 CSV로 저장
                calculated_df.to_csv(
                    os.path.join(store_path_final, f'{ticker}_indicators.csv')
                )
                print(f"Successfully saved data for ticker {ticker}")
            except Exception as e:
                print(f"Error saving data for {ticker}: {e}")

def get_sector_indicators():
    '''
    실행 시 store_data/raw/market_data/sector 내에 있는 업종별 df를 하나로 합치고, 해당 df에 MA, RSI, BB를 컬럼으로 더함.
    '''
    for ticker in tickers_sector:
        if ticker not in ['.DS_Store', 'temptext']:
            time_list_path = os.path.join(raw_index_path_parent, ticker)
            time_list = os.listdir(time_list_path)

            df_list = []
            for time in time_list:
                try:
                    print(time)
                    # 각 시점별 가격 데이터 파일 경로 생성
                    price_df_path = os.path.join(time_list_path, time, f'{time}_{ticker}.csv')
                    
                    # CSV 파일 로드
                    price_df = pd.read_csv(price_df_path, encoding='utf-8', delimiter=',')
                    df_list.append(price_df)
                except Exception as e:
                    # 예외 발생 시 경로와 오류 메시지 출력
                    print(f"Error processing {price_df_path}: {e}")
                    continue

            # DataFrame들을 세로로 합치기
            if df_list:
                merged_df = pd.concat(df_list, axis=0, ignore_index=True)
            else:
                print(f"No valid data for ticker {ticker}")
                continue

            # 날짜 컬럼을 datetime으로 변환 후 유효한 데이터만 남기기
            merged_df['날짜'] = pd.to_datetime(merged_df['날짜'], errors='coerce')
            merged_df = merged_df.dropna(subset=['날짜'])

            # 날짜를 기준으로 정렬
            merged_df = merged_df.sort_values(by='날짜').reset_index(drop=True)

            # 지표 계산 후 저장
            try:
                calculated_df = calculate_indicators(merged_df)

                store_path_final = os.path.join(store_index_path_parent, ticker)
                os.makedirs(store_path_final, exist_ok=True)

                # 인덱스 포함하여 CSV로 저장
                calculated_df.to_csv(
                    os.path.join(store_path_final, f'{ticker}_indicators.csv')
                )
                print(f"Successfully saved data for ticker {ticker}")
            except Exception as e:
                print(f"Error saving data for {ticker}: {e}")