import os
import pandas as pd

quarter_map = {
    'Q1': ['Q1', '01', '02', '03'],
    'Q2': ['Q2', '04', '05', '06'],
    'Q3': ['Q3', '07', '08', '09'],
    'Q4': ['Q4', '10', '11', '12']
}

def fin_statement_info(ticker:str, year:str, quarter:str) -> pd.DataFrame:
    '''
    종목 코드, 연도, 분기를 입력하면 df 형태로 요청한 재무제표 반환
    단, quarter를 '01', '02', ... 처럼 월별로 입력한다면 해당하는 분기의 재무제표 반환
    ex. fin_statement_info('005930', '2019', 'Q1')
    '''
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        fin_statement_path = f'../../store_data/raw/opendart/store_financial_statement/{ticker}'
        fin_statement_path = os.path.join(current_dir, fin_statement_path)

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
            
            if quarter == 'Q1' or str(quarter) in quarter_map['Q1']:
                if str(bsns_year) == str(year) and str(reprt_code) == str('11013'):
                    month_date = path
                
            elif quarter == 'Q2' or str(quarter) in quarter_map['Q2']:
                if str(bsns_year) == str(year) and str(reprt_code) == str('11012'):
                    month_date = path

            elif quarter == 'Q3' or str(quarter) in quarter_map['Q3']:
                if str(bsns_year) == str(year) and str(reprt_code) == str('11014'):
                    month_date = path

            elif quarter == 'Q4' or str(quarter) in quarter_map['Q4']:
                if str(bsns_year) == str(year) and str(reprt_code) == str('11011'):
                    month_date = path

            else:
                print(f'유효하지 않은 quarter입니다. | quarter: {quarter}')

        final_path = os.path.join(fin_statement_path, month_date, f'{month_date}_{ticker}_재무제표 ({month_date}).csv')
        statement_df = pd.read_csv(final_path)

        return statement_df
    except Exception as e:
        print(f'재무제표를 불러오는 과정에서 오류가 발생했습니다 | {e}')