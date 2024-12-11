import os
import pandas as pd
import numpy as np
import statsmodels.api as sm
import re
from pykrx import stock
import json
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))

# 데이터 경로 설정
price_data_path = os.path.join(current_dir, '../../store_data/raw/market_data/price')
corp_in_index_path = os.path.join(current_dir, '../../store_data/raw/market_data/sector')
index_OHLCV_path = os.path.join(current_dir, '../../store_data/raw/market_data/sector')
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

# OLS 회귀 model.summary를 추후 재가공을 위해 dict형식으로 변경
def get_model_summary_dict(model_summary):
    ols_dict = {}
    # ols_result_list = model_summary.split('\n')    
    ols_result_list = model_summary
    r_squared_match = re.search(r'R-squared:\s+([\d.]+)', ols_result_list[2])

    try:
        if r_squared_match:
            ols_dict['R-squared'] = float(r_squared_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(R_squared): {e}')

    adj_r_squared_match = re.search(r'Adj. R-squared:\s+([\d.]+)', ols_result_list[3])
    try:
        if adj_r_squared_match:
            ols_dict['Adj. R-squared'] = float(adj_r_squared_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(adj_R_squared): {e}')

    f_statistic_match = re.search(r'F-statistic:\s+([\d.]+)', ols_result_list[4])
    try:
        if f_statistic_match:
            ols_dict['F-statistic'] = float(f_statistic_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(f_statistic): {e}')

    prob_f_statistic_match = re.search(r'Prob \(F-statistic\):\s+([\d.]+)', ols_result_list[5])
    try:
        if prob_f_statistic_match:
            ols_dict['Prob (F-statistic)'] = float(prob_f_statistic_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(prob_f_statistic): {e}')

    log_likelihood_match = re.search(r'Log-Likelihood:\s+([\d.]+)', ols_result_list[6])
    try:
        if log_likelihood_match:
            ols_dict['Log-Likelihood'] = float(log_likelihood_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(log_likelihood): {e}')

    num_observations_match = re.search(r'No. Observations:\s+(\d+)', ols_result_list[7])
    try:
        if num_observations_match:
            ols_dict['No. Observations'] = int(num_observations_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(no. observation): {e}')

    aic_match = re.search(r'AIC:\s+([-\d.]+)', ols_result_list[7])
    try:
        if aic_match:
            ols_dict['AIC'] = float(aic_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(aic): {e}')

    bic_match = re.search(r'BIC:\s+([-\d.]+)', ols_result_list[8])
    try:
        if bic_match:
            ols_dict['BIC'] = float(bic_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(bic): {e}')

    const_numbers_raw = re.findall(r'-?\d+\.\d+', ols_result_list[14])
    try:
        if const_numbers_raw:
            const_number = [float(num) for num in const_numbers_raw]
            temp_dict = {}
            temp_dict['const_coef'] = const_number[0]
            temp_dict['const_std_err'] = const_number[1]
            temp_dict['const_t'] = const_number[2]
            temp_dict['const_P_t'] = const_number[3]
            temp_dict['const_confid_interval'] = [const_number[4], const_number[5]]

            ols_dict['const_result'] = temp_dict
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(const_num): {e}')

    R_m_minus_R_f_numbers_raw = re.findall(r'-?\d+\.\d+', ols_result_list[15])
    try:
        if R_m_minus_R_f_numbers_raw:
            R_m_minus_R_f_number = [float(num) for num in R_m_minus_R_f_numbers_raw]
            temp_dict = {}
            temp_dict['R_m_minus_R_f_coef'] = R_m_minus_R_f_number[0]
            temp_dict['R_m_minus_R_f_std_err'] = R_m_minus_R_f_number[1]
            temp_dict['R_m_minus_R_f_t'] = R_m_minus_R_f_number[2]
            temp_dict['R_m_minus_R_f_P_t'] = R_m_minus_R_f_number[3]
            temp_dict['R_m_minus_R_f_confid_interval'] = [R_m_minus_R_f_number[4], R_m_minus_R_f_number[5]]

            ols_dict['R_m_minus_R_f_result'] = temp_dict
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(R_m_minus_R_f_num): {e}')

    SMB_numbers_raw = re.findall(r'-?\d+\.\d+', ols_result_list[16])
    try:
        if SMB_numbers_raw:
            SMB_number = [float(num) for num in SMB_numbers_raw]
            temp_dict = {}
            temp_dict['SMB_coef'] = SMB_number[0]
            temp_dict['SMB_std_err'] = SMB_number[1]
            temp_dict['SMB_t'] = SMB_number[2]
            temp_dict['SMB_P_t'] = SMB_number[3]
            temp_dict['SMB_confid_interval'] = [SMB_number[4], SMB_number[5]]

            ols_dict['SMB_result'] = temp_dict
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(SMB_num): {e}')

    HML_numbers_raw = re.findall(r'-?\d+\.\d+', ols_result_list[17])
    try:
        if HML_numbers_raw:
            HML_number = [float(num) for num in HML_numbers_raw]
            temp_dict = {}
            temp_dict['HML_coef'] = HML_number[0]
            temp_dict['HML_std_err'] = HML_number[1]
            temp_dict['HML_t'] = HML_number[2]
            temp_dict['HML_P_t'] = HML_number[3]
            temp_dict['HML_confid_interval'] = [HML_number[4], HML_number[5]]

            ols_dict['HML_result'] = temp_dict
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(HML_num): {e}')

    MOM_numbers_raw = re.findall(r'-?\d+\.\d+', ols_result_list[18])
    try:
        if MOM_numbers_raw:
            MOM_number = [float(num) for num in MOM_numbers_raw]
            temp_dict = {}
            temp_dict['MOM_coef'] = MOM_number[0]
            temp_dict['MOM_std_err'] = MOM_number[1]
            temp_dict['MOM_t'] = MOM_number[2]
            temp_dict['MOM_P_t'] = MOM_number[3]
            temp_dict['MOM_confid_interval'] = [MOM_number[4], MOM_number[5]]

            ols_dict['MOM_result'] = temp_dict
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(MOM_num): {e}')

    omnibus_match = re.search(r'Omnibus:\s+([-\d.]+)', ols_result_list[20])
    try:
        if omnibus_match:
            ols_dict['Omnibus'] = float(omnibus_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(omnibus): {e}')

    durbin_watson_match = re.search(r'Durbin-Watson:\s+([-\d.]+)', ols_result_list[20])
    try:
        if durbin_watson_match:
            ols_dict['Durbin-Watson'] = float(durbin_watson_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(durbin_watson): {e}')

    prob_omnibus_match = re.search(r'Prob(Omnibus):\s+([-\d.]+)', ols_result_list[21])
    try:
        if prob_omnibus_match:
            ols_dict['Prob(Omnibus)'] = float(prob_omnibus_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(prob_omnibus): {e}')

    jarque_bera_match = re.search(r'Jarque-Bera:\s+([-\d.]+)', ols_result_list[21])
    try:
        if jarque_bera_match:
            ols_dict['Jarque-Bera'] = float(jarque_bera_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(jarque_bera): {e}')

    skew_match = re.search(r'Skew:\s+([-\d.]+)', ols_result_list[22])
    try:
        if skew_match:
            ols_dict['Skew'] = float(skew_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(skew): {e}')

    prob_JB_match = re.search(r'Prob\(JB\):\s+([-\d.eE]+)', ols_result_list[22])
    try:
        if prob_JB_match:
            ols_dict['Prob(JB)'] = float(prob_JB_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(prob_JB): {e}')

    kurtosis_match = re.search(r'Kurtosis:\s+([-\d.]+)', ols_result_list[23])
    try:
        if kurtosis_match:
            ols_dict['Kurtosis'] = float(kurtosis_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(kurtosis): {e}')

    cond_num_match = re.search(r'Cond. No.\s+([-\d.]+)', ols_result_list[23])
    try:
        if cond_num_match:
            ols_dict['Cond. No.'] = float(cond_num_match.group(1))
    except Exception as e:
        print(f'model.summary()를 dict로 변환하는 과정에서 오류 발생(cond_num): {e}')

    return ols_dict

def load_json(path):
    with open(path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    return data

def preprocess_financial_text(text: str) -> dict:
    """
    금융 도메인 텍스트 데이터를 전처리하는 함수
    """
    # 1. 불필요한 공백 및 특수문자 제거
    cleaned_text = re.sub(r'\s+', ' ', text)  # 여러 개 공백 제거
    cleaned_text = re.sub(r'[ㆍ▲▶▣-]', '', cleaned_text)  # 특수문자 제거
    cleaned_text = cleaned_text.replace('\xa0', ' ')
    
    # 2. 키-값 추출 패턴 정의
    patterns = {
        'directors': re.findall(r'(이름|직위|보수총액)\s+(.*?)\s', cleaned_text),
        'board_decisions': re.findall(r'(의안내용|가결여부|찬반여부)\s+(.*?)\s', cleaned_text),
        'approval_amounts': re.findall(r'(주주총회 승인금액|보수총액|평균보수액)\s+(\d+)', cleaned_text),
        'dates': re.findall(r'(\d{4}[-\.]\d{1,2}[-\.]\d{1,2})', cleaned_text),
    }
    
    # 3. 날짜 변환
    parsed_dates = []
    for date in patterns['dates']:
        try:
            parsed_date = datetime.strptime(date.replace('.', '-'), '%Y-%m-%d').date()
            parsed_dates.append(str(parsed_date))
        except ValueError:
            pass
    patterns['dates'] = parsed_dates
    
    # 4. 표 형식 데이터 추출
    table_sections = re.findall(r'(구 분.*?)\(단위 : 백만원\)(.*?)(?=\n\n|\Z)', cleaned_text, re.DOTALL)
    tables = {header.strip(): content.strip() for header, content in table_sections}
    
    # 5. 결과 반환
    return {
        "cleaned_text": cleaned_text,
        "extracted_data": patterns,
        "tables": tables,
    }