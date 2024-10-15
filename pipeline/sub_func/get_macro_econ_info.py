import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
path = os.path.join(current_dir, '../../store_data/raw/FRED/')

def macro_econ_info(year:str, start_date:str, end_date:str) -> dict:
    '''
    연도, 시작일, 종료일을 입력하면 

    CN, EU, JP, UK, US 국가들에 대해 

    국채 수익률, 중앙은행금리, 환율, GDP 성장률, 인플레이션률, 이자율, 실업률 반환.
    단, 중국의 경우 실업률 정보 없음.
    단, 미국의 경우 VIX 관련 정보 포함.

    반환 형태는 {
        'US': {
            'VIX': (해당하는 df),
            'Bond Market Trend': (해당하는 df),
            ...
        },
        'UK': {
            'Bond Market Trend': (해당하는 df),
            ...
        }
    }
    와 같이 dict 내에 df를 담은 형태로 반환
    '''

    df_dict = {}

    country_list = os.listdir(path)

    for country in country_list:
        df_dict[country] = {}
        sub_path = os.path.join(path, country)
        econ_items_list = os.listdir(sub_path)
        for econ_items in econ_items_list:
            csv_path = os.path.join(sub_path, econ_items, year, f'{year}_{econ_items}.csv')
            df = pd.read_csv(csv_path)
            df.set_index(df['Date'], inplace=True)
            df.index = pd.to_datetime(df.index)
            df_dict[country][econ_items] = df.loc[start_date:end_date]

    return df_dict
