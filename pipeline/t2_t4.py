from sub_func import *
from pf_selection import *
from pipeline_utils import *

from crawl_tradingview import *

from datetime import datetime, timedelta

current_dir = os.path.dirname(os.path.abspath(__file__))

# trader 중심 코드
def generate_trade_log(all_stocks):
    """GPT를 이용하여 거래 로그 생성 (매수/매도 포함)"""
    system_prompt = (
        "당신은 한국 주식 시장 트레이더입니다. "
        "주어진 종목 코드에 대해 거래 로그를 작성하세요. "
    )

    print("\nDEBUG: 종목 코드 사용 (Before Sending to GPT)")
    for code, stock in all_stocks.items():
        print(f"📌 종목 코드: {code}")  # 종목 코드만 출력

    stock_list = "\n".join([
        f"{code}: {stock['매수/매도']} | 목표가 {stock.get('목표가', 'Unknown')}원, 투자포인트 {stock.get('투자포인트', 'N/A')}"
        for code, stock in all_stocks.items()
    ])
    
    prompt = f"""
    다음 종목들에 대한 거래 로그를 작성하세요.
    해당 종목의 매수/매도 전략을 포함하여 아래 형식으로 작성하세요:

    형식:
    종목 코드 | 매수/매도 | 가격 | 투자포인트

    종목 리스트:
    {stock_list}
    
    또한 종목들에 대한 매수/매도 전략이 끝났다면 투자 순위와 주의할 점 등을 마지막에 한글로 첨부해주세요.
    """

    print("\n📝 Sending trade log request to GPT...")
    print(f"DEBUG: GPT로 전달하는 데이터:\n{stock_list}")  # GPT에 전달하는 데이터 확인

    response = to_GPT(system_prompt, prompt)

    trade_log = response["choices"][0]["message"]["content"]
    print("\n✅ Generated Trade Log:", trade_log)  # 최종 출력 확인
    
    return trade_log


# analyst 중심 코드
def fetch_news_data(ticker: str, year: int, quarter: int) -> pd.DataFrame:
    base_path = f"store_data/raw/crawling/corp_rel_news/{ticker}/{year}"
    quarter_months = {1: ['01', '02', '03'], 2: ['04', '05', '06'], 3: ['07', '08', '09'], 4: ['10', '11', '12']}
    news_data = []

    for month in quarter_months[quarter]:
        month_path = os.path.join(base_path, month)
        if os.path.exists(month_path):
            for file in os.listdir(month_path):
                if file.endswith(".csv"):
                    file_path = os.path.join(month_path, file)
                    print(f"📂 CSV 파일 로드 시도: {file_path}")
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8')  # CSV 파일 읽기
                        
                        # 1️**파일이 정상적으로 로드되었는지 확인**
                        print(f"CSV 데이터 미리보기 ({file_path}):")
                        print(df.head())  # CSV 내용 확인
                        
                        # 2️**컬럼명이 정확한지 확인**
                        print(f"CSV 파일의 컬럼명: {df.columns.tolist()}")

                        df.columns = [col.strip() for col in df.columns]  # 공백 제거
                        
                        # 3️*필요한 컬럼이 존재하는지 확인**
                        if not {'news_title', 'news_category', 'news_date'}.issubset(df.columns):
                            print(f"CSV 파일 {file_path}에 예상된 컬럼이 없습니다: {df.columns}")
                            continue  # 컬럼이 다르면 스킵

                        # 4️**날짜 변환이 정상적으로 되는지 확인**
                        df['news_date'] = pd.to_datetime(df['news_date'], format='%Y.%m.%d', errors='coerce')
                        print(f"변환된 날짜 데이터 (최초 5개):")
                        print(df['news_date'].head())

                        df = df.dropna(subset=['news_date'])  # 변환 실패한 날짜 제거
                        df.rename(columns={'news_title': 'headline'}, inplace=True)  # 컬럼명 변경
                        news_data.append(df[['news_date', 'headline']])
                    
                    except Exception as e:
                        print(f"⚠️ CSV 파일 읽기 오류: {file_path} - {e}")

    if news_data:
        news_df = pd.concat(news_data, ignore_index=True)
        news_df = news_df.sort_values(by='news_date')
        news_df.set_index('news_date', inplace=True)
    else:
        print(f"⚠️ {ticker}에 대한 {year} Q{quarter} 뉴스 데이터가 없습니다.")
        news_df = pd.DataFrame(columns=['news_date', 'headline'])

    return news_df


def analyze_news_combined(all_stocks, year, quarter):
    """모든 종목의 뉴스 분석을 한글로 요약하여 2000자 제한으로 리포트 생성"""
    system_prompt = f"""
    당신은 금융 애널리스트이며, 주식 뉴스를 분석하는 역할을 합니다.
    분석 대상 기간은 반드시 **{year}년 {quarter}분기**입니다. 
    다른 연도나 분기의 정보를 추가하지 말고, 제공된 데이터만 활용하세요.
    """

    stock_news = []
    for ticker in all_stocks.keys():
        news_df = fetch_news_data(ticker, year, quarter)

        if news_df.empty or 'headline' not in news_df.columns:
            print(f"🚨 {ticker} 뉴스 데이터가 비어 있음: news_df.empty = {news_df.empty}")
            stock_news.append(f"**종목 코드: {ticker}**\n현재 해당 종목과 관련된 주요 뉴스가 없습니다.")
        else:
            print(f"✅ {ticker} 뉴스 분석 중...")
            stock_news.append(f"**종목 코드: {ticker}**\n" + "\n".join(news_df['headline'].tolist()))

    news_report = "\n\n".join(stock_news)

    prompt = f"""
    아래는 {year}년 {quarter}분기 동안 각 종목과 관련된 뉴스 헤드라인입니다.
    반드시 **{year}년 {quarter}분기**에 해당하는 뉴스만 반영하여 한국어로 애널리스트 리포트를 작성하세요.
    **다른 연도나 최신 데이터를 언급하지 마세요.**
    
    {news_report}
    
    **출력 형식 예시**:
    
    **통합 애널리스트 리포트**
    
    {year}년 {quarter}분기 기준으로 여러 주요 종목에 대한 최근 뉴스와 시장 동향을 분석하여 다음과 같이 리포트를 작성합니다.
    
    1. **삼성전자 (005930)**  
    - 최근 반도체 시장 전망이 긍정적이며, {year}년 {quarter}분기 실적이 예상보다 강세를 보일 가능성이 있음.
    
    2. **현대차 (005380)**  
    - 전기차 사업 확장과 글로벌 공급망 개선이 예상되며, {year}년 {quarter}분기 동안 지속적인 성장세를 유지 중.

    같은 방식으로 보고서를 작성하세요.
    """

    response = to_GPT(system_prompt, prompt)
    
    return response["choices"][0]["message"]["content"][:2000]

def get_t_1_trader_report(today):
    json_file_path = os.path.join(current_dir, './notion_page_ids.json')
    data = read_json(json_file_path)
    t_1_trader_report_id = data['t_1'][f'{today}_t_1_trader_report']
    t_1_trader_report = get_all_text_from_page(t_1_trader_report_id)

    return t_1_trader_report

def get_t_2_t_4_trader_prompts(t_1_trader_report):
    trader_output_format = """{
        "log": "{매수/매도} | {수량} | {가격}"
    }"""

    trader_prompt = f"""당신은 주식 트레이더입니다.
    주어진 데이터를 분석하여 매수 또는 매도, 관망 여부를 결정하고 거래 로그를 작성해야 합니다.
    이때, 이전에 저장된 t1의 트레이더 output을 참고하여 더욱 정확한 거래를 해야 합니다.

    만약 매수 또는 매도를 진행한다면, 다음 양식을 따라야 합니다: {trader_output_format}
    만약 관망을 진행한다면, "관망"이라고 작성해야 합니다.

    추가적인 단어 생성 없이, 반드시 {trader_output_format}에 따라 dict만을 작성하거나, "관망"이라고 작성해야 합니다.

    당신의 역할은 수익성을 극대화하기 위해 정확하고 신속한 거래 결정을 내리는 것입니다.
    거래 로그는 반드시 지정된 형식을 따라야 합니다.

    t1의 트레이더 output: {t_1_trader_report}
    """

    return trader_prompt

def get_pf_weights_prompts(target_year, target_quarter, today, logs):
    pf_path = os.path.join(current_dir, f'./pf_logs/{target_year}_{target_quarter}/{today}_portfolio_weights.json')
    pf_before_update = read_json(pf_path)

    pf_update_system = """주어진 다음 거래 로그를 바탕으로 포트폴리오를 정확히 업데이트 하세요.
    추가적인 글이나 json delimiter 따위를 생성하지 말고, output을 바로 json으로 저장할 수 있도록 출력하세요.

    포트폴리오는 반드시 {ticker: weight} 형식을 따라야 합니다. 이때, 모든 종목의 weight의 합은 반드시 1이어야 합니다.
    """

    pf_update_prompt = f"""
    오늘의 거래 로그: {logs}
    이전 포트폴리오: {pf_before_update}
    """

    return {
        'pf_update_system': pf_update_system,
        'pf_update_prompt': pf_update_prompt
    }

def get_hourly_sp(tickers, start_date, today):
    sp_dict = {}

    # t2_trader
    for i, ticker in enumerate(tickers):
        print(f'=== {i+1}/{len(tickers)} ===')

        try:
            sp_dict[ticker] = {}

            sp = stock_price_info(ticker, start_date, today)[['Close', 'RSI_14', 'BBP_20_2.0']]
            date_obj = datetime.strptime(today, "%Y%m%d")
            new_date_obj = date_obj + timedelta(days=10)
            end_day = new_date_obj.strftime("%Y%m%d")
            sp_dict[ticker]['sp'] = sp

            df = scrape_tradingview_data(ticker, today, end_day)
            filtered_df = df[df['Timestamp'].dt.strftime('%Y%m%d') == today]
            sp_dict[ticker]['hourly_sp'] = filtered_df
        except Exception as e:
            print(f'{e} | Error occurred at {ticker}')
            continue    

    return sp_dict

def t_2_t_4_main(tickers, start_date, today, target_year, target_quarter, base_year, base_quarter):

    t_1_trader_report = get_t_1_trader_report(today)
    trader_prompt = get_t_2_t_4_trader_prompts(t_1_trader_report)

    sp_dict = get_hourly_sp(tickers, start_date, today)


    curr_hour = 9
    t_2_trader_response = {}

    while curr_hour < 16:
        t_2_trader_response[curr_hour] = {}

        for i, ticker in enumerate(tickers):
            print(f'=== [{curr_hour}] {i+1}/{len(tickers)} ({ticker}) ===')

            sp = sp_dict[ticker]['sp'] if ticker in sp_dict and 'sp' in sp_dict[ticker] else '역대 가격 정보를 가져올 수 없습니다.'

            # `sp_dict[ticker]['hourly_sp']`이 존재하면 DataFrame을 필터링하여 바인딩
            if ticker in sp_dict and 'hourly_sp' in sp_dict[ticker]:
                df = sp_dict[ticker]['hourly_sp']

                # curr_hour 이전의 데이터만 필터링
                filtered_df = df[df['Timestamp'].dt.hour < curr_hour]

                # 데이터가 존재하면 최신 데이터 가져오기 (Timestamp 기준 가장 최근 값)
                if not filtered_df.empty:
                    hourly_sp = filtered_df  # 가장 최근 데이터 선택
                else:
                    hourly_sp = '해당 시간 이전의 데이터가 없습니다.'
            else:
                hourly_sp = '실시간 정보를 가져올 수 없습니다.'

            price_info = f"""역대 주식 가격: {sp}
            실시간 주식 가격: {hourly_sp}"""

            response = to_GPT(trader_prompt, price_info)['choices'][0]['message']['content']
            t_2_trader_response[curr_hour][ticker] = response

        curr_hour += 1

    to_DB('t_2', f'{today}_t_2_t_4_trader_log', f'{base_quarter}_{base_year}', str(t_2_trader_response))

    pf_weight_prompts = get_pf_weights_prompts(target_year, target_quarter, today, str(t_2_trader_response))
    pf_update_system = pf_weight_prompts['pf_update_system']
    pf_update_prompt = pf_weight_prompts['pf_update_prompt']

    pf_update = to_GPT(pf_update_system, pf_update_prompt)['choices'][0]['message']['content']

    # 파일 경로
    file_path = os.path.join(os.path.join(current_dir, f'./pf_logs/{target_year}_{target_quarter}'), f"{today}_portfolio_weights.json")

    # JSON 파일 저장
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(eval(pf_update), f, indent=2, ensure_ascii=False)

    print(f"포트폴리오 비중 데이터가 {file_path}에 저장되었습니다.")
    to_DB('t_2', f'{today}_t_2_t_4_pf_update', f'{base_quarter}_{base_year}', str(pf_update))