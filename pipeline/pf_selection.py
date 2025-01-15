from sub_func import *

pf_selection_report_format = """{
report: '(생성한 레포트 본문 전체)',
sector: '[레포트 내에 언급된 주요 섹터를 리스트 형식으로 반환]'
}
"""

pf_selection_system = f"""당신은 증권회사의 포트폴리오 전문가입니다.
주어진 다음 정보들은 이전 분기의 국제 뉴스, 거시경제 정보, 인덱스 지표들의 가격입니다.
이를 바탕으로 다음 분기에 주목해야 할 섹터를 정리해서 보고서 형식으로 출력해야 합니다.
보고서의 의견은 반드시 주어진 정보에 기반하여야 합니다.
보고서의 형식은 반드시 다음을 따라야 합니다. {pf_selection_report_format}

** Return only pure JSON format without any code block or delimiters. **
** Make sure that the response does not create JSON decode error. **
"""

# ================================ #

pf_selection_corp_format = """{
report: '(생성한 레포트 본문 전체)',
invest: '(True or False로만 답하세요.)'
}
"""

pf_selection_corp_system = f"""당신은 증권회사의 분석가입니다.
주어진 자료들을 바탕으로 다음 분기동안 해당 종목을 보유해야할지 판단하고 이를 보고서 형식으로 작성해야 합니다.
보고서의 의견은 반드시 주어진 정보에 기반하여야 합니다.
보고서의 형식은 반드시 다음을 따라야 합니다. {pf_selection_corp_format}

** Return only pure JSON format without any code block or delimiters. **
** Make sure that the response does not create JSON decode error. **
"""

# ================================ #

def get_sector_selection_report(target_year, start_date, end_date):
    """
    pf_selection_agent가 1차적으로 국제뉴스, 거시경제정보, 인덱스가격에 기반해 어떤 섹터에 투자할지 결정

    이때,
    pf_selection_report: 생성한 보고서
    pf_selection_sector: 보고서의 결론 (어떤 업종에 투자할 것인가?), list
    """
    print('='*50)
    print(f'{target_year}의 {start_date} ~ {end_date} 섹터 선정 보고서 생성 시작...')

    pf_selection_prompt = f""""""

    # ==== 국제 뉴스 수집 ==== #
    intl_news_title_list = list(intl_news_info(target_year, start_date, end_date)['news_title'])
    pf_selection_prompt += f"""국제 뉴스 헤드라인: {intl_news_title_list}\n"""
    print('-'*50)
    print('국제 뉴스 수집 완료!')

    # ==== 거시경제 정보 수집 ==== #
    def create_macro_econ_dict(country, econ_item):
        result_dict = macro_econ_dict[country][econ_item].set_index('Date').to_dict('index')
        final_dict = {k: v[list(v.keys())[0]] for k, v in result_dict.items()}

        return final_dict

    reports_dict = {}
    macro_econ_dict = macro_econ_info(target_year, start_date, end_date)
    country_list = list(macro_econ_dict.keys())

    for country in country_list:
        target_country_dict = macro_econ_dict[country]
        econ_items = list(target_country_dict.keys())
        for econ_item in econ_items:
            final_dict = create_macro_econ_dict(country, econ_item)
            reports_dict[f"{country}_{econ_item}"] = final_dict
    pf_selection_prompt += f"""국가별 거시경제 정보: {reports_dict}\n"""
    print('-'*50)
    print('거시경제 정보 수집 완료!')

    # ==== 인덱스 가격 수집 ==== #
    index_prices = {}
    sector_list = [s for s in os.listdir('../store_data/raw/market_data/sector') if '코스피' not in s]

    for sector in sector_list:
        # 토큰수 제한때문에 컬럼 선별해서 넣기...
        index_price = index_price_info(sector, start_date, end_date)[['Close', 'Transaction_Val','Market_Cap', 'RSI_14']]
        index_prices[sector] = index_price.T.to_dict()

    pf_selection_prompt += f"""인덱스 가격 지표: {index_prices}\n"""
    print('-'*50)
    print('인덱스 가격 지표 수집 완료! GPT 생성을 기다리는 중...')

    stock_selection_response = to_GPT(pf_selection_system, pf_selection_prompt)
    print('-'*50)
    print('GPT 응답 수신 완료!')

    # 여기까지 해서, 투자할 섹터 결정
    try:
        sample = eval(stock_selection_response['choices'][0]['message']['content'])
        pf_selection_report = sample['report']
        pf_selection_sector = sample['sector']
    except Exception as e:
        print('-'*50)
        print(f"GPT 응답 구조가 올바르지 않음: {e}")

    return {
        'pf_selection_report': pf_selection_report,
        'pf_selection_sector': pf_selection_sector
    }

def generate_final_portfolio(target_year, target_quarter, start_date, end_date, pf_selection_sector):
    """
    주어진 조건에 따라 최종 포트폴리오 리스트를 생성하는 함수.

    Args:
        target_year (int): 대상 연도
        target_quarter (int): 대상 분기
        start_date (str): 시작 날짜 (YYYYMMDD)
        end_date (str): 종료 날짜 (YYYYMMDD)
        pf_selection_sector (list): 선택된 섹터 리스트

    Returns:
        list: 최종 포트폴리오에 포함된 티커 리스트
    """
    temp_tickers_list = []
    store_all_raw_pf_selection = {}

    print('='*50)
    print('최종 포트폴리오 종목 선정 시작...')

    # 섹터 기반 포트폴리오 가져오기
    print('-'*50)
    temp_pf = get_pf(target_year, target_quarter, pf_selection_sector)
    print('공시 보고서 탐색 완료!')

    # 중복되지 않은 티커 리스트 생성 (다른 업종이지만 같은 종목이 있는 경우)
    for sector in temp_pf:
        for ticker in temp_pf[sector]:
            if ticker not in temp_tickers_list:
                temp_tickers_list.append(ticker)

    print('-'*50)
    print('각 티커에 대해 데이터를 처리합니다...')
    # 각 티커에 대한 데이터 처리
    for i, ticker in enumerate(temp_tickers_list):
        print(f'({i+1}/{len(temp_tickers_list)}) | {ticker}에 대해 정보 수집을 시작합니다...')
        pf_selection_corp_prompt = ""

        try:
            # 기업 관련 뉴스 수집 및 처리
            corp_rel_news_df = corp_rel_news_info(ticker, target_year, start_date, end_date)
            corp_rel_news_df = corp_rel_news_df[corp_rel_news_df['news_category'].str.contains('증권')]
            SA_result_corp_rel_news_dict = {'positive': [], 'negative': []}

            for i in range(len(corp_rel_news_df)):
                news_title = corp_rel_news_df.iloc[i]['news_title']
                SA_result = get_SA_result(news_title)

                if SA_result['label'] == 'positive' and SA_result['prob'] > 0.9:
                    SA_result_corp_rel_news_dict['positive'].append(news_title)
                elif SA_result['label'] == 'negative' and SA_result['prob'] > 0.9:
                    SA_result_corp_rel_news_dict['negative'].append(news_title)

            pf_selection_corp_prompt += f"기업 관련 뉴스: {SA_result_corp_rel_news_dict}\n"

        except Exception as e:
            print(f"{ticker}에 대해 뉴스를 찾을 수 없습니다. | {e}")

        try:
            # 가격 정보 수집
            price_dict = stock_price_info(ticker, start_date, end_date)[['Close', 'MA_20', 'RSI_14']].T.to_dict()
            pf_selection_corp_prompt += f"가격 정보: {price_dict}\n"
        except Exception as e:
            print(f"{ticker}에 대해 가격 정보를 찾을 수 없습니다. | {e}")

        try:
            # 재무 비율 정보 수집
            fin_statement_df = fin_statement_info(ticker, target_year, target_quarter)
            pf_selection_corp_prompt += f"재무비율: {fin_statement_df}\n"
        except Exception as e:
            print(f"{ticker}에 대해 재무 비율을 찾을 수 없습니다. | {e}")

        try:
            # 재무 보고서 정보 수집
            main_reports_df = reports_info(ticker, target_year, target_quarter)
            fin_report_df = main_reports_df['1. 요약재무정보.csv'][0]
            pf_selection_corp_prompt += f"재무보고서: {fin_report_df}\n"
        except Exception as e:
            print(f"{ticker}에 대해 재무보고서를 찾을 수 없습니다. | {e}")

        try:
            # GPT로 분석 요청
            pf_selection_corp_response = to_GPT(pf_selection_corp_system, pf_selection_corp_prompt)
            final_pf_selection_corp_response = eval(pf_selection_corp_response['choices'][0]['message']['content'])
            store_all_raw_pf_selection[ticker] = final_pf_selection_corp_response
            print('-'*50)
            print(f'{ticker}에 대해 보고서를 생성했습니다!')
        except Exception as e:
            print(f"{ticker}에 대한 분석의 GPT 응답 구조에 오류가 있습니다. | {e}")

    # 최종 포트폴리오 선정, invest가 'True'인 항목만 필터링하는 코드
    filtered_temp_pf = {
        sector: {ticker: value for ticker, value in tickers.items()
                if store_all_raw_pf_selection.get(ticker, {}).get('invest') == 'True'}
        for sector, tickers in temp_pf.items()
    }

    filtered_temp_pf['corp_analysis_report'] = store_all_raw_pf_selection

    return filtered_temp_pf

def pf_selection_main(target_year, target_quarter, start_date, end_date):
    sector_selection_report = get_sector_selection_report(target_year, start_date, end_date)

    pf_selection_report = sector_selection_report['pf_selection_report']
    pf_selection_sector = sector_selection_report['pf_selection_sector']

    final_portfolio = generate_final_portfolio(target_year, target_quarter, start_date, end_date, pf_selection_sector)

    return {
        'pf_selection_report': pf_selection_report,
        'pf_selection_sector': pf_selection_sector,
        'final_portfolio': final_portfolio
    }