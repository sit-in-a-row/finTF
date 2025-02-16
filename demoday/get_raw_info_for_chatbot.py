from chatbot_modules import *
from datetime import datetime, timedelta
import concurrent.futures
import asyncio
import sys

final_system = f"""당신은 전문적인 증권사 애널리스트입니다.
다음 주어진 정보를 보고, 해당 종목에 대해 최종적으로 매수 매도 여부를 결정하는 레포트를 작성하세요.

레포트는 다음 형식을 따라야 합니다.

# 레포트 제목

# 뉴스 분석

# 공시 보고서 분석

# 재무제표 분석

# 주요 재무지표 분석

# 주가 추이 분석

# 결론

** 반드시 Markdown 형식으로 작성해야 합니다. **
** 레포트 외 필요없는 내용은 생성하지 마세요. **
** 분석 타겟 종목에 집중하세요. **
"""

import openai
import os
import yaml

def get_api_key():
    # 현재 파일의 디렉토리 경로 가져오기
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # yaml 파일의 절대 경로 생성
    yaml_path = os.path.join(current_dir, '../config/api_keys.yaml')

    # YAML 파일 읽기
    with open(yaml_path, "r") as file:
        config = yaml.safe_load(file)

    # 필요한 값 가져오기
    api_key = config['api_keys']['open_ai']

    return api_key

# OpenAI API 클라이언트 초기화

client = openai.OpenAI(api_key=get_api_key())

# GPT 호출 함수
def to_GPT(system, prompt):
    # print('Prompt: ', prompt)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000,
        temperature=0.7
    ).to_dict()
    return response

async def get_raw_info_for_chatbot(past_date, today, ticker):
    loop = asyncio.get_event_loop()

    # 동기 함수 실행 (스레드 풀 사용)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_sp = executor.submit(get_stock_prices, past_date, today, ticker)
        # future_dart = executor.submit(get_dart, ticker, past_date)
        fin_statements_ratio = executor.submit(get_fin_statement_naver, ticker)
        future_fin_info = executor.submit(get_fin_info_from_naver, ticker)

        # 비동기 함수 실행 (asyncio.create_task 사용)
        future_news = asyncio.create_task(get_ticker_news(ticker))

        # 결과 수집
        sp = future_sp.result()
        # print('주가데이터 수집 완료')
        # fin_report, fin_statement = future_dart.result()
        fin_infos_crawled = fin_statements_ratio.result()
        # print('재무보고서 및 재무제표 수집 완료')
        fin_info = future_fin_info.result()
        # print('재무지표 수집 완료')
        ticker_news = await future_news  # 비동기 함수 결과 기다리기
        # print('뉴스 정보 수집 완료')

    # return sp, fin_report, fin_statement, ticker_news, fin_info
    # return sp, ticker_news, fin_info
    return sp, fin_infos_crawled, ticker_news, fin_info

async def get_raw_info_for_chatbot_main(user_input):
    # 실행 예시
    ticker = get_stock_code_fuzzy(user_input)
    print(f'분석 목표 티커: {ticker}')

    today = datetime.today().strftime('%Y%m%d')
    past_date = datetime.today() - timedelta(days=90)
    past_date = past_date.strftime('%Y%m%d')

    if ticker:
        result = await get_raw_info_for_chatbot(past_date, today, ticker)

        final_report = to_GPT(final_system + f"\n분석 타겟 종목: {ticker}", str(result))['choices'][0]['message']['content']
        print(final_report)
        return result
    else:
        print('종목명 추출 실패')
        return '종목명 추출 실패'
    
if __name__ == "__main__":
    user_input = sys.argv[1] if len(sys.argv) > 1 else ""
    asyncio.run(get_raw_info_for_chatbot_main(user_input))


