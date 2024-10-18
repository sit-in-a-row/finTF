import os
import re
import json

from .regression import get_carhart_regression

current_dir = os.path.dirname(os.path.abspath(__file__))
ticker_path = os.path.join(current_dir, '../../../../../store_data/raw/market_data/price')
index_path = os.path.join(current_dir, '../../../../../store_data/raw/market_data/sector')

def get_carhart_analysis(year:str, markets:list):
    '''
    year와 markets를 입력하면 해당 연도와 시장에 대해 분석결과를 ./sector_analysis/index_analysis에 저장
    단, 이때 markets는 list 형태로 전달해야 함

    ex. get_carhart_analysis('2019', ['코스피'])
    '''
    tickers = os.listdir(ticker_path) + os.listdir(index_path)
    quarters = ['Q1', 'Q2', 'Q3', 'Q4']

    for quarter in quarters:
        # 결과 저장을 위한 경로 생성
        save_path = os.path.join(current_dir, f'../../../../../store_data/process/analysis/index_analysis/{year}/{quarter}')
        if not os.path.exists(save_path):
            os.makedirs(save_path)

        # 분석을 시장별로 수행
        for i, market in enumerate(markets):
            market_json_path = os.path.join(save_path, f'{market}_carhart_results.json')
            
            # 이미 존재하는 파일이 있으면 기존 데이터를 로드하고, 없으면 빈 딕셔너리 초기화
            if os.path.exists(market_json_path):
                with open(market_json_path, 'r', encoding='utf-8') as f:
                    market_results = json.load(f)
            else:
                market_results = {}
            
            for j, ticker in enumerate(tickers):
                try:
                    # Carhart 4 Factor 모델 회귀 분석 수행
                    result = get_carhart_regression(ticker, market, year, quarter)
                    
                    # 회귀 결과를 문자열로 변환 후 리스트로 저장
                    result_str = str(result.summary()).split('\n')
                    
                    # ticker를 key로 하고 회귀 결과를 value로 저장
                    market_results[ticker] = result_str

                    print(f'({quarter}) 시장 {market} ({i+1}/{len(markets)}) 와(과) 종목 {ticker} ({j+1}/{len(tickers)})에 대해 분석 완료!')

                    # 실시간으로 JSON 파일에 저장
                    with open(market_json_path, 'w', encoding='utf-8') as f:
                        json.dump(market_results, f, ensure_ascii=False, indent=4)

                except Exception as e:
                    print(f'({quarter}) 시장 {market} ({i+1}/{len(markets)}) 와(과) 종목 {ticker} ({j+1}/{len(tickers)})에 대해 분석 실패! {e}')