import pandas as pd
import requests
import zipfile
import xml.etree.ElementTree as ET
import json
import io
import time
import OpenDartReader

from .util import cleanse_text
from .config import get_api_key

# dart 초기화
api_key = get_api_key()
dart = OpenDartReader(api_key)

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
    except Exception as e:
        print(f'dart 기준 기업 고유 번호 수집 실패: {str(e)}')
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
    except Exception as e:
        print(f'재무제표 정보 api 요청 실패 {str(e)}')
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

        print('보고서 코드 다운로드 성공.')
        return report_code_dict
    except Exception as e:
        print(f'보고서 코드 다운로드 실패. {str(e)}')
        return None
     
def get_sub_report_text(url):
    '''
    텍스트를 실제로 api에 요청하는 코드
    최초에 time.sleep(0.1)로 했더니 서버가 문 닫아버림..ㅠ
    일단 time.sleep(5)로 하니까 잘 돌아감 (2024.08.22)
    '''
    try:
        time.sleep(3)
        response = requests.get(url)
        cleaned_text = cleanse_text(response)

        print('보고서 텍스트 api 요청 성공')
        return cleaned_text
    except Exception as e:
        print(f'보고서 텍스트 api 요청 실패 {str(e)}')
        return None
    
def get_sub_report(stock_code:str, target_business_year:str):
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
        if report_code_dict is None:
            raise ValueError("report_code_dict가 None입니다.")

        report_name_list = list(report_code_dict.keys())
        for i in range(len(report_name_list)):
            sub_report_df = dart.sub_docs(report_code_dict[report_name_list[i]])
            for j in range(len(sub_report_df)):
                sub_report_title = sub_report_df.iloc[j]['title']
                sub_report_url = sub_report_df.iloc[j]['url']
                sub_report_text = get_sub_report_text(sub_report_url)
                sub_report_dict[f'{report_name_list[i]} | {sub_report_title}'] = [sub_report_text]
                count += 1
                print(f'{report_name_list[i]} | {sub_report_title} 추출 완료. {count}/{len(report_name_list) * len(sub_report_df)}')

        print('하위 보고서 다운로드에 성공했습니다.')
        return sub_report_dict
    
    except Exception as e:
        print(f'하위 보고서 다운로드에 실패했습니다. {str(e)}')
        return None
    
# 종목코드를 입력받아 재무제표 데이터를 반환하는 함수
def get_financial_statements(stock_code: str, target_business_year: str):
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

        start_year = int(target_business_year)
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
    except Exception as e:
        print(f'재무제표 데이터 다운로드에 실패했습니다. {str(e)}')
        return None