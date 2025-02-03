from sub_func import *
import sys
import os
import notion_client

# API 및 DB 설정
def load_api_keys():
    """api_keys.yaml에서 API 키를 로드"""
    config_path = os.path.join(os.path.dirname(__file__), "../config/api_keys.yaml")
    with open(config_path, "r") as file:
        return yaml.safe_load(file)

api_keys = load_api_keys()
NOTION_API_KEY = api_keys["api_keys"]["NOTION_API_TOKEN"]
T1_DB_ID = api_keys["DB_IDs"]["t_1"]
T2_DB_ID = api_keys["DB_IDs"]["t_2"]
T3_DB_ID = api_keys["DB_IDs"]["t_3"]
T4_DB_ID = api_keys["DB_IDs"]["t_4"]
T5_DB_ID = api_keys["DB_IDs"]["t_5"]

notion = notion_client.Client(auth=NOTION_API_KEY)


# def save_final_report(self, final_response: dict) -> None:
#         """최종 포트폴리오 매니저 보고서 저장"""
#         page_title = f"{self.year}_{self.quarter}_analyst_rp"
#         content = self._get_response_content(final_response)
        
#         print(f"{page_title} 보고서를 노션 DB에 저장합니다…")
#         to_DB('t_5', page_title, f"{self.quarter}_{self.year}", content)

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
    print("\n📜 Extracted Text from Notion:\n", full_text)  
    return full_text


def gen_trader(period):
    pages = []
    temp = fetch_specific_notion_data(T1_DB_ID, [f"{period}_final_trader_report"])
    for i in temp:
        pages.append(fetch_notion_page_content(i['id']))

    # temp = fetch_specific_notion_data(T2_DB_ID, [f"{period}_final_trader_report"])
    # for i in temp:
    #     pages.append(fetch_notion_page_content(i['id']))
    pages.append("")

    temp = fetch_specific_notion_data(T4_DB_ID, [f"{period}_trader_log"])
    for i in temp:
        pages.append(fetch_notion_page_content(i['id']))


    system_prompt = """
        당신은 한국 주식 시장 트레이더입니다.
        이전 t1, t2, t4의 트레이더 output을 참조해서 당일 거래 성과 보고서를 작성하세요.
        당일 거래 내역을 리뷰하고 거래에 개선해야 할 점을 작성하세요.
    """

    prompt = f"""
        아래는 당일 주식시장 거래시간 전과 거래시간 때 생성된 주식 트레이더의 레포트와 로그입니다.
        레포트와 로그를 사용해 당일거래성과 보고서를 작성하세요.
        당일거래에 개선할 점 또한 보고서에 포함하세요. 개선할 점을 구체적으로 알려주세요.

        주식시장 거래시간 전 레포트:
        {pages[0]}

        주식시장 거래시간 중 로그:
        T2:
        {pages[1]}
        T3:
        {pages[2]}

        보고서를 Markdown 형식으로 작성하세요.
        보고서는 반드시 주어진 정보에 대한 분석이 필요합니다.
        """

    response = to_GPT(system_prompt, prompt)
    trader_report = response["choices"][0]["message"]["content"]
    print("\n✅ Generated Trade Report:", trader_report)  # 최종 출력 확인
    
    return trader_report

def gen_analyst(period):
    pages = []
    temp = fetch_specific_notion_data(T1_DB_ID, [f"{period}_analyst_rp"])
    for i in temp:
        pages.append(fetch_notion_page_content(i['id']))

    # temp = fetch_specific_notion_data(T2_DB_ID, [f"{period}_analyst_rp"])
    # for i in temp:
    #     pages.append(fetch_notion_page_content(i['id']))
    pages.append("")

    # temp = fetch_specific_notion_data(T3_DB_ID, [f"{period}_analyst_rp"])
    # for i in temp:
    #     pages.append(fetch_notion_page_content(i['id']))
    pages.append("")

    temp = fetch_specific_notion_data(T4_DB_ID, [f"{period}_analyst_report"])
    for i in temp:
        pages.append(fetch_notion_page_content(i['id']))

    system_prompt = """
    당신은 금융 분석가입니다.
    당일 주식시장은 마감을 했습니다. 현재 시장 흐름을 분석하고 내일 시장 흐름을 예측해야합니다. 
    """

    prompt = f"""
    주식시장 거래시간 전과 거래시간 중의 에널리스트 레포트를 참조해서 다음 두 가 작업을 수행하여 결과를 제공합니다:
    1. 오늘 시장 흐름에 대한 요약 보고서를 제공합니다. 요약 보고서는 특징적인 종목 및 섹터를 포함합니다.
    2. 내일 시장 흐름에 대한 예측 보서를 제공합니다. 예측 보고서는 상승 및 하락 할 것 같은 섹터와 이에 따른 대응 방안을 포함합니다.

    ---주식시장 거래시간 전 애널리스트 레포트---
    {pages[0]}

    ---주식시장 거래시간 중 애널리스트 레포트---
    T2:
    {pages[1]}


    T3:
    {pages[2]}

    
    T4:
    {pages[3]}

    보고서를 Markdown 형식으로 작성하세요.
    보고서는 반드시 주어진 정보에 대한 분석이 필요합니다.
    """
    response = to_GPT(system_prompt, prompt)
    analyst_report = response["choices"][0]["message"]["content"]
    print("\n✅ Generated Analyst Report:", analyst_report)

    return analyst_report

def gen_portfolio(trader_report, analyst_report, period):
    pages = []
    temp = fetch_specific_notion_data(T1_DB_ID, [f"{period}_final_portfolio_report"])
    for i in temp:
        pages.append(fetch_notion_page_content(i['id']))


    system_prompt = """
        당신은 주식 포트폴리오를 분석하는 금용 포트폴리오 매니저입니다.
        주식시장 거래시간 이후, 포트폴리오 성과 및 리스크 분석을 하고 주식시장 거래시간 전 포트폴리오와 비교를 합니다. 
    """

    prompt = f"""
    주식시장 거래시간 이후, 포트폴리오 성과 및 리스크 분석을 하고 주식시장 거래시간 전 포트폴리오와 비교를 합니다. 
    주식시장 거래시간 이후 트레이터 레포트와 애널리스트 레포트와 주식시장 거래시간 전 애널리스트 레포트를 참조해 현재 포트폴리오 성과 및 리스크 분석을 합니다.
    주식시장 거래시간 전 포트폴리오와 비교를 해서 전략이 잘 들어맞았는지 평가를 합니다.
    만약, 잘 맞지 않았다면 이에 대한 개선방안을 제안합니다.
    또한, 레포트에 주식시장 거래시간 전 포트폴리오와 주식시장 거래시간 마감 후 변동된 포트폴리오를 기재합니다.

    --트레이더 레포트--
    {trader_report}

    
    --애널리스트 레포트--
    {analyst_report}


    --주식시장 거래시간 전 포트폴리오 레포트--
    {pages[0]}
    

    보고서를 Markdown 형식으로 작성하세요.
    보고서는 반드시 주어진 정보에 대한 분석이 필요합니다.
    """

    response = to_GPT(system_prompt, prompt)
    portfolio_report = response["choices"][0]["message"]["content"]
    print("\n✅ Generated Portfolio Report:", portfolio_report)

    return portfolio_report


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


def main(year, quarter):
    period = f"{year}_Q{quarter}"
    trader_report = gen_trader(period)
    save_to_notion(f"{period}_trader_report", trader_report, T5_DB_ID, period)
    analyst_report = gen_analyst(period)
    save_to_notion(f"{period}_analyst_report", analyst_report, T5_DB_ID, period)
    portfolio_report = gen_portfolio(trader_report, analyst_report, period)
    save_to_notion(f"{period}_portfolio_report", portfolio_report, T5_DB_ID, period)
    
if __name__ == "__main__":
    main(2022, 4) 