import os
import pandas as pd
import ast
import re
from .utils import get_corp_OHLCV

quarter_map = {
    'Q1': ['Q1', '01', '02', '03'],
    'Q2': ['Q2', '04', '05', '06'],
    'Q3': ['Q3', '07', '08', '09'],
    'Q4': ['Q4', '10', '11', '12']
}

def get_raw_fin_statement_info(ticker:str, year:str, quarter:str) -> pd.DataFrame:
    '''
    종목 코드, 연도, 분기를 입력하면 df 형태로 요청한 재무제표 반환
    단, quarter를 '01', '02', ... 처럼 월별로 입력한다면 해당하는 분기의 재무제표 반환
    ex. get_raw_fin_statement_info('005930', '2019', 'Q1')
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

        # 월별 재무제표 경로 탐색
        for path in path_to_verify:
            target_path_to_verify = os.path.join(fin_statement_path, path, f'{path}_{ticker}_재무제표 ({path}).csv')
            
            try:
                df = pd.read_csv(target_path_to_verify)
                verify_row = df.iloc[0]
                reprt_code = verify_row['reprt_code']
                bsns_year = verify_row['bsns_year']

                # print(f"Checking file: {target_path_to_verify} | reprt_code: {reprt_code}, bsns_year: {bsns_year}")

                # 각 분기에 대한 조건 확인 및 month_date 값 저장
                if quarter == 'Q1' or str(quarter) in quarter_map['Q1']:
                    if str(bsns_year) == str(year) and str(reprt_code) == '11013':
                        month_date = path

                elif quarter == 'Q2' or str(quarter) in quarter_map['Q2']:
                    if str(bsns_year) == str(year) and str(reprt_code) == '11012':
                        month_date = path

                elif quarter == 'Q3' or str(quarter) in quarter_map['Q3']:
                    if str(bsns_year) == str(year) and str(reprt_code) == '11014':
                        month_date = path

                elif quarter == 'Q4' or str(quarter) in quarter_map['Q4']:
                    if str(bsns_year) == str(year) and str(reprt_code) == '11011':
                        month_date = path

                # if month_date:
                #     print(f"Selected month_date final!: {month_date}")
                # else:
                #     print(f"No matching report for path: {path}")

            except FileNotFoundError as e:
                print(f"File not found: {target_path_to_verify} | Error: {e}")


        final_path = os.path.join(fin_statement_path, month_date, f'{month_date}_{ticker}_재무제표 ({month_date}).csv')
        statement_df = pd.read_csv(final_path)

        return statement_df
    except Exception as e:
        print(f'재무제표를 불러오는 과정에서 오류가 발생했습니다 | {e}')

# 이익 성장률과 CAGR 계산 함수
def calculate_growth_rates(current_net_income, previous_net_income, years=1):
    '''
    이익 성장률과 CAGR 계산 함수
    '''
    if previous_net_income == 0:
        profit_growth_rate = None  # 0으로 나누는 것을 방지
        cagr = None
    else:
        # 이익 성장률 계산
        profit_growth_rate = ((current_net_income - previous_net_income) / previous_net_income) * 100
        
        # CAGR 계산
        cagr = ((current_net_income / previous_net_income) ** (1 / years)) - 1
    
    return profit_growth_rate, cagr

def calculate_pbr_per_roe(fin_statement_info_dict:dict):
    '''
    pbr, per, roe 계산을 위한 함수, dict 형태로 정보를 받아 

    pd.DataFrame({
        'Stock Price': [selected_price],
        'PER': [per],
        'PBR': [pbr],
        'ROE': [roe],
        'Profit Growth Rate (%)': [profit_growth_rate],
        'CAGR (%)': [cagr]
    })

    형태로 반환.

    input은

    fin_statement_info_dict = {
        stock_price_data = pd.DataFrame ...
        financial_data = pd.DataFrame ...
        shares_outstanding = int ...
        previous_net_income = int ...
    }
    '''

    stock_price_data = fin_statement_info_dict['stock_price_data'] 
    financial_data = fin_statement_info_dict['financial_data'] 
    shares_outstanding = fin_statement_info_dict['shares_outstanding']
    previous_net_income = fin_statement_info_dict['previous_net_income'] 

    if not stock_price_data.empty:
        selected_price = stock_price_data['Close'].iloc[-1]
    else:
        print(f"주식 가격 데이터가 비어있습니다.")
        return None

    # 현재 순이익 계산
    net_income = financial_data.loc[financial_data['account_id'] == 'ifrs-full_ProfitLoss', 'thstrm_amount']
    if net_income.empty:
        print(f"순이익 데이터를 찾을 수 없습니다.")
        return None
    net_income = net_income.values[0]

    # 총 자본 (Equity) 계산
    total_equity = financial_data.loc[financial_data['account_id'] == 'ifrs-full_Equity', 'thstrm_amount'].values[0]

    if shares_outstanding is None:
        print(f"발행 주식수를 찾을 수 없습니다.")
        return None

    # EPS, BVPS, PER, PBR, ROE 계산
    eps = net_income / shares_outstanding
    bvps = total_equity / shares_outstanding
    per = selected_price / eps if eps != 0 else None
    pbr = selected_price / bvps if bvps != 0 else None
    roe = net_income / total_equity if total_equity != 0 else None

    # 이익 성장률 및 CAGR 계산 (이전 년도 순이익을 매개변수로 받음)
    profit_growth_rate, cagr = calculate_growth_rates(net_income, previous_net_income, years=1)

    # 결과 생성
    result = pd.DataFrame({
        'Stock Price': [selected_price],
        'PER': [per],
        'PBR': [pbr],
        'ROE': [roe],
        'Profit Growth Rate (%)': [profit_growth_rate],
        'CAGR (%)': [cagr]
    })

    return result

def extract_shares_outstanding(ticker: str, year: str, quarter: str) -> int:
    '''
    종목코드, 연도, 분기(혹은 월)을 입력하면 int로 발행 주식 총수 반환
    ex. extract_shares_outstanding('005930', '2019', 'Q1')
    '''

    current_dir = os.path.dirname(os.path.abspath(__file__))
    fin_report_path = f'../../store_data/raw/opendart/store_reports'
    fin_report_path = os.path.join(current_dir, fin_report_path)

    ticker = str(ticker)
    year = str(year)
    quarter = str(quarter)

    # 분기별 매핑
    if quarter in quarter_map['Q1']:
        quarter = '03'
    elif quarter in quarter_map['Q2']:
        quarter = '06'
    elif quarter in quarter_map['Q3']:
        quarter = '09'
    elif quarter in quarter_map['Q4']:
        quarter = '12'
    else:
        print(f'유효하지 않은 quarter입니다. | {quarter}')
        return None
    
    # 금융 보고서 경로 리스트 가져오기 함수
    def get_financial_reports_path_list(ticker: str, year: str, quarter: str) -> list:
        report_path = os.path.join(fin_report_path, ticker, f'{year}.{quarter}')
        return os.listdir(report_path)

    # 발행 주식 데이터 추출 함수
    def extract_issued_stock_count(issued_stock_file_path: str) -> int:
        issued_stock_data = pd.read_csv(issued_stock_file_path)
        raw_text = issued_stock_data.iloc[0, 0]
        cleaned_text = ast.literal_eval(raw_text)[0]

        start_index = cleaned_text.find("발행주식의 총수")
        end_index = cleaned_text.find("자기주식수", start_index)
        issued_stock_section = cleaned_text[start_index:end_index]
        issued_stock_count = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b', issued_stock_section)

        return int(issued_stock_count[0].replace(',', '')) if issued_stock_count else None

    try:
        # 보고서 파일 리스트 가져오기
        issued_stock_files = get_financial_reports_path_list(ticker, year, quarter)

        # '주식의 총수 등' 파일 찾기
        matching_file = next((file_name for file_name in issued_stock_files if "4. 주식의 총수 등.csv" in file_name), None)

        if matching_file:
            issued_stock_file_path = os.path.join(fin_report_path, ticker, f'{year}.{quarter}', matching_file)
            issued_stock_count = extract_issued_stock_count(issued_stock_file_path)
            
            if issued_stock_count:
                return issued_stock_count
            else:
                # 분기 보고서에 생략된 경우 가장 가까운 보고서를 탐색
                closest_year, closest_quarter = str(int(year)-1), '12' if quarter == '03' else '06'
                issued_stock_files = get_financial_reports_path_list(ticker, closest_year, closest_quarter)
                matching_file = next((file_name for file_name in issued_stock_files if "4. 주식의 총수 등.csv" in file_name), None)

                if matching_file:
                    issued_stock_file_path = os.path.join(fin_report_path, ticker, f'{closest_year}.{closest_quarter}', matching_file)
                    return extract_issued_stock_count(issued_stock_file_path)
                else:
                    print(f"{closest_year}의 {ticker} 발행 주식 파일을 찾을 수 없습니다.")
                    return None

        else:
            print(f"{year}의 {ticker} 발행 주식 파일을 찾을 수 없습니다.")
            return None

    except Exception as e:
        print(f"{year}의 {ticker} 발행 주식수 파일을 읽는 중 오류 발생: {e}")
        return None

def fin_statement_info(ticker:str, year:str, quarter:str) -> pd.DataFrame:
    '''
    pd.DataFrame({
        'Stock Price': [selected_price],
        'PER': [per],
        'PBR': [pbr],
        'ROE': [roe],
        'Profit Growth Rate (%)': [profit_growth_rate],
        'CAGR (%)': [cagr]
    })

    형태로 반환
    '''

    stock_price_data = get_corp_OHLCV(ticker, year, quarter)
    financial_data = get_raw_fin_statement_info(ticker, year, quarter)
    shares_outstanding = extract_shares_outstanding(ticker, year, quarter)

    # 분기별 매핑
    if quarter in quarter_map['Q1']:
        quarter = 'Q1'
    elif quarter in quarter_map['Q2']:
        quarter == 'Q2'
    elif quarter in quarter_map['Q3']:
        quarter == 'Q3'
    elif quarter in quarter_map['Q4']:
        quarter == 'Q4'
    else:
        print(f'유효하지 않은 quarter입니다. | {quarter}')
        return None

    # 이전 년도 재무 데이터를 읽고 비어 있는지 확인
    try:
        prev_year = str(int(year)-1)
        try:
            previous_financial_data = get_raw_fin_statement_info(ticker, prev_year, quarter)
            if previous_financial_data.empty:
                print(f"{ticker}의 이전 년도 재무 데이터가 비어 있습니다.")
                return None
        except:
            print(f'{ticker}의 이전 년도 재무 데이터를 불러올 수 없습니다.')
    except pd.errors.EmptyDataError:
        print(f"{ticker}의 이전 년도 재무 데이터 파일이 비어 있습니다.")
        return None
    except FileNotFoundError:
        print(f"{ticker}의 이전 년도 재무 데이터 파일을 찾을 수 없습니다.")
        return None

    # 이전 년도 순이익 데이터 확인
    try:
        previous_net_income = previous_financial_data.loc[previous_financial_data['account_id'] == 'ifrs-full_ProfitLoss', 'thstrm_amount']
        if previous_net_income.empty:
            # 국제회계기준 적용하여 ifrs-full_ProfitLoss 컬럼으로 변경되기 이전인 경우를 체크
            previous_net_income = previous_financial_data.loc[previous_financial_data['account_id'] == 'ifrs_ProfitLoss', 'thstrm_amount']
            if previous_net_income.empty:
                print(f"{ticker}의 이전 년도 순이익 데이터를 찾을 수 없습니다.")
                return None
    except Exception as e:
        print(f'{ticker}의 fin_statement_info 정보를 확인할 수 없습니다.')
        return None
    
    previous_net_income = previous_net_income.values[0]

    fin_statement_info_dict = {
        'stock_price_data': stock_price_data,
        'financial_data': financial_data,
        'shares_outstanding': shares_outstanding,
        'previous_net_income': previous_net_income,
    }
    
    # calculate_pbr_per_roe 함수로 순이익 데이터를 전달
    result = calculate_pbr_per_roe(fin_statement_info_dict)

    return result