import notion_client
import pandas as pd
import yaml
import os
import sys
import re

#시작 전 세팅

# pipeline 모듈을 찾을 수 있도록 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../pipeline/sub_func")))
from to_gpt import to_GPT

# API 및 DB 설정
def load_api_keys():
    """api_keys.yaml에서 API 키를 로드"""
    config_path = os.path.join(os.path.dirname(__file__), "../config/api_keys.yaml")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

api_keys = load_api_keys()
NOTION_API_KEY = api_keys["api_keys"]["NOTION_API_TOKEN"]
T1_DB_ID = api_keys["DB_IDs"]["t_1"]
T4_DB_ID = api_keys["DB_IDs"]["t_4"]

notion = notion_client.Client(auth=NOTION_API_KEY)

def fetch_specific_notion_data(database_id, titles):
    """노션 데이터베이스에서 특정 제목을 가진 페이지 목록을 가져옴"""
    response = notion.databases.query(database_id)
    results = []

    for page in response["results"]:
        title_property = page["properties"].get("Title", {}).get("title", [])
        if title_property:
            title = title_property[0]["text"]["content"]
            if title in titles:
                results.append(page)

    print("\n🔍 Fetched Notion Pages:", results)  
    return results

def fetch_notion_page_content(page_id):
    """Notion 페이지의 본문 내용을 가져오기"""
    response = notion.blocks.children.list(block_id=page_id)
    content = []

    for block in response["results"]:
        if block["type"] == "paragraph":
            text_content = block["paragraph"]["rich_text"]
            if text_content:
                content.append(text_content[0]["plain_text"])

    full_text = "\n".join(content)
    print("\n📜 Extracted Text from Notion:\n", full_text[:500])  
    return full_text

def extract_stocks_from_text(text):
    """Notion 본문에서 종목 정보를 추출"""
    stock_dict = {}

    pattern_table = r"\|\s*(\d{6})\s*\|\s*(.*?)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+%)\s*\|\s*([\d.]+%)\s*\|\s*([\d,]+)\s*\|\s*(.*?)\s*\|"
    matches_table = re.findall(pattern_table, text)

    print("\nDEBUG: Extracted Stocks (Before Saving)")
    
    for match in matches_table:
        stock_code, company_name, per, pbr, roe, growth, target_price, notes = match
        # 매수/매도 여부 판별
        action = "매수" if "저평가" in notes or "반등" in notes else "매도"

        stock_dict[stock_code] = {
            "종목명": company_name.strip(),
            "PER": float(per),
            "PBR": float(pbr),
            "ROE": roe,
            "이익 성장률": growth,
            "목표가": int(target_price.replace(",", "")),
            "투자포인트": notes.strip(),
            "매수/매도": action
        }

        print(f"📌 종목 코드: {stock_code}, 종목명: {company_name.strip()}")  # 디버깅용

    return stock_dict


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


# 노션에 저장
def save_to_notion(title, content, database_id, period):
    """Notion 데이터베이스에 새로운 페이지를 추가하고 본문을 한글로 채움"""

    new_page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Title": {
                "title": [{"text": {"content": title}}]
            },
            "Period": {
                "rich_text": [{"text": {"content": period}}]
            }
        }
    )

    page_id = new_page["id"]
    notion.blocks.children.append(
        block_id=page_id,
        children=[
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": content[:2000]}}]
                }
            }
        ]
    )

# 메인
def main(year, quarter):
    period = f"{year}_Q{quarter}"  

    pages = fetch_specific_notion_data(T1_DB_ID, [f"{period}_analyst_rp", f"{period}_final_trader_report"])
    all_stocks = {}

    for page in pages:
        stocks = extract_stocks_from_text(fetch_notion_page_content(page["id"]))
        all_stocks.update(stocks)

    trade_log = generate_trade_log(all_stocks)
    save_to_notion(f"{period}_trader_log", trade_log, T4_DB_ID, period)

    analyst_report = analyze_news_combined(all_stocks, year, quarter)
    save_to_notion(f"{period}_analyst_report", analyst_report, T4_DB_ID, period)

if __name__ == "__main__":
    main(2022, 4) # 예시
