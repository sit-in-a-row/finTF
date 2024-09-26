from pykrx import stock
import os
import time

def get_index_csvs(target_business_year:str):
    '''
    목표한 사업연도에 대해 pykrx가 제공하는 
    ['코스피','코스피 대형주','코스피 중형주','코스피 소형주','음식료품','섬유의복','종이목재','화학','의약품','비금속광물','철강금속','기계','전기전자','의료정밀','운수장비','유통업','전기가스업','건설업','운수창고업','통신업','금융업','증권','보험','서비스업','제조업','코스피 200','코스피 100','코스피 50','코스피 200 커뮤니케이션서비스','코스피 200 건설','코스피 200 중공업','코스피 200 철강/소재','코스피 200 에너지/화학','코스피 200 정보기술','코스피 200 금융','코스피 200 생활소비재','코스피 200 경기소비재','코스피 200 산업재','코스피 200 헬스케어','코스피 200 중소형주','코스피 200 초대형제외 지수','코스피 200 비중상한 30%','코스피 200 비중상한 25%','코스피 200 비중상한 20%','코스피200제외 코스피지수','코스피 200 TOP 10']
    의 인덱스들 모두 가져와서, 각 csv파일을 모두 별도로 저장.

    이때, 경로는 ~./{store_data}/raw/market_data/{인덱스명}/{사업연도}/{사업연도}_{인덱스명}.csv
    '''
    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # 저장 경로 부모 디렉토리의 절대 경로 생성
    store_path_parent = os.path.join(current_dir, f'../../../store_data/raw/market_data/')

    # 종목 코드를 key, 종목명을 value로 하는 dict 생성
    index_ticker_dict = {}
    for ticker in stock.get_index_ticker_list():
        index_ticker_dict[ticker] = stock.get_index_ticker_name(ticker)

    # 종목 코드만 list로 담아두기
    index_ticker_list = list(index_ticker_dict.keys())

    # 정보 조회 후 정의된 경로에 저장하기
    for i in range(len(index_ticker_list)):
        index_ticker = index_ticker_list[i]
        index_name = index_ticker_dict[index_ticker]

        start_date = f'{target_business_year}0101'
        end_date = f'{target_business_year}1231'
        
        info = stock.get_index_ohlcv(start_date, end_date, index_ticker)

        # 최종 저장 경로 생성
        store_path = os.path.join(store_path_parent, f'{index_name}/{target_business_year}/{target_business_year}_{index_name}.csv')

        # 디렉토리 생성 (이미 존재하는 경우 예외 처리)
        os.makedirs(os.path.dirname(store_path), exist_ok=True)

        # DataFrame을 CSV 파일로 저장
        info.to_csv(store_path, index=True)

        # api 호출 빈도 조정
        time.sleep(0.5)

        print(f'{target_business_year} {index_name} CSV 파일 저장 {i+1}/{len(index_ticker_list)}')

    print(f'인덱스 지표 CSV 파일 저장 성공')