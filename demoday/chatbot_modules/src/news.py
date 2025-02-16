import asyncio
import aiohttp
import json
import asyncio
import aiohttp
import json
import os
import yaml
from .to_gpt import to_GPT

current_dir = os.path.dirname(os.path.abspath(__file__))

summarize_news_system = f"""당신은 증권회사의 리서치센터장입니다.
다음 주어진 월별 뉴스를 보고, 주식 투자에 중요한 내용들을 중심으로 이 내용들을 요약하여 알아보기 쉽게 정리해주세요.
레포트 형식을 따라야 합니다.
"""
final_summarize_news_system = f"""당신은 증권회사의 리서치센터장입니다.
다음 주어진 월별 요약레포트를 보고, 주식 투자에 중요한 내용들을 중심으로 이 내용들을 요약하여 알아보기 쉽게 정리해주세요.
레포트 형식을 따라야 합니다.
"""

def get_api_key():
    yaml_path = os.path.join(current_dir, '../../../config/api_keys.yaml')

    with open(yaml_path, "r") as file:
        config = yaml.safe_load(file)

    api_key = config['api_keys']['open_ai']
    return api_key

# JSON 파일 열기 및 읽기
def read_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        return {}

def classify_news_type_by_day(json_path):
    target_json = read_json(json_path)

    news_by_tickers = {}
    non_tickers_news = []

    for json in target_json:
        try:
            news_ticker_list = json['ticker']
            for news_ticker in news_ticker_list:
                try:
                    if news_ticker not in news_by_tickers:
                        news_by_tickers[news_ticker] = []
                    news_data_without_ticker = {key: value for key, value in json.items() if key != 'ticker'}
                    news_by_tickers[news_ticker].append(news_data_without_ticker)
                except Exception as e:
                    print(f"Error processing ticker {news_ticker}: {e}")
                    pass
        except KeyError:
            non_tickers_news.append(json)

    return {
        'news_by_tickers': news_by_tickers,
        'non_tickers_news': non_tickers_news
    }

def get_corp_rel_naver_news(ticker):
    news_base_path = os.path.join(current_dir, '../news')
    years = os.listdir(news_base_path)

    final_news_by_tickers = {}
    final_non_tickers_news = {}

    for year in years:
        months_path = os.path.join(news_base_path, year)
        months = os.listdir(months_path)

        final_news_by_tickers[year] = {}
        final_non_tickers_news[year] = {}

        for month in months:
            jsons_list_path = os.path.join(months_path, month)
            jsons_list = os.listdir(jsons_list_path)

            final_news_by_tickers[year][month] = {}
            final_non_tickers_news[year][month] = {}

            for json_path in jsons_list:
                json_path = os.path.join(jsons_list_path, json_path)
                classified_news_dict = classify_news_type_by_day(json_path)

                # 비티커 뉴스 카테고리화
                try:
                    final_non_tickers_news[year][month]['non_tickers_news'] = classified_news_dict['non_tickers_news']
                except:
                    continue

                # 종목별 뉴스 카테고리화
                if ticker in classified_news_dict['news_by_tickers']:
                    final_news_by_tickers[year][month][ticker] = classified_news_dict['news_by_tickers'][ticker]
                else:
                    final_news_by_tickers[year][month][ticker] = f'이 종목에 대한 {json_path}날짜의 기사가 존재하지 않습니다.'
                
                # 비티커 뉴스 카테고리화 (non_tickers_news도 종목별로 정리)
                for news_item in classified_news_dict['non_tickers_news']:
                    # 예시로, 비티커 뉴스의 카테고리화 (키를 'no_ticker'로 설정)
                    final_non_tickers_news[year][month].setdefault('no_ticker', []).append(news_item)
            
    return {
        'final_news_by_tickers': final_news_by_tickers,
        'final_non_tickers_news': final_non_tickers_news
    }

# 비동기적으로 여러 요청을 처리하는 함수
async def process_news_by_month(news_by_tickers_dict, ticker):
    async with aiohttp.ClientSession() as session:
        tasks = []
        # GPT API 요청을 병렬로 추가
        for year in news_by_tickers_dict:
            for month in news_by_tickers_dict[year]:
                target_news_info = str(news_by_tickers_dict[year][month])
                summarize_ticker_news_prompt = f"다음 종목에 대한 뉴스입니다. {ticker}\n{target_news_info}"
                
                task = asyncio.ensure_future(
                    async_to_GPT(session, summarize_news_system, summarize_ticker_news_prompt)
                )
                tasks.append(task)
        
        # 요청이 모두 끝날 때까지 대기
        responses = await asyncio.gather(*tasks)
        return responses

# GPT 호출을 위한 비동기 함수
async def async_to_GPT(session, system, prompt):
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {get_api_key()}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-4o-mini',
        'messages': [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        'max_tokens': 3000,
        'temperature': 0.7
    }
    
    async with session.post(url, headers=headers, json=data) as response:
        response_data = await response.json()
        return response_data['choices'][0]['message']['content']

# 비동기적으로 여러 요청을 처리하는 함수
async def process_news_by_month(news_by_tickers_dict, ticker):
    async with aiohttp.ClientSession() as session:
        tasks = []
        # GPT API 요청을 병렬로 추가
        for year in news_by_tickers_dict:
            for month in news_by_tickers_dict[year]:
                target_news_info = str(news_by_tickers_dict[year][month])
                summarize_ticker_news_prompt = f"다음 종목에 대한 뉴스입니다. {ticker}\n{target_news_info}"
                
                task = asyncio.ensure_future(
                    async_to_GPT(session, summarize_news_system, summarize_ticker_news_prompt)
                )
                tasks.append(task)
        
        # 요청이 모두 끝날 때까지 대기
        responses = await asyncio.gather(*tasks)
        return responses

# Jupyter 환경에서 asyncio 실행
async def get_ticker_news(ticker):
    news_by_tickers_dict = get_corp_rel_naver_news(ticker)['final_news_by_tickers']
    
    # 비동기 함수 호출
    responses = await process_news_by_month(news_by_tickers_dict, ticker)
    
    # for idx, response in enumerate(responses):
    #     print(f"Response {idx + 1}: {response}")

    final_response = to_GPT(final_summarize_news_system, str(responses))['choices'][0]['message']['content']

    return final_response