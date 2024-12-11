import pandas as pd
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
fin_report_path = os.path.join(current_dir, '../../store_data/raw/opendart/store_reports')

quarter_map = {
    'Q1': [1, 2, 3],
    'Q2': [4, 5, 6],
    'Q3': [7, 8, 9],
    'Q4': [10, 11, 12]
}

def reports_info(ticker:str, year:str, quarter:str) -> pd.DataFrame:
    '''
    
    종목 코드, 연도, 분기를 입력하면 df로 반환하는 함수

    ex. report_info('000020', '2019', 'Q1')
    
    |I. 회사의 개요.csv| 분기보고서.csv | ... | 5. 재무제표 주석.csv |
    | [내용]         |              |     |                  |
    ...

    '''
    df_path_list = os.path.join(fin_report_path, ticker, f'{year}.{str(quarter_map[quarter][-1]).zfill(2)}')
    store_dfs_dict = {}

    for path in os.listdir(df_path_list):
        df = pd.read_csv(os.path.join(df_path_list, path))
        df_name = path.split('|')[-1]
        store_dfs_dict[df_name.strip()] = list(df['text'])

    return_df = pd.DataFrame(store_dfs_dict)

    return return_df