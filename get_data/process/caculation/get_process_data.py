import os
import pandas as pd
import ast
import re
'''
# 이익 성장률과 CAGR 계산 함수
def calculate_growth_rates(current_net_income, previous_net_income, years=1):
    if previous_net_income == 0:
        profit_growth_rate = None  # 0으로 나누는 것을 방지
        cagr = None
    else:
        # 이익 성장률 계산
        profit_growth_rate = ((current_net_income - previous_net_income) / previous_net_income) * 100
        
        # CAGR 계산
        cagr = ((current_net_income / previous_net_income) ** (1 / years)) - 1
    
    return profit_growth_rate, cagr
'''
def calculate_pbr_per_roe(stock_price_data, financial_data, shares_outstanding, quarter_month):
    stock_price_data['Month'] = pd.to_datetime(stock_price_data['날짜']).dt.to_period('M')
    
    # quarter_month를 사용하여 동적으로 해당 월 데이터를 가져옴
    selected_month_data = stock_price_data[stock_price_data['Month'] == f'2020-{quarter_month}']
    
    if not selected_month_data.empty:
        selected_price = selected_month_data['종가'].iloc[-1]
    else:
        print(f"2020년 {quarter_month}월 데이터가 존재하지 않습니다.")
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
        print("발행 주식수를 찾을 수 없습니다.")
        return None

    # EPS, BVPS, PER, PBR, ROE 계산
    eps = net_income / shares_outstanding
    bvps = total_equity / shares_outstanding
    per = selected_price / eps if eps != 0 else None
    pbr = selected_price / bvps if bvps != 0 else None
    roe = net_income / total_equity if total_equity != 0 else None
    '''
    # 이익 성장률 및 CAGR 계산 (이전 년도 순이익을 매개변수로 받음)
    profit_growth_rate, cagr = calculate_growth_rates(net_income, previous_net_income, years=1)
    '''
    # 결과 생성
    result = pd.DataFrame({
        'Month': ['2020-03'],
        'Stock Price': [selected_price],
        'PER': [per],
        'PBR': [pbr],
        'ROE': [roe],
        #'Profit Growth Rate (%)': [profit_growth_rate],
        #'CAGR (%)': [cagr]
    })

    return result

def extract_shares_outstanding(issued_stock_folder, month):
    try:
        # 폴더 내 파일 리스트 가져오기
        issued_stock_files = os.listdir(issued_stock_folder)
        
        # 파일명에 (2020.{month}) | 4. 주식의 총수 등.csv 패턴이 포함된 파일 찾기
        matching_file = None
        pattern = f"(2020.{month}) | 4. 주식의 총수 등.csv"
        
        for file_name in issued_stock_files:
            if pattern in file_name:
                matching_file = file_name
                break

        if matching_file:
            issued_stock_file_path = os.path.join(issued_stock_folder, matching_file)
            print(f"발행 주식 파일 경로: {issued_stock_file_path}")
            
            # 발행 주식 파일 읽기
            issued_stock_data = pd.read_csv(issued_stock_file_path)
            raw_text = issued_stock_data.iloc[0, 0]
            cleaned_text = ast.literal_eval(raw_text)[0]

            start_index = cleaned_text.find("발행주식의 총수")
            end_index = cleaned_text.find("자기주식수", start_index)
            issued_stock_section = cleaned_text[start_index:end_index]

            issued_stock_count = re.findall(r'\b\d{1,3}(?:,\d{3})*(?:\.\d+)?\b', issued_stock_section)
            
            if issued_stock_count:
                return int(issued_stock_count[0].replace(',', ''))
            else:
                print("발행주식수를 찾을 수 없습니다.")
                return None
        else:
            print("발행 주식 파일을 찾을 수 없습니다.")
            return None
    except Exception as e:
        print(f"발행주식수 파일을 읽는 중 오류 발생: {e}")
        return None
    
def process_single_company(stock_price_file, financial_file, issued_stock_file, output_folder, company_code, quarter_month):
    try:
        stock_price_data = pd.read_csv(stock_price_file)
    except pd.errors.EmptyDataError:
        print(f"{company_code}의 주식 가격 파일이 비어 있습니다.")
        return

    financial_data = pd.read_csv(financial_file)
    shares_outstanding = extract_shares_outstanding(issued_stock_file, quarter_month)
    '''
    # 이전 년도 재무 데이터를 읽고 비어 있는지 확인
    try:
        previous_financial_data = pd.read_csv(previous_financial_file)
        if previous_financial_data.empty:
            print(f"{company_code}의 이전 년도 재무 데이터가 비어 있습니다.")
            return None
    except pd.errors.EmptyDataError:
        print(f"{company_code}의 이전 년도 재무 데이터 파일이 비어 있습니다.")
        return None
    except FileNotFoundError:
        print(f"{company_code}의 이전 년도 재무 데이터 파일을 찾을 수 없습니다.")
        return None

    # 이전 년도 순이익 데이터 확인
    previous_net_income = previous_financial_data.loc[previous_financial_data['account_id'] == 'ifrs_ProfitLoss', 'thstrm_amount']
    if previous_net_income.empty:
        print(f"{company_code}의 이전 년도 순이익 데이터를 찾을 수 없습니다.")
        return None
    previous_net_income = previous_net_income.values[0]
    '''
    # calculate_pbr_per_roe 함수로 순이익 데이터를 전달
    result = calculate_pbr_per_roe(stock_price_data, financial_data, shares_outstanding, quarter_month)

    if result is not None:
        company_output_folder = os.path.join(output_folder, company_code)
        os.makedirs(company_output_folder, exist_ok=True)
        
        # 동적으로 파일 이름 생성 (예: calculated_result_2020_06.csv)
        output_file = os.path.join(company_output_folder, f'calculated_result_2020_{quarter_month}.csv')
        result.to_csv(output_file, index=False)
        print(f'Saved: {output_file}')

# 모든 분기를 처리하도록 process_all_companies 확장
def process_all_companies(base_financial_folder, base_issued_stock_folder, stock_price_base_folder, output_folder):
    quarters = {
        'Q1': ['03', '03'],
        'Q2': ['06', '05'],
        'Q3': ['09', '08'],
        'Q4': ['12', '11']
    }
    
    
    for company_code in os.listdir(base_financial_folder):
        print(f"처리 중인 기업 코드: {company_code}")
        for quarter, months in quarters.items():
            try:
                financial_folder = os.path.join(base_financial_folder, company_code, f'2020.{months[1]}')
                #previous_financial_folder = os.path.join(base_financial_folder, company_code, f'2019.{months[1]}')

                if os.path.exists(financial_folder):
                    financial_file = os.path.join(financial_folder, f'2020.{months[1]}_{company_code}_재무제표 (2020.{months[1]}).csv')
                    #previous_financial_file = os.path.join(previous_financial_folder, f'2019.{months[1]}_{company_code}_재무제표 (2019.{months[1]}).csv')

                    issued_stock_folder = os.path.join(base_issued_stock_folder, company_code, f'2020.{months[0]}')

                    stock_price_file = os.path.join(stock_price_base_folder, '2020', company_code, f'{quarter}_{company_code}.csv')

                    # 각 파일의 존재 여부를 확인 후 처리
                if os.path.exists(financial_file) and os.path.exists(issued_stock_folder) and os.path.exists(stock_price_file):
                    process_single_company(stock_price_file, financial_file, issued_stock_folder, output_folder, company_code, months[0])
                else:
                    print(f'{company_code}의 필요한 파일이 존재하지 않습니다.')
            except Exception as e:
                print(f"{company_code} 처리 중 오류 발생: {str(e)}")



# 경로 설정
base_financial_folder = '/Users/gamjawon/finTF/store_data/raw/opendart/store_financial_statement'
base_issued_stock_folder = '/Users/gamjawon/finTF/store_data/raw/opendart/store_reports'
stock_price_base_folder = '/Users/gamjawon/Downloads/price_data'
output_folder = '/Users/gamjawon/Documents/store_financial_statement'

# 모든 기업 처리 실행
process_all_companies(base_financial_folder, base_issued_stock_folder, stock_price_base_folder, output_folder)
