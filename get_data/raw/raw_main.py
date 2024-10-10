# # 매일 업데이트가 필요한 정보
# get_daily_OHLCV(start_date, end_date, stock_code)
# get_real_time_OHLCV(stock_code)
# get_index_csvs(target_business_year)
# crawl_sedaily_news(keyword, start_date, end_date)

# # 매주 업데이트가 필요한 정보
# crawl_ir_pdfs()

# # 매달 업데이트가 필요한 정보
# get_financial_info(stock_code, target_business_year)
# get_global_info(start_date, end_date)

from .opendart import get_financial_info
from .market_data import get_daily_OHLCV, get_real_time_OHLCV, get_index_csvs, get_bond_yield_data, get_market_cap
from .crawling import crawl_ir_pdfs, crawl_sedaily_news
from .FRED import get_global_info

from .util import get_quarterly_market_ticker_list

def update_all_raw_info(start_date:str, end_date:str):
    '''
    start_date, end_date 사이의

    ====================================================

    1. 주식 가격 데이터 (일별)
    2. 주요 산업 지표 (일별)
    3. 재무제표 (분기별)
    4. IR 자료 (업데이트 되는대로)
    5. 뉴스 헤드라인 (종목별, 일별)
    6. 뉴스 헤드라인 (경제 동향, 경제 주체 심리, 국제정치 동향, 일별)
    7. 글로벌 경제 지표 (미, EU, 영, 일, 중, 월별)
    
    ====================================================

    데이터를 모두 업데이트
    '''
    # 분기별로 종목리스트 나누어서 받아오기
    market_list = get_quarterly_market_ticker_list(start_date, end_date)
    quarter_keys = list(market_list.keys())
    print('=== 분기별 종목리스트 생성 완료 ===')

    is_already_updated = False

    # 분기별로 나눈 값에 대해 처리
    for i in range(len(quarter_keys)):
        print(f'=== {quarter_keys[i]}에 대한 정보 수집 시작 ({i+1}/{len(quarter_keys)}) ===')

        target_quarter = market_list[quarter_keys[i]]

        # 각 쿼터별 시작일, 종료일 및 티커 딕셔너리 ({티커}: {종목명}}) 를 각각 바인딩
        target_quarter_start_date = target_quarter['start_date']
        target_quarter_end_date = target_quarter['end_date']
        target_quarter_market_list = target_quarter['market_list']

        target_business_year = target_quarter_start_date[:4]

        # 각 분기에 해당하는 종목 리스트
        stock_code_list = list(target_quarter_market_list.keys())

        is_fin_info_updated = {}
        ### === get_daily_OHLCV() 업데이트 ===
        ### === crawl_sedaily_news() 업데이트 (종목에 대한 크롤링 진행) === 
        ### === get_financial_info() 업데이트 ===
        stock_size = len(stock_code_list)
        # stock_code_list
        for j in range(0, stock_size):
            stock_code = stock_code_list[j];
            print("" + str(j+1) + " / " + str(stock_size));
            print(f'=== {quarter_keys[i]}의 {stock_code}에 대해 정보 수집 시작 ({stock_code_list.index(stock_code) + 1}/{len(stock_code_list)}) ===')

            print(f'=== {stock_code}에 대한 {target_quarter_start_date}에서 {target_quarter_end_date}까지의 가격데이터 저장 중... ===')
            get_daily_OHLCV(target_quarter_start_date, target_quarter_end_date, stock_code)
            print(f'=== {stock_code}에 대한 {target_quarter_start_date}에서 {target_quarter_end_date}까지의 가격데이터 저장 완료 ===')

            print(f'=== {stock_code}에 대한 {target_quarter_start_date}에서 {target_quarter_end_date}까지의 뉴스 헤드라인 데이터 저장 중... ===')
            crawl_sedaily_news(stock_code, target_quarter_start_date, target_quarter_end_date)
            print(f'=== {stock_code}에 대한 {target_quarter_start_date}에서 {target_quarter_end_date}까지의 뉴스 헤드라인 데이터 저장 완료 ===')

            try:
                is_updated = is_fin_info_updated[stock_code]
                print(f'=== {stock_code}에 대한 {target_business_year} 재무 데이터가 이미 존재합니다. 요청을 건너뜁니다 ===')
            except:
                print(f'=== {stock_code}에 대한 {target_business_year} 재무 데이터 저장 중 ===')
                get_financial_info(stock_code, target_business_year)
                print(f'=== {stock_code}에 대한 {target_business_year} 재무 데이터 저장 완료 ===')
                is_fin_info_updated[stock_code] = True

            # # 인자로 연도를 받고, 한번만 실행해도 모든 연도에 대한 값이 들어오기 때문에 1번만 실행 (플래그를 활용하여 False일 때만 진행)
            # if is_fin_info_updated == False:
            #     print(f'=== {stock_code}에 대한 {target_business_year} 재무 데이터 저장 중... ===')
            #     get_financial_info(stock_code, target_business_year)
            #     print(f'=== {stock_code}에 대한 {target_business_year} 재무 데이터 저장 완료 ===')

            #     is_fin_info_updated = True
            # else:
            #     print(f'=== 이미 업데이트된 {stock_code}에 대한 {target_business_year} 재무 데이터입니다. ===')
            #     continue

        ### === get_index_csvs() 업데이트 ===
        # 인자로 연도를 받고, 한번만 실행해도 모든 연도에 대한 값이 들어오기 때문에 1번만 실행 (플래그를 활용하여 False일 때만 진행)
        if is_already_updated == False:
            print(f'=== {target_business_year} 산업군 지표 데이터 저장 중... ===')
            get_index_csvs(target_business_year)
            print(f'=== {target_business_year} 산업군 지표 데이터 저장 완료 ===')

            is_already_updated = True
        else:
            print(f'=== 이미 업데이트된 {target_business_year} 산업군 지표 데이터입니다. ===')
            continue

        ### === crawl_sedaily_news() 업데이트 (검색어에 대한 크롤링 진행) ===
        # 검색 시 활용할 키워드 모음.
        # 각각 경제동향, 경제 주체의 심리, 국제정치 동향에 대한 키워드
        search_keyword_list = [
            '금리 환율 물가 통화',
            '소비자 생산 투자',
            '전쟁 제재 갈등'
        ]
        for search_keyword in search_keyword_list:
            print(f'=== {search_keyword}에 대한 {target_quarter_start_date}에서 {target_quarter_end_date}까지의 뉴스 헤드라인 데이터 저장 중... ===')
            crawl_sedaily_news(search_keyword, target_quarter_start_date, target_quarter_end_date)
            print(f'=== {search_keyword}에 대한 {target_quarter_start_date}에서 {target_quarter_end_date}까지의 뉴스 헤드라인 데이터 저장 완료 ===')

    # ### === crawl_ir_pdfs() 업데이트 ===
    # # 한 번 실행 시 모든 정보를 다 가져오므로 분기별로 나누어 실행할 필요 없음
    # print('=== IR 자료 저장 중... ===')
    # crawl_ir_pdfs()
    # print('=== IR 자료 저장 완료 ===')

    # ### === get_global_info() 업데이트 ===
    # # start_date와 end_date에 대해 한 번에 받아와도 되는 함수
    # # FRED api로 가져오기 때문에 정보를 금방 가져오기도 하고, 분기별로 나누어 실행할 필요가 없음
    # # 국내 주식장이 아니라 해외 경제 지표들에 대한 함수이기 때문
    # print('=== 글로벌 경제 지표 저장 중... ===')
    # get_global_info(start_date, end_date)
    # print('=== 글로벌 경제 지표 저장 완료 ===')

    ### === get_bond_yield_data() 업데이트 ===
    year = start_date[:4]
    print('=== 국채 1년물 수익률 저장 중... ===')
    get_bond_yield_data(year, start_date, end_date)
    print('=== 국채 1년물 수익률 저장 완료 ===')

    ### === get_market_cap() 업데이트 ===
    print('=== 시가총액 정보 저장 중... ===')
    get_market_cap(year)
    print('=== 시가총액 정보 저장 완료 ===')
    

    print(f'{start_date}에서 {end_date}까지의 정보를 모두 업데이트 하였습니다!')