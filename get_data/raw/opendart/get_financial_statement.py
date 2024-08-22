import io
import re
import os
import json
import yaml
import time
import zipfile
import requests
import OpenDartReader

import pandas as pd
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

yaml_path = '../../../config/api_keys.yaml'
# YAML 파일 읽기
with open(yaml_path, "r") as file:
    config = yaml.safe_load(file)

# 필요한 값 가져오기
api_key = config['api_keys']['open_dart']

# dart 초기화
dart = OpenDartReader(api_key)

# 검색대상 종목코드
stock_code = '005930'
target_business_year = 2019

# 고유번호 수집 함수
def opendart_corp_codes(api_key):
    '''
    고유번호 수집하여 종목코드와 dart상의 corpcode간의 호환성 대응
    종목코드 수집 후 df로 변환하여 추가 작업 진행
    '''
    try:
        url = 'https://opendart.fss.or.kr/api/corpCode.xml'
        params = { 'crtfc_key': api_key }
        r = requests.get(url, params=params)
        zf = zipfile.ZipFile(io.BytesIO(r.content))
        xml_data = zf.read('CORPCODE.xml')
        tree = ET.XML(xml_data)
        all_records = []
        element = tree.findall('list')
        for child in element:
            record = {subchild.tag: subchild.text for subchild in child}
            all_records.append(record)
        corp_codes = pd.DataFrame(all_records)
        print('dart 기준 기업 고유 번호 수집 성공')
        return corp_codes
    except:
        print('dart 기준 기업 고유 번호 수집 실패')
        return None


# 종목코드를 고유번호로 변환하는 함수
def change_stock_code(corp_codes, stock_code):
    '''
    수집한 정보에 대한 df를 바탕으로 종목코드와 corpcode 변환
    '''
    df = corp_codes[corp_codes['stock_code'] == stock_code]
    return df.iloc[0]['corp_code'] if not df.empty else None

# 재무제표 요청 함수
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
        print('재무제표 정보 api 요청 성공')
        return pd.json_normalize(jo, 'list')
    except:
        print('재무제표 정보 api 요청 실패')
        return None

# 종목코드를 입력받아 재무제표 데이터를 반환하는 함수
def get_financial_statements(stock_code: str, target_business_year: int):
    '''
    재무제표 데이터를 api로 받아오는 기능의 main 함수
    종목코드와 목표 영업연도 입력 시 df 반환
    '''
    try:
        corp_codes = opendart_corp_codes(api_key)
        corp_code = change_stock_code(corp_codes, stock_code)
        reprt_codes = ['11013', '11012', '11014', '11011']
        fs_div = 'CFS'
        
        total_df = pd.DataFrame()

        start_year = target_business_year
        end_year = start_year + 1

        for bsns_year in range(start_year, end_year):
            bsns_year = str(bsns_year)
            for reprt_code in reprt_codes:
                df = opendart_finance(api_key, corp_code, bsns_year, reprt_code, fs_div)
                if not df.empty:
                    df['연결구분'] = '연결' if fs_div == 'CFS' else '개별'
                    total_df = pd.concat([total_df, df], ignore_index=True)
        
        print('재무제표 데이터 다운로드에 성공했습니다.')
        return total_df
    except:
        print('재무제표 데이터 다운로드에 실패했습니다.')
        return None
    
def get_report_code_dict(stock_code: str, target_business_year: int):
    '''
    보고서의 코드를 가져오는 코드. {리포트 이름: 리포트 코드} 형식으로 반환
    '''
    start_year = target_business_year
    end_year = target_business_year + 1

    try:
        report = dart.list(stock_code, start=str(start_year), end=str(end_year), kind='A', final=False)

        report_code_dict = {}
        for ix, row in report.iterrows():
            report_name = row['report_nm']
            report_code = row['rcept_no']
            report_code_dict[report_name] = report_code

        print('보고서 코드 다운로드 성공.')
        return report_code_dict
    except:
        print('보고서 코드 다운로드 실패.')
        return None
    
def get_sub_report_text(url):
    '''
    텍스트를 실제로 api에 요청하는 코드
    최초에 time.sleep(0.1)로 했더니 서버가 문 닫아버림..ㅠ
    일단 time.sleep(5)로 하니까 잘 돌아감 (2024.08.22)
    '''
    try:
        time.sleep(5)
        response = requests.get(url)
        cleaned_text = cleanse_text(response)

        print('보고서 텍스트 api 요청 성공')
        return cleaned_text
    
    except:
        print('보고서 텍스트 api 요청 실패')
        return None

def cleanse_text(response):
    '''
    과도한 줄바꿈을 클렌징해주는 코드 (줄바꿈이 연속될 시, 줄바꿈을 1개로 제한)
    '''
    try:
        # 연속된 줄바꿈을 하나의 줄바꿈으로 바꾸기
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        cleaned_text = re.sub(r'\n+', '\n', text)

        print('텍스트 클렌징 성공')
        return cleaned_text
    except:
        print('텍스트 클렌징 실패')
        return None


def get_sub_report(stock_code, target_business_year):
    '''
    하위 보고서를 모두 가져오는 main함수.
    하위 보고서의 코드를 get_report_code_dict()를 통해 가져온 다음,
    report_code에 대해 존재하는 모든 하위 문서를 dart.sub_docs()로 추출한 뒤
    get_sub_report_text()로 데이터 클렌징 및 딕셔너리 양식으로 정리하여
    sub_report_dict에 저장
    '''
    sub_report_dict = {}
    count = 0

    try:
        report_code_dict = get_report_code_dict(stock_code, target_business_year)
        report_name_list = list(report_code_dict.keys())
        for i in range(len(report_name_list)):
            sub_report_df = dart.sub_docs(report_code_dict[report_name_list[i]])
            for j in range(len(sub_report_df)):
                sub_report_title = sub_report_df.iloc[j]['title']
                sub_report_url = sub_report_df.iloc[j]['url']
                sub_report_text = get_sub_report_text(sub_report_url)
                sub_report_dict[f'{report_name_list[i]} | {sub_report_title}'] = [sub_report_text]

                count += 1
                print(f'{report_name_list[i]} | {sub_report_title} 추출 완료. {round(((i*j)/count)*100, 2)}% 완료')

        print('하위 보고서 다운로드에 성공했습니다.')
        return sub_report_dict
    
    except:
        print('하위 보고서 다운로드에 실패했습니다.')
        return None

def get_index_dict(sub_report_dict):
    '''
    보고서 머리글에 있는 날짜 형식을 추출해서, 동일한 날짜에 해당하는 인덱스값을 같은 키로 묶어서 반환
    '''
    try:
        sub_report_dict_keys_list = list(sub_report_dict.keys())
        index_dict = {}
        for i in range(len(sub_report_dict_keys_list)):
            date = sub_report_dict_keys_list[i].split(' | ')[0].split(' ')[1][1:-1]
            if date in index_dict:  # date가 이미 index_dict에 존재하는지 확인
                sub_list = index_dict[date]
                sub_list.append(i)
            else:
                index_dict[date] = [i]  # date가 없으면 새로운 리스트 생성
        print('index_dict 생성 성공')
        return index_dict
    except:
        print('index_dict 생성 실패')
        return None

def sub_reports_to_csv(sub_report_dict):
    '''
    csv 저장 경로 설정 및 저장
    '''
    try:
        index_dict = get_index_dict(sub_report_dict)

        sub_report_dict_keys_list = list(sub_report_dict.keys())
        store_path_parent = f'../../../store_data/raw/opendart/store_reports/{stock_code}'
        
        index_dict_keys_list = list(index_dict.keys())

        for i in range(len(index_dict)):
            for j in range(len(index_dict_keys_list)):
                date = index_dict_keys_list[j]
                for k in range(len(index_dict[date])):
                    report_title = sub_report_dict_keys_list[index_dict[date][k]]
                    store_path = f'{store_path_parent}/{date}/{date}_{stock_code}_{report_title}.csv'

                    # 디렉토리 생성 (이미 존재하는 경우 예외 처리)
                    os.makedirs(os.path.dirname(store_path), exist_ok=True)

                    temp_df = pd.DataFrame(
                        {'text': [sub_report_dict[report_title]]},
                        index=[report_title]
                    )
                    temp_df.to_csv(store_path, index=False)
        print('csv 저장 성공')
        return None
    except:
        print('csv 저장 실패')
        return None

def save_sub_reports(stock_code, target_business_year):
    '''
    보고서 저장 기능의 main함수
    '''
    try:
        sub_report_dict = get_sub_report(stock_code, target_business_year)
        sub_reports_to_csv(sub_report_dict)
        print('사업보고서 저장에 성공했습니다.')
    except:
        print('사업보고서 저장에 실패했습니다.')

def divide_statement_df(financial_statements):
    '''
    하나의 business year 안에 있는 n개의 보고서를 n개의 데이터프레임으로 분할하는 함수
    '''
    try:
        # rcept_no 값들을 리스트로 추출
        rcept_no_list = list(set(financial_statements['rcept_no']))

        df_list = []
        # 각 rcept_no에 대해 데이터프레임 필터링 후 리스트에 추가
        for rcept_no in rcept_no_list:
            filtered_df = financial_statements[financial_statements['rcept_no'] == rcept_no]
            df_list.append(filtered_df)

        print('재무제표 필터링 성공')
        return df_list
    except:
        print('재무제표 필터링 실패')
        return None
    
def save_financial_statement(stock_code, target_business_year):
    '''
    분할된 데이터프레임을 필요 경로에 저장하는 함수, main함수
    '''
    try:
        financial_statements = get_financial_statements(stock_code, target_business_year)
        df_list = divide_statement_df(financial_statements)
        store_path_parent = f'../../../store_data/raw/opendart/store_financial_statement/{stock_code}'

        for i in range(len(df_list)):
            df_to_save = df_list[i]
            time_raw = list(df_to_save['rcept_no'])[0][0:9]
            year = time_raw[0:4]
            month = time_raw[4:6]
            folder_path = f'{year}.{month}'
            statement_title = f'{folder_path}_{stock_code}_재무제표 ({folder_path}).csv'
            store_path = f'{store_path_parent}/{folder_path}/{statement_title}'

            # 디렉토리 생성 (이미 존재하는 경우 예외 처리)
            os.makedirs(os.path.dirname(store_path), exist_ok=True)
            df_to_save.to_csv(store_path, index=False)

        print('재무제표 저장에 성공했습니다.')
        return None
    except:
        print('재무제표 저장에 실패했습니다.')
        return None
    
def get_financial_info(stock_code, target_business_year):
    '''
    Opendart 관련 기능의 최종 main 함수.
    재무제표 및 공시 보고서를 모두 가져와 저장
    '''
    save_financial_statement(stock_code, target_business_year)
    save_sub_reports(stock_code, target_business_year)
    return print(f'OpenDart API를 통해 {stock_code}의 재무제표와 보고서를 성공적으로 저장하였습니다.') 

get_financial_info(stock_code, target_business_year)