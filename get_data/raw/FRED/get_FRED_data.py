import pandas as pd
from fredapi import Fred
import os
import yaml
import pandas as pd

def split_df_by_year(df):
    """
    주어진 DataFrame을 연도별로 나누어 리스트에 담아 반환하는 함수
    :param df: 연도별로 나눌 DataFrame
    :return: 연도별 DataFrame을 담은 리스트
    """
    # 'Date' 열을 Datetime 형식으로 변환 (이미 인덱스로 되어 있다면 생략 가능)
    df.index = pd.to_datetime(df.index)

    # 연도별로 DataFrame을 나누어 리스트에 담기
    yearly_dfs = []
    for year in df.index.year.unique():
        yearly_df = df[df.index.year == year]
        yearly_dfs.append(yearly_df)

    return yearly_dfs

def get_global_info(start_date:str, end_date:str):
        """
        전체 데이터를 하나로 묶은 뒤 규칙에 맞추어 경로에 저장하는 함수
        """
        def change_date_format(date):
            if len(date) == 8:
                year = date[:4]
                month = date[4:6]
                day = date[6:8]
                return f'{year}-{month}-{day}'
            else:
                print('유효한 날짜 형식 (YYYYMMDD) 으로 입력해주세요.')
                return None

        fred_data = get_FRED_data()

        start_date = change_date_format(start_date)
        end_date = change_date_format(end_date)
        
        try:
            us_data = fred_data.get_us_data(start_date, end_date)
            eu_data = fred_data.get_eu_data(start_date, end_date)
            uk_data = fred_data.get_uk_data(start_date, end_date)
            japan_data = fred_data.get_japan_data(start_date, end_date)
            china_data = fred_data.get_china_data(start_date, end_date)

            total = {
                'US': us_data,
                'EU': eu_data,
                'UK': uk_data,
                'JP': japan_data,
                'CN': china_data
            }

            country_list = list(total.keys())

            current_dir = os.path.dirname(os.path.abspath(__file__))
            base_save_path = os.path.join(current_dir, '../../../store_data/raw/FRED/')

            for country in country_list:
                print(f'{country}에 대해 CSV 변환 및 저장 시작...')
                target_country_df = total[country]

                for df_key, sub_df in target_country_df.items():
                    sub_sub_dfs = split_df_by_year(sub_df)
                    for yearly_df in sub_sub_dfs:
                        year = str(yearly_df.index[0].year)
                        save_path = os.path.join(base_save_path, country, df_key, year)
                        os.makedirs(save_path, exist_ok=True)
                        file_name = f'{year}_{df_key}.csv'
                        file_path = os.path.join(save_path, file_name)
                        yearly_df.to_csv(file_path)
                        # print(f'{file_path} 저장 완료')
                print(f'{country}에 대해 CSV 변환 및 저장 완료.')                        

            print('FRED에서 가져온 국가별 경제지표를 csv로 저장했습니다.')
            return None
        
        except Exception as e:
            print(f'CSV로 저장하는 과정에서 오류 발생: {e}')
            return None

# 미국, EU, 영국, 일본, 중국의 경제 데이터 가져오는 클래스
class get_FRED_data:
    def __init__(self):
        # 현재 파일의 디렉토리 경로 가져오기
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # yaml 파일의 절대 경로 생성
        yaml_path = os.path.join(current_dir, '../../../config/api_keys.yaml')
        # YAML 파일 읽기
        with open(yaml_path, "r") as file:
            config = yaml.safe_load(file)
        # 필요한 값 가져오기
        api_key = config['api_keys']['FRED']

        self.fred = Fred(api_key=api_key)
    
    def get_data(self, series_id, start_date='2019-01-01', end_date=None):
        """
        FRED에서 특정 시리즈 데이터를 가져오는 함수
        :param series_id: FRED 시리즈 ID
        :param start_date: 데이터의 시작 날짜 (기본값: 2019-01-01)
        :param end_date: 데이터의 종료 날짜 (기본값: 현재)
        :return: Pandas DataFrame 형태로 반환

        중앙은행 금리, GDP 성장률, 10년물 국채 수익률, 소비자 물가 지수, 실업률, 개인 소비 지출, 10년물 국채 수익률, 환율, VIX지수, 소비자 신뢰지수 반환.
        단, 미국 외의 경우 개인소비지출, VIX지수 및 소비자 신뢰지수는 제공X
        중국은 상기 지표에 실업률도 부재
        """
        try:
            data = self.fred.get_series(series_id, start_date, end_date)
            df = pd.DataFrame(data, columns=[series_id])
            df.index.name = 'Date'
            return df
        except Exception as e:
            print(f"Error retrieving data for {series_id}: {e}")
            return None
    
    def get_us_data(self, start_date, end_date):
        """미국 주요 경제 지표 데이터 가져오기"""
        print('US 데이터를 가져오는 중...')
        data = {
            'Central Bank Policy Rate': self.get_data('FEDFUNDS', start_date, end_date),  # 연방기금금리
            'GDP Growth Rate': self.get_data('A191RL1Q225SBEA', start_date, end_date),    # 연간 GDP 성장률
            'Interest Rate': self.get_data('DGS10', start_date, end_date),                # 10년물 국채 수익률
            'Inflation Rate': self.get_data('CPIAUCSL', start_date, end_date),            # 소비자물가지수
            'Unemployment Rate': self.get_data('UNRATE', start_date, end_date),           # 실업률
            'Bond Market Trend': self.get_data('DGS10', start_date, end_date),            # 10년물 국채 수익률 (반복)
            'Exchange Rate': self.get_data('DEXUSEU', start_date, end_date),              # USD/EUR 환율
            'VIX': self.get_data('VIXCLS', start_date, end_date),                         # VIX 지수
            'Consumer Confidence Index': self.get_data('UMCSENT', start_date, end_date),  # 소비자 신뢰지수
            'Consumer Spending': self.get_data('PCE', start_date, end_date),              # 개인소비지출
        }
        return data
    
    def get_eu_data(self, start_date, end_date):
        """유럽연합 주요 경제 지표 데이터 가져오기"""
        print('EU 데이터를 가져오는 중...')
        data = {
            'Central Bank Policy Rate': self.get_data('ECBDFR', start_date, end_date),      # 유럽 중앙은행 금리
            'GDP Growth Rate': self.get_data('CLVMNACSCAB1GQEA19', start_date, end_date),   # 유럽 GDP 성장률
            'Interest Rate': self.get_data('IR3TIB01EZM156N', start_date, end_date),        # 유럽 10년물 국채 수익률
            'Inflation Rate': self.get_data('CP0000EZ19M086NEST', start_date, end_date),    # 유럽 소비자물가지수
            'Unemployment Rate': self.get_data('LRHUTTTTEZM156S', start_date, end_date),    # 유럽 실업률
            'Bond Market Trend': self.get_data('IR3TIB01EZM156N', start_date, end_date),    # 유럽 10년물 국채 수익률 (반복)
            'Exchange Rate': self.get_data('DEXUSEU', start_date, end_date),                # USD/EUR 환율 (미국과 동일)
        }
        return data

    def get_uk_data(self, start_date, end_date):
        """영국 주요 경제 지표 데이터 가져오기"""
        print('UK 데이터를 가져오는 중...')
        data = {
            'Central Bank Policy Rate': self.get_data('IR3TIB01GBM156N', start_date, end_date),  # 영국 정책 금리
            'GDP Growth Rate': self.get_data('NAEXKP01GBQ652S', start_date, end_date),           # 영국 GDP 성장률
            'Interest Rate': self.get_data('IR3TIB01GBM156N', start_date, end_date),             # 영국 10년물 국채 수익률
            'Inflation Rate': self.get_data('CP0000GBM086NEST', start_date, end_date),           # 영국 소비자물가지수
            'Unemployment Rate': self.get_data('LRHUTTTTGBQ156S', start_date, end_date),         # 영국 실업률
            'Bond Market Trend': self.get_data('IR3TIB01GBM156N', start_date, end_date),         # 영국 10년물 국채 수익률 (반복)
            'Exchange Rate': self.get_data('DEXUSUK', start_date, end_date),                     # USD/GBP 환율
        }
        return data
        
    def get_japan_data(self, start_date, end_date):
        """일본 주요 경제 지표 데이터 가져오기"""
        print('JP 데이터를 가져오는 중...')
        data = {
            'Central Bank Policy Rate': self.get_data('INTDSRJPM193N', start_date, end_date),  # 일본 정책 금리
            'GDP Growth Rate': self.get_data('JPNRGDPEXP', start_date, end_date),              # 일본 GDP 성장률
            'Interest Rate': self.get_data('IR3TIB01JPM156N', start_date, end_date),           # 일본 10년물 국채 수익률
            'Inflation Rate': self.get_data('JPNCPIALLMINMEI', start_date, end_date),          # 일본 소비자물가지수 (수정된 ID)
            'Unemployment Rate': self.get_data('LRHUTTTTJPM156S', start_date, end_date),       # 일본 실업률
            'Bond Market Trend': self.get_data('IR3TIB01JPM156N', start_date, end_date),       # 일본 10년물 국채 수익률 (반복)
            'Exchange Rate': self.get_data('DEXJPUS', start_date, end_date),                   # USD/JPY 환율
        }
        return data

    def get_china_data(self, start_date, end_date):
        """중국 주요 경제 지표 데이터 가져오기"""
        print('CN 데이터를 가져오는 중...')
        data = {
            'Central Bank Policy Rate': self.get_data('INTDSRCNM193N', start_date, end_date), # 중국 정책 금리
            'GDP Growth Rate': self.get_data('MKTGDPCNA646NWDB', start_date, end_date),       # 중국 GDP 성장률
            'Interest Rate': self.get_data('IR3TIB01CNM156N', start_date, end_date),          # 중국 10년물 국채 수익률
            'Inflation Rate': self.get_data('CHNCPIALLMINMEI', start_date, end_date),         # 중국 소비자물가지수
            'Bond Market Trend': self.get_data('IR3TIB01CNM156N', start_date, end_date),      # 중국 10년물 국채 수익률 (반복)
            'Exchange Rate': self.get_data('DEXCHUS', start_date, end_date),                  # USD/CNY 환율
        }
        return data

    