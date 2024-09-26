import os
import pandas as pd
from pykrx import bond

# 디렉토리 생성 함수
def create_directory(path):
    if not os.path.exists(path):
        os.makedirs(path)

# pykrx를 이용하여 국채 수익률 데이터를 가져오는 함수
def get_bond_yield_data(year, start_date, end_date, bond_type="전종목"):
    """
    pykrx를 이용하여 국채 수익률 데이터를 가져오는 함수
    :param start_date: 데이터 조회 시작 날짜 (예: "20190208")
    :param end_date: 데이터 조회 종료 날짜 (예: "20190208")
    :param quarter: 저장할 분기명 (예: "Q1")
    :param bond_type: 조회할 채권 종류 (예: "국고채3년", "국고채10년" 등)
    :return: None
    """
    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 저장 경로 부모 디렉토리의 절대 경로 생성
    store_path_parent = os.path.join(current_dir, f'../../../store_data/raw/market_data/interest_rate_data')
    try:
        # 장외 채권 수익률 조회
        if bond_type == "전종목":
            df = bond.get_otc_treasury_yields(start_date)
        else:
            df = bond.get_otc_treasury_yields(start_date, end_date, bond_type)
        
        if df is not None and not df.empty:
            # 저장할 디렉토리 설정
            create_directory(store_path_parent)
            
            # 파일 경로 설정
            file_path = f"{store_path_parent}/{year}/{year}_korea_bond_yield.csv"
            os.makedirs(f"{store_path_parent}/{year}", exist_ok=True)
            
            # 데이터 CSV로 저장
            df.to_csv(file_path, encoding='utf-8-sig')
            print(f"{year} 국채 수익률 데이터 저장 완료: {file_path}")
        else:
            print(f"{start_date} ~ {end_date} 기간에 대한 {bond_type} 데이터가 없습니다.")
    
    except Exception as e:
        print(f"국채 수익률 데이터 가져오기 실패: {str(e)}")

# 분기별 국채 수익률 데이터를 저장하는 함수
def save_bond_yield_data(year):
    """
    분기별로 국채 수익률 데이터를 pykrx를 통해 가져와 저장하는 함수
    :param year: 조회할 연도 (예: 2023)
    :return: None
    """
    start_date = f'{year}0101'
    end_date = f'{year}1231'   
    # 전종목 채권 수익률 데이터를 저장
    get_bond_yield_data(year, start_date, end_date, bond_type="국고채1년")