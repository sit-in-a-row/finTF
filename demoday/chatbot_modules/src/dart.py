import pandas as pd
import requests
import zipfile
import xml.etree.ElementTree as ET
import json
import io
import os
import time
import OpenDartReader
import yaml
from bs4 import BeautifulSoup
import re
import concurrent.futures

# 현재 파일의 디렉토리 경로 가져오기
current_dir = os.path.dirname(os.path.abspath(__file__))
# yaml 파일의 절대 경로 생성
yaml_path = os.path.join(current_dir, '../../../config/api_keys.yaml')

# YAML 파일 읽기
with open(yaml_path, "r") as file:
    config = yaml.safe_load(file)

# 필요한 값 가져오기
api_key = config['api_keys']['open_dart']
dart = OpenDartReader(api_key)

csv_path = os.path.join(current_dir, '../corp_code/corp_code.csv')
corp_codes = pd.read_csv(csv_path)

def cleanse_text(response):
    '''
    과도한 줄바꿈을 클렌징해주는 코드 (줄바꿈이 연속될 시, 줄바꿈을 1개로 제한)
    '''
    try:
        # 연속된 줄바꿈을 하나의 줄바꿈으로 바꾸기
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        cleaned_text = re.sub(r'\n+', '\n', text)

        # print('텍스트 클렌징 성공')
        return cleaned_text
    except Exception as e:
        # print(f'텍스트 클렌징 실패 {str(e)}')
        return None

def change_stock_code(corp_codes, stock_code):
    '''
    수집한 정보에 대한 df를 바탕으로 종목코드와 corpcode 변환
    '''
    df = corp_codes[corp_codes['stock_code'] == stock_code]
    return str(df.iloc[0]['corp_code']).zfill(8) if not df.empty else None

def opendart_finance(api_key, corp_code, bsns_year, reprt_code, fs_div):
    '''
    dart로 정보 요청 (api 호출)
    '''
    try:
        url = 'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
        params = {
            'crtfc_key': api_key, 
            'corp_code': corp_code,
            'bsns_year': bsns_year,
            'reprt_code': reprt_code,
            'fs_div': fs_div
        }
        r = requests.get(url, params=params)
        jo = json.loads(r.text)
        if jo['status'] == '013':
            return pd.DataFrame()
        # print('재무제표 정보 api 요청 성공')
        return pd.json_normalize(jo, 'list')
    except Exception as e:
        # print(f'재무제표 정보 api 요청 실패 {str(e)}')
        return None
       
def get_report_code_dict(stock_code: str, target_business_year: str):
    '''
    보고서의 코드를 가져오는 코드. {리포트 이름: 리포트 코드} 형식으로 반환
    '''
    start_year = target_business_year  # 이미 문자열로 받아옴
    end_year = str(int(target_business_year) + 1)

    try:
        report = dart.list(stock_code, start=start_year, end=end_year, kind='A', final=False)

        report_code_dict = {}
        for ix, row in report.iterrows():
            report_name = row['report_nm']
            report_code = row['rcept_no']
            report_code_dict[report_name] = report_code

        # print('보고서 코드 다운로드 성공.')
        return report_code_dict
    except Exception as e:
        # print(f'보고서 코드 다운로드 실패. {str(e)}')
        return None
     
def get_sub_report_text(url):
    '''
    텍스트를 실제로 api에 요청하는 코드
    최초에 time.sleep(0.1)로 했더니 서버가 문 닫아버림..ㅠ
    일단 time.sleep(5)로 하니까 잘 돌아감 (2024.08.22)
    '''
    try:
        time.sleep(1)
        response = requests.get(url)
        cleaned_text = cleanse_text(response)

        # print('보고서 텍스트 api 요청 성공')
        return cleaned_text
    except Exception as e:
        # print(f'보고서 텍스트 api 요청 실패 {str(e)}')
        return None
    
def get_sub_report(stock_code:str, target_business_year:str):
    '''
    하위 보고서를 모두 가져오는 main함수.
    하위 보고서의 코드를 get_report_code_dict()를 통해 가져온 다음,
    report_code에 대해 존재하는 모든 하위 문서를 dart.sub_docs()로 추출한 뒤
    get_sub_report_text()로 데이터 클렌징 및 딕셔너리 양식으로 정리하여
    sub_report_dict에 저장
    '''

    try:
        report_code_dict_raw = get_report_code_dict(stock_code, target_business_year)
        keys = list(report_code_dict_raw.keys())[:2]
        report_code_dict = {key: report_code_dict_raw[key] for key in keys}

        report_name_list = list(report_code_dict.keys())
        sub_report_df = dart.sub_docs(report_code_dict[report_name_list[0]])
        sub_report_url = sub_report_df[sub_report_df['title']=='1. 요약재무정보']['url'].item()

        sub_report_text = get_sub_report_text(sub_report_url)
        return sub_report_text
    
    except Exception as e:
        # print(f'하위 보고서 다운로드에 실패했습니다. {str(e)}')
        return None

def get_financial_statements(stock_code: str, target_business_year: str):
    '''
    재무제표 데이터를 api로 받아오는 기능의 main 함수
    종목코드와 목표 영업연도 입력 시 df 반환
    '''
    try:
        corp_code = change_stock_code(corp_codes, stock_code)
        reprt_codes = ['11013', '11012', '11014', '11011']
        fs_div = 'CFS'
        
        total_df = pd.DataFrame()

        start_year = int(target_business_year)
        end_year = start_year + 1

        for bsns_year in range(start_year, end_year):
            bsns_year = str(bsns_year)
            for reprt_code in reprt_codes:
                df = opendart_finance(api_key, corp_code, bsns_year, reprt_code, fs_div)
                if not df.empty:
                    df['연결구분'] = '연결' if fs_div == 'CFS' else '개별'
                    total_df = pd.concat([total_df, df], ignore_index=True)
        
        # print('재무제표 데이터 다운로드에 성공했습니다.')
        return total_df
    except Exception as e:
        # print(f'재무제표 데이터 다운로드에 실패했습니다. {str(e)}')
        return None
    
def get_dart(ticker, past_date):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future1 = executor.submit(get_sub_report, ticker, past_date[:4])
        future2 = executor.submit(get_financial_statements, ticker, past_date[:4])

        fin_report = future1.result()
        fin_statement = future2.result()

    return fin_report, fin_statement
