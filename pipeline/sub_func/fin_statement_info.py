import os
import pandas as pd

def get_fin_statement(ticker, year, quarter):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fin_statement_path = f'../../store_data/raw/opendart/store_financial_statement/{ticker}'

        path_to_verify = []
        path_list = os.listdir(fin_statement_path)
        for path in path_list:
            if year in path or str(int(year)+1) in path:
                path_to_verify.append(path)

        path_to_verify = sorted(path_to_verify)[:4]

        month_date = ''

        for path in path_to_verify:
            target_path_to_verify = os.path.join(fin_statement_path, path, f'{path}_{ticker}_재무제표 ({path}).csv')
            df = pd.read_csv(target_path_to_verify)
            verify_row = df.iloc[0]
            reprt_code = verify_row['reprt_code']
            bsns_year = verify_row['bsns_year']
            
            if quarter == 'Q1':
                if str(bsns_year) == str(year) and str(reprt_code) == str('11013'):
                    month_date = path
                
            elif quarter == 'Q2':
                if str(bsns_year) == str(year) and str(reprt_code) == str('11012'):
                    month_date = path

            elif quarter == 'Q3':
                if str(bsns_year) == str(year) and str(reprt_code) == str('11014'):
                    month_date = path

            elif quarter == 'Q4':
                if str(bsns_year) == str(year) and str(reprt_code) == str('11011'):
                    month_date = path

            else:
                print(f'유효하지 않은 quarter입니다. | quarter: {quarter}')

        final_path = os.path.join(fin_statement_path, month_date, f'{month_date}_{ticker}_재무제표 ({month_date}).csv')
        statement_df = pd.read_csv(final_path)

        return statement_df
    except Exception as e:
        print(f'재무제표를 불러오는 과정에서 오류가 발생했습니다 | {e}')